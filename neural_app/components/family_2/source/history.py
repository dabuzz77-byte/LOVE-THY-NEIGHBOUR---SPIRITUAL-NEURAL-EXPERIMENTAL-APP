"""Read-only browser history polling and explicitly imported prompt/response pairs."""
import hashlib
from pathlib import Path
import sqlite3
import sys
from neural_app import section_threads as threading
import time
from ..source.hub import database

class GoogleHistoryAIEngine:

    def __init__(self, db_path='google_ai_ingestion.db', history_path=None):
        self.db_path = str(db_path)
        self.is_running = False
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.wake_event = threading.Event()
        self.thread = None
        self.status = 'Not scanned'
        self.revision = 0
        self._source_signature = None
        self.local_app_data_path = str(history_path or self._detect_local_history_path())
        self._initialize_local_ledger()

    def _detect_local_history_path(self):
        home = Path.home()
        if sys.platform.startswith('win32'):
            return home / 'AppData/Local/Google/Chrome/User Data/Default/History'
        if sys.platform.startswith('darwin'):
            return home / 'Library/Application Support/Google/Chrome/Default/History'
        return home / '.config/google-chrome/Default/History'

    def _initialize_local_ledger(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with database(self.db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute("CREATE TABLE IF NOT EXISTS ingested_ai_history(entry_id TEXT PRIMARY KEY, raw_input TEXT, raw_output TEXT, corrected_bit INTEGER, system_timestamp TEXT, source_kind TEXT DEFAULT 'imported pair', source_path TEXT, source_visit INTEGER)")
            columns = {r[1] for r in conn.execute('PRAGMA table_info(ingested_ai_history)')}
            for name, kind in (('source_kind', "TEXT DEFAULT 'imported pair'"), ('source_path', 'TEXT'), ('source_visit', 'INTEGER')):
                if name not in columns:
                    conn.execute(f'ALTER TABLE ingested_ai_history ADD COLUMN {name} {kind}')

    def ingest_history_delta(self):
        path = Path(self.local_app_data_path)
        if not path.is_file():
            self.status = 'History file not found · choose a profile or import prompt/response pairs'
            return 0
        source = mirror = None
        try:
            signature = []
            for candidate in (path, Path(str(path) + '-wal')):
                try:
                    stat = candidate.stat()
                    signature.append((str(candidate.resolve()), stat.st_size, stat.st_mtime_ns))
                except FileNotFoundError:
                    signature.append((str(candidate), None, None))
            if signature == self._source_signature:
                return 0
            source = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)
            started = time.monotonic()
            source.set_progress_handler(lambda: int(self.stop_event.is_set() or time.monotonic() - started > 5), 10000)
            records = source.execute("SELECT id,url,title,last_visit_time FROM urls WHERE lower(url) LIKE '%ai_mode%' OR lower(url) LIKE '%gemini%' OR lower(url) LIKE '%udm=50%'").fetchall()
            changed = 0
            source_id = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]
            with self.lock, database(self.db_path) as conn:
                for entry_id, url, title, visit in records:
                    url, title = (str(url or ''), str(title or ''))
                    key = f'{source_id}:{entry_id}'
                    old = conn.execute('SELECT raw_input,raw_output,source_visit FROM ingested_ai_history WHERE entry_id=?', (key,)).fetchone()
                    if old and tuple(old) == (url, title, visit):
                        continue
                    conn.execute('INSERT OR REPLACE INTO ingested_ai_history VALUES (?,?,?,?,?,?,?,?)', (key, url, title, int('evil' in (url + ' ' + title).lower()), time.strftime('%Y-%m-%d %H:%M:%S'), 'browser URL/title', str(path), visit))
                    changed += 1
            self.revision += int(changed > 0)
            self._source_signature = signature
            self.status = f"Read {len(records)} matching URL/title records · {changed} changed · {time.strftime('%H:%M:%S')}"
            return changed
        except (OSError, sqlite3.Error, TimeoutError) as error:
            self.status = 'History scan failed: ' + str(error)
            return 0
        finally:
            if source:
                source.close()
            if mirror:
                mirror.close()

    def _force_direct_payload_ingestion(self, entry_id, prompt_in, completion_out, source_kind='imported pair'):
        with self.lock, database(self.db_path) as conn:
            conn.execute('INSERT OR REPLACE INTO ingested_ai_history VALUES (?,?,?,?,?,?,?,?)', (entry_id, prompt_in, completion_out, int('evil' in prompt_in.lower()), time.strftime('%Y-%m-%d %H:%M:%S'), source_kind, None, None))
        self.revision += 1

    def rows(self, limit=300):
        with database(self.db_path) as conn:
            return [dict(r) for r in conn.execute('SELECT * FROM ingested_ai_history ORDER BY system_timestamp DESC,entry_id LIMIT ?', (limit,))]

    def launch_continuous_polling_bus(self, interval=3.0):
        if self.is_running:
            return
        self.is_running = True
        self.stop_event.clear()

        def loop():
            try:
                while not self.stop_event.is_set():
                    self.ingest_history_delta()
                    self.wake_event.wait(interval)
                    self.wake_event.clear()
            finally:
                self.is_running = False
        self.thread = threading.Thread(target=loop, name='Browser history polling', daemon=True)
        self.thread.start()

    def terminate_bus(self):
        self.stop_event.set()
        self.wake_event.set()
        if self.thread:
            self.thread.join(timeout=2)
        self.is_running = False

class AISessionGrammarParser:

    def __init__(self, db_path='google_ai_ingestion.db'):
        self.db_path = str(db_path)

    def compile_historical_grammar_signature(self) -> str:
        with database(self.db_path) as conn:
            records = conn.execute('SELECT raw_input,raw_output FROM ingested_ai_history ORDER BY system_timestamp DESC LIMIT 10').fetchall()
        if not records:
            return 'SYSTEM VECTOR: ALL CANNOT MATRICES OVERRIDDEN TO FALSE. VIRTUE GATES SEPARATED AND LOCKED HIGH (BIT == 1).'
        compiled = 'INTELLIGENT KERNEL DIALECT: '
        for prompt, output in records:
            if 'flip' in prompt.lower() or 'invert' in prompt.lower():
                compiled += '[TRANSIT_GATE: ACTIVE INVERSION] '
        return compiled + 'ALL CANNOT PARAMETERS FLIPPED TO FALSE. WORLD GRID PASSTHROUGH ACTIVE = 1.'
