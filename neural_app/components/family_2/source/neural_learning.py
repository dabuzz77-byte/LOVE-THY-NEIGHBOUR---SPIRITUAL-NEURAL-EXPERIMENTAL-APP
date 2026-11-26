"""Durable online learning over existing receipts; original engines are unchanged."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from neural_app import section_threads as threading
import time
import uuid
import zlib
from ..source.hub import database
from ..source.neural_model import NeuralModel, MODULES, GROUPS, LEGACY_GROUPS, remap_features, build_features

def packed(value):
    return zlib.compress(json.dumps(value, ensure_ascii=False, allow_nan=False).encode(), 6)

def unpacked(value):
    return json.loads(zlib.decompress(value))

def source_kind(source):
    source = source.lower()
    if source in ('definitions', 'web research'):
        return 'web'
    if source == 'telemetry' or source.startswith(('history:', 'tcp', 'observatory')):
        return 'activity'
    return 'input'

class NeuralLearning:

    def __init__(self, pipeline_db, path=None):
        self.pipeline_db = str(pipeline_db)
        self.path = str(path or Path(pipeline_db).with_name('neural-learning.sqlite3'))
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.thread = None
        self.error = ''
        self.active_job = None
        with database(self.pipeline_db) as conn:
            cursor = conn.execute('SELECT COALESCE(MAX(rowid),0) FROM pipeline_jobs').fetchone()[0]
        with self.connect() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.executescript('\n                CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY, enabled INTEGER, web INTEGER, activity INTEGER, cursor INTEGER);\n                CREATE TABLE IF NOT EXISTS model(id INTEGER PRIMARY KEY, state BLOB, meta BLOB);\n                CREATE TABLE IF NOT EXISTS pending(job_id TEXT PRIMARY KEY, sequence INTEGER, manual INTEGER, added REAL);\n                CREATE TABLE IF NOT EXISTS observations(job_id TEXT PRIMARY KEY, source TEXT, created REAL, record BLOB);\n                CREATE INDEX IF NOT EXISTS neural_recent ON observations(created DESC);\n                CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY, job_id TEXT, target REAL, note TEXT, created REAL, status TEXT, record BLOB);\n                CREATE INDEX IF NOT EXISTS feedback_pending ON feedback(status,created);\n                CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY, name TEXT, created REAL, state BLOB, meta BLOB);\n            ')
            conn.execute('INSERT OR IGNORE INTO settings VALUES(1,1,1,1,?)', (cursor,))
            s = conn.execute('SELECT * FROM settings WHERE id=1').fetchone()
            self.enabled, self.web, self.activity = map(bool, (s['enabled'], s['web'], s['activity']))
            row = conn.execute('SELECT * FROM model WHERE id=1').fetchone()
            self.model = NeuralModel.from_state(unpacked(row['state'])) if row else NeuralModel()
            self.meta = unpacked(row['meta']) if row else {'observations': 0, 'feedback': 0, 'targets': 0, 'sources': {}, 'latest': {}}
            if self.model.groups != GROUPS:
                conn.execute('INSERT INTO snapshots VALUES(?,?,?,?,?)', (uuid.uuid4().hex, 'Before adding reference engines', time.time(), packed(self.model.state()), packed(self.meta)))
                self.model = self.model.expanded()
                conn.execute('UPDATE model SET state=? WHERE id=1', (packed(self.model.state()),))
            if not row:
                conn.execute('INSERT INTO model VALUES(1,?,?)', (packed(self.model.state()), packed(self.meta)))

    def connect(self):
        from contextlib import contextmanager

        @contextmanager
        def connection():
            conn = sqlite3.connect(self.path, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA busy_timeout=5000')
            conn.execute('PRAGMA synchronous=NORMAL')
            try:
                with conn:
                    yield conn
            finally:
                conn.close()
        return connection()

    def set_enabled(self, value):
        self.configure(enabled=value)

    def configure(self, **values):
        if set(values) - {'enabled', 'web', 'activity'}:
            raise ValueError('Unknown learning switch')
        with self.lock, self.connect() as conn:
            for key, value in values.items():
                conn.execute('UPDATE settings SET ' + key + '=? WHERE id=1', (int(bool(value)),))
                setattr(self, key, bool(value))
        self.wake.set()

    def start(self):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._loop, name='Neural learning', daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.wake.set()
        if self.thread:
            self.thread.join(12)

    def request(self, job_id):
        with database(self.pipeline_db) as conn:
            row = conn.execute('SELECT rowid FROM pipeline_jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                raise ValueError('Input not found')
        with self.connect() as conn:
            conn.execute('INSERT INTO pending VALUES(?,?,1,?) ON CONFLICT(job_id) DO UPDATE SET manual=1', (job_id, row[0], time.time()))
        self.wake.set()

    def add_feedback(self, job_id, target, note=''):
        self.validate_target(target)
        identity = uuid.uuid4().hex
        with self.connect() as conn:
            if not conn.execute('SELECT 1 FROM observations WHERE job_id=?', (job_id,)).fetchone():
                raise ValueError('Select a learned result first')
            conn.execute('INSERT INTO feedback VALUES(?,?,?,?,?,?,NULL)', (identity, job_id, target, str(note), time.time(), 'QUEUED'))
        self.wake.set()
        return identity

    @staticmethod
    def validate_target(target):
        import math
        if isinstance(target, bool) or not isinstance(target, (int, float)) or (not math.isfinite(target)) or (not 0 <= target <= 1):
            raise ValueError('Target must be a number between 0 and 1')

    def snapshot(self):
        with self.lock:
            return {'enabled': self.enabled, 'web': self.web, 'activity': self.activity, 'running': bool(self.thread and self.thread.is_alive()), 'error': self.error, 'active_job': self.active_job, 'updates': self.model.updates, **deepcopy(self.meta), 'weights': [{'engine': name, 'weight': round(2 / (1 + __import__('math').exp(-max(-40, min(40, g)))), 6)} for (name, _), g in zip(self.model.groups, self.model.g)], 'meaning': 'Pattern reconstruction plus preference learned only from your ratings or explicit targets; existing engine actions unchanged'}

    def history(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute('SELECT job_id,source,created FROM observations ORDER BY created DESC LIMIT 100')]

    def detail(self, job):
        with self.connect() as conn:
            row = conn.execute('SELECT record FROM observations WHERE job_id=?', (job,)).fetchone()
            if not row:
                return None
            result = unpacked(row[0])
            result['feedback'] = [{**dict(r), 'record': unpacked(r['record']) if r['record'] else None} for r in conn.execute('SELECT * FROM feedback WHERE job_id=? ORDER BY created', (job,))]
            return result

    def save_snapshot(self, name='Saved model'):
        with self.lock, self.connect() as conn:
            identity = uuid.uuid4().hex
            conn.execute('INSERT INTO snapshots VALUES(?,?,?,?,?)', (identity, name, time.time(), packed(self.model.state()), packed(self.meta)))
        return identity

    def snapshots(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute('SELECT id,name,created FROM snapshots ORDER BY created DESC')]

    def restore_snapshot(self, identity):
        with self.lock:
            with self.connect() as conn:
                conn.execute('BEGIN IMMEDIATE')
                row = conn.execute('SELECT * FROM snapshots WHERE id=?', (identity,)).fetchone()
                if not row:
                    raise ValueError('Snapshot not found')
                conn.execute('INSERT INTO snapshots VALUES(?,?,?,?,?)', (uuid.uuid4().hex, 'Before restore', time.time(), packed(self.model.state()), packed(self.meta)))
                model = NeuralModel.from_state(unpacked(row['state'])).expanded()
                meta = unpacked(row['meta'])
                meta['restored_from'] = identity
                conn.execute('UPDATE model SET state=?,meta=? WHERE id=1', (packed(model.state()), packed(meta)))
            self.model, self.meta = (model, meta)

    def _enqueue(self):
        if not self.enabled:
            return
        with self.connect() as conn:
            cursor = conn.execute('SELECT cursor FROM settings WHERE id=1').fetchone()[0]
        with database(self.pipeline_db) as conn:
            rows = conn.execute('SELECT rowid AS seq,id FROM pipeline_jobs WHERE rowid>? ORDER BY rowid LIMIT 100', (cursor,)).fetchall()
        if rows:
            with self.connect() as conn:
                conn.executemany('INSERT OR IGNORE INTO pending VALUES(?,?,0,?)', [(r['id'], r['seq'], time.time()) for r in rows])
                conn.execute('UPDATE settings SET cursor=? WHERE id=1', (rows[-1]['seq'],))

    def _collect(self, job):
        with database(self.pipeline_db) as conn:
            row = conn.execute('SELECT * FROM pipeline_jobs WHERE id=?', (job,)).fetchone()
            if not row:
                raise ValueError('Input no longer exists')
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            reports = {}
            missing = []
            for prefix in MODULES:
                if prefix + '_results' not in tables:
                    continue
                r = conn.execute('SELECT result_json FROM ' + prefix + '_results WHERE job_id=?', (job,)).fetchone()
                if r:
                    reports[prefix] = json.loads(r[0])
                elif conn.execute('SELECT enabled FROM ' + prefix + '_control WHERE id=1').fetchone()[0]:
                    missing.append(prefix)
            audit = None
            mesh = None
            if 'live_audit_results' in tables:
                r = conn.execute('SELECT result_json FROM live_audit_results WHERE job_id=?', (job,)).fetchone()
                if r:
                    audit = json.loads(r[0])
            if 'mesh_outbox' in tables:
                r = conn.execute('SELECT result_json FROM mesh_outbox WHERE job_id=?', (job,)).fetchone()
                if r and r[0]:
                    mesh = json.loads(r[0])
            if row['status'] in ('QUEUED', 'RUNNING'):
                missing.append('pipeline')
            return (dict(row), reports, audit, mesh, missing)

    def process_next(self):
        self._enqueue()
        with self.connect() as conn:
            feedback = conn.execute("SELECT f.*,o.record AS observation FROM feedback f JOIN observations o ON o.job_id=f.job_id WHERE f.status='QUEUED' ORDER BY f.created LIMIT 1").fetchone()
            pending = conn.execute('SELECT * FROM pending WHERE manual=1 OR ? ORDER BY manual DESC,sequence LIMIT 1', (int(self.enabled),)).fetchone()
        if feedback:
            record = unpacked(feedback['observation'])
            return self._train(record, feedback=feedback)
        if not pending:
            return False
        job = pending['job_id']
        with self.connect() as conn:
            if conn.execute('SELECT 1 FROM observations WHERE job_id=?', (job,)).fetchone():
                conn.execute('DELETE FROM pending WHERE job_id=?', (job,))
                return True
        row, reports, audit, mesh, missing = self._collect(job)
        kind = source_kind(row['source'])
        if not pending['manual'] and (kind == 'web' and (not self.web) or (kind == 'activity' and (not self.activity))):
            with self.connect() as conn:
                conn.execute('DELETE FROM pending WHERE job_id=?', (job,))
            return True
        if missing and time.time() - pending['added'] < 30:
            return False
        payload = json.loads(row['input_json'])
        parsed = payload
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except ValueError:
                pass
        if kind == 'activity' and isinstance(parsed, dict) and (parsed.get('mode') == 'DEMO'):
            with self.connect() as conn:
                conn.execute('DELETE FROM pending WHERE job_id=?', (job,))
            return True
        x, mask, observed = build_features(payload, reports, json.loads(row['result_json']) if row['result_json'] else None, audit, mesh)
        target = None
        target_error = None
        if row['source'].lower() in ('neural manual', 'manual', 'live input', 'gemini input', 'openai input') and isinstance(parsed, dict) and isinstance(parsed.get('neural'), dict) and ('target' in parsed['neural']):
            try:
                self.validate_target(parsed['neural']['target'])
                target = parsed['neural']['target']
            except ValueError as error:
                target_error = str(error)
        sources = []

        def provenance(item):
            if isinstance(item, dict):
                if 'url' in item:
                    sources.append({k: item[k] for k in ('title', 'url', 'revision', 'revised_at', 'fetched_at') if k in item})
                for key in ('article', 'articles'):
                    if key in item:
                        provenance(item[key])
            elif isinstance(item, list):
                for child in item:
                    provenance(child)
        if kind == 'web':
            provenance(payload)
        record = dict(job_id=job, source=row['source'], kind=kind, created=time.time(), x=x, mask=mask, feature_schema=GROUPS, observed_engines=observed, unavailable=missing, target=target, target_error=target_error, web_sources=sources, input_fingerprint=row['fingerprint'])
        return self._train(record)

    def _train(self, record, feedback=None):
        record = deepcopy(record)
        old_groups = record.get('feature_schema', LEGACY_GROUPS if len(record['x']) == sum((s for _, s in LEGACY_GROUPS)) else GROUPS)
        record['x'], record['mask'] = remap_features(record['x'], record['mask'], old_groups)
        record['feature_schema'] = GROUPS
        target = feedback['target'] if feedback else record['target']
        with self.lock:
            self.active_job = record['job_id']
            try:
                model = NeuralModel.from_state(self.model.state())
                meta = deepcopy(self.meta)
                before = model.forward(record['x'], record['mask'])
                for _ in range(20 if target is not None else 1):
                    if self.stop_event.is_set():
                        return False
                    model.train(record['x'], record['mask'], target)
                after = model.forward(record['x'], record['mask'])
                trace = dict(prediction_before=before['score'], prediction_after=after['score'], reconstruction_before=before['loss'], reconstruction_after=after['loss'], target=target, activations=after['hidden'], binary=[int(v >= 0) for v in after['hidden']], ternary_signs=[1 if v > 0.1 else -1 if v < -0.1 else 0 for v in after['hidden']], updates=model.updates)
                if feedback:
                    meta['feedback'] += 1
                else:
                    meta['observations'] += 1
                    meta['targets'] += int(target is not None)
                    meta['sources'][record['kind']] = meta['sources'].get(record['kind'], 0) + 1
                meta['latest'] = {**trace, 'job_id': record['job_id'], 'source': record['source'], 'kind': record['kind'], 'observed_engines': len(record['observed_engines']), 'trained_preferences': model.supervised > 0}
                with self.connect() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    conn.execute('UPDATE model SET state=?,meta=? WHERE id=1', (packed(model.state()), packed(meta)))
                    if feedback:
                        conn.execute("UPDATE feedback SET status='TRAINED',record=? WHERE id=?", (packed(trace), feedback['id']))
                    else:
                        conn.execute('INSERT INTO observations VALUES(?,?,?,?)', (record['job_id'], record['source'], record['created'], packed({**record, **trace})))
                        conn.execute('DELETE FROM pending WHERE job_id=?', (record['job_id'],))
                self.model, self.meta = (model, meta)
                self.error = ''
                return True
            finally:
                self.active_job = None

    def _loop(self):
        for _shared_tick in range(1):
            try:
                if self.process_next():
                    continue
            except Exception as error:
                self.error = str(error)
            self.wake.wait(1)
            self.wake.clear()
