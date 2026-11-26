"""Original keyword/mean-integrity bit rules, available locally and over TCP.

The listener is optional, loopback-only, bounded and stoppable. TCP requests use
UTF-8 JSON followed by a newline (one response per connection). A complete JSON
object without a newline is also accepted for compatibility with old clients.
"""
from collections import deque
from datetime import datetime, timezone
import json
import re
import socket
from neural_app import section_threads as threading

class ProductionNetworkGateway:

    def __init__(self, ledger_reference, host='127.0.0.1', port=9999):
        if host != '127.0.0.1':
            raise ValueError('The desktop gateway listens on 127.0.0.1 only.')
        if type(port) is not int or not 0 <= port <= 65535:
            raise ValueError('Port must be an integer from 0 to 65535.')
        self.ledger, self.host, self.port = (ledger_reference, host, port)
        self.virtue_dimensions = {'energetic_resonance': ['frequency', 'vibration', 'energy', 'resonance', 'gnosis'], 'spiritual_cultivation': ['truthfulness', 'compassion', 'forbearance', 'zhen', 'shan', 'ren'], 'systemic_automation': ['automation', 'cybernetic', 'resource', 'abundance', 'cooperation'], 'resource_optimization': ['synergy', 'ephemeralization', 'sustainability', 'efficiency'], 'sky_elevator': ['elevate', 'floor', 'protect', 'wealth', 'maintain', 'sky', 'elevator']}
        self.corporate_indicators = ['monopolize', 'hoard', 'leverage', 'exclusive', 'exploit', 'privatize']
        self._stop = threading.Event()
        self._server = None
        self._thread = None
        self._lock = threading.RLock()
        self._clients = set()
        self._client_threads = set()
        self.events = deque(maxlen=50)
        self.last_response = None

    @property
    def running(self):
        return self._thread is not None and self._thread.is_alive() and (not self._stop.is_set())

    def cast_bit_array(self, bits, virtue_pass):
        if not virtue_pass:
            return ([0 if b == 1 else 1 for b in bits], 'INVERSION_MODE')
        return (list(bits), 'PRESERVATION_MODE')

    def process_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('Send a JSON object with text and bits.')
        text, bits = (payload.get('text', ''), payload.get('bits', []))
        if not isinstance(text, str) or len(text) > 8000:
            raise ValueError('Text must contain at most 8000 characters.')
        if not isinstance(bits, list) or len(bits) > 2048 or any((type(b) is not int or b not in (0, 1) for b in bits)):
            raise ValueError('Bits must be a list of at most 2048 integer zeros or ones.')
        tokens = re.sub('[^\\w\\s]', '', text.lower()).split()
        virtue_count = sum((1 for token in tokens if any((token in words for words in self.virtue_dimensions.values()))))
        corporate_count = sum((1 for token in tokens if token in self.corporate_indicators))
        with self.ledger.lock:
            weights, _, mean = self.ledger.get_weights()
            virtue_pass = virtue_count > corporate_count and mean >= 0.6
            output, transformation = self.cast_bit_array(bits, virtue_pass)
            logistics = 'Logistics Locked: Extraction profile detected or network convergence insufficient.'
            if virtue_pass:
                logistics = self.ledger.execute_sky_elevator()
            response = {'server_status': 'ONLINE', 'virtue_pass': virtue_pass, 'transformation_state': transformation, 'output_bits': output, 'logistics_log': logistics, 'active_neural_weights': [round(w, 4) for w in weights], 'mean_integrity_index': round(mean, 4), 'physical_ledger_state': self.ledger.read_ledger(), 'virtue_count': virtue_count, 'corporate_count': corporate_count}
        with self._lock:
            self.last_response = response
            self.events.appendleft({'time': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'mode': transformation, 'text': text[:160], 'virtue_count': virtue_count, 'corporate_count': corporate_count})
        return response

    def handle_client_connection(self, client_socket):
        try:
            client_socket.settimeout(3)
            buffer = bytearray()
            while True:
                part = client_socket.recv(min(4096, 32769 - len(buffer)))
                if not part:
                    raise ValueError('Connection ended before a complete JSON request.')
                buffer.extend(part)
                if len(buffer) > 32768:
                    raise ValueError('Request limit is 32 KB.')
                if b'\n' in buffer:
                    payload = json.loads(bytes(buffer).split(b'\n', 1)[0].decode('utf-8'))
                    break
                try:
                    payload = json.loads(buffer.decode('utf-8'))
                    break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
            result = self.process_payload(payload)
            client_socket.sendall(json.dumps(result, allow_nan=False).encode('utf-8') + b'\n')
        except (ValueError, TypeError, OSError) as error:
            try:
                client_socket.sendall(json.dumps({'status': 'ERROR', 'message': str(error)}).encode() + b'\n')
            except OSError:
                pass
        finally:
            client_socket.close()
            with self._lock:
                self._clients.discard(client_socket)
                self._client_threads.discard(threading.current_thread())

    def start_gateway(self):
        with self._lock:
            if self.running:
                return self.port
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                    server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                server.bind((self.host, self.port))
                server.listen(8)
                server.settimeout(0.2)
            except OSError:
                server.close()
                raise
            self._server = server
            self.port = server.getsockname()[1]
            self._stop.clear()
            self._thread = threading.Thread(target=self._listen, args=(server,), name='local-weight-gateway', daemon=True)
            self._thread.start()
            return self.port

    def _listen(self, server):
        for _shared_tick in range(1):
            try:
                client, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with self._lock:
                if self._stop.is_set() or len(self._clients) >= 8:
                    client.close()
                    continue
                self._clients.add(client)
                thread = threading.Thread(target=self.handle_client_connection, args=(client,), daemon=True)
                self._client_threads.add(thread)
                thread.start()

    def stop_gateway(self):
        self._stop.set()
        with self._lock:
            server, self._server = (self._server, None)
            clients = list(self._clients)
            threads = list(self._client_threads)
            listener = self._thread
        if server:
            server.close()
        for client in clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()
        if listener and listener is not threading.current_thread():
            listener.join(timeout=1)
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(timeout=1)

    def snapshot(self):
        with self._lock:
            return {'running': self.running, 'host': self.host, 'port': self.port, 'events': list(self.events), 'last_response': self.last_response}
