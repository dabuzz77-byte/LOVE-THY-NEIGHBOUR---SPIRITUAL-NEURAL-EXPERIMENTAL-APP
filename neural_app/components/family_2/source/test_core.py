"""Core behavior, failure recovery, live process lifecycle, and UI integration tests."""
from neural_app import capture_output as contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from ..source import routing as routing
from ..source import monitor as monitor
from ..source.library import LibraryStore, LibrarySync, fetch_article
from ..source import llama as llama

class RoutingTests(unittest.TestCase):

    def test_all_node_combinations(self):
        from itertools import product
        for bits in product((False, True), repeat=2):
            for states in product(('good', 'evil'), repeat=2):
                expected = [not b if s == 'evil' else b for b, s in zip(bits, states)]
                for mode in ('PASS', 'FAIL'):
                    self.assertEqual(routing.resolve_nodes(bits, states, mode), expected)

    def test_good_false_can_is_preserved(self):
        result = routing.Trajectory(stored_bit=False, state='good').resolve()
        self.assertFalse(result['can_after'])
        self.assertTrue(result['cannot_after'])
        self.assertFalse(result['corrective_shift'])

    def test_evil_false_can_is_corrected(self):
        result = routing.Trajectory(stored_bit=False, state='evil').resolve()
        self.assertTrue(result['can_after'])
        self.assertFalse(result['cannot_after'])
        self.assertFalse(result['local_can_before'])

    def test_alternative_encoding(self):
        result = routing.Trajectory(stored_bit=True, false_is_one=True, state='evil').resolve()
        self.assertFalse(result['local_can_before'])
        self.assertTrue(result['can_after'])
        self.assertFalse(result['stored_bit_after'])

    def test_good_alternative_encoding_preserved(self):
        result = routing.Trajectory(stored_bit=True, false_is_one=True, state='good').resolve()
        self.assertFalse(result['can_after'])
        self.assertTrue(result['stored_bit_after'])

    def test_true_can_is_not_inverted_by_capability_correction(self):
        result = routing.Trajectory(stored_bit=True, state='evil').resolve()
        self.assertTrue(result['can_after'])
        self.assertFalse(result['corrective_shift'])

    def test_second_flip_restores_bits(self):
        self.assertEqual(routing.corrective_shift([False, True])['output'], [False, True])
        self.assertEqual(routing.corrective_shift([False, True], 'good')['output'], [True, False])

    def test_cannot_vectors_correct_in_right_direction(self):
        result = routing.drill_cannot_vectors("cannot help\nI can't move\nordinary text", 'evil')
        self.assertEqual(result['corrected_count'], 2)
        self.assertFalse(result['vectors'][0]['cannot_after'])
        self.assertTrue(result['vectors'][0]['can_after'])
        self.assertIsNone(result['vectors'][2]['can_after'])

    def test_good_cannot_vectors_hold(self):
        vector = routing.drill_cannot_vectors('cannot do it', 'good')['vectors'][0]
        self.assertTrue(vector['cannot_after'])
        self.assertFalse(vector['can_after'])

    def test_ternary_roundtrip_signed_values(self):
        for value in range(-2000, 2001):
            digits = routing.balanced_ternary(value)
            self.assertTrue(all((d in {-1, 0, 1} for d in digits)))
            self.assertEqual(sum((d * 3 ** i for i, d in enumerate(reversed(digits)))), value)
        self.assertEqual(routing.balanced_ternary(2), [1, -1])
        self.assertEqual(routing.balanced_ternary(-2), [-1, 1])

    def test_flux_matches_binary_and_ternary(self):
        record = routing.flux_record(routing.run_model())
        self.assertEqual(len(record['after']), 16)
        self.assertEqual(int(''.join((str(int(v)) for v in record['after'])), 2), record['decimal'])
        self.assertEqual(sum((v * 3 ** i for i, v in enumerate(reversed(record['trits'])))), record['decimal'])

class ClassificationTests(unittest.TestCase):

    def test_runtimes_and_case(self):
        for name in ('python.exe', 'PythonW.exe', 'python3.13t', 'python3.12', 'pypy3.exe', 'py.exe'):
            self.assertEqual(monitor.classify(name), 'python', name)
        for name in ('java.exe', 'javaw.exe', 'javaws', 'javac.exe', 'jshell'):
            self.assertEqual(monitor.classify(name), 'java', name)
        for name in ('opera.exe', 'Opera_GX.exe', 'opera_crashreporter.exe'):
            self.assertEqual(monitor.classify(name), 'opera', name)

    def test_not_editor_or_unrelated_arguments(self):
        self.assertIsNone(monitor.classify('notepad.exe', 'C:/python/notepad.exe', ['notepad.exe', 'app.py']))
        self.assertIsNone(monitor.classify('powershell.exe', '', ['powershell.exe', 'echo java python opera']))

    def test_opera_install_helper(self):
        self.assertEqual(monitor.classify('crashpad_handler.exe', 'C:/Apps/Opera GX/100/crashpad_handler.exe'), 'opera')

    def test_java_source_jar_python_module_entries(self):
        self.assertEqual(monitor.entrypoint(['java', 'Main.java'], 'java', 'java'), 'Main.java')
        self.assertEqual(monitor.entrypoint(['java', '-jar', 'app.jar'], 'java', 'java'), 'app.jar')
        self.assertEqual(monitor.entrypoint(['python', '-m', 'http.server'], 'python', 'python'), 'module: http.server')

class MonitorTests(unittest.TestCase):

    def test_demo_is_labelled(self):
        s = monitor.SystemBusMonitor(demo=True).sample_once()
        self.assertEqual(s['mode'], 'DEMO')
        self.assertTrue(all((p['status'] == 'simulated' for p in s['processes'])))

    def test_fatal_scan_retains_previous_sample(self):
        m = monitor.SystemBusMonitor(demo=True)
        first = m.sample_once()
        with patch.object(m, '_demo_sample', side_effect=RuntimeError('test failure')):
            second = m.sample_once()
        self.assertEqual(second['mode'], 'STALE')
        self.assertEqual(first['counts'], second['counts'])
        self.assertEqual(first['timestamp'], second['timestamp'])

    def test_snapshot_is_independent(self):
        m = monitor.SystemBusMonitor(demo=True)
        s = m.sample_once()
        s['counts']['python'] = 9999
        self.assertNotEqual(m.get_counts()['python'], 9999)

    def test_thread_stops_without_waiting_full_interval(self):
        m = monitor.SystemBusMonitor(interval=30, demo=True)
        m.start()
        time.sleep(0.05)
        start = time.monotonic()
        m.stop()
        self.assertFalse(m.thread.is_alive())
        self.assertLess(time.monotonic() - start, 1)

    @unittest.skipUnless(monitor.PSUTIL_ACTIVE, 'psutil needed')
    def test_real_python_process_start_and_exit(self):
        m = monitor.SystemBusMonitor()
        m.sample_once()
        proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(15)'], creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            time.sleep(0.3)
            snapshot = m.sample_once()
            self.assertTrue(any((p['pid'] == proc.pid and p['family'] == 'python' for p in snapshot['processes'])))
            self.assertTrue(any((e['pid'] == proc.pid and e['event'] == 'STARTED' for e in snapshot['events'])))
        finally:
            proc.terminate()
            proc.wait(timeout=5)
        snapshot = m.sample_once()
        self.assertTrue(any((e['pid'] == proc.pid and e['event'] == 'EXITED' for e in snapshot['events'])))

    @unittest.skipUnless(monitor.PSUTIL_ACTIVE, 'psutil needed')
    def test_child_families_and_partial_metadata(self):

        class FakeProcess:

            def __init__(self, pid, ppid, name, denied=False):
                self.pid, self.denied = (pid, denied)
                self.info = dict(pid=pid, ppid=ppid, name=name, exe=name, cmdline=[name], create_time=1)

            def oneshot(self):
                return contextlib.nullcontext()

            def cpu_percent(self, interval=None):
                return 12.0

            def memory_info(self):
                if self.denied:
                    raise monitor.psutil.AccessDenied(self.pid)
                return SimpleNamespace(rss=1024)

            def status(self):
                return 'running'
        processes = [FakeProcess(3, 2, 'worker.exe'), FakeProcess(2, 1, 'helper.exe', True), FakeProcess(1, 0, 'opera.exe')]
        m = monitor.SystemBusMonitor()
        with patch.object(monitor.psutil, 'process_iter', return_value=processes):
            s = m.sample_once()
        self.assertEqual(s['counts']['opera'], 3)
        self.assertEqual(s['partial_processes'], 1)

class LibraryTests(unittest.TestCase):

    def test_cache_search_and_offline_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            store = LibraryStore(Path(temp) / 'lib.db')
            store.save(dict(title='Good', summary='A beneficial outcome', url='https://en.wikipedia.org/wiki/Good', revision='1', revised_at='2026', fetched_at=1))
            self.assertEqual(store.search('beneficial')[0]['title'], 'Good')
            sync = LibrarySync(store, fetcher=lambda title: (_ for _ in ()).throw(OSError('offline')))
            with patch.object(sync.stop_event, 'wait', return_value=False):
                sync.sync_once()
            self.assertEqual(len(store.search()), 1)
            self.assertTrue(sync.get_status()['errors'])

    def test_fetch_redirect_and_missing(self):
        data = {'query': {'pages': [{'title': 'Good', 'extract': 'Source definition', 'fullurl': 'https://en.wikipedia.org/wiki/Good', 'revisions': [{'revid': 123, 'timestamp': 'date'}]}]}}

        def opener(req, timeout):
            return io.BytesIO(json.dumps(data).encode())
        self.assertEqual(fetch_article('Goodness', opener)['revision'], '123')
        data['query']['pages'][0] = {'missing': True}
        with self.assertRaises(ValueError):
            fetch_article('Missing', opener)

class LlamaTests(unittest.TestCase):
    sources = [dict(title='Good', summary='Good is associated with desirable and beneficial outcomes.', url='https://en.wikipedia.org/wiki/Good', revision='42')]

    def test_uncited_assessment_is_not_applied(self):
        reply = {'message': {'content': json.dumps(dict(answer='Example', assessment='evil', reason='Test', citations=[]))}}
        with patch.object(llama, 'request_json', return_value=reply):
            result = llama.guide('test', 'action', {}, self.sources, {})
        self.assertEqual(result['assessment'], 'unresolved')

    def test_source_quote_verified(self):
        reply = {'message': {'content': json.dumps(dict(answer='Example', assessment='good', reason='Test', citations=[dict(title='Good', quote='desirable and beneficial outcomes')]))}}
        with patch.object(llama, 'request_json', return_value=reply):
            result = llama.guide('test', 'action', {}, self.sources, {})
        self.assertEqual(result['assessment'], 'good')
        self.assertEqual(result['citations'][0]['revision'], '42')

    def test_invented_quote_rejected(self):
        reply = {'message': {'content': json.dumps(dict(answer='Example', assessment='evil', reason='Test', citations=[dict(title='Good', quote='This quote does not exist in the source.')]))}}
        with patch.object(llama, 'request_json', return_value=reply):
            result = llama.guide('test', 'action', {}, self.sources, {})
        self.assertEqual(result['assessment'], 'unresolved')

class AppIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from ..source import app as app
        cls.application = QApplication.instance() or QApplication([])
        app.load_fonts(cls.application)

    def test_all_pages_filter_export_and_model(self):
        from ..source import app as app
        with tempfile.TemporaryDirectory() as temp:
            m = monitor.SystemBusMonitor(demo=True)
            m.sample_once()
            window = app.GraphicalVirtueMatrixEngine(m, temp, start_services=False)
            window.show()
            window.tick()
            for i in range(window.pages.count()):
                window.navigate(i)
                self.application.processEvents()
                self.assertFalse(window.grab().isNull())
            window.search.setText('impossible-search-value')
            self.assertEqual(window.process_table.rowCount(), 0)
            window.search.clear()
            self.assertGreater(window.process_table.rowCount(), 0)
            window.cap_state.setCurrentIndex(1)
            window.apply_route('Test good hold')
            self.assertFalse(window.route['trajectory']['can_after'])
            window.cap_state.setCurrentIndex(0)
            window.apply_route('Test evil flip')
            self.assertTrue(window.route['trajectory']['can_after'])
            app.write_export(Path(temp) / 'snapshot.json', window.snapshot, window.route, window.flux_grid.records)
            self.assertEqual(json.loads((Path(temp) / 'snapshot.json').read_text())['model']['trajectory']['can_after'], True)
            app.write_export(Path(temp) / 'snapshot.csv', window.snapshot, window.route, [], True)
            self.assertIn('cpu_percent_machine', (Path(temp) / 'snapshot.csv').read_text(encoding='utf-8-sig'))
            window.close()
