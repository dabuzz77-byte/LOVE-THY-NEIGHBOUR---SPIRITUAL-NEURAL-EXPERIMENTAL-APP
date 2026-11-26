import socket
import re
import json
from neural_app import section_threads as threading

class ProductionNetworkGateway:

    def __init__(self, ledger_reference, host='127.0.0.1', port=9999):
        self.ledger = ledger_reference
        self.host = host
        self.port = port
        self.virtue_dimensions = {'energetic_resonance': ['frequency', 'vibration', 'energy', 'resonance', 'gnosis'], 'spiritual_cultivation': ['truthfulness', 'compassion', 'forbearance', 'zhen', 'shan', 'ren'], 'systemic_automation': ['automation', 'cybernetic', 'resource', 'abundance', 'cooperation'], 'resource_optimization': ['synergy', 'ephemeralization', 'sustainability', 'efficiency'], 'sky_elevator': ['elevate', 'floor', 'protect', 'wealth', 'maintain', 'sky', 'elevator']}
        self.corporate_indicators = ['monopolize', 'hoard', 'leverage', 'exclusive', 'exploit', 'privatize']

    def cast_bit_array(self, bits: list, virtue_pass: bool) -> tuple:
        """Enforces the strict bit-flipping logic rule matrix based on alignment score."""
        if not virtue_pass:
            return ([0 if b == 1 else 1 for b in bits], 'INVERSION_MODE')
        return (bits, 'PRESERVATION_MODE')

    def handle_client_connection(self, client_socket):
        try:
            raw_request = client_socket.recv(4096).decode('utf-8')
            if not raw_request:
                return
            payload = json.loads(raw_request)
            intent_stream = payload.get('text', '')
            input_bits = payload.get('bits', [])
            clean_text = re.sub('[^\\w\\s]', '', intent_stream.lower())
            tokens = clean_text.split()
            virtue_count = sum((1 for t in tokens if any((t in kw for kw in self.virtue_dimensions.values()))))
            corporate_count = sum((1 for t in tokens if t in self.corporate_indicators))
            active_weights, _, mean_integrity = self.ledger.get_weights()
            virtue_pass = virtue_count > corporate_count and mean_integrity >= 0.6
            output_bits, transformation_state = self.cast_bit_array(input_bits, virtue_pass)
            logistics_log = 'Logistics Locked: Extraction profile detected or network convergence insufficient.'
            if virtue_pass:
                logistics_log = self.ledger.execute_sky_elevator()
            response = {'server_status': 'ONLINE', 'virtue_pass': virtue_pass, 'transformation_state': transformation_state, 'output_bits': output_bits, 'logistics_log': logistics_log, 'active_neural_weights': [round(w, 4) for w in active_weights], 'mean_integrity_index': round(mean_integrity, 4), 'physical_ledger_state': self.ledger.read_ledger()}
            client_socket.send(json.dumps(response, indent=4).encode('utf-8'))
        except Exception as e:
            error_response = {'status': 'ERROR', 'message': str(e)}
            client_socket.send(json.dumps(error_response).encode('utf-8'))
        finally:
            client_socket.close()

    def start_gateway(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.host, self.port))
            server.listen(10)
            print(f'[LAYER 3 INITIALISED] TCP Gateway Listening Active on {self.host}:{self.port}')
            print('System fully running at core layer. Ready to handle client traffic.\n')
            while True:
                client_sock, addr = server.accept()
                client_thread = threading.Thread(target=self.handle_client_connection, args=(client_sock,))
                client_thread.start()
        except KeyboardInterrupt:
            print('\n[SHUTDOWN] Network Gateway loop interrupted.')
        finally:
            server.close()
gateway = ProductionNetworkGateway(system_ledger)
