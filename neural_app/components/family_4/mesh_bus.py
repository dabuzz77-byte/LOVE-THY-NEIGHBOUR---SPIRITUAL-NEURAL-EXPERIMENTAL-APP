"""Authenticated loopback pub/sub with durable messages, cursors and receipts."""
from __future__ import annotations
import dataclasses
from contextlib import contextmanager
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
from neural_app import section_threads as threading
import time
import uuid
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
MAX_BYTES = 262144
COMPRESSED = b'HMSZ1\x00'

def plain(value):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    raise TypeError(type(value).__name__)

def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, default=plain).encode('utf-8')

class Ledger:

    def __init__(self, path, max_storage_mb=64, max_messages=4000, max_age_hours=24):
        self.path = str(path)
        self.lock = threading.RLock()
        self.max_bytes = max(1, int(max_storage_mb)) * 1024 * 1024
        self.payload_budget = int(self.max_bytes * 0.42)
        self.max_messages = max(10, int(max_messages))
        self.max_age = max(60, float(max_age_hours) * 3600)
        self.next_maintenance = 0
        self._advance_count = 0
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('PRAGMA journal_mode=WAL;\n            CREATE TABLE IF NOT EXISTS messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE,body TEXT,created REAL);\n            CREATE TABLE IF NOT EXISTS receipts(client TEXT,id TEXT,status TEXT,created REAL,PRIMARY KEY(client,id));\n            CREATE TABLE IF NOT EXISTS cursors(client TEXT PRIMARY KEY,seq INTEGER);\n            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);\n            CREATE TABLE IF NOT EXISTS storage_meta(id INTEGER PRIMARY KEY CHECK(id=1),payload_bytes INTEGER,pruned INTEGER);\n            CREATE INDEX IF NOT EXISTS messages_created ON messages(created);\n            ')
            columns = {r[1] for r in db.execute('PRAGMA table_info(messages)')}
            if 'stored_bytes' not in columns:
                db.execute('ALTER TABLE messages ADD COLUMN stored_bytes INTEGER NOT NULL DEFAULT 0')
            newest = db.execute('SELECT seq,length(CAST(body AS BLOB)) FROM messages ORDER BY seq DESC LIMIT ?', (self.max_messages,)).fetchall()
            size = 0
            cutoff = None
            for seq, n in newest:
                if size + n > self.payload_budget:
                    break
                size += n
                cutoff = seq
            if cutoff is None:
                cutoff = self._highwater(db) + 1
            while True:
                deleted = db.execute('DELETE FROM messages WHERE seq IN (SELECT seq FROM messages WHERE seq<? LIMIT 128)', (cutoff,)).rowcount
                db.commit()
                if not deleted:
                    break
                db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            db.execute('UPDATE messages SET stored_bytes=length(CAST(body AS BLOB)) WHERE stored_bytes=0')
            total = db.execute('SELECT COALESCE(SUM(stored_bytes),0) FROM messages').fetchone()[0]
            db.execute('INSERT INTO storage_meta VALUES(1,?,0) ON CONFLICT(id) DO UPDATE SET payload_bytes=excluded.payload_bytes', (total,))
            db.commit()
            if db.execute('PRAGMA auto_vacuum').fetchone()[0] != 2 or Path(self.path).stat().st_size > self.max_bytes:
                db.execute('PRAGMA auto_vacuum=INCREMENTAL')
                db.execute('VACUUM')
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            self._latest = self._highwater(db)
        db.close()
        self.maintenance(force=True)

    @staticmethod
    def _highwater(db):
        row = db.execute("SELECT seq FROM sqlite_sequence WHERE name='messages'").fetchone()
        return row[0] if row else 0

    @staticmethod
    def unpack(body):
        if isinstance(body, bytes) and body.startswith(COMPRESSED):
            decoder = zlib.decompressobj()
            body = decoder.decompress(body[len(COMPRESSED):], MAX_BYTES + 1)
            if len(body) > MAX_BYTES or not decoder.eof:
                raise ValueError('Stored message exceeds its size limit')
        return json.loads(body)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute('PRAGMA synchronous=NORMAL')
        db.execute('PRAGMA wal_autocheckpoint=256')
        db.execute('PRAGMA journal_size_limit=4194304')
        page_size = db.execute('PRAGMA page_size').fetchone()[0]
        db.execute('PRAGMA max_page_count=' + str(max(256, self.max_bytes // page_size)))
        try:
            with db:
                yield db
        finally:
            db.close()

    def latest(self):
        return self._latest

    def _trim(self, db, extra=0):
        total = db.execute('SELECT payload_bytes FROM storage_meta WHERE id=1').fetchone()[0]
        count = db.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
        cutoff = time.time() - self.max_age
        removed = 0
        while total + extra > self.payload_budget or count >= self.max_messages:
            rows = db.execute('SELECT seq,stored_bytes FROM messages ORDER BY seq LIMIT 64').fetchall()
            if not rows:
                break
            db.execute('DELETE FROM messages WHERE seq<=?', (rows[-1][0],))
            total -= sum((r[1] for r in rows))
            count -= len(rows)
            removed += len(rows)
        expired = db.execute('SELECT COALESCE(SUM(stored_bytes),0),COUNT(*) FROM messages WHERE created<?', (cutoff,)).fetchone()
        if expired[1]:
            db.execute('DELETE FROM messages WHERE created<?', (cutoff,))
            total -= expired[0]
            removed += expired[1]
        db.execute('UPDATE storage_meta SET payload_bytes=?,pruned=pruned+? WHERE id=1', (max(0, total), removed))
        if removed:
            db.execute('DELETE FROM receipts WHERE id NOT IN (SELECT id FROM messages)')

    def maintenance(self, force=False, compact=False):
        if not force and time.monotonic() < self.next_maintenance:
            return
        with self.lock:
            with self.db() as db:
                self._trim(db)
                db.execute('DELETE FROM receipts WHERE rowid NOT IN (SELECT rowid FROM receipts ORDER BY rowid DESC LIMIT 10000)')
                db.execute("DELETE FROM cursors WHERE rowid NOT IN (SELECT rowid FROM cursors ORDER BY rowid DESC LIMIT 256) AND client NOT IN ('hydrogen.engine','bridge:fluxbus','bridge:observatory')")
            with self.db() as db:
                db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
                db.execute('PRAGMA incremental_vacuum(256)')
            if compact:
                with self.db() as db:
                    db.execute('VACUUM')
            self.next_maintenance = time.monotonic() + 60

    def publish(self, msg):
        if not isinstance(msg, dict):
            raise ValueError('Message must be an object')
        if not isinstance(msg.get('topic'), str) or not 1 <= len(msg['topic']) <= 120:
            raise ValueError('Topic required, up to 120 characters')
        route = msg.get('route', [])
        if not isinstance(route, list) or len(route) > 12 or any((not isinstance(x, str) or len(x) > 120 for x in route)):
            raise ValueError('Invalid route')
        identity = msg.get('id') or uuid.uuid4().hex
        if not isinstance(identity, str) or len(identity) > 160:
            raise ValueError('Invalid message ID')
        for key in ('source', 'target'):
            if not isinstance(msg.get(key, '*'), str) or len(msg.get(key, '*')) > 120:
                raise ValueError('Invalid ' + key)
        if msg.get('reply_to') is not None and (not isinstance(msg['reply_to'], str) or len(msg['reply_to']) > 120):
            raise ValueError('Invalid reply_to')
        event = dict(id=identity, topic=msg['topic'], source=msg.get('source', 'application'), target=msg.get('target', '*'), data=msg.get('data'), route=route, reply_to=msg.get('reply_to'), time=time.time())
        raw = encoded(event)
        if len(raw) > MAX_BYTES:
            raise ValueError('Message exceeds 256 KiB; split it into chunks')
        body = raw.decode()
        stored = len(raw)
        if len(raw) > 2048:
            compressed = COMPRESSED + zlib.compress(raw, level=1)
            if len(compressed) < len(raw) * 0.9:
                body = compressed
                stored = len(compressed)
        if stored > self.payload_budget:
            raise ValueError('Message exceeds the configured history storage budget')
        with self.lock, self.db() as db:
            row = db.execute('SELECT seq,body FROM messages WHERE id=?', (identity,)).fetchone()
            if row:
                old = self.unpack(row[1])
                comparison = {k: v for k, v in event.items() if k != 'time'}
                if {k: v for k, v in old.items() if k != 'time'} != comparison:
                    raise ValueError('Message ID reused with different content')
                return dict(accepted=True, duplicate=True, seq=row[0], id=identity)
            self._trim(db, extra=stored)
            cursor = db.execute('INSERT INTO messages(id,body,created,stored_bytes) VALUES(?,?,?,?)', (identity, body, time.time(), stored))
            db.execute('UPDATE storage_meta SET payload_bytes=payload_bytes+? WHERE id=1', (stored,))
            self._latest = cursor.lastrowid
            return dict(accepted=True, duplicate=False, seq=cursor.lastrowid, id=identity)

    def read(self, after=0, limit=100):
        if int(after) >= self._latest:
            return []
        with self.db() as db:
            rows = db.execute('SELECT seq,body FROM messages WHERE seq>? ORDER BY seq LIMIT ?', (int(after), min(100, max(1, int(limit))))).fetchall()
        result = []
        used = 0
        for seq, body in rows:
            event = dict(self.unpack(body), seq=seq)
            result.append(event)
            used += MAX_BYTES if isinstance(body, bytes) else len(body.encode('utf-8'))
            if used >= 1048576:
                break
        return result

    def find(self, identity):
        with self.db() as db:
            row = db.execute('SELECT body FROM messages WHERE id=?', (identity,)).fetchone()
        return self.unpack(row[0]) if row else None

    def cursor(self, client, initial=0):
        with self.lock, self.db() as db:
            db.execute('INSERT OR IGNORE INTO cursors VALUES(?,?)', (client, initial))
            return db.execute('SELECT seq FROM cursors WHERE client=?', (client,)).fetchone()[0]

    def advance(self, client, seq, identity=None, status='handled'):
        with self.lock, self.db() as db:
            db.execute('INSERT INTO cursors VALUES(?,?) ON CONFLICT(client) DO UPDATE SET seq=MAX(seq,excluded.seq)', (client, seq))
            if identity:
                db.execute('INSERT OR REPLACE INTO receipts VALUES(?,?,?,?)', (client, identity, status, time.time()))
            self._advance_count += 1
            if self._advance_count % 128 == 0:
                db.execute('DELETE FROM receipts WHERE rowid NOT IN (SELECT rowid FROM receipts ORDER BY rowid DESC LIMIT 10000)')

    def setting(self, key, value=None, default=None):
        with self.lock, self.db() as db:
            if value is not None:
                db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)', (key, json.dumps(value)))
                return value
            row = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
            return json.loads(row[0]) if row else default

    def stats(self):
        with self.db() as db:
            first, count = db.execute('SELECT MIN(seq),COUNT(*) FROM messages').fetchone()
            payload, pruned = db.execute('SELECT payload_bytes,pruned FROM storage_meta WHERE id=1').fetchone()
            disk = sum((p.stat().st_size for p in (Path(self.path), Path(self.path + '-wal'), Path(self.path + '-shm')) if p.exists()))
            return dict(messages=self._highwater(db), retained=count, history_start=first or self._highwater(db) + 1, receipts=db.execute('SELECT COUNT(*) FROM receipts').fetchone()[0], storage=dict(disk_bytes=disk, database_limit_bytes=self.max_bytes, payload_bytes=payload, retention_messages=self.max_messages, retention_hours=self.max_age / 3600, pruned_messages=pruned), clients=[dict(name=r[0], cursor=r[1]) for r in db.execute('SELECT client,seq FROM cursors')])

class BusServer:

    def __init__(self, data_dir, port=8794, broadcast_port=8796, storage=None):
        self.data = Path(data_dir)
        self.data.mkdir(parents=True, exist_ok=True)
        from .data_lock import DataLock
        self.instance_lock = DataLock(self.data / 'runtime.lock')
        try:
            self._initialize(port, broadcast_port, storage)
        except Exception:
            self.instance_lock.close()
            raise

    def _initialize(self, port, broadcast_port, storage):
        self.ledger = Ledger(self.data / 'mesh.sqlite3', **storage or {})
        token_path = self.data / 'token.txt'
        if not token_path.exists():
            token_path.write_text(secrets.token_urlsafe(32))
        self.token = token_path.read_text().strip()
        owner = self

        class Handler(BaseHTTPRequestHandler):

            def log_message(self, *args):
                pass

            def send(self, status, data):
                raw = encoded(data)
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def authorized(self):
                return hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + owner.token)

            def do_GET(self):
                if not self.authorized():
                    return self.send(401, {'error': 'Authentication required'})
                try:
                    parsed = urlsplit(self.path)
                    q = parse_qs(parsed.query)
                    if parsed.path == '/events':
                        return self.send(200, {'events': owner.ledger.read(int(q.get('after', ['0'])[0]))})
                    if parsed.path == '/inbox':
                        name = q.get('client', [''])[0]
                        events = owner.ledger.read(int(q.get('after', ['0'])[0]))
                        cursor = events[-1]['seq'] if events else int(q.get('after', ['0'])[0])
                        selected = [e for e in events if e['source'] != name and (name not in e['route'] or e.get('reply_to') == name or e['target'] == name) and (e['target'] in ('*', name))]
                        return self.send(200, dict(cursor=cursor, events=selected))
                    if parsed.path == '/status':
                        return self.send(200, dict(owner.ledger.stats(), transport=dict(host='127.0.0.1', http_port=owner.port, udp_port=owner.udp.port, broadcast_port=owner.udp.broadcast_port, udp_received=owner.udp.received, udp_datagrams_sent=owner.udp.sent, udp_errors=owner.udp.errors)))
                    return self.send(404, {'error': 'Not found'})
                except (ValueError, TypeError) as e:
                    self.send(400, {'error': str(e)})

            def do_POST(self):
                if not self.authorized():
                    return self.send(401, {'error': 'Authentication required'})
                try:
                    n = int(self.headers.get('Content-Length', '0'))
                    if not 0 < n <= MAX_BYTES:
                        return self.send(413, {'error': 'Body must fit 256 KiB'})
                    msg = json.loads(self.rfile.read(n))
                    if self.path == '/publish':
                        return self.send(200, owner.ledger.publish(msg))
                    if self.path == '/receipt':
                        owner.ledger.advance(str(msg['client'])[:120], int(msg['seq']), str(msg['id'])[:160], str(msg.get('status', 'handled'))[:120])
                        return self.send(200, {'accepted': True})
                    return self.send(404, {'error': 'Not found'})
                except (ValueError, TypeError, KeyError) as e:
                    self.send(400, {'error': str(e)})
        self.http = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.http.daemon_threads = True
        self.port = self.http.server_address[1]
        from .udp_port import UDPPort
        try:
            self.udp = UDPPort(self.ledger, self.token, self.port, broadcast_port)
        except Exception:
            self.http.server_close()
            raise
        self.connection = self.data / 'connection.json'
        self.connection.write_text(json.dumps(dict(url=f'http://127.0.0.1:{self.port}', token=self.token, udp_host='127.0.0.1', udp_port=self.udp.port, broadcast_port=self.udp.broadcast_port)), encoding='utf-8')
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        try:
            self.udp.close()
            self.http.shutdown()
            self.http.server_close()
            self.thread.join(timeout=2)
        finally:
            self.instance_lock.close()
