"""Two-way adapter for the Observatory's existing authenticated local bus."""
from collections import deque
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import queue
import socket
from neural_app import section_threads as threading
import time
import urllib.parse
import urllib.request
from ..source.audit import DeepVirtueAuditor
from ..source.hub import database
from ..source.payload_storage import pack_text
DEFAULT_CONNECTION = Path.home() / 'Desktop/CHAT GPT APPS/Postscarcity Observatory v4/graphical_app/data/connection.json'

def evaluate_payload(payload):
    """Use explicit assessments on actual Boolean registers; preserve unknowns.

Every leaf remains in original/result. A label by itself isn't an assessment
of unrelated fields. No source text is executed.
"""
    transitions = []

    def visit(value, path='root', registered='unresolved', evaluated='unresolved'):
        if isinstance(value, dict):
            registered = str(value.get('state_reg', value.get('state', registered))).lower()
            evaluated = str(value.get('evaluate', value.get('evaluation', evaluated))).lower()
            return {k: visit(v, path + '.' + k, registered, evaluated) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v, path + f'[{i}]', registered, evaluated) for i, v in enumerate(value)]
        if isinstance(value, bool) or (type(value) is int and value in (0, 1)):
            before = bool(value)
            assessment = evaluated if evaluated in {'good', 'evil'} else registered
            if registered in {'good', 'evil'} and evaluated in {'good', 'evil'}:
                node = {'state_reg': registered, 'evaluate': evaluated}
                detail = DeepVirtueAuditor([node, node], (before, before)).execute_fine_evaluation()['NODES'][0]
                after, action, flag = (detail['BIT_AFTER'], detail['ACTION'], detail['FLAG'])
            else:
                after = not before if assessment == 'evil' else before
                action = 'evil_flip' if assessment == 'evil' else 'good_hold' if assessment == 'good' else 'unresolved_hold'
                flag = None
            transitions.append({'path': path, 'before': before, 'after': after, 'registered': registered, 'evaluated': evaluated, 'action': action, 'flag': flag})
            return after if isinstance(value, bool) else int(after)
        return value
    result = visit(deepcopy(payload))
    return {'original': payload, 'result': result, 'transitions': transitions, 'flips': sum((t['before'] != t['after'] for t in transitions)), 'status': 'EVALUATED', 'basis': 'Explicit good/evil fields; unassessed values held'}

class ObservatoryBridge:

    def __init__(self, db_path, connection_path=DEFAULT_CONNECTION):
        self.path = Path(connection_path)
        self.db_path = str(db_path)
        self.config = None
        self.stop_event = threading.Event()
        self.lock = threading.RLock()
        self.socket = None
        self.threads = []
        self.pending = queue.Queue(maxsize=512)
        self.events = deque(maxlen=200)
        self.seen = deque(maxlen=3000)
        self.status = 'Not connected'
        self.received = self.sent = self.acknowledged = self.dropped = 0
        self.last_receipt = None
        self.last_seen = 0
        self.outbox = {}
        self.started = False
        with database(self.db_path) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS observatory_receipts(id TEXT PRIMARY KEY, module_id TEXT, input_json TEXT, result_json TEXT, timestamp REAL, acknowledged INTEGER DEFAULT 0)')

    def request(self, path):
        config = self.config
        req = urllib.request.Request(f"http://127.0.0.1:{config['port']}" + path, headers={'Authorization': 'Bearer ' + config['token']})
        with urllib.request.urlopen(req, timeout=8) as response:
            return json.load(response)

    def start(self):
        if self.started:
            return
        self.started = True
        self.stop_event.clear()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', 0))
        self.socket.settimeout(0.5)
        self.threads = [threading.Thread(target=target, daemon=True, name=name) for target, name in ((self._listen, 'Observatory bus'), (self._evaluate, 'Observatory audit'))]
        for thread in self.threads:
            thread.start()

    def _send(self, payload):
        with self.lock:
            if not self.config or not self.socket:
                return False
            envelope = {'token': self.config['token'], 'pid': os.getpid(), 'name': 'Flux Bus v2', **payload}
            data = json.dumps(envelope, allow_nan=False).encode()
            if len(data) > 14000:
                raise ValueError('Observatory bus payload exceeds 14 KB')
            self.socket.sendto(data, ('127.0.0.1', self.config['port']))
        return True

    def publish(self, topic, data):
        try:
            return self._send({'type': 'event', 'topic': 'fluxbus.' + topic, 'data': data})
        except OSError as error:
            self.status = 'Send failed: ' + str(error)
            return False

    def _enqueue(self, data):
        identity = (data.get('id'), data.get('runs'), data.get('last_run'))
        if identity in self.seen:
            return
        try:
            self.pending.put_nowait(data)
            self.seen.append(identity)
        except queue.Full:
            self.dropped += 1

    def _listen(self):
        next_subscribe, bootstrapped = (0, False)
        for _shared_tick in range(1):
            try:
                if time.monotonic() >= next_subscribe:
                    config = json.loads(self.path.read_text(encoding='utf-8-sig'))
                    if type(config.get('port')) is not int or not 1 <= config['port'] <= 65535 or (not isinstance(config.get('token'), str)):
                        raise ValueError('Invalid Observatory connection file')
                    changed = self.config != config
                    self.config = config
                    self._send({'type': 'subscribe'})
                    with self.lock:
                        retry = list(self.outbox.values())
                    for feedback in retry:
                        self.publish('audit', feedback)
                    next_subscribe = time.monotonic() + 5
                    if not bootstrapped or changed:
                        snapshot = self.request('/api/state')
                        if snapshot.get('name') != 'Postscarcity Observatory' or snapshot.get('version') != '4.0':
                            raise ValueError('Connection is not Observatory v4')
                        for module in snapshot.get('modules', []):
                            if module.get('status') in {'complete', 'error'}:
                                self._enqueue(module)
                        bootstrapped = True
                raw, addr = self.socket.recvfrom(65535)
                if addr != ('127.0.0.1', self.config['port']):
                    continue
                event = json.loads(raw)
                self.last_seen = time.time()
                self.status = 'Connected · Observatory ↔ Flux Bus'
                if event.get('type') == 'module' and event.get('data', {}).get('status') in {'complete', 'error'}:
                    self._enqueue(event['data'])
                elif event.get('type') == 'process-event':
                    data = event.get('data', {})
                    if data.get('topic') == 'fluxbus.audit' and data.get('pid') == os.getpid():
                        receipt_id = data.get('payload', {}).get('receipt_id')
                        with database(self.db_path) as conn:
                            changed = conn.execute('UPDATE observatory_receipts SET acknowledged=1 WHERE id=? AND acknowledged=0', (receipt_id,)).rowcount
                        self.acknowledged += changed
                        with self.lock:
                            self.outbox.pop(receipt_id, None)
            except socket.timeout:
                if self.last_seen and time.time() - self.last_seen > 15:
                    self.status = 'No recent Observatory response · reconnecting'
            except (OSError, ValueError, KeyError) as error:
                if not self.stop_event.is_set():
                    self.status = 'Observatory unavailable: ' + str(error)
                    self.stop_event.wait(2)
                    next_subscribe = 0

    def _evaluate(self):
        while not self.stop_event.is_set():
            try:
                module = self.pending.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                module_id = module['id']
                response = self.request('/api/module?' + urllib.parse.urlencode({'id': module_id}))
                if response.get('result') is None:
                    continue
                result = evaluate_payload(response['result'])
                encoded = json.dumps(response, sort_keys=True, ensure_ascii=False)
                receipt_id = hashlib.sha256((module_id + encoded).encode()).hexdigest()
                with database(self.db_path) as conn:
                    inserted = conn.execute('INSERT OR IGNORE INTO observatory_receipts(id,module_id,input_json,result_json,timestamp) VALUES (?,?,?,?,?)', (receipt_id, module_id, pack_text(conn, encoded), pack_text(conn, json.dumps(result)), time.time())).rowcount
                if not inserted:
                    with database(self.db_path) as conn:
                        acknowledged = conn.execute('SELECT acknowledged FROM observatory_receipts WHERE id=?', (receipt_id,)).fetchone()[0]
                    if acknowledged:
                        continue
                receipt = {'receipt_id': receipt_id, 'module_id': module_id, 'result': result, 'time': time.time()}
                with self.lock:
                    self.received += 1
                    self.last_receipt = receipt
                    self.events.append(receipt)
                feedback = {'receipt_id': receipt_id, 'module_id': module_id, 'status': result['status'], 'flips': result['flips'], 'register_count': len(result['transitions']), 'source': 'Flux Bus v2', 'transitions': result['transitions'], 'full_result_sha256': hashlib.sha256(json.dumps(result).encode()).hexdigest()}
                if len(json.dumps(feedback).encode()) > 11000:
                    groups = []
                    group = []
                    for transition in result['transitions']:
                        if group and len(json.dumps(group + [transition]).encode()) > 8000:
                            groups.append(group)
                            group = []
                        group.append(transition)
                    if group:
                        groups.append(group)
                    for index, group in enumerate(groups):
                        self.publish('audit.part', {'receipt_id': receipt_id, 'part': index + 1, 'parts': len(groups), 'transitions': group})
                    feedback['transitions'] = []
                    feedback['transition_parts'] = len(groups)
                with self.lock:
                    self.outbox[receipt_id] = feedback
                if self.publish('audit', feedback):
                    self.sent += 1
            except Exception as error:
                self.status = 'Audit exchange failed: ' + str(error)
            finally:
                self.pending.task_done()

    def view(self, include_receipt=True):
        with self.lock:
            return {'status': self.status, 'received': self.received, 'sent': self.sent, 'acknowledged': self.acknowledged, 'pending': self.pending.qsize(), 'dropped': self.dropped, 'last_seen': self.last_seen, 'last_receipt': deepcopy(self.last_receipt) if include_receipt else None}

    def drain_events(self):
        with self.lock:
            result = list(self.events)
            self.events.clear()
            return result

    def stop(self):
        self.stop_event.set()
        if self.socket:
            self.socket.close()
        for thread in self.threads:
            thread.join(timeout=1)
        self.started = False
