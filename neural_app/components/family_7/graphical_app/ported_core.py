"""Core Interaction System — Python desktop workspace (standard library only).

Framework vocabulary comes from the original Java app and the user's Google AI
Mode conversation, 26 September 2026. Numeric models are software simulations;
network receipts, processing counters and journal hashes are measured data.
Run: python core_interaction_system.py   |   python core_interaction_system.py --self-test
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import math
import os
from pathlib import Path
import queue
import re
import sqlite3
import sys
import tempfile
from neural_app import section_threads as threading
import time
from collections import deque
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from urllib.error import HTTPError
from urllib.request import Request, HTTPRedirectHandler, build_opener
import xml.etree.ElementTree as ET
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / 'data'
DEFAULT_URL = 'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml'
LAYERS = ('ZERO POINT', 'HYDROGEN', 'STAR', 'EARTH / CHNO', 'LIFE', 'KARMA', 'SILICON')
MODES = ('Taoist · balance', 'Science · direct', 'Angel Taiji · gentle', 'Monkey · explore', 'God mind · target')
BG, PANEL, CARD, LINE = ('#0a111d', '#111d2d', '#152437', '#263b50')
TEXT, MUTED, TEAL, BLUE, PURPLE, AMBER = ('#e5edf6', '#99aec3', '#49dfbc', '#68b7ff', '#b7a0ff', '#ffbd79')

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def atomic_write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(text)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def read_small(path: Path, limit=262144):
    with path.open('rb') as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f'Use a text file smaller than {limit // 1024} KB.')
    return data.decode('utf-8-sig')

@dataclass
class Framework:
    name: str = 'Stateful Elevation Bridge'
    frequency_hz: float = 7.83
    cycles: int = 0
    self_response: float = 0.28
    mirror_response: float = 0.42
    balance_target: float = 0.0
    shield_limit: float = 0.85
    eco_floor: float = 1.0
    elevation_step: float = 0.05
    positive_words: str = 'growth,success,improve,discovery,progress,stable,solution,protect,care'
    negative_words: str = 'risk,loss,failure,conflict,decline,crisis,error,harm'

    def validate(self):
        if not isinstance(self.name, str) or not 1 <= len(self.name.strip()) <= 80:
            raise ValueError('Framework name must contain 1–80 characters.')
        bounds = {'frequency_hz': (0.2, 30), 'self_response': (0.01, 1), 'mirror_response': (0.01, 1), 'balance_target': (-1, 1), 'shield_limit': (0.05, 1), 'eco_floor': (1, 1000000), 'elevation_step': (0, 10)}
        for name, (low, high) in bounds.items():
            value = getattr(self, name)
            if type(value) not in (float, int) or not math.isfinite(value) or (not low <= value <= high):
                raise ValueError(f'{name} must be a finite number between {low} and {high}.')
        if type(self.cycles) is not int or not 0 <= self.cycles <= 1000000:
            raise ValueError('cycles must be 0 (continuous) or a whole number up to 1000000.')
        if abs(self.balance_target) > self.shield_limit:
            raise ValueError('The balance target must fit inside the containment limit.')
        for name in ('positive_words', 'negative_words'):
            if not isinstance(getattr(self, name), str) or len(getattr(self, name)) > 4000:
                raise ValueError(f'{name} must be a comma-separated word list under 4000 characters.')
        return self

    @classmethod
    def parse(cls, text):
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError('Rules must be a JSON object.')
        unknown = set(data) - {field.name for field in fields(cls)}
        if unknown:
            raise ValueError('Unknown rules: ' + ', '.join(sorted(unknown)))
        return cls(**data).validate()

    def text(self):
        return json.dumps(asdict(self), indent=2, ensure_ascii=False) + '\n'

@dataclass
class Signal:
    source: str
    text: str
    value: float
    received: str

@dataclass
class Sample:
    cycle: int
    time: str
    source: str
    input: float
    self_value: float
    balance: float
    output: float
    stability: float
    contained: bool
    layer: str
    phase: float
    probability_zero: float
    probability_one: float
    eco_floor: float
    sky_elevation: float

class CoreEngine:
    """Single-owner deterministic model. UI and tests drive it on one thread."""

    def __init__(self, framework=None, persistent=None):
        self.framework = (framework or Framework()).validate()
        persistent = persistent or {}
        self.floor = max(self.framework.eco_floor, self._finite_state(persistent.get('floor', 1), 1))
        self.elevation = self._finite_state(persistent.get('elevation', 0), 0)
        self.pending = deque()
        self.history = deque(maxlen=2400)
        self.state = 'READY'
        self.mode = MODES[0]
        self.reset_session()

    @staticmethod
    def _finite_state(value, fallback):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (value > 1000000000000.0):
            raise ValueError('Saved model state contains an invalid number.')
        return max(fallback, float(value))

    def reset_session(self):
        self.state = 'READY'
        self.cycle = self.processed = self.contained = self.rejected = 0
        self.self_value = self.output = self.framework.balance_target
        self.elapsed = 0.0
        self.pending.clear()
        self.history.clear()

    def configure(self, framework):
        if self.state in ('RUNNING', 'PAUSED'):
            raise ValueError('Stop the session before applying rules.')
        framework.validate()
        if framework.eco_floor < self.floor:
            raise ValueError(f'Anti-degradation: eco_floor must stay at or above {self.floor:g}.')
        self.framework = framework
        self.floor = max(self.floor, framework.eco_floor)
        self.reset_session()

    def start(self, mode=None):
        if self.state == 'RUNNING':
            return
        if self.state == 'PAUSED':
            self.state = 'RUNNING'
            return
        pending = deque(self.pending)
        self.reset_session()
        self.pending = pending
        self.mode = mode or MODES[0]
        if self.mode not in MODES:
            raise ValueError('Unknown mind mode.')
        self.state = 'RUNNING'

    def pause(self):
        if self.state == 'RUNNING':
            self.state = 'PAUSED'

    def stop(self):
        self.state = 'STOPPED'
        self.pending.clear()

    def enqueue(self, source, text, explicit=None):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Enter some input text.')
        if len(text) > 16000:
            raise ValueError('Input is limited to 16000 characters.')
        if re.search('(?<![\\d.])(?:1\\s*={1,2}\\s*0|0\\s*={1,2}\\s*1)(?![\\d.])', text):
            self.rejected += 1
            raise ValueError('Identity check: input contains 1=0 or 0=1. It was not queued. Review the source text.')
        if len(self.pending) >= 128:
            self.rejected += 1
            raise ValueError('The 128-item input queue is full. Wait for processing to catch up.')
        value = self.score(text) if explicit is None else explicit
        if type(value) not in (int, float) or not math.isfinite(value) or (not -1 <= value <= 1):
            raise ValueError('The input signal must be between -1 and +1.')
        self.pending.append(Signal(str(source)[:200], text, float(value), utc_now()))
        return float(value)

    def score(self, text):
        positive = {w.strip().lower() for w in self.framework.positive_words.split(',')}
        negative = {w.strip().lower() for w in self.framework.negative_words.split(',')}
        tokens = re.findall('\\w+', text.lower())
        plus = sum((word in positive for word in tokens))
        minus = sum((word in negative for word in tokens))
        return (plus - minus) / (plus + minus) if plus + minus else 0.0

    def tick(self, dt=None):
        if self.state != 'RUNNING':
            return None
        f = self.framework
        dt = 1 / f.frequency_hz if dt is None else dt
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('Cycle duration must be a positive finite number.')
        item = self.pending.popleft() if self.pending else None
        raw = item.value if item else f.balance_target
        self.processed += int(item is not None)
        gain = {MODES[0]: 1, MODES[1]: 1, MODES[2]: 0.65, MODES[3]: 1.35, MODES[4]: 0.5}[self.mode]
        desired = raw * gain + (f.balance_target * 0.5 if self.mode == MODES[4] else 0)
        response = desired if self.mode == MODES[1] else self.self_value + f.self_response * (desired - self.self_value)
        balance = response + f.self_response * (f.balance_target - response)
        proposed = self.output + f.mirror_response * (balance - self.output)
        contained = abs(response) > f.shield_limit or abs(proposed) > f.shield_limit
        self.self_value = max(-f.shield_limit, min(f.shield_limit, response))
        self.output = max(-f.shield_limit, min(f.shield_limit, proposed))
        self.contained += int(contained)
        stability = max(0, 100 * (1 - abs(self.output - f.balance_target) / 2))
        self.elapsed += dt
        phase = math.tau * f.frequency_hz * self.elapsed
        p0 = math.cos(phase / 2 + self.output) ** 2
        p1 = 1.0 - p0
        if not all((math.isfinite(x) for x in (self.self_value, self.output, stability, p0, p1))) or not math.isclose(p0 + p1, 1, abs_tol=1e-12):
            self.state = 'FAULT'
            raise ValueError('Numeric invariant failed. Processing stopped.')
        if item:
            self.elevation = min(1000000000000.0, self.elevation + f.elevation_step * stability / 100)
        self.cycle += 1
        sample = Sample(self.cycle, utc_now(), item.source if item else 'Feedback', raw, self.self_value, balance, self.output, stability, contained, LAYERS[(self.cycle - 1) % len(LAYERS)], phase % math.tau, p0, p1, self.floor, self.elevation)
        self.history.append(sample)
        if f.cycles and self.cycle >= f.cycles:
            self.state = 'COMPLETE'
        return sample

    def snapshot(self):
        return {'floor': self.floor, 'elevation': self.elevation}

class Journal:
    """Local event chain. Hashes detect changes; they do not prove factual truth."""

    def __init__(self, path):
        self.path = Path(path)
        recovered = self.path.with_name(self.path.stem + ".recovered" + self.path.suffix)
        if recovered.is_file():
            self.path = recovered
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, timeout=10.0, check_same_thread=False)
        self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=NORMAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time TEXT NOT NULL, payload TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)')
        self.db.commit()
        try:
            self.verify()
        except Exception:
            self.db.close()
            raise

    @staticmethod
    def digest(previous, stamp, payload):
        return hashlib.sha256((previous + '\n' + stamp + '\n' + payload).encode()).hexdigest()

    def append(self, kind, details, state):
        stamp = utc_now()
        payload = json.dumps({'kind': kind, 'details': details, 'state': state}, sort_keys=True, ensure_ascii=False, allow_nan=False)
        with self.lock, self.db:
            self.db.execute('BEGIN IMMEDIATE')
            last = self.db.execute('SELECT digest FROM events ORDER BY id DESC LIMIT 1').fetchone()
            previous = last[0] if last else '0' * 64
            digest = self.digest(previous, stamp, payload)
            self.db.execute('INSERT INTO events(time,payload,previous,digest) VALUES(?,?,?,?)', (stamp, payload, previous, digest))
        return digest

    def verify(self):
        with self.lock:
            return self._verify_locked()

    def _verify_locked(self):
        previous, count = ('0' * 64, 0)
        for event_id, stamp, payload, prior, digest in self.db.execute('SELECT id,time,payload,previous,digest FROM events ORDER BY id'):
            if prior != previous or digest != self.digest(prior, stamp, payload):
                raise ValueError(f'Journal integrity mismatch at event {event_id}. The existing journal was preserved.')
            previous, count = (digest, count + 1)
        return count

    def restore(self):
        with self.lock:
            row = self.db.execute('SELECT payload FROM events ORDER BY id DESC LIMIT 1').fetchone()
        return json.loads(row[0])['state'] if row else {}

    def close(self):
        with self.lock:
            self.db.close()

def validate_url(address):
    parsed = urlsplit(address.strip())
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Enter an HTTPS address without embedded login details.')
    if parsed.scheme != 'https' and (not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1'))):
        raise ValueError('Use HTTPS. HTTP is supported only for local testing.')
    _ = parsed.port
    return address.strip()

class CheckedRedirect(HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, request, response, code, message, headers, address):
        validate_url(address)
        if urlsplit(request.full_url).scheme == 'https' and urlsplit(address).scheme != 'https':
            raise ValueError('An HTTPS source tried to redirect to an unencrypted address.')
        return super().redirect_request(request, response, code, message, headers, address)

class ReadableHTML(HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = ([], 0)

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())

def fetch_source(address, cancel=None):
    """Read a public text source with certificate checks, size and time limits."""
    address = validate_url(address)
    started = time.monotonic()
    request = Request(address, headers={'User-Agent': 'CoreInteractionSystem/2.0 (desktop feed reader)', 'Accept': 'application/rss+xml, application/atom+xml, application/json, text/plain, text/html;q=0.8', 'Accept-Encoding': 'identity'})
    try:
        response = build_opener(CheckedRedirect()).open(request, timeout=5)
    except HTTPError as exc:
        code = exc.code
        exc.close()
        raise ValueError(f'Source returned HTTP {code}.') from None
    with response:
        kind = response.headers.get_content_type()
        if not (kind.startswith('text/') or 'json' in kind or 'xml' in kind):
            raise ValueError('The source must return text, HTML, JSON, RSS or Atom.')
        chunks, size = ([], 0)
        while True:
            if cancel is not None and cancel.is_set():
                raise InterruptedError('Request cancelled.')
            if time.monotonic() - started > 15:
                raise TimeoutError('The source exceeded the 15-second request limit.')
            chunk = response.read1(16384)
            if not chunk:
                break
            size += len(chunk)
            if size > 512 * 1024:
                raise ValueError('The source exceeds the 512 KB response limit.')
            chunks.append(chunk)
        charset = response.headers.get_content_charset() or 'utf-8'
        body = b''.join(chunks).decode(charset, errors='replace')
        final_url = response.url
    title = urlsplit(final_url).hostname
    if 'xml' in kind or body.lstrip().startswith(('<?xml', '<rss', '<feed')):
        if re.search('<!\\s*(?:DOCTYPE|ENTITY)', body, re.I):
            raise ValueError('XML declarations that load or expand entities are not supported.')
        root = ET.fromstring(body)
        titles = [element.text.strip() for element in root.iter() if element.tag.split('}')[-1] == 'title' and element.text and element.text.strip()]
        title = titles[0] if titles else title
        text = '\n'.join(('• ' + item for item in titles[1:21])) if len(titles) > 1 else ' '.join(root.itertext())
    elif 'html' in kind:
        parser = ReadableHTML()
        parser.feed(body)
        text = ' '.join(parser.parts)
    elif 'json' in kind:
        text = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
    else:
        text = body
    text = html.unescape(text).strip()[:12000]
    if not text:
        raise ValueError('The source returned no readable content.')
    return {'url': final_url, 'title': title, 'text': text, 'bytes': size, 'latency_ms': round((time.monotonic() - started) * 1000), 'received': utc_now()}

def export_csv(path, samples):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=[field.name for field in fields(Sample)])
    writer.writeheader()
    for sample in samples:
        row = asdict(sample)
        for key, value in row.items():
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                row[key] = "'" + value
        writer.writerow(row)
    atomic_write(Path(path), stream.getvalue())
