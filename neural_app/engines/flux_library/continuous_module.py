"""Durable independent workers over the shared input ledger."""
from copy import deepcopy
import json
import re
import threading
import time
from .hub import database
from .live_audit import utc_now
from .payload_storage import pack_text

class ContinuousInputModule:
    prefix = None
    engine_names = ()
    worker_name = 'Input engines'

    def __init__(self, db_path):
        if not isinstance(self.prefix, str) or not re.fullmatch('[a-z_]+', self.prefix):
            raise ValueError('A fixed module table prefix is required')
        self.db_path = str(db_path)
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.thread = None
        self.latest = {}
        self.error = ''
        self.active_job = None
        self.control = self.prefix + '_control'
        self.results = self.prefix + '_results'
        self.requests = self.prefix + '_requests'
        self.MANUAL_SQL = f'SELECT p.rowid AS sequence,p.id,p.source,p.fingerprint,p.input_json FROM {self.requests} r CROSS JOIN pipeline_jobs p ON p.id=r.job_id ORDER BY r.rowid LIMIT 1'
        self.NEXT_SQL = f'SELECT rowid AS sequence,id,source,fingerprint,input_json FROM pipeline_jobs WHERE rowid>(SELECT cursor FROM {self.control} WHERE id=1) ORDER BY rowid LIMIT 1'
        with database(self.db_path) as conn:
            conn.execute(f'CREATE TABLE IF NOT EXISTS {self.control}(id INTEGER PRIMARY KEY CHECK(id=1),enabled INTEGER NOT NULL,cursor INTEGER NOT NULL)')
            cursor = conn.execute('SELECT COALESCE(MAX(rowid),0) FROM pipeline_jobs').fetchone()[0]
            conn.execute(f'INSERT OR IGNORE INTO {self.control} VALUES(1,1,?)', (cursor,))
            conn.execute(f'CREATE TABLE IF NOT EXISTS {self.results}(job_id TEXT PRIMARY KEY,source TEXT NOT NULL,status TEXT NOT NULL,created_at REAL NOT NULL,result_json TEXT NOT NULL)')
            conn.execute(f'CREATE INDEX IF NOT EXISTS {self.prefix}_recent ON {self.results}(created_at DESC)')
            conn.execute(f'CREATE TABLE IF NOT EXISTS {self.requests}(job_id TEXT PRIMARY KEY)')
            self.enabled = bool(conn.execute(f'SELECT enabled FROM {self.control} WHERE id=1').fetchone()[0])
            row = conn.execute(f'SELECT result_json FROM {self.results} ORDER BY created_at DESC LIMIT 1').fetchone()
            if row:
                self.latest = self.summary(json.loads(row[0]))

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._loop, name=self.worker_name, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=12)

    def set_enabled(self, value):
        with self.lock, database(self.db_path) as conn:
            conn.execute(f'UPDATE {self.control} SET enabled=? WHERE id=1', (int(bool(value)),))
            self.enabled = bool(value)
        self.wake.set()

    def request(self, job_id):
        with database(self.db_path) as conn:
            if not conn.execute('SELECT 1 FROM pipeline_jobs WHERE id=?', (job_id,)).fetchone():
                raise ValueError('Input was not found')
            conn.execute(f'INSERT OR IGNORE INTO {self.requests} VALUES(?)', (job_id,))
        self.wake.set()

    def snapshot(self):
        with self.lock:
            return {'enabled': self.enabled, 'running': bool(self.thread and self.thread.is_alive()), 'active_job': self.active_job, 'latest': deepcopy(self.latest), 'error': self.error, 'engine_count': len(self.engine_names)}

    def history(self):
        with database(self.db_path) as conn:
            return [dict(r) for r in conn.execute(f'SELECT job_id,source,status,created_at FROM {self.results} ORDER BY created_at DESC LIMIT 100')]

    def detail(self, job_id):
        with database(self.db_path) as conn:
            row = conn.execute(f'SELECT result_json FROM {self.results} WHERE job_id=?', (job_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def ready(self, job_id):
        with database(self.db_path) as conn:
            return bool(conn.execute(f'SELECT 1 FROM {self.results} WHERE job_id=?', (job_id,)).fetchone())

    def process_next(self):
        with self.lock, database(self.db_path) as conn:
            manual = conn.execute(self.MANUAL_SQL).fetchone()
            row = manual or (conn.execute(self.NEXT_SQL).fetchone() if self.enabled else None)
            if row is None:
                return False
            self.active_job = row['id']
            existing = conn.execute(f'SELECT result_json FROM {self.results} WHERE job_id=?', (row['id'],)).fetchone()
        try:
            if existing:
                result = json.loads(existing[0])
            else:
                try:
                    result = self.execute(json.loads(row['input_json']), self.stop_event)
                except InterruptedError:
                    return False
                except Exception as error:
                    result = {'status': 'ERROR', 'error': str(error), 'timestamp': utc_now(), 'stages': []}
                result.update(job_id=row['id'], source=row['source'], input_fingerprint=row['fingerprint'])
            with database(self.db_path) as conn:
                conn.execute('BEGIN IMMEDIATE')
                packed = pack_text(conn, json.dumps(result, ensure_ascii=False, sort_keys=True))
                conn.execute(f'INSERT OR IGNORE INTO {self.results} VALUES(?,?,?,?,?)', (row['id'], row['source'], result['status'], time.time(), packed))
                conn.execute(f'DELETE FROM {self.requests} WHERE job_id=?', (row['id'],))
                if manual is None:
                    conn.execute(f'UPDATE {self.control} SET cursor=MAX(cursor,?) WHERE id=1', (row['sequence'],))
            with self.lock:
                self.latest = self.summary(result)
                self.error = ''
            return True
        finally:
            with self.lock:
                self.active_job = None

    def _loop(self):
        idle = 0.5
        while not self.stop_event.is_set():
            try:
                if self.process_next():
                    idle = 0.5
                    continue
            except Exception as error:
                with self.lock:
                    self.error = str(error)
            signalled = self.wake.wait(idle)
            self.wake.clear()
            idle = 0.5 if signalled else min(4, idle * 2)
