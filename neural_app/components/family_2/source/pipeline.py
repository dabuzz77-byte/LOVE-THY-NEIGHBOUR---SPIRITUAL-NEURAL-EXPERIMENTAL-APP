"""Persistent, resumable application-data pipeline with automatic/manual dispatch."""
import ast
from copy import deepcopy
import hashlib
import json
import queue
from neural_app import section_threads as threading
import time
import uuid
from ..source.engines import run_engine_suite
from ..source.hub import database, MultiSessionHistoryParser
from ..source.observatory import evaluate_payload
from ..source.routing import balanced_ternary
from ..source.payload_storage import pack_text

def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)

def parse_content(value):
    """Keep source text intact; extract JSON structure and Python syntax metadata."""
    if isinstance(value, (dict, list)):
        embedded = []

        def visit(item, path='root'):
            if isinstance(item, dict):
                return {key: visit(child, path + '.' + str(key)) for key, child in item.items()}
            if isinstance(item, list):
                return [visit(child, path + f'[{i}]') for i, child in enumerate(item)]
            if isinstance(item, str) and item.lstrip().startswith(('{', '[')):
                try:
                    parsed = json.loads(item)
                    embedded.append({'path': path, 'kind': 'embedded JSON'})
                    return visit(parsed, path)
                except (ValueError, RecursionError):
                    pass
            if isinstance(item, str) and ('\n' in item or item.lstrip().startswith(('import ', 'class ', 'def '))):
                parsed = parse_content(item)
                embedded.append({'path': path, **{k: v for k, v in parsed.items() if k != 'value'}})
            return item
        return {'kind': 'structured data', 'value': visit(value), 'embedded_sources': embedded}
    if not isinstance(value, str):
        return {'kind': 'scalar', 'value': value}
    try:
        return {'kind': 'JSON', 'value': json.loads(value)}
    except (ValueError, RecursionError):
        pass
    try:
        tree = ast.parse(value)
        return {'kind': 'Python source', 'value': value, 'syntax_nodes': sum((1 for _ in ast.walk(tree))), 'functions': [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))], 'classes': [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]}
    except (SyntaxError, ValueError, RecursionError) as error:
        return {'kind': 'text / other code', 'value': value, 'python_syntax': str(error)}

class DataPipeline:

    def __init__(self, db_path, auto=True):
        self.db_path = str(db_path)
        self.auto = auto
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.lock = threading.RLock()
        self.manual_ids = set()
        self.events = queue.Queue()
        self.thread = None
        self.lexer = MultiSessionHistoryParser(db_path)
        with database(self.db_path) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS pipeline_jobs (id TEXT PRIMARY KEY, source TEXT, identity TEXT, fingerprint TEXT, input_json TEXT, context_json TEXT, status TEXT, created_at REAL, updated_at REAL, result_json TEXT, error TEXT)')
            conn.execute('CREATE INDEX IF NOT EXISTS pipeline_identity ON pipeline_jobs(source,identity,fingerprint)')
            conn.execute('CREATE INDEX IF NOT EXISTS pipeline_pending ON pipeline_jobs(status,created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS pipeline_recent ON pipeline_jobs(created_at DESC)')
            conn.execute("UPDATE pipeline_jobs SET status='QUEUED',error='Resuming interrupted local run' WHERE status='RUNNING'")

    def submit(self, source, identity, payload, context=None, force=False, run_now=False):
        return self.submit_many([(source, identity, payload, context, force, run_now)])[0]

    def submit_many(self, records):
        prepared = []
        for source, identity, payload, context, force, run_now in records:
            serialized = encoded(payload)
            prepared.append((source, identity, serialized, hashlib.sha256(serialized.encode('utf-8')).hexdigest(), encoded(context or {}), force, run_now))
        if not prepared:
            return []
        result = []
        manual = []
        with self.lock, database(self.db_path) as conn:
            conn.execute('PRAGMA busy_timeout=100')
            conn.execute('BEGIN IMMEDIATE')
            for source, identity, serialized, fingerprint, context, force, run_now in prepared:
                if not force and conn.execute('SELECT 1 FROM pipeline_jobs WHERE source=? AND identity=? AND fingerprint=? LIMIT 1', (source, identity, fingerprint)).fetchone():
                    result.append(None)
                    continue
                job_id = uuid.uuid4().hex
                conn.execute('INSERT INTO pipeline_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)', (job_id, source, identity, fingerprint, pack_text(conn, serialized), pack_text(conn, context), 'QUEUED', time.time(), time.time(), None, None))
                result.append(job_id)
                if run_now:
                    manual.append(job_id)
        with self.lock:
            self.manual_ids.update(manual)
        self.wake.set()
        return result

    def run_pending(self):
        with self.lock, database(self.db_path) as conn:
            self.manual_ids.update((r[0] for r in conn.execute("SELECT id FROM pipeline_jobs WHERE status='QUEUED'")))
        self.wake.set()

    def run_selected(self, job_id):
        with self.lock, database(self.db_path) as conn:
            conn.execute("UPDATE pipeline_jobs SET status='QUEUED',error=NULL WHERE id=? AND status!='RUNNING'", (job_id,))
            self.manual_ids.add(job_id)
        self.wake.set()

    def set_auto(self, enabled):
        self.auto = bool(enabled)
        self.wake.set()

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True, name='Full data pipeline')
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=3)

    def _claim(self):
        with self.lock, database(self.db_path) as conn:
            if self.auto:
                row = conn.execute("SELECT * FROM pipeline_jobs WHERE status='QUEUED' ORDER BY created_at,rowid LIMIT 1").fetchone()
            elif self.manual_ids:
                row = conn.execute("SELECT * FROM pipeline_jobs WHERE status='QUEUED' AND id IN (" + ','.join(('?' for _ in self.manual_ids)) + ') ORDER BY created_at,rowid LIMIT 1', tuple(self.manual_ids)).fetchone()
            else:
                return None
            if not row:
                return None
            conn.execute('BEGIN IMMEDIATE')
            changed = conn.execute("UPDATE pipeline_jobs SET status='RUNNING',updated_at=? WHERE id=? AND status='QUEUED'", (time.time(), row['id']))
            if not changed.rowcount:
                return None
            self.manual_ids.discard(row['id'])
            return dict(row)

    def _loop(self):
        idle = 0.5
        for _shared_tick in range(1):
            try:
                job = self._claim()
                if job:
                    self.process(job)
                    idle = 0.5
                    continue
            except Exception as error:
                self.events.put({'status': 'ERROR', 'error': str(error)})
            signalled = self.wake.wait(idle)
            self.wake.clear()
            idle = 0.5 if signalled else min(4, idle * 2)

    def process(self, job):
        stages = []
        result = {'id': job['id'], 'source': job['source'], 'fingerprint': job['fingerprint'], 'stages': stages}

        def stage(name, operation):
            started = time.perf_counter()
            try:
                value = operation()
                stages.append({'name': name, 'status': 'COMPLETE', 'milliseconds': round((time.perf_counter() - started) * 1000, 3)})
                return value
            except Exception as error:
                stages.append({'name': name, 'status': 'ERROR', 'error': str(error)})
                raise
        try:
            payload = json.loads(job['input_json'])
            context = json.loads(job['context_json'])
            result['input'] = payload
            result['tokens_ingested'] = stage('History lexer', lambda: self.lexer.batch_ingest_historical_strings([job['input_json']], 'pipeline:' + job['source']))
            parsed = stage('Text / JSON / code parser', lambda: parse_content(payload))
            result['parsed'] = parsed
            result['audit'] = stage('Contextual good / evil audit', lambda: evaluate_payload(parsed['value']))
            result['route'] = stage('Current Boolean trajectory and deep audit', lambda: deepcopy(context.get('route', {})))
            result['engines'] = stage('All nine supplied engines', lambda: run_engine_suite(context.get('virtue', 'PASS'), result['audit']['result']))
            result['grammar'] = stage('Historical grammar', self.lexer.synthesize_code_style_language)
            bits = [int(t['after']) for t in result['audit']['transitions']]
            result['binary_ternary'] = stage('Exact binary / balanced ternary', lambda: [{'binary': bits[i:i + 16], 'decimal': int(''.join(map(str, bits[i:i + 16])), 2), 'trits': balanced_ternary(int(''.join(map(str, bits[i:i + 16])), 2))} for i in range(0, len(bits), 16)])
            result['context'] = context
            result['status'] = 'COMPLETE'
        except Exception as error:
            result['status'], result['error'] = ('ERROR', str(error))
        with database(self.db_path) as conn:
            conn.execute('UPDATE pipeline_jobs SET status=?,updated_at=?,result_json=?,error=? WHERE id=?', (result['status'], time.time(), pack_text(conn, encoded(result)), result.get('error'), job['id']))
        self.events.put(result)
        return result

    def rows(self, limit=200):
        with database(self.db_path) as conn:
            return [dict(r) for r in conn.execute('SELECT id,source,identity,status,created_at,updated_at,error FROM pipeline_jobs ORDER BY created_at DESC,rowid DESC LIMIT ?', (limit,))]

    def detail(self, job_id):
        with database(self.db_path) as conn:
            row = conn.execute('SELECT * FROM pipeline_jobs WHERE id=?', (job_id,)).fetchone()
        return dict(row) if row else None

    def stats(self):
        with database(self.db_path) as conn:
            return {r[0]: r[1] for r in conn.execute('SELECT status,COUNT(*) FROM pipeline_jobs GROUP BY status')}
