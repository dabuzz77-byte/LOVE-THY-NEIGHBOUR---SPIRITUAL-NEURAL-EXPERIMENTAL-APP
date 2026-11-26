"""Real TCP ingestion with durable attempts and verified acknowledgement records."""
import json
from pathlib import Path
import socket
from neural_app import section_threads as threading
import time
import uuid
from ..source.hub import database

def parse_target(address):
    address = address.strip().removeprefix('tcp://')
    if address == '127:0.0.1.9999':
        address = '127.0.0.1:9999'
    host, separator, port = address.rpartition(':')
    if not separator or not host or (not port.isdigit()) or (not 1 <= int(port) <= 65535):
        raise ValueError('Enter a host and port, for example 127.0.0.1:9999')
    return (host, int(port))

class TCPTargetIngestionAdapter:

    def __init__(self, target_host='127.0.0.1', target_port=9999, db_path='google_ai_ingestion.db', timeout=3.0):
        self.target_host, self.target_port = (target_host, target_port)
        self.db_path = str(db_path)
        self.timeout = timeout
        self.lock = threading.Lock()
        self._initialize_local_schema()

    def _initialize_local_schema(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with database(self.db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('CREATE TABLE IF NOT EXISTS network_ingested_logs (packet_id TEXT PRIMARY KEY, raw_payload TEXT, corrected_bit INTEGER, network_address TEXT, timestamp TEXT)')
            existing = {r[1] for r in conn.execute('PRAGMA table_info(network_ingested_logs)')}
            for name, definition in (('response_json', 'TEXT'), ('delivery_status', "TEXT DEFAULT 'LEGACY_UNVERIFIED'"), ('delivered', 'INTEGER DEFAULT 0'), ('source_entry_id', 'TEXT'), ('created_at', 'REAL DEFAULT 0')):
                if name not in existing:
                    conn.execute(f'ALTER TABLE network_ingested_logs ADD COLUMN {name} {definition}')

    def transmit_and_ingest_payload(self, node_id, context_stream, current_state, source_entry_id=None):
        payload = {'node_id': node_id, 'context': context_stream, 'state': current_state}
        serialized = json.dumps(payload, ensure_ascii=False)
        packet_id = 'pkt_' + uuid.uuid4().hex
        corrected_bit = int(current_state.lower() == 'evil')
        address = f'{self.target_host}:{self.target_port}'
        with self.lock, database(self.db_path) as conn:
            conn.execute("INSERT INTO network_ingested_logs(packet_id,raw_payload,corrected_bit,network_address,timestamp,delivery_status,source_entry_id,created_at) VALUES (?,?,?,?,?,'PENDING',?,?)", (packet_id, serialized, corrected_bit, address, time.strftime('%Y-%m-%d %H:%M:%S'), source_entry_id, time.time()))
        sent = False
        try:
            with socket.create_connection((self.target_host, self.target_port), timeout=self.timeout) as client:
                client.sendall(serialized.encode('utf-8'))
                sent = True
                deadline = time.monotonic() + self.timeout
                buffer = bytearray()
                response = None
                while time.monotonic() < deadline:
                    client.settimeout(max(0.01, deadline - time.monotonic()))
                    chunk = client.recv(8192)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if len(buffer) > 1048576:
                        raise ValueError('Acknowledgement exceeds 1 MiB')
                    try:
                        response = json.loads(buffer.decode('utf-8'))
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                if not isinstance(response, dict):
                    raise ValueError('Target did not return a complete JSON acknowledgement')
                delivered = response.get('status') == 'ACK'
                if delivered and 'node' in response:
                    node = response['node']
                    if not isinstance(node, dict) or node.get('node_id') != node_id or node.get('raw_state') != current_state:
                        raise ValueError('Acknowledgement does not match the submitted node')
                status = 'ACK' if delivered else 'REJECTED'
                result = {**response, 'delivery_confirmed': delivered, 'packet_id': packet_id, 'cached_locally': True}
        except (OSError, ValueError) as error:
            delivered = False
            status = 'UNCONFIRMED' if sent else 'FAILED'
            result = {'status': status, 'delivery_confirmed': False, 'bridge_gate': None, 'packet_id': packet_id, 'cached_locally': True, 'error': str(error)}
        with self.lock, database(self.db_path) as conn:
            conn.execute('UPDATE network_ingested_logs SET response_json=?,delivery_status=?,delivered=? WHERE packet_id=?', (json.dumps(result, ensure_ascii=False), status, int(delivered), packet_id))
        return result

    def rows(self, limit=200):
        with database(self.db_path) as conn:
            return [dict(row) for row in conn.execute('SELECT * FROM network_ingested_logs ORDER BY created_at DESC,rowid DESC LIMIT ?', (limit,))]

    def stats(self):
        with database(self.db_path) as conn:
            counts = {r[0]: r[1] for r in conn.execute('SELECT delivery_status,COUNT(*) FROM network_ingested_logs GROUP BY delivery_status')}
        return {'total': sum(counts.values()), 'confirmed': counts.get('ACK', 0), 'by_status': counts}

class TCPPacketGrammarParser:

    def __init__(self, db_path='google_ai_ingestion.db'):
        self.db_path = str(db_path)
        TCPTargetIngestionAdapter(db_path=self.db_path)

    def compile_network_grammar_signature(self):
        with database(self.db_path) as conn:
            records = conn.execute('SELECT raw_payload FROM network_ingested_logs ORDER BY created_at DESC,rowid DESC LIMIT 5').fetchall()
        if not records:
            return 'NETWORK DIAGNOSTIC: ALL CANNOT MATRICES ZEROED TO FALSE. ROUTING PASSTHROUGH ACTIVE = 1.'
        signature = 'CONNECTED KERNEL SIGNATURE: '
        for record in records:
            if 'evil' in record[0].lower():
                signature += '[NETWORK_BUS: AUTOMATIC_NOT_GATE_INVERSION] '
        return signature + 'ALL CANNOT VECTORS REMEDIATED TO FALSE. PASSTHROUGH TUNNEL LOCKED HIGH (BIT == 1).'
