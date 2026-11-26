"""Behavior checks for processing, persistence and bounded read-only networking."""
import json
import math
from pathlib import Path
import tempfile
from neural_app import section_threads as threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
_core = import_module('neural_app.components.family_1.CoreInteractionSystem-Python.core_interaction_system')
APP_DIR, CoreEngine, Framework, Journal, MODES, atomic_write, export_csv, fetch_source, read_small, validate_url = (getattr(_core, name) for name in ['APP_DIR', 'CoreEngine', 'Framework', 'Journal', 'MODES', 'atomic_write', 'export_csv', 'fetch_source', 'read_small', 'validate_url'])

class ProcessingTests(unittest.TestCase):

    def test_full_lifecycle_and_restart(self):
        engine = CoreEngine(Framework(cycles=2))
        engine.enqueue('Manual', 'progress', 0.8)
        engine.start()
        first = engine.tick()
        self.assertGreater(first.output, 0)
        engine.pause()
        self.assertIsNone(engine.tick())
        self.assertEqual(engine.cycle, 1)
        engine.start()
        engine.tick()
        self.assertEqual(engine.state, 'COMPLETE')
        engine.start()
        self.assertEqual(engine.cycle, 0)
        engine.tick()
        self.assertEqual(engine.cycle, 1)

    def test_stop_clears_queue_and_retains_history(self):
        engine = CoreEngine()
        engine.start()
        engine.tick()
        engine.enqueue('Manual', 'queued')
        engine.stop()
        self.assertEqual(len(engine.pending), 0)
        self.assertEqual(len(engine.history), 1)
        self.assertIsNone(engine.tick())

    def test_containment_and_normalized_probabilities(self):
        engine = CoreEngine(Framework(self_response=1, shield_limit=0.1))
        engine.enqueue('Test', 'signal', 1)
        engine.start(MODES[1])
        sample = engine.tick(0.173)
        self.assertTrue(sample.contained)
        self.assertLessEqual(abs(sample.self_value), 0.1)
        self.assertLessEqual(abs(sample.output), 0.1)
        self.assertAlmostEqual(sample.probability_one + sample.probability_zero, 1)

    def test_keyword_scoring(self):
        engine = CoreEngine()
        self.assertEqual(engine.score('progress progress error'), 1 / 3)
        self.assertEqual(engine.score('neutral text'), 0)
        self.assertEqual(engine.score('PROGRESS!'), 1)

    def test_contradictory_identity_is_not_silently_rewritten(self):
        engine = CoreEngine()
        with self.assertRaisesRegex(ValueError, 'Identity'):
            engine.enqueue('Test', '1=0')
        self.assertEqual(len(engine.pending), 0)
        engine.enqueue('Test', '1=1 and 0=0')
        self.assertEqual(len(engine.pending), 1)

    def test_nonfinite_input_and_bounded_queue(self):
        engine = CoreEngine()
        for bad in (float('nan'), float('inf'), -2, 2, True):
            with self.assertRaises(ValueError):
                engine.enqueue('Test', 'input', bad)
        for _ in range(128):
            engine.enqueue('Test', 'input', 0)
        with self.assertRaisesRegex(ValueError, 'full'):
            engine.enqueue('Test', 'one too many')

    def test_baseline_persistence_and_no_degradation(self):
        engine = CoreEngine(Framework(eco_floor=2), {'floor': 3, 'elevation': 4})
        self.assertEqual(engine.floor, 3)
        with self.assertRaisesRegex(ValueError, 'degradation'):
            engine.configure(Framework(eco_floor=2))
        engine.configure(Framework(eco_floor=4))
        self.assertEqual(engine.floor, 4)
        engine.reset_session()
        self.assertEqual(engine.elevation, 4)

    def test_elevation_only_for_accepted_input(self):
        engine = CoreEngine()
        engine.start()
        engine.tick()
        self.assertEqual(engine.elevation, 0)
        engine.enqueue('Test', 'progress')
        engine.tick()
        self.assertGreater(engine.elevation, 0)

    def test_rules_validation(self):
        for text in ('{"frequency_hz": 0}', '{"cycles": 1.5}', '{"cycles": true}', '{"balance_target": NaN}', '{"unknown": 1}', '[]', '{"shield_limit":0.1,"balance_target":0.8}'):
            with self.assertRaises(ValueError):
                Framework.parse(text)
        config = Framework.parse(Framework().text())
        self.assertEqual(config.frequency_hz, 7.83)

    def test_history_is_bounded(self):
        engine = CoreEngine()
        engine.start()
        for _ in range(2500):
            engine.tick()
        self.assertEqual(len(engine.history), 2400)
        self.assertEqual(engine.cycle, 2500)

class StorageTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='core-test-', dir=APP_DIR)
        self.folder = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reopen_saved_state_and_detect_tampering(self):
        path = self.folder / 'journal.sqlite3'
        journal = Journal(path)
        journal.append('start', {}, {'floor': 2, 'elevation': 3})
        journal.append('cycle', {}, {'floor': 2, 'elevation': 4})
        self.assertEqual(journal.verify(), 2)
        journal.close()
        journal = Journal(path)
        self.assertEqual(journal.restore(), {'floor': 2, 'elevation': 4})
        journal.db.execute("UPDATE events SET payload='changed' WHERE id=1")
        journal.db.commit()
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            journal.verify()
        journal.close()

    def test_atomic_write_import_and_csv(self):
        path = self.folder / 'rules.json'
        atomic_write(path, Framework().text())
        self.assertEqual(Framework.parse(read_small(path)).name, Framework().name)
        engine = CoreEngine()
        engine.enqueue('=formula', 'test', 0.5)
        engine.start()
        engine.tick()
        export_csv(self.folder / 'session.csv', engine.history)
        text = read_small(self.folder / 'session.csv')
        self.assertIn("'=formula", text)
        self.assertIn('probability_zero', text)

class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def do_GET(self):
        routes = {'/rss': ('application/rss+xml', b'<rss><channel><title>Test feed</title><item><title>Progress and discovery</title></item></channel></rss>'), '/atom': ('application/atom+xml', b'<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom feed</title><entry><title>Solution</title></entry></feed>'), '/json': ('application/json', b'{"value":123}'), '/html': ('text/html', b'<html><script>hidden_payload</script><style>hidden_style</style><h1>Visible progress</h1></html>'), '/large': ('text/plain', b'x' * (512 * 1024 + 1)), '/binary': ('application/octet-stream', b'binary'), '/entity': ('application/xml', b'<!DOCTYPE rss [<!ENTITY x "expand">]><rss>&x;</rss>'), '/empty': ('text/plain', b'')}
        if self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/rss')
            self.end_headers()
            return
        if self.path not in routes:
            self.send_error(503)
            return
        kind, body = routes[self.path]
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (ConnectionError, OSError):
            pass

class NetworkTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def test_rss_atom_json_html_and_redirect(self):
        for suffix, expected in (('/rss', 'discovery'), ('/atom', 'Solution'), ('/json', '123'), ('/html', 'Visible progress'), ('/redirect', 'discovery')):
            result = fetch_source(self.base + suffix)
            self.assertIn(expected, result['text'])
            self.assertNotIn('hidden_payload', result['text'])
            self.assertGreater(result['bytes'], 0)

    def test_rejected_bodies(self):
        for suffix in ('/large', '/binary', '/entity', '/empty', '/missing'):
            with self.assertRaises(Exception):
                fetch_source(self.base + suffix)

    def test_cancellation(self):
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(InterruptedError):
            fetch_source(self.base + '/rss', cancel)

    def test_url_validation(self):
        for address in ('http://example.com', 'file:///C:/secret', 'https://user:maintainer@example.invalid', 'https://', 'https://example.com:bad'):
            with self.assertRaises(ValueError):
                validate_url(address)
        self.assertEqual(validate_url(' https://example.com '), 'https://example.com')
