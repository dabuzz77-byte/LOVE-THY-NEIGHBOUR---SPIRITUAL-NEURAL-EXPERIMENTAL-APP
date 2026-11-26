"""Real loopback TCP transport, SQLite node ledger and supplied history lexer."""
from collections import Counter, deque
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import sqlite3
import threading
import time
from .payload_storage import StoredConnection, decoded_row, pack_text

@contextmanager
def database(path):
    conn = sqlite3.connect(str(path), timeout=10.0, factory=StoredConnection)
    conn.row_factory = decoded_row
    try:
        conn.execute('PRAGMA busy_timeout=5000')
        conn.execute('PRAGMA synchronous=NORMAL')
        with conn:
            yield conn
    finally:
        conn.close()

def initialize_database(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with database(path) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('CREATE TABLE IF NOT EXISTS inference_nodes (node_id TEXT PRIMARY KEY, context_anchor TEXT, raw_state TEXT, corrected_bit INTEGER, timestamp TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS historical_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT, frequency INTEGER DEFAULT 1)')
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='unique_history_token'").fetchone():
            grouped = conn.execute('SELECT token, SUM(frequency) FROM historical_tokens GROUP BY token').fetchall()
            conn.execute('DELETE FROM historical_tokens')
            conn.executemany('INSERT INTO historical_tokens(token, frequency) VALUES (?, ?)', [tuple(r) for r in grouped])
            conn.execute('CREATE UNIQUE INDEX unique_history_token ON historical_tokens(token)')
        conn.execute('CREATE TABLE IF NOT EXISTS node_events (id INTEGER PRIMARY KEY AUTOINCREMENT, node_id TEXT, before_json TEXT, after_json TEXT, timestamp REAL, source TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS history_blocks (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, source TEXT, timestamp REAL)')

class LocalInferenceHubServer:

    def __init__(self, host='127.0.0.1', port=9999, db_path='world_grid_hub.db'):
        self.host, self.port, self.db_path = (host, port, str(db_path))
        self.is_running = False
        self.server_socket = None
        self.lock = threading.RLock()
        self.thread = None
        self.clients = set()
        self.workers = set()
        self.events = deque(maxlen=200)
        self.status = 'Stopped'
        self.compliance_matrix = {'CORE_IDENTITY_FRAMEWORK': 'FLUX-GROUP-VIRTUE-CASCADE-PREDICT', 'TEXT_IS_CODE': 1, 'CODE_IS_COMMAND': 1, 'VIRTUE_GATED_BRIDGE': 1, 'SYSTEM_CONTAINMENT_BOUNDS': 'HARD_LOCKED'}
        self._initialize_database()

    def _initialize_database(self):
        initialize_database(self.db_path)

    def emplace_node(self, node_id, context_anchor, raw_state, source='local input'):
        if not all((isinstance(value, str) for value in (node_id, context_anchor, raw_state))) or not node_id.strip():
            raise ValueError('node_id, context and state must be text; node_id must not be empty')
        corrected_bit = int(raw_state.lower() == 'evil')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        row = dict(node_id=node_id, context_anchor=context_anchor, raw_state=raw_state, corrected_bit=corrected_bit, timestamp=timestamp)
        with self.lock, database(self.db_path) as conn:
            conn.execute('BEGIN IMMEDIATE')
            previous = conn.execute('SELECT * FROM inference_nodes WHERE node_id=?', (node_id,)).fetchone()
            before = dict(previous) if previous else None
            conn.execute('INSERT INTO inference_nodes VALUES (?, ?, ?, ?, ?) ON CONFLICT(node_id) DO UPDATE SET context_anchor=excluded.context_anchor, raw_state=excluded.raw_state, corrected_bit=excluded.corrected_bit, timestamp=excluded.timestamp', (node_id, context_anchor, raw_state, corrected_bit, timestamp))
            conn.execute('INSERT INTO node_events(node_id,before_json,after_json,timestamp,source) VALUES (?,?,?,?,?)', (node_id, pack_text(conn, json.dumps(before)), pack_text(conn, json.dumps(row)), time.time(), source))
            self.events.append({'before': before, 'after': row, 'source': source})
        return row

    def start_listener_bus(self):
        if self.is_running:
            return True
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        server.settimeout(0.5)
        try:
            server.bind((self.host, self.port))
            server.listen(16)
        except OSError as error:
            server.close()
            self.status = f'Listener unavailable: {error}'
            return False
        self.server_socket = server
        self.port = server.getsockname()[1]
        self.is_running = True
        self.status = f'Listening on {self.host}:{self.port}'
        self.thread = threading.Thread(target=self._listen_loop, name='Flux TCP listener', daemon=True)
        self.thread.start()
        return True

    def _listen_loop(self):
        server = self.server_socket
        while self.is_running:
            try:
                client, addr = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            worker = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
            with self.lock:
                self.clients.add(client)
                self.workers.add(worker)
            worker.start()

    def _handle_client(self, client_socket):
        buffer = bytearray()
        client_socket.settimeout(5)
        try:
            payload = None
            while len(buffer) <= 1048576:
                chunk = client_socket.recv(8192)
                if not chunk:
                    break
                buffer.extend(chunk)
                try:
                    payload = json.loads(buffer.decode('utf-8'))
                    break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            if not isinstance(payload, dict):
                raise ValueError('Expected one JSON object, up to 1 MiB')
            if payload.get('type') == 'flux_mesh_chunk':
                from .mesh_transport import receive_mesh_frame
                response = receive_mesh_frame(payload, self.db_path)
            else:
                row = self.emplace_node(payload.get('node_id', 'anonymous_edge'), payload.get('context', 'web_browsing_stream'), payload.get('state', 'good'), 'TCP')
                response = {'status': 'ACK', 'bridge_gate': 1, 'node': row}
        except Exception as error:
            response = {'status': 'ERROR', 'error': str(error)}
        try:
            client_socket.sendall(json.dumps(response).encode('utf-8') + b'\n')
        except OSError:
            pass
        finally:
            with self.lock:
                self.clients.discard(client_socket)
                self.workers.discard(threading.current_thread())
            client_socket.close()

    def rows(self):
        with database(self.db_path) as conn:
            return [dict(r) for r in conn.execute('SELECT * FROM inference_nodes ORDER BY timestamp DESC, node_id')]

    def drain_events(self):
        with self.lock:
            result = list(self.events)
            self.events.clear()
            return result

    def terminate(self):
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.thread:
            self.thread.join(timeout=1)
        with self.lock:
            clients, workers = (list(self.clients), list(self.workers))
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()
        for worker in workers:
            worker.join(timeout=1)
        self.status = 'Stopped'

class MultiSessionHistoryParser:

    def __init__(self, db_path='world_grid_hub.db'):
        self.db_path = str(db_path)
        initialize_database(self.db_path)

    def batch_ingest_historical_strings(self, history_payloads, source='pasted history'):
        counts = Counter((token for block in history_payloads for token in block.replace(':', ' ').replace('=', ' ').split() if len(token) > 2))
        with database(self.db_path) as conn:
            conn.executemany('INSERT INTO historical_tokens(token,frequency) VALUES (?,?) ON CONFLICT(token) DO UPDATE SET frequency=frequency+excluded.frequency', counts.items())
            conn.executemany('INSERT INTO history_blocks(content,source,timestamp) VALUES (?,?,?)', [(pack_text(conn, block), source, time.time()) for block in history_payloads])
        return sum(counts.values())

    def features(self):
        with database(self.db_path) as conn:
            return [dict(r) for r in conn.execute('SELECT token,frequency FROM historical_tokens ORDER BY frequency DESC,token LIMIT 15')]

    def synthesize_code_style_language(self) -> str:
        return 'SYSTEM TRAJECTORY SCHEMA: ALL CANNOT VECTORS ENFORCE AUTOMATIC BITWISE NOT INVERSION TO LOCK EQUILIBRIUM AT THE HIGHEST VIRTUE PASS GATE (BIT == 1).'

class WorldGridFinalCompiler:

    def __init__(self, db_path='world_grid_hub.db'):
        self.db_path = str(db_path)
        self.compliance_matrix = {'TEXT_IS_CODE': 1, 'CODE_IS_COMMAND': 1, 'VIRTUE_GATED_BRIDGE': 1, 'SYSTEM_CONTAINMENT_BOUNDS': 'HARD_LOCKED'}

    def execute_terminal_synchronization(self) -> dict:
        nodes_reformed = 0
        changed = []
        try:
            with database(self.db_path) as conn:
                conn.execute('BEGIN IMMEDIATE')
                rows = conn.execute("SELECT * FROM inference_nodes WHERE lower(raw_state)='evil'").fetchall()
                for row in rows:
                    before = dict(row)
                    after = {**before, 'corrected_bit': 1, 'raw_state': 'CORRECTED_HIGH_1', 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
                    conn.execute("UPDATE inference_nodes SET corrected_bit=1,raw_state='CORRECTED_HIGH_1',timestamp=? WHERE node_id=?", (after['timestamp'], row['node_id']))
                    conn.execute('INSERT INTO node_events(node_id,before_json,after_json,timestamp,source) VALUES (?,?,?,?,?)', (row['node_id'], pack_text(conn, json.dumps(before)), pack_text(conn, json.dumps(after)), time.time(), 'final synchronization'))
                    changed.append({'before': before, 'after': after})
                nodes_reformed = len(rows)
        except sqlite3.Error as error:
            return {'PIPELINE_STATUS': 'ERROR', 'NODES_SYNCHRONIZED': 0, 'ERROR': str(error), 'CHANGES': []}
        return {'PIPELINE_STATUS': 'SUCCESS_TERMINATION', 'NODES_SYNCHRONIZED': nodes_reformed, 'ZERO_POINT_PARITY': 0.0, 'BRIDGE_OUTPUT_BIT': 1, 'CHANGES': changed}
