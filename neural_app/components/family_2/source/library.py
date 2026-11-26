"""A local, attributed Wikipedia reference library with periodic background sync."""
import json
from contextlib import contextmanager
import sqlite3
from neural_app import section_threads as threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
DEFAULT_TOPICS = ('Good and evil', 'Good', 'Evil', 'Morality', 'Ethics', 'Consequentialism', 'Deontology', 'Virtue ethics', 'Moral relativism')
LICENSE_URL = 'https://creativecommons.org/licenses/by-sa/4.0/'
API = 'https://en.wikipedia.org/w/api.php'

class LibraryStore:

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('\n                CREATE TABLE IF NOT EXISTS topics(title TEXT PRIMARY KEY);\n                CREATE TABLE IF NOT EXISTS articles(\n                    title TEXT PRIMARY KEY, summary TEXT NOT NULL, url TEXT NOT NULL,\n                    revision TEXT, revised_at TEXT, fetched_at REAL NOT NULL);\n                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);\n            ')
            db.executemany('INSERT OR IGNORE INTO topics(title) VALUES (?)', [(t,) for t in DEFAULT_TOPICS])

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10.0)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA busy_timeout=5000')
            db.execute('PRAGMA synchronous=NORMAL')
            with db:
                yield db
        finally:
            db.close()

    def topics(self):
        with self.connect() as db:
            return [r[0] for r in db.execute('SELECT title FROM topics ORDER BY title')]

    def add_topic(self, title):
        title = title.strip().replace('_', ' ')
        if title:
            with self.connect() as db:
                db.execute('INSERT OR IGNORE INTO topics(title) VALUES (?)', (title,))

    def save(self, article):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO articles VALUES (:title,:summary,:url,:revision,:revised_at,:fetched_at)', article)

    def search(self, query=''):
        with self.connect() as db:
            rows = db.execute('SELECT * FROM articles ORDER BY title').fetchall()
        q = query.casefold()
        return [dict(row) for row in rows if q in row['title'].casefold() or q in row['summary'].casefold()]

    def setting(self, key, default=None):
        with self.connect() as db:
            row = db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, str(value)))

def fetch_article(title, opener=None):
    params = {'action': 'query', 'prop': 'extracts|info|revisions', 'inprop': 'url', 'exintro': '1', 'explaintext': '1', 'redirects': '1', 'titles': title, 'rvprop': 'ids|timestamp', 'format': 'json', 'formatversion': '2', 'maxlag': '5'}
    request = urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers={'User-Agent': 'FluxBus/1.0 (personal desktop reference library; Python urllib)', 'Accept': 'application/json'})
    with (opener or urllib.request.urlopen)(request, timeout=18) as response:
        payload = json.load(response)
    if 'error' in payload:
        raise RuntimeError(payload['error'].get('info', 'Wikipedia is busy'))
    pages = payload.get('query', {}).get('pages', [])
    if not pages or pages[0].get('missing') or (not pages[0].get('extract')):
        raise ValueError('No introductory article found for ' + title)
    page = pages[0]
    rev = (page.get('revisions') or [{}])[0]
    return {'title': page['title'], 'summary': page['extract'], 'url': page.get('fullurl') or 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(page['title'].replace(' ', '_')), 'revision': str(rev.get('revid', '')), 'revised_at': rev.get('timestamp', ''), 'fetched_at': time.time()}

class LibrarySync:

    def __init__(self, store, interval=1800, fetcher=fetch_article):
        self.store = store
        self.interval = interval
        self.fetcher = fetcher
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.enabled = store.setting('auto_sync', 'true') == 'true'
        self.last_sync = float(store.setting('last_sync', '0'))
        self.status = {'busy': False, 'message': 'Cached library ready', 'updated': self.last_sync, 'errors': [], 'revision': 0}
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._loop, name='Wikipedia library', daemon=True)
        self.thread.start()

    def get_status(self):
        with self.lock:
            return {**self.status, 'errors': self.status['errors'][:]}

    def set_status(self, **fields):
        with self.lock:
            self.status.update(fields)
            self.status['revision'] += 1

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.store.set_setting('auto_sync', 'true' if enabled else 'false')
        if enabled:
            self.sync_now()

    def sync_now(self):
        self.wake.set()

    def _loop(self):
        for _shared_tick in range(1):
            requested = self.wake.is_set()
            if requested or (self.enabled and time.time() - self.last_sync >= self.interval):
                self.wake.clear()
                self.sync_once()
            self.wake.wait(1)

    def sync_once(self):
        self.set_status(busy=True, message='Connecting to Wikipedia…', errors=[])
        errors = []
        success = 0
        topics = self.store.topics()
        for i, title in enumerate(topics):
            if self.stop_event.is_set():
                break
            self.set_status(message=f'Reading {title} · {i + 1}/{len(topics)}')
            try:
                article = self.fetcher(title)
                self.store.save(article)
                success += 1
                self.set_status(updated=time.time())
            except Exception as error:
                errors.append(f'{title}: {error}')
            if self.stop_event.wait(1.2):
                break
        self.last_sync = time.time()
        self.store.set_setting('last_sync', self.last_sync)
        if errors:
            message = f'{success} updated · {len(errors)} unavailable · cached articles kept'
        else:
            message = f'{success} articles updated · next sync in {self.interval // 60} min'
        self.set_status(busy=False, message=message, errors=errors)

    def stop(self):
        self.stop_event.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=1)
