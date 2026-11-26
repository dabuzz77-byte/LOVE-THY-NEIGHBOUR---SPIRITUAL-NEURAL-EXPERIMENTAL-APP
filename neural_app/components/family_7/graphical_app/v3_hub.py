"""Measured laboratory, persistent memory, connection receipts and coding work folder."""
import ast
from dataclasses import asdict
import hashlib
import http.client
from ..graphical_app.privacy_network import public_host, local_host, connection as private_connection
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import socket
import sqlite3
import ssl
import subprocess
import sys
from neural_app import section_threads as threading
import time
import urllib.parse
import uuid
from ..graphical_app.elevation import OPERATIONS, VIRTUE_RULES, cosine, evaluate
from ..graphical_app.local_knowledge import LocalKnowledge, redact, redact_tree
from ..graphical_app.ported_core import CoreEngine, Journal, MODES
from ..graphical_app.sources import now, save_json, PageText
from ..graphical_app.wav_modulator import WavModulator
import psutil

class V3Hub:

    def __init__(self, rt):
        self.rt = rt
        self.lock = threading.RLock()
        self.wav = WavModulator()
        self.knowledge = LocalKnowledge(rt)
        self.path = rt.data / 'v3-state.json'
        self.folder = rt.data / 'work' / 'code'
        self.folder.mkdir(parents=True, exist_ok=True)
        try:
            self.saved = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.saved = {'memory': [], 'connections': [], 'plans': [], 'revisions': []}
        self.journal = Journal(rt.data / 'journal.sqlite3')
        self.credentials = {}
        self.core = CoreEngine(persistent=self.journal.restore())
        self.core.start()
        self.last_core = None
        self.latest = {}
        self.migration = json.loads((Path(__file__).parent / 'reference' / 'migration.json').read_text(encoding='utf-8'))
        self.connection_busy = set()
        self.index_started = False
        for key, title in (('core', 'Core interaction'), ('wav', 'WAV modulation'), ('memory', 'Spectral memory'), ('robin', 'Virtuous Robin Hood'), ('agent', 'Active Llama')):
            rt.node('v3:' + key, title, 'Restoration' if key == 'robin' else 'module')
            rt.edges.setdefault('v3:' + key + '|chiral', 0.1)

    def save(self):
        save_json(self.path, self.saved)

    def record(self, kind, details):
        with self.lock:
            digest = self.journal.append(kind, details, self.core.snapshot())
        self.rt.publish('v3-' + kind, {'details': details, 'journal_hash': digest})
        return digest

    def tick(self):
        with self.lock:
            sample = self.core.tick()
            if sample:
                self.last_core = asdict(sample)
        if sample:
            self.rt.activate('v3:core', sample.output)

    def run(self, operation, data):
        result = evaluate(operation, data)
        with self.lock:
            self.latest[operation] = result
        self.record(operation, {'input': data, 'result': result})
        if operation == 'karma_review':
            item = {'id': uuid.uuid4().hex[:12], 'created': now(), 'result': result}
            with self.lock:
                self.saved.setdefault('cases', []).append(item)
                self.save()
        if operation == 'robin_hood':
            self.rt.activate('v3:robin', result['VIRTUE_TRIT'])
        return result

    def remember(self, text, title='Memory'):
        if not isinstance(text, str) or not 1 <= len(text) <= 30000:
            raise ValueError('Memory must contain 1–30,000 characters')
        item = {'id': uuid.uuid4().hex[:12], 'title': str(title)[:160], 'text': text, 'created': now()}
        with self.lock:
            self.saved['memory'].append(item)
            self.saved['memory'] = self.saved['memory'][-1000:]
            self.save()
        self.rt.activate('v3:memory', 1)
        self.record('memory', item)
        return item

    def recall(self, text):
        with self.lock:
            items = list(self.saved['memory'])
        return sorted([{**i, 'score': cosine(text, i['title'] + ' ' + i['text'])} for i in items], key=lambda i: i['score'], reverse=True)[:8]

    def write_code(self, name, text):
        if not isinstance(name, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,70}\\.py', name):
            raise ValueError('Use a plain Python filename, such as my_tool.py')
        if not isinstance(text, str) or not 1 <= len(text.encode()) <= 128000:
            raise ValueError('Code must be 1–128,000 bytes')
        ast.parse(text, filename=name)
        target = self.folder / name
        if target.is_symlink() or not target.resolve().is_relative_to(self.folder.resolve()):
            raise ValueError('Code path is outside the work folder')
        digest = hashlib.sha256(text.encode()).hexdigest()
        version = uuid.uuid4().hex
        with self.lock:
            archive = self.folder / 'history'
            archive.mkdir(exist_ok=True)
            if archive.is_symlink() or not archive.resolve().is_relative_to(self.folder.resolve()):
                raise ValueError('History folder is outside the work folder')
            (archive / (version + '.py')).write_bytes(text.encode('utf-8'))
            temporary = self.folder / (version + '.tmp')
            temporary.write_bytes(text.encode('utf-8'))
            temporary.replace(target)
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError('Saved bytes did not verify')
            item = {'id': version, 'name': name, 'path': str(target), 'sha256': digest, 'bytes': len(text.encode()), 'created': now(), 'syntax': 'passed', 'execution': 'not run'}
            self.saved['revisions'].append(item)
            self.save()
        self.record('code', item)
        self.rt.binary_bus.feed('generated-code', text)
        return item

    def code_read(self, name):
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,70}\\.py', str(name)):
            raise ValueError('Choose a Python filename')
        path = (self.folder / name).resolve()
        if not path.is_relative_to(self.folder.resolve()):
            raise ValueError('Code path is outside the work folder')
        raw = path.read_bytes()
        return {'name': name, 'text': raw.decode('utf-8')[:128000], 'sha256': hashlib.sha256(raw).hexdigest()}

    def code_run(self, name, expected_hash):
        """Explicit user control only; ordinary Windows account permissions, not a sandbox."""
        file = self.code_read(name)
        if file['sha256'] != expected_hash:
            raise ValueError('Saved code changed; open and review the current version before running')
        runs = self.folder / 'runs'
        runs.mkdir(exist_ok=True)
        if runs.is_symlink() or not runs.resolve().is_relative_to(self.folder.resolve()):
            raise ValueError('Invalid run-output folder')
        run_id = uuid.uuid4().hex
        output_path = runs / (run_id + '.txt')
        snapshot = runs / (run_id + '.py')
        snapshot.write_bytes(file['text'].encode('utf-8'))
        start = time.monotonic()
        limited = None
        with output_path.open('wb') as output:
            process = subprocess.Popen([sys.executable, '-I', '-u', str(snapshot)], cwd=self.folder, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            while process.poll() is None:
                if time.monotonic() - start > 20 or output_path.stat().st_size > 1024 * 1024 or self.rt.stop.is_set():
                    limited = 'Run stopped: 20-second / 1 MB output limit or runtime shutdown'
                    try:
                        parent = psutil.Process(process.pid)
                        for child in parent.children(recursive=True):
                            try:
                                child.kill()
                            except psutil.Error:
                                pass
                        parent.kill()
                    except psutil.Error:
                        pass
                    break
                time.sleep(0.05)
            process.wait(timeout=5)
        size = output_path.stat().st_size
        with output_path.open('rb') as output:
            preview = output.read(64000)
        result = {'name': name, 'sha256': file['sha256'], 'exit_code': process.returncode, 'duration_ms': round((time.monotonic() - start) * 1000), 'output': preview.decode('utf-8', errors='replace'), 'output_truncated': size > len(preview), 'output_bytes': size, 'limited': limited, 'permissions': 'Current Windows user; no isolation claim'}
        self.record('reviewed-code-run', result)
        return result

    @staticmethod
    def address(url):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password or parts.fragment:
            raise ValueError('Use an HTTP(S) endpoint without embedded credentials or fragments')
        local = local_host(parts.hostname)
        if not local:
            public_host(parts.hostname)
            if parts.scheme != 'https':
                raise ValueError('Public connections require HTTPS')
        return (parts, '127.0.0.1' if parts.hostname == 'localhost' else parts.hostname)

    def connection_add(self, data):
        url = str(data.get('url', '')).strip()
        self.address(url)
        interval = data.get('interval', 300)
        if type(interval) not in (int, float) or not math.isfinite(interval) or (not 30 <= interval <= 86400):
            raise ValueError('Refresh interval must be 30–86,400 seconds')
        targets = data.get('targets', [])
        if not isinstance(targets, list) or any((t not in self.rt.modules for t in targets)):
            raise ValueError('Select existing modules')
        item = {'id': uuid.uuid4().hex[:12], 'title': str(data.get('title') or urllib.parse.urlsplit(url).hostname)[:120], 'url': url, 'interval': interval, 'automatic': bool(data.get('automatic', True)), 'next_fetch': 0, 'status': 'pending', 'targets': targets, 'attempts': 0, 'text': '', 'result': None, 'retrieved': None, 'error': None}
        with self.lock:
            if len(self.saved['connections']) >= 50:
                raise ValueError('Connection limit reached')
            self.saved['connections'].append(item)
            self.credentials[item['id']] = str(data.get('bearer', ''))
            self.save()
        return item

    def connection_fetch(self, key):
        with self.lock:
            item = next((c for c in self.saved['connections'] if c['id'] == key), None)
            if item is None:
                raise ValueError('Unknown connection')
            if key in self.connection_busy:
                raise ValueError('Connection is already fetching')
            self.connection_busy.add(key)
            item['status'] = 'fetching'
            url = item['url']
            bearer = self.credentials.get(key, '')
        start = time.monotonic()
        connection = None
        try:
            parts, ip = self.address(url)
            port = parts.port or (443 if parts.scheme == 'https' else 80)
            if local_host(parts.hostname):
                connection = http.client.HTTPSConnection(parts.hostname, port, timeout=12) if parts.scheme == 'https' else http.client.HTTPConnection(parts.hostname, port, timeout=12)
            else:
                connection = private_connection(parts.hostname, port, timeout=45)
            headers = {'User-Agent': 'PostscarcityObservatory/3.0', 'Accept': 'application/json,text/plain,text/html,application/xml', 'Accept-Encoding': 'identity'}
            if bearer:
                headers['Authorization'] = 'Bearer ' + bearer
            connection.request('GET', urllib.parse.urlunsplit(('', '', parts.path or '/', parts.query, '')), headers=headers)
            response = connection.getresponse()
            if not 200 <= response.status < 300:
                raise ValueError(f'Endpoint returned HTTP {response.status}; supply its final API URL')
            content_type = response.getheader('Content-Type', 'text/plain').split(';')[0]
            if not (content_type.startswith('text/') or content_type in ('application/json', 'application/xml', 'application/rss+xml', 'application/atom+xml', 'application/xhtml+xml')):
                raise ValueError('Endpoint must return readable text, JSON, RSS or XML')
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError('Response exceeds 1 MB')
            text = raw.decode('utf-8', errors='replace')
            result = json.loads(text) if 'json' in content_type else None
            if 'html' in content_type:
                parser = PageText()
                parser.feed(text)
                text, _ = parser.result()
            if result is not None:
                result = redact_tree(result)
                text = json.dumps(result, ensure_ascii=False)
            text = redact(text)[:30000] if result is None else text[:30000]
            with self.lock:
                item.update(status='ready', text=text, result=result, retrieved=now(), error=None, bytes=len(raw), latency_ms=round((time.monotonic() - start) * 1000), next_fetch=time.time() + item['interval'], attempts=0, sha256=hashlib.sha256(raw).hexdigest())
                self.save()
            with self.rt.source_hub.lock:
                source = {'id': 'connection-' + key, 'kind': 'connection', 'title': item['title'], 'url': url, 'requested_url': url, 'text': text, 'retrieved': item['retrieved'], 'status': 'ready', 'targets': item['targets'], 'automatic': False, 'next_fetch': 1e+30, 'attempts': 0, 'created': item['retrieved'], 'error': None}
                self.rt.source_hub.items[source['id']] = source
                self.rt.source_hub.save()
            self.rt.source_hub.attach(source['id'], source)
            self.record('connection', {'id': key, 'status': 'ready', 'bytes': len(raw), 'sha256': item['sha256']})
            self.rt.binary_bus.feed('connection:' + key, text)
            return dict(item)
        except Exception as exc:
            with self.lock:
                item['attempts'] += 1
                item.update(status='error', error=str(exc), next_fetch=time.time() + min(3600, 30 * 2 ** min(item['attempts'], 7)))
                self.save()
            self.record('connection', {'id': key, 'status': 'error', 'error': str(exc)})
            return dict(item)
        finally:
            if connection:
                connection.close()
            with self.lock:
                self.connection_busy.discard(key)

    def loop(self):
        for _shared_tick in range(1):
            if not self.index_started:
                self.index_started = True
                threading.Thread(target=self.knowledge.index, daemon=True).start()
            with self.lock:
                due = [c['id'] for c in self.saved['connections'] if c['automatic'] and c['next_fetch'] <= time.time() and (c['id'] not in self.connection_busy)]
            if self.rt.config['ingestion'] and self.rt.privacy.ready():
                for key in due[:1]:
                    self.connection_fetch(key)
            self.rt.stop.wait(2)

    def view(self):
        with self.lock:
            return {'core': self.last_core, 'core_modes': MODES, 'wav': self.wav.view(), 'rules': VIRTUE_RULES, 'latest': self.latest, 'memory_count': len(self.saved['memory']), 'connections': [{k: v for k, v in c.items() if k not in ('text', 'result')} for c in self.saved['connections']], 'plans': self.saved['plans'][-20:], 'cases': self.saved.get('cases', [])[-50:], 'revisions': self.saved['revisions'][-20:], 'code_folder': str(self.folder), 'journal_entries': self.journal.db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 'migration': self.migration['summary'], 'knowledge': self.knowledge.view(), 'worker_limit': 16}

    def dispatch(self, action, body):
        if action == 'evaluate':
            return self.run(body['operation'], body.get('input', {}))
        if action == 'core':
            with self.lock:
                if body.get('mode'):
                    if body['mode'] not in MODES:
                        raise ValueError('Unknown core mode')
                    self.core.mode = body['mode']
                value = self.core.enqueue('User text', body['text'], body.get('value'))
            self.record('core-input', {'text': body['text'], 'value': value})
            return {'queued': True, 'signal': value}
        if action == 'memory':
            return self.remember(body['text'], body.get('title', 'Memory'))
        if action == 'recall':
            return self.recall(body.get('text', ''))
        if action == 'plan':
            result = self.run('allocation', body['input'])
            item = {'id': uuid.uuid4().hex[:12], 'created': now(), 'input': body['input'], 'result': result}
            with self.lock:
                self.saved['plans'].append(item)
                self.save()
            return item
        if action == 'code':
            return self.write_code(body['name'], body['text'])
        if action == 'code-read':
            return self.code_read(body['name'])
        if action == 'code-run':
            return self.code_run(body['name'], body['sha256'])
        if action == 'case-decision':
            text = str(body.get('decision', '')).strip()
            reference = str(body.get('reference', '')).strip()
            if not text or not reference:
                raise ValueError('Record the human decision and its source reference')
            with self.lock:
                item = next((c for c in self.saved.get('cases', []) if c['id'] == body.get('id')), None)
                if item is None:
                    raise ValueError('Unknown case')
                decision = {'text': text[:10000], 'reference': reference[:2000], 'entered': now(), 'basis': 'User-entered human decision; source not independently authenticated'}
                item.setdefault('human_decisions', []).append(decision)
                self.save()
            self.record('human-decision', {'case': item['id'], 'decision': decision})
            return item
        if action == 'connection':
            return self.connection_add(body)
        if action == 'fetch':
            return self.connection_fetch(body['id'])
        if action == 'connection-control':
            with self.lock:
                item = next((c for c in self.saved['connections'] if c['id'] == body['id']))
                item['automatic'] = bool(body['automatic'])
                if 'bearer' in body:
                    self.credentials[item['id']] = str(body['bearer'])
                self.save()
                return item
        if action == 'index':
            return self.knowledge.index(body.get('roots'))
        if action == 'search':
            return self.knowledge.search(body.get('text', ''))
        if action == 'read':
            return self.knowledge.read(body['path'])
        if action == 'system':
            return self.knowledge.system()
        if action == 'wav':
            return self.wav.control(body)
        if action == 'verify':
            with self.lock:
                return {'verified_entries': self.journal.verify(), 'status': 'hash chain verified'}
        raise ValueError('Unknown v3 action')
