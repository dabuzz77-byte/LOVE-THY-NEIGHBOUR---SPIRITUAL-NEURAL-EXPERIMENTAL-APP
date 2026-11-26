import base64
import hashlib
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
from neural_app import section_threads as threading
import time
import unittest
from contextlib import closing
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from .mesh_bus import BusServer, Ledger
from .mesh_client import MeshClient
from .bridges import FluxBridge, ObservatoryBridge, publish_chunks, DEFAULTS
from .signals import packet, from_bits, generate, decode
TEST_ROOT = Path(__file__).resolve().parents[2] / 'work' / 'mesh-tests'
TEST_ROOT.mkdir(parents=True, exist_ok=True)

def temporary():
    return tempfile.TemporaryDirectory(dir=TEST_ROOT)

def wait_for(predicate, seconds=5):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.04)
    raise AssertionError('Timed out waiting for expected state')

class SignalTests(unittest.TestCase):

    def test_leading_zeroes_and_padding(self):
        value = from_bits('00001')
        self.assertEqual(decode(value), '00001')
        self.assertEqual(value['padding_bits'], 3)

    def test_unicode_round_trip(self):
        raw = 'Hydrogen 🌍 零'.encode()
        value = packet(raw)
        self.assertEqual(base64.b64decode(value['base64']), raw)
        self.assertEqual(len(decode(value)), len(raw) * 8)

    def test_hash_tampering(self):
        value = packet(b'abc')
        value['base64'] = base64.b64encode(b'abd').decode()
        with self.assertRaises(ValueError):
            decode(value)

    def test_generators(self):
        for mode in ('Seeded test', 'Counter', 'Cellular automaton'):
            a = generate(mode, 97, 'seed', 3)
            b = generate(mode, 97, 'seed', 3)
            self.assertEqual(a, b)
            self.assertEqual(len(decode(a)), 776)
        self.assertNotEqual(generate('OS random', 64)['sha256'], generate('OS random', 64)['sha256'])

    def test_invalid_bits(self):
        for text in ('', '001x'):
            with self.assertRaises(ValueError):
                from_bits(text)

class BusTests(unittest.TestCase):

    def setUp(self):
        self.tmp = temporary()
        self.server = BusServer(self.tmp.name, 0)
        self.ledger = self.server.ledger
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.server.close()
        self.tmp.cleanup()

    def client(self, name, events):
        client = MeshClient(name, self.server.connection, events.append, replay=True)
        self.clients.append(client)
        return client

    def test_two_way_python(self):
        left = []
        right = []
        a = self.client('alpha', left)
        b = self.client('beta', right)
        a.publish('probe', {'bit': 0}, target='beta')
        b.publish('reply', {'bit': 1}, target='alpha')
        wait_for(lambda: any((x['topic'] == 'reply' for x in left)) and any((x['topic'] == 'probe' for x in right)))
        self.assertFalse(any((x['source'] == 'alpha' for x in left)))
        self.assertGreaterEqual(self.ledger.stats()['receipts'], 2)

    def test_authentication_required(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(f'http://127.0.0.1:{self.server.port}/status')
        self.assertEqual(caught.exception.code, 401)

    def test_dedup_and_conflicting_id(self):
        value = dict(id='fixed', topic='test', data={'a': 1}, source='test')
        first = self.ledger.publish(value)
        second = self.ledger.publish(value)
        self.assertEqual(first['seq'], second['seq'])
        self.assertTrue(second['duplicate'])
        with self.assertRaises(ValueError):
            self.ledger.publish(dict(value, data=2))

    def test_routes_exclude_echo(self):
        seen = []
        client = self.client('recipient', seen)
        self.ledger.publish(dict(topic='blocked', source='other', route=['recipient'], data=1))
        self.ledger.publish(dict(topic='allowed', source='other', route=['other'], data=2))
        wait_for(lambda: any((e['topic'] == 'allowed' for e in seen)))
        self.assertFalse(any((e['topic'] == 'blocked' for e in seen)))

    def test_persistence(self):
        event = self.ledger.publish(dict(topic='persistent', data='x'))
        self.ledger.advance('persist-client', event['seq'], event['id'])
        reopened = Ledger(Path(self.tmp.name) / 'mesh.sqlite3')
        self.assertEqual(reopened.cursor('persist-client'), event['seq'])
        self.assertEqual(reopened.read()[0]['data'], 'x')

    def test_large_transfer_lossless(self):
        data = {'text': '🧬' * 90000}
        publish_chunks(self.ledger, 'test', 'large', data, ['test'], 'large-1')
        parts = self.ledger.read()
        raw = b''.join((base64.b64decode(e['data']['chunk']) for e in parts))
        self.assertEqual(json.loads(raw), data)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), parts[0]['data']['sha256'])

    def test_invalid_envelopes(self):
        for value in ({'topic': ''}, {'topic': 'x', 'route': [None]}, {'topic': 'x', 'data': float('nan')}):
            with self.assertRaises(ValueError):
                self.ledger.publish(value)

    def test_udp_listen_and_broadcast(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listener.bind(('127.0.0.1', 0))
        listener.settimeout(3)
        self.server.udp.broadcast_port = listener.getsockname()[1]
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender.bind(('127.0.0.1', 0))
        sender.settimeout(3)
        try:
            value = dict(type='publish', token=self.server.token, id='udp-probe', source='udp-test', topic='port.probe', data={'bits': '0001'}, route=['udp-test'])
            sender.sendto(json.dumps(value).encode(), ('127.0.0.1', self.server.port))
            receipt = json.loads(sender.recvfrom(65535)[0])
            self.assertTrue(receipt['accepted'])
            event = json.loads(listener.recvfrom(65535)[0])
            self.assertEqual(event['id'], 'udp-probe')
            self.assertEqual(event['data']['bits'], '0001')
        finally:
            sender.close()
            listener.close()

    def test_udp_large_fragments_reassemble(self):
        from .udp_port import frames
        event = dict(id='large', data='零' * 19000)
        parts = [json.loads(x) for x in frames(event)]
        raw = b''.join((base64.b64decode(x['chunk']) for x in parts))
        self.assertEqual(json.loads(raw), event)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), parts[0]['sha256'])

    def test_udp_subscription(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.bind(('127.0.0.1', 0))
        client.settimeout(3)
        try:
            client.sendto(json.dumps({'type': 'subscribe', 'token': self.server.token}).encode(), ('127.0.0.1', self.server.port))
            self.assertEqual(json.loads(client.recvfrom(65535)[0])['type'], 'attached')
            self.ledger.publish(dict(topic='broadcast', data=42))
            self.assertEqual(json.loads(client.recvfrom(65535)[0])['data'], 42)
        finally:
            client.close()

class RealFluxTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source = Path(DEFAULTS['flux_source'])
        if not cls.source.exists():
            raise unittest.SkipTest('Installed Flux source unavailable')
        sys.path.insert(0, str(cls.source))
        from hub import LocalInferenceHubServer
        from pipeline import DataPipeline
        cls.Hub = LocalInferenceHubServer
        cls.Pipeline = DataPipeline

    def test_real_hub_pipeline_return_and_no_echo(self):
        with temporary() as tmp:
            ledger = Ledger(Path(tmp) / 'mesh.db')
            path = Path(tmp) / 'flux.db'
            hub = self.Hub(port=0, db_path=path)
            self.assertTrue(hub.start_listener_bus())
            pipeline = self.Pipeline(path)
            bridge = FluxBridge(ledger, dict(DEFAULTS, flux_database=str(path), flux_port=hub.port))
            try:
                receipt = ledger.publish(dict(source='hydrogen', topic='signal.frame', route=['hydrogen'], data={'bits': '0010101'}))
                event = ledger.read()[0]
                bridge.send(event)
                node = hub.rows()[0]
                self.assertEqual(json.loads(node['context_anchor'])['data']['bits'], '0010101')
                pipeline.submit('local hub', node['node_id'], node, run_now=True)
                job = pipeline._claim()
                result = pipeline.process(job)
                self.assertEqual(result['status'], 'COMPLETE')
                bridge.poll()
                messages = ledger.read()
                returned = messages[-1]
                self.assertEqual(returned['topic'], 'fluxbus.pipeline.result')
                self.assertIn('hydrogen', returned['route'])
                self.assertIn('fluxbus', returned['route'])
                bridge.poll()
                self.assertEqual(len(ledger.read()), 2)
                self.assertEqual(list(bridge.pending()), [])
            finally:
                pipeline.stop()
                hub.terminate()

    def test_timestamp_ties_do_not_lose_results(self):
        with temporary() as tmp:
            ledger = Ledger(Path(tmp) / 'mesh.db')
            path = Path(tmp) / 'flux.db'
            hub = self.Hub(port=0, db_path=path)
            pipeline = self.Pipeline(path)
            bridge = FluxBridge(ledger, dict(DEFAULTS, flux_database=str(path)))
            stamp = time.time() + 1
            with closing(sqlite3.connect(path)) as db:
                with db:
                    for i in range(93):
                        db.execute('INSERT INTO pipeline_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?)', (f'{i:03}', 'test', str(i), 'hash', '{}', '{}', 'COMPLETE', stamp, stamp, json.dumps({'value': i}), None))
            for _ in range(4):
                bridge.poll()
            self.assertEqual(ledger.latest(), 93)
            pipeline.stop()
            hub.terminate()

class ObservatoryProtocolTests(unittest.TestCase):

    def test_subscribe_and_authenticated_return(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        with temporary() as tmp:
            ledger = Ledger(Path(tmp) / 'mesh.db')
            accepted = []
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.bind(('127.0.0.1', 0))
            port = udp.getsockname()[1]
            udp.settimeout(3)

            class Handler(BaseHTTPRequestHandler):

                def log_message(self, *args):
                    pass

                def do_POST(self):
                    if self.headers.get('Authorization') != 'Bearer fixture-token':
                        self.send_error(401)
                        return
                    accepted.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                    raw = b'{"accepted":true}'
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
            http = ThreadingHTTPServer(('127.0.0.1', port), Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True)
            thread.start()
            config = Path(tmp) / 'observatory.json'
            config.write_text(json.dumps({'port': port, 'token': 'fixture-token'}))
            bridge = ObservatoryBridge(ledger, config)
            bridge.start()
            try:
                raw, addr = udp.recvfrom(65535)
                self.assertEqual(json.loads(raw)['type'], 'subscribe')
                udp.sendto(b'{"type":"attached"}', addr)
                udp.sendto(b'{"type":"module","seq":1,"time":"fixture","data":{"id":"demo","status":"complete"}}', addr)
                wait_for(lambda: bridge.received == 1)
                ledger.publish(dict(source='hydrogen', topic='test.return', route=['hydrogen'], data={'text': '🌍' * 5000}))
                wait_for(lambda: bridge.sent == 1)
                parts = [x['data'] for x in accepted]
                parts.sort(key=lambda x: x['index'])
                restored = json.loads(b''.join((base64.b64decode(x['chunk']) for x in parts)))
                self.assertEqual(restored['data']['text'], '🌍' * 5000)
                self.assertGreater(len(parts), 1)
                udp.sendto(json.dumps({'type': 'process-event', 'seq': 2, 'data': {'pid': __import__('os').getpid(), 'topic': 'hydrogen.mesh', 'payload': {}}}).encode(), addr)
                time.sleep(0.3)
                self.assertEqual(bridge.received, 1)
            finally:
                bridge.close()
                bridge.thread.join(timeout=4)
                udp.close()
                http.shutdown()
                http.server_close()

class PreservedEngineTests(unittest.TestCase):

    def test_all_active_models_and_unicode(self):
        sys.path.insert(0, str(Path(__file__).parent / 'legacy'))
        from .legacy.sovereign_engine import SovereignEngine
        result = SovereignEngine().process('Hello 🌍')
        self.assertEqual(result['utf8_bytes'], len('Hello 🌍'.encode()))
        self.assertEqual(len(result['modules']), 8)
        self.assertIn('dyson_power_model_w', result)
        self.assertIn('biosphere_carrier_hz', result)

    def test_runtime_returns_processed_input_to_client(self):
        from .hydrogen_mesh import Runtime
        with temporary() as tmp:
            path = Path(tmp)
            (path / 'settings.json').write_text(json.dumps(dict(apps_root=tmp, flux_database=str(path / 'absent.db'), observatory_connection=str(path / 'absent.json'), broadcast_port=0)))
            runtime = Runtime(path, 0)
            received = []
            client = MeshClient('runtime-probe', runtime.server.connection, on_event=received.append, replay=True)
            try:
                self.assertFalse(runtime.catalog['scanned'])
                runtime.scan()
                wait_for(lambda: runtime.catalog.get('scanned'))
                client.publish('compute.request', {'text': '0001 🌍'}, target='hydrogen')
                wait_for(lambda: any((e['topic'] == 'hydrogen.result' for e in received)), 10)
                response = next((e for e in received if e['topic'] == 'hydrogen.result'))
                self.assertIn('hydrogen', response['route'])
                self.assertIn('runtime-probe', response['route'])
                self.assertIn('0001', response['data']['result']['command'])
                self.assertEqual(runtime.errors.__len__(), 0)
                initial = runtime.ledger.latest()
                time.sleep(0.4)
                self.assertEqual(runtime.ledger.latest(), initial)
            finally:
                client.close()
                runtime.close()
