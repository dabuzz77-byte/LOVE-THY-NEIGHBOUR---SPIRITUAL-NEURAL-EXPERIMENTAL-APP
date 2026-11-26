"""Offline lossless compaction. Close Flux Bus before using this utility.

Copies every row and rowid, verifies hashes of all decoded values, checks
SQLite integrity, and only then replaces the original database. No pruning.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import struct
import time
from ..source.payload_storage import StoredConnection, decoded_row, pack_text, PAYLOAD_COLUMNS

def quoted(name):
    return '"' + name.replace('"', '""') + '"'

def row_hash(digest, row):
    for value in row:
        if value is None:
            data = b'n'
        elif isinstance(value, bytes):
            data = b'b' + value
        elif isinstance(value, float):
            data = b'f' + struct.pack('!d', value)
        else:
            data = (('i' if isinstance(value, int) else 's') + str(value)).encode('utf-8')
        digest.update(struct.pack('!Q', len(data)))
        digest.update(data)

def compact_database(path, progress=None, resume=False):
    path = Path(path).resolve(strict=True)
    temporary = path.with_name(path.name + '.compacting')
    previous = path.with_name(path.name + '.precompact')
    if previous.exists() or (temporary.exists() and (not resume)):
        raise FileExistsError('A previous compaction file exists; inspect it before retrying')
    if resume and (not temporary.exists()):
        raise FileNotFoundError('No temporary compaction exists to resume')
    report = {'path': str(path), 'before_bytes': path.stat().st_size, 'tables': {}, 'started_at': time.time()}
    source = target = None
    try:
        source = sqlite3.connect(str(path), timeout=5, factory=StoredConnection)
        source.row_factory = decoded_row
        if source.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0]:
            raise RuntimeError('Database is in use; close Flux Bus before compaction')
        source.execute('BEGIN IMMEDIATE')
        schema = source.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' AND name NOT IN ('_flux_chunks','_flux_manifests') ORDER BY type,name").fetchall()
        target = sqlite3.connect(str(temporary), factory=StoredConnection)
        target.row_factory = decoded_row
        if resume and [r[0] for r in target.execute('PRAGMA quick_check')] != ['ok']:
            raise RuntimeError('Temporary database is damaged; the original has not been changed')
        target.execute('PRAGMA journal_mode=OFF')
        target.execute('PRAGMA synchronous=OFF')
        target.execute('PRAGMA cache_size=-65536')
        target.execute('PRAGMA temp_store=MEMORY')
        expected_names = {name for kind, name, sql in schema if kind == 'table'}
        existing_names = {r[0] for r in target.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if existing_names - expected_names - {'sqlite_sequence', '_flux_chunks', '_flux_manifests'}:
            raise RuntimeError('Unexpected tables in temporary database')
        for kind, name, sql in schema:
            if kind == 'table':
                existing = target.execute('SELECT sql FROM sqlite_master WHERE type=? AND name=?', (kind, name)).fetchone()
                if existing and existing[0] != sql:
                    raise RuntimeError('Temporary schema differs for ' + name)
                if not existing:
                    target.execute(sql)
        target.commit()
        for kind, name, sql in schema:
            if kind != 'table':
                continue
            columns = [r[1] for r in source.execute('PRAGMA table_info(' + quoted(name) + ')')]
            has_rowid = 'WITHOUT ROWID' not in sql.upper()
            selection = ('rowid,' if has_rowid else '') + ','.join(map(quoted, columns))
            order = 'rowid' if has_rowid else ','.join(map(quoted, columns))
            query = f'SELECT {selection} FROM {quoted(name)} ORDER BY {order}'
            insert_columns = (['rowid'] if has_rowid else []) + columns
            statement = f"INSERT INTO {quoted(name)} ({','.join(map(quoted, insert_columns))}) VALUES ({','.join(('?' for _ in insert_columns))})"
            payloads = PAYLOAD_COLUMNS.get(name, set())
            expected = hashlib.sha256()
            count = 0
            already_copied = target.execute(f'SELECT COUNT(*) FROM {quoted(name)}').fetchone()[0]
            if progress and already_copied:
                progress({'table': name, 'resuming_rows': already_copied})
            cursor = source.execute(query)
            while (batch := cursor.fetchmany(100)):
                for row in batch:
                    row_hash(expected, row)
                    count += 1
                    if count > already_copied:
                        values = [pack_text(target, value) if col in payloads else value for col, value in zip(insert_columns, row)]
                        target.execute(statement, values)
                target.commit()
                if progress and count % 1000 == 0:
                    progress({'table': name, 'copied': count, 'output_bytes': temporary.stat().st_size})
            actual = hashlib.sha256()
            verified = 0
            for row in target.execute(query):
                row_hash(actual, row)
                verified += 1
            if verified != count or actual.digest() != expected.digest():
                raise RuntimeError('Lossless verification failed for ' + name)
            report['tables'][name] = {'rows': count, 'sha256': actual.hexdigest(), 'all_values_verified': True}
            if progress:
                progress({'table': name, 'verified': count, 'output_bytes': temporary.stat().st_size})
        if source.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_sequence'").fetchone():
            target.execute('DELETE FROM sqlite_sequence')
            target.executemany('INSERT INTO sqlite_sequence VALUES (?,?)', source.execute('SELECT name,seq FROM sqlite_sequence'))
        for kind, name, sql in schema:
            if kind != 'table':
                existing = target.execute('SELECT sql FROM sqlite_master WHERE type=? AND name=?', (kind, name)).fetchone()
                if existing and existing[0] != sql:
                    raise RuntimeError('Temporary schema differs for ' + name)
                if not existing:
                    target.execute(sql)
        target.commit()
        if [r[0] for r in target.execute('PRAGMA integrity_check')] != ['ok']:
            raise RuntimeError('Compacted database failed SQLite integrity check')
        report['integrity_check'] = 'ok'
        target.execute('PRAGMA journal_mode=DELETE')
        target.execute('PRAGMA synchronous=FULL')
        target.close()
        target = None
        with temporary.open('r+b') as file:
            os.fsync(file.fileno())
        source.rollback()
        source.close()
        source = None
        path.replace(previous)
        try:
            temporary.replace(path)
        except BaseException:
            previous.replace(path)
            raise
        report['after_bytes'] = path.stat().st_size
        report['recovered_bytes'] = report['before_bytes'] - report['after_bytes']
        report['elapsed_seconds'] = round(time.time() - report['started_at'], 2)
        path.with_suffix(path.suffix + '.storage-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        previous.unlink()
        return report
    finally:
        if target is not None:
            target.close()
        if source is not None:
            source.close()
