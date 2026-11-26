"""Inference Observatory: local source engine, durable receipts, cryptography and cooperative buses."""
from neural_app import capture_output as contextlib
import argparse
import ast
import base64
import hashlib
import hmac
import http.server
import importlib.util
import json
import mimetypes
import os
import pathlib
import secrets
import socket
import sqlite3
import subprocess
import sys
from neural_app import section_threads as threading
import time
import urllib.request
import urllib.parse
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
ROOT = pathlib.Path(__file__).resolve().parent
APPS = pathlib.Path.home() / 'Desktop/CHAT GPT APPS'
CONNECTION = APPS / 'Postscarcity Observatory v4/graphical_app/data/connection.json'
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
DB = DATA / 'observatory.sqlite3'
LOCK = threading.RLock()
START = time.time()
AUTH = secrets.token_urlsafe(32)
CAT = json.loads((ROOT / 'catalog.json').read_text(encoding='utf8'))
clients = set()
bridge = {'status': 'Awaiting Observatory', 'received': 0, 'sent': 0, 'acknowledged': 0, 'last_seen': 0}
bus = None
registry = []
runs = {}
revoked = set()
prompt_loop = None
autonomous = None
federation = None
native_research = None
sync_state = {'status': 'idle', 'batches': 0, 'files': 0, 'last_results': []}

@contextlib.contextmanager
def db():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    try:
        with c:
            yield c
    finally:
        c.close()
with db() as c:
    c.executescript('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,ts REAL,topic TEXT,payload TEXT); CREATE TABLE IF NOT EXISTS accounts(id TEXT PRIMARY KEY,units INTEGER NOT NULL CHECK(units>=0)); CREATE TABLE IF NOT EXISTS used_tokens(id TEXT PRIMARY KEY);')
    for name, units in [('commons', 1000000000), ('roots', 500000), ('canopy', 5000000), ('sovereign', 25000000)]:
        c.execute('INSERT OR IGNORE INTO accounts VALUES(?,?)', (name, units))
secretfile = DATA / 'signing.key'
if not secretfile.exists():
    secretfile.write_bytes(secrets.token_bytes(32))
SECRET = secretfile.read_bytes()

def event(topic, payload):
    raw = json.dumps(payload, ensure_ascii=True, default=str, allow_nan=False)
    with LOCK, db() as c:
        cur = c.execute('INSERT INTO events(ts,topic,payload) VALUES(?,?,?)', (time.time(), topic, raw))
        ident = cur.lastrowid
    return {'id': ident, 'topic': topic, 'payload': payload}

def history(limit=100):
    with db() as c:
        return [{'id': r['id'], 'ts': r['ts'], 'topic': r['topic'], 'payload': json.loads(r['payload'])} for r in c.execute('SELECT * FROM events ORDER BY id DESC LIMIT ?', (limit,))]

def inventory():
    global registry
    result = []
    for folder, dirs, files in os.walk(APPS):
        dirs[:] = [d for d in dirs if d.lower() not in {'_internal', 'vendor', 'node_modules', '.git', '__pycache__', 'work', 'upgrades', '.venv', 'venv'}]
        for name in files:
            p = pathlib.Path(folder) / name
            if p.suffix.lower() not in {'.py', '.java'}:
                continue
            try:
                raw = p.read_bytes()
                text = raw.decode('utf-8-sig', errors='replace')
                defs = []
                imports = []
                if p.suffix == '.py':
                    try:
                        tree = ast.parse(text)
                        defs = [n.name for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
                        imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
                    except SyntaxError:
                        pass
                result.append({'id': hashlib.sha256(str(p).encode()).hexdigest()[:20], 'path': str(p.relative_to(APPS)), 'language': p.suffix[1:], 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'definitions': defs, 'imports': imports, 'bus_capable': 'PostscarcityBus' in text or 'python_bus' in text, 'status': 'indexed'})
            except OSError:
                pass
    registry = result
    event('inventory.indexed', {'files': len(result), 'python': sum((r['language'] == 'py' for r in result)), 'java': sum((r['language'] == 'java' for r in result))})
    return result

class Bridge:

    def __init__(self):
        self.config = None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(('127.0.0.1', 0))
        self.s.settimeout(1)
        threading.Thread(target=self.listen, daemon=True).start()

    def send(self, topic, data):
        if not self.config:
            return {'status': 'unavailable', 'reason': 'Observatory connection configuration unavailable'}
        raw = json.dumps({'token': self.config['token'], 'pid': os.getpid(), 'name': 'Inference Observatory', 'type': 'event', 'topic': topic, 'data': data}).encode()
        if len(raw) > 14000:
            raise ValueError('Use a compact event under 14 KB; full result remains in local receipts')
        self.s.sendto(raw, ('127.0.0.1', self.config['port']))
        bridge['sent'] += 1
        return {'status': 'sent_unconfirmed', 'bytes': len(raw)}

    def listen(self):
        nextsub = 0
        for _shared_tick in range(1):
            try:
                if time.time() > nextsub:
                    self.config = json.loads(CONNECTION.read_text(encoding='utf-8-sig'))
                    p = self.config['port']
                    if type(p) != int or not 0 < p < 65536:
                        raise ValueError('Invalid bus port')
                    self.s.sendto(json.dumps({'token': self.config['token'], 'pid': os.getpid(), 'name': 'Inference Observatory', 'type': 'subscribe'}).encode(), ('127.0.0.1', p))
                    nextsub = time.time() + 5
                raw, addr = self.s.recvfrom(65535)
                if addr != ('127.0.0.1', self.config['port']):
                    continue
                e = json.loads(raw)
                bridge.update(status='Connected', last_seen=time.time())
                bridge['received'] += 1
                if e.get('type') == 'process-event' and e.get('data', {}).get('pid') == os.getpid():
                    bridge['acknowledged'] += 1
                if e.get('type') != 'pulse':
                    event('observatory.' + e.get('type', 'event'), e.get('data', {}))
            except socket.timeout:
                if time.time() - bridge['last_seen'] > 15:
                    bridge['status'] = 'No recent response'
            except Exception as e:
                bridge['status'] = 'Unavailable: ' + str(e)
                time.sleep(2)

def obs_request(path, payload=None):
    cfg = json.loads(CONNECTION.read_text(encoding='utf-8-sig'))
    req = urllib.request.Request('http://127.0.0.1:' + str(int(cfg['port'])) + path, data=json.dumps(payload).encode() if payload is not None else None, headers={'Authorization': 'Bearer ' + cfg['token'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def flux(data):
    wire = {'node_id': 'inference-observatory', 'context': json.dumps(data, ensure_ascii=False), 'state': 'unassessed'}
    with socket.create_connection(('127.0.0.1', 9999), timeout=4) as s:
        s.sendall(json.dumps(wire).encode())
        s.shutdown(socket.SHUT_WR)
        raw = b''
        while len(raw) < 1000000:
            part = s.recv(65536)
            if not part:
                break
            raw += part
            if b'\n' in raw:
                break
    if not raw:
        return {'status': 'unconfirmed', 'reason': 'No acknowledgment received'}
    try:
        ack = json.loads(raw)
    except ValueError:
        return {'status': 'unconfirmed', 'response': raw.decode(errors='replace')}
    return {'status': 'response_received', 'ack': ack}

def source_run(req):
    started = time.time()
    try:
        p = subprocess.run([sys.executable, str(ROOT / 'runner.py')], input=json.dumps(req), capture_output=True, text=True, encoding='utf8', timeout=20, cwd=ROOT)
        result = json.loads(p.stdout) if p.stdout.strip() else {'ok': False, 'error': p.stderr[-6000:]}
    except subprocess.TimeoutExpired:
        result = {'ok': False, 'error': 'Execution stopped after 20 seconds'}
    result['elapsed_ms'] = round((time.time() - started) * 1000, 2)
    result['module_id'] = req.get('id')
    event('engine.result', result)
    return result

def sync_sources():
    if sync_state['status'] == 'running':
        return dict(sync_state)
    sync_state.update(status='running', batches=0, files=0, last_results=[])

    def worker():
        if not registry:
            inventory()
        for offset in range(0, len(registry), 12):
            batch = registry[offset:offset + 12]
            payload = {'receipt_id': uuid.uuid4().hex, 'kind': 'source_registry', 'offset': offset, 'total': len(registry), 'files': [{k: f[k] for k in ['id', 'path', 'language', 'bytes', 'sha256', 'bus_capable']} for f in batch], 'scope': 'Indexed source metadata; no script execution implied'}
            result = {'offset': offset, 'count': len(batch)}
            for name, fn in [('observatory', lambda: bus.send('inference.source_registry', payload)), ('fluxbus', lambda: flux(payload))]:
                try:
                    result[name] = fn()
                except Exception as e:
                    result[name] = {'status': 'unavailable', 'error': str(e)}
            sync_state['batches'] += 1
            sync_state['files'] += len(batch)
            sync_state['last_results'] = (sync_state['last_results'] + [result])[-5:]
            event('source.bus_sync', result)
            time.sleep(0.1)
        sync_state['status'] = 'complete'
        event('source.bus_sync_complete', dict(sync_state))
    threading.Thread(target=worker, daemon=True).start()
    return dict(sync_state)

def script_run(ident):
    item = next((r for r in registry if r['id'] == ident))
    path = (APPS / item['path']).resolve()
    if not path.is_relative_to(APPS.resolve()):
        raise ValueError('Path outside source registry')
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Source changed; rescan before running')
    if ident in runs and runs[ident]['status'] == 'running':
        return runs[ident]
    result = {'id': ident, 'status': 'running', 'started': time.time(), 'path': item['path']}
    runs[ident] = result

    def worker():
        log = DATA / (ident + '.log')
        try:
            with log.open('wb') as out:
                p = subprocess.Popen([sys.executable, str(path)] if path.suffix == '.py' else ['java', str(path)], cwd=path.parent, stdout=out, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                result['pid'] = p.pid
                try:
                    code = p.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
                    result.update(status='timeout', error='Stopped after 60 seconds')
                    code = None
            if code is not None:
                result.update(status='complete' if code == 0 else 'error', exit_code=code)
            result['output'] = log.read_bytes()[-100000:].decode(errors='replace')
        except Exception as e:
            result.update(status='error', error=str(e))
        event('script.result', result)
        try:
            bus.send('inference.script.result', {'id': ident, 'status': result['status'], 'path': item['path']})
        except Exception:
            pass
    threading.Thread(target=worker, daemon=True).start()
    return result

def action(path, x):
    if path == '/api/shutdown':
        threading.Thread(target=server.shutdown, daemon=True).start()
        return {'status': 'stopping'}
    if path == '/api/research/native':
        return native_research.configure(x)
    if path == '/api/research/ingest':
        return federation.accept(x)
    if path == '/api/federation/predict':
        return federation.router.predict(str(x.get('text', '')))
    if path == '/api/research/retry':
        threading.Thread(target=federation.deliver, args=(str(x['id']),), daemon=True).start()
        return {'status': 'retry_queued'}
    if path == '/api/automatic':
        return autonomous.configure(x)
    if path == '/api/ingress':
        return {'input_id': autonomous.ingest('Local process · ' + str(x.get('producer', 'connected process')), 'bus', str(x.get('title', 'Connected process input')), '', str(x.get('text', json.dumps(x.get('data', {})))), x.get('data', {}), str(x.get('producer', 'connected process')))}
    if path == '/api/loop':
        return prompt_loop.update(x)
    if path == '/api/sync':
        return sync_sources()
    if path == '/api/run':
        return source_run(x)
    if path == '/api/scan':
        return {'files': inventory()}
    if path == '/api/script':
        return script_run(x['id'])
    if path == '/api/publish':
        payload = {'receipt_id': str(uuid.uuid4()), 'text': str(x.get('text', '')), 'sha256': hashlib.sha256(str(x.get('text', '')).encode()).hexdigest()}
        results = {}
        for name, fn in [('observatory', lambda: bus.send('inference.payload', payload)), ('flux', lambda: flux(payload))]:
            try:
                results[name] = fn()
            except Exception as e:
                results[name] = {'status': 'unavailable', 'error': str(e)}
        event('bus.delivery', results)
        return results
    if path == '/api/observatory':
        return obs_request('/api/state')
    if path == '/api/crypto':
        mode = x['mode']
        text = str(x.get('text', ''))
        password = str(x.get('password', ''))
        if mode == 'hash':
            result = {'sha256': hashlib.sha256(text.encode()).hexdigest(), 'bytes': len(text.encode())}
        elif mode == 'sign':
            key = ed25519.Ed25519PrivateKey.generate()
            data = text.encode()
            sig = key.sign(data)
            key.public_key().verify(sig, data)
            result = {'algorithm': 'Ed25519', 'signature': sig.hex(), 'public_key': key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex(), 'verified': True, 'private_key': 'Ephemeral; not exported'}
        elif mode == 'derive':
            if not password:
                raise ValueError('Enter a passphrase')
            salt = bytes.fromhex(x['salt']) if x.get('salt') else secrets.token_bytes(16)
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000, 32)
            result = {'algorithm': 'PBKDF2-HMAC-SHA256', 'iterations': 600000, 'salt': salt.hex(), 'derived_key': key.hex()}
        elif mode == 'encrypt':
            if not password:
                raise ValueError('Enter a passphrase')
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 600000, 32)
            packet = {'version': 1, 'algorithm': 'AES-256-GCM', 'salt': salt.hex(), 'nonce': nonce.hex(), 'ciphertext': AESGCM(key).encrypt(nonce, text.encode(), b'inference-observatory-v1').hex()}
            result = {'packet': json.dumps(packet), 'authenticated': True}
        elif mode == 'decrypt':
            p = json.loads(text)
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(p['salt']), 600000, 32)
            result = {'plaintext': AESGCM(key).decrypt(bytes.fromhex(p['nonce']), bytes.fromhex(p['ciphertext']), b'inference-observatory-v1').decode(), 'authenticated': True}
        elif mode in ['caesar', 'vigenere']:
            key = password.upper() or 'KEY'
            shift = int(x.get('shift', 3))
            decrypt = bool(x.get('decrypt'))
            n = 0
            res = ''
            for ch in text:
                if ch.isascii() and ch.isalpha():
                    k = shift if mode == 'caesar' else ord(key[n % len(key)]) - 65
                    base = 65 if ch.isupper() else 97
                    res += chr((ord(ch) - base + (-k if decrypt else k)) % 26 + base)
                    n += 1
                else:
                    res += ch
            result = {'output': res, 'purpose': 'Historical cipher; educational, not secure encryption'}
        else:
            raise ValueError('Unknown cryptography operation')
        event('crypto.operation', {'algorithm': result.get('algorithm', mode), 'input_bytes': len(text.encode()), 'success': True})
        return result
    if path == '/api/token':
        if x['node'] not in ['roots', 'canopy', 'sovereign']:
            raise ValueError('Unknown account')
        payload = {'id': uuid.uuid4().hex, 'node': x['node'], 'cap': 'settle', 'exp': int(time.time()) + 300}
        raw = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).decode()
        sig = hmac.new(SECRET, raw.encode(), hashlib.sha256).hexdigest()
        return {'token': raw + '.' + sig, 'expires': payload['exp'], 'capability': 'One settlement, five minutes'}
    if path == '/api/settle':
        raw, sig = x['token'].split('.')
        if not hmac.compare_digest(hmac.new(SECRET, raw.encode(), hashlib.sha256).hexdigest(), sig):
            raise ValueError('Invalid token signature')
        p = json.loads(base64.urlsafe_b64decode(raw))
        sender = x['sender']
        receiver = x['receiver']
        amount = round(float(x['amount']) * 100)
        if p['exp'] < time.time() or p['node'] != sender or p['cap'] != 'settle' or (p['id'] in revoked):
            raise ValueError('Expired, revoked or mismatched capability')
        if amount <= 0 or amount > 10 ** 14 or sender == receiver:
            raise ValueError('Use a positive amount and different accounts')
        with LOCK, db() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute('SELECT 1 FROM used_tokens WHERE id=?', (p['id'],)).fetchone():
                raise ValueError('Token already used')
            balances = dict(c.execute('SELECT id,units FROM accounts'))
            if sender not in balances or receiver not in balances or receiver == 'commons':
                raise ValueError('Unknown endpoint; commons is reserve only')
            if balances[sender] < amount:
                raise ValueError('Insufficient local resource units')
            dividend = (amount * 369 + 5000) // 10000 if sender in ['canopy', 'sovereign'] else 0
            c.execute('UPDATE accounts SET units=units-? WHERE id=?', (amount, sender))
            c.execute('UPDATE accounts SET units=units+? WHERE id=?', (amount - dividend, receiver))
            c.execute('UPDATE accounts SET units=units+? WHERE id=?', (dividend, 'commons'))
            c.execute('INSERT INTO used_tokens VALUES(?)', (p['id'],))
            result = {'sender': sender, 'receiver': receiver, 'gross_ru': amount / 100, 'net_ru': (amount - dividend) / 100, 'commons_dividend_ru': dividend / 100, 'token_id': p['id'], 'ts': time.time(), 'basis': 'Persistent local resource-unit ledger; no external money or goods moved'}
            seal = hmac.new(SECRET, json.dumps(result, sort_keys=True).encode(), hashlib.sha256).hexdigest()
            result['receipt_seal'] = seal
            c.execute('INSERT INTO events(ts,topic,payload) VALUES(?,?,?)', (time.time(), 'ledger.settlement', json.dumps(result)))
        return result
    if path == '/api/inference':
        prompt = str(x['prompt'])
        model = str(x['model'])
        req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=json.dumps({'model': model, 'prompt': prompt, 'stream': False}).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as r:
            result = json.load(r)
        event('inference.result', {'model': model, 'response': result.get('response'), 'eval_count': result.get('eval_count')})
        return result
    raise ValueError('Unknown operation')

class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def send(self, data, status=200, kind='application/json'):
        raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=True, default=str, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self):
        return self.headers.get('X-Observatory-Key') == AUTH and self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}']

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            if path == '/api/session':
                if self.headers.get('Sec-Fetch-Site') not in [None, 'same-origin', 'none']:
                    return self.send({'error': 'Origin rejected'}, 403)
                return self.send({'key': AUTH})
            if path.startswith('/api/') and (not self.authorized()):
                return self.send({'error': 'Local session required'}, 403)
            if path == '/api/federation':
                return self.send(dict(federation.view(), native=native_research.view()))
            if path == '/api/research/native':
                return self.send(native_research.view())
            if path == '/api/research/next':
                return self.send(federation.next_task())
            if path == '/api/research/result':
                ident = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('id', [''])[0]
                with federation.db() as c:
                    row = c.execute('SELECT * FROM research WHERE id=?', (ident,)).fetchone()
                return self.send(dict(row) if row else {'error': 'Research record not found'}, 200 if row else 404)
            if path == '/api/automatic':
                return self.send(autonomous.view())
            if path == '/api/loop':
                return self.send(prompt_loop.view())
            if path == '/api/catalog':
                return self.send(CAT)
            if path == '/api/inventory':
                return self.send(registry)
            if path == '/api/events':
                return self.send(history(250))
            if path == '/api/models':
                try:
                    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=4) as r:
                        return self.send(json.load(r))
                except Exception as e:
                    return self.send({'models': [], 'error': str(e)})
            if path == '/api/state':
                with db() as c:
                    accounts = {r['id']: r['units'] / 100 for r in c.execute('SELECT * FROM accounts')}
                    count = c.execute('SELECT count(*) FROM events').fetchone()[0]
                return self.send({'sync': sync_state, 'uptime': time.time() - START, 'pid': os.getpid(), 'modules': len(CAT['modules']), 'sections': len(CAT['sections']), 'files': len(registry), 'events': count, 'bridge': bridge, 'accounts': accounts, 'runs': list(runs.values()), 'memory': __import__('resource').getrusage(0).ru_maxrss if os.name != 'nt' else None})
            if path == '/api/export':
                return self.send({'events': history(100000), 'inventory': registry, 'modules': [{'id': m['id'], 'name': m['name'], 'line': m['line']} for m in CAT['modules']]})
            if path == '/manuscript.txt':
                return self.send((ROOT / 'manuscript.txt').read_bytes(), kind='text/plain')
            target = ROOT / 'web' / ('index.html' if path == '/' else path.lstrip('/'))
            if not target.resolve().is_relative_to((ROOT / 'web').resolve()):
                return self.send({'error': 'Invalid path'}, 403)
            if not target.is_file():
                return self.send({'error': 'Not found'}, 404)
            return self.send(target.read_bytes(), kind=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        except Exception as e:
            self.send({'error': str(e)}, 500)

    def do_POST(self):
        if not self.authorized():
            return self.send({'error': 'Local session required'}, 403)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length > 2000000:
                raise ValueError('Request exceeds 2 MB')
            x = json.loads(self.rfile.read(length))
            return self.send(action(self.path, x))
        except Exception as e:
            return self.send({'error': f'{type(e).__name__}: {e}'}, 400)
