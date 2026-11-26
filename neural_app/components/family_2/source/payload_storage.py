"""Lossless, content-addressed storage for large telemetry and audit text.

No retention limit, dropped samples, truncated text, or changes to inference.
Small indexed fields remain ordinary SQLite values. Large payloads reference
shared compressed chunks; the database row factory restores the exact text.
"""
import hashlib
import re
import sqlite3
import zlib
from collections import OrderedDict
MAGIC = b'\x00FLUX:CHUNKS:2\x00'
ANCHOR = re.compile(b'(?:,\\s*|\\{\\s*)"[^"\\\\\\r\\n]{1,80}"\\s*:|\\n')
PAYLOAD_COLUMNS = {'pipeline_jobs': {'input_json', 'context_json', 'result_json'}, 'history_blocks': {'content'}, 'observatory_receipts': {'input_json', 'result_json'}, 'node_events': {'before_json', 'after_json'}, 'execution_ledger': {'detail'}, 'live_audit_results': {'result_json'}, 'mesh_control': {'settings_json'}, 'mesh_outbox': {'packet_json', 'result_json'}, 'mesh_receipts': {'payload_json'}, 'mesh_attempts': {'result_json'}, 'unified_results': {'result_json'}, 'platform_alignment_results': {'result_json'}, 'karmic_welfare_results': {'result_json'}, 'virtue_text_results': {'result_json'}, 'souls_ingress_results': {'result_json'}, 'reference_results': {'result_json'}}

def chunks(raw):
    start = 0
    for match in ANCHOR.finditer(raw):
        position = match.start()
        while position - start > 16384:
            yield raw[start:start + 8192]
            start += 8192
        if position - start >= 1024 and (position - start >= 8192 or zlib.crc32(match[0]) & 7 == 0):
            yield raw[start:position]
            start = position
    while len(raw) - start > 16384:
        yield raw[start:start + 8192]
        start += 8192
    if start < len(raw):
        yield raw[start:]

class StoredConnection(sqlite3.Connection):

    def ensure_payload_store(self):
        if not getattr(self, '_payload_ready', False):
            self.execute('CREATE TABLE IF NOT EXISTS _flux_chunks (digest BLOB PRIMARY KEY, data BLOB NOT NULL, raw_size INTEGER NOT NULL) WITHOUT ROWID')
            self.execute('CREATE TABLE IF NOT EXISTS _flux_manifests (digest BLOB PRIMARY KEY, refs BLOB NOT NULL) WITHOUT ROWID')
            self._payload_ready = True

def pack_text(conn, value):
    if not isinstance(value, str) or len(value) < 512:
        return value
    raw = value.encode('utf-8')
    conn.ensure_payload_store()
    whole_digest = hashlib.sha256(raw).digest()
    if conn.execute('SELECT 1 FROM _flux_manifests WHERE digest=?', (whole_digest,)).fetchone():
        return MAGIC + whole_digest
    references = []
    cache = getattr(conn, '_packed_cache', None)
    if cache is None:
        cache = conn._packed_cache = OrderedDict()
    entries = {}
    for chunk in chunks(raw):
        digest = hashlib.sha256(chunk).digest()
        references.append(digest)
        if digest not in entries:
            compressed = cache.get(digest)
            if compressed is None:
                compressed = zlib.compress(chunk, 6)
                cache[digest] = compressed
                if len(cache) > 4096:
                    cache.popitem(last=False)
            else:
                cache.move_to_end(digest)
            entries[digest] = (digest, compressed, len(chunk))
    conn.executemany('INSERT OR IGNORE INTO _flux_chunks VALUES (?,?,?)', entries.values())
    conn.execute('INSERT OR IGNORE INTO _flux_manifests VALUES (?,?)', (whole_digest, b''.join(references)))
    return MAGIC + whole_digest

def unpack_text(conn, value):
    if not isinstance(value, bytes) or not value.startswith(MAGIC):
        return value
    body = value[len(MAGIC):]
    if len(body) != 32:
        raise sqlite3.DatabaseError('Invalid Flux payload reference')
    cursor = conn.cursor()
    cursor.row_factory = None
    manifest = cursor.execute('SELECT refs FROM _flux_manifests WHERE digest=?', (body,)).fetchone()
    if manifest is None or not manifest[0] or len(manifest[0]) % 32:
        raise sqlite3.DatabaseError('Missing or invalid Flux payload manifest')
    references = manifest[0]
    cache = getattr(conn, '_payload_cache', None)
    if cache is None:
        cache = conn._payload_cache = OrderedDict()
    pieces = []
    for offset in range(0, len(references), 32):
        digest = references[offset:offset + 32]
        chunk = cache.get(digest)
        if chunk is None:
            cursor = conn.cursor()
            cursor.row_factory = None
            record = cursor.execute('SELECT data,raw_size FROM _flux_chunks WHERE digest=?', (digest,)).fetchone()
            if record is None:
                raise sqlite3.DatabaseError('Missing Flux payload chunk')
            chunk = zlib.decompress(record[0])
            if len(chunk) != record[1] or hashlib.sha256(chunk).digest() != digest:
                raise sqlite3.DatabaseError('Flux payload integrity check failed')
            cache[digest] = chunk
            if len(cache) > 512:
                cache.popitem(last=False)
        else:
            cache.move_to_end(digest)
        pieces.append(chunk)
    raw = b''.join(pieces)
    if hashlib.sha256(raw).digest() != body:
        raise sqlite3.DatabaseError('Flux payload text integrity check failed')
    return raw.decode('utf-8')

def decoded_row(cursor, values):
    return sqlite3.Row(cursor, tuple((unpack_text(cursor.connection, value) for value in values)))
