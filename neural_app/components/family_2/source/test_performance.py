import hashlib
import json
import os
from pathlib import Path
import tempfile
from neural_app import section_threads as threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from ..source.hub import database, initialize_database, LocalInferenceHubServer
from ..source.library import LibraryStore
from ..source.pipeline import DataPipeline
from ..source.routing import run_model, flux_record, dispatch_operation, Trajectory

class DatabaseContentionTests(unittest.TestCase):

    def test_connection_settings_and_parallel_writers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'db'
            initialize_database(path)
            with database(path) as conn:
                self.assertEqual(conn.execute('PRAGMA journal_mode').fetchone()[0], 'wal')
                self.assertEqual(conn.execute('PRAGMA busy_timeout').fetchone()[0], 5000)
                self.assertEqual(conn.execute('PRAGMA synchronous').fetchone()[0], 1)
            hubs = [LocalInferenceHubServer(db_path=path) for _ in range(4)]

            def write(index):
                for step in range(20):
                    hubs[index].emplace_node(f'{index}:{step}', 'contention check', 'good')
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(write, range(4)))
            with database(path) as conn:
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM inference_nodes').fetchone()[0], 80)
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM node_events').fetchone()[0], 80)
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            store = LibraryStore(Path(folder) / 'library.db')
            with store.connect() as conn:
                self.assertEqual(conn.execute('PRAGMA journal_mode').fetchone()[0], 'wal')

    def test_wait_for_short_writer_without_losing_update(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'db'
            hub = LocalInferenceHubServer(db_path=path)
            locked = threading.Event()

            def occupy():
                with database(path) as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    locked.set()
                    time.sleep(0.15)
            thread = threading.Thread(target=occupy)
            thread.start()
            self.assertTrue(locked.wait(2))
            hub.emplace_node('after-lock', 'test', 'evil')
            thread.join()
            self.assertEqual(hub.rows()[0]['corrected_bit'], 1)

    def test_batch_deduplicates_and_keeps_every_unique_input(self):
        with tempfile.TemporaryDirectory() as folder:
            engine = DataPipeline(Path(folder) / 'db', False)
            records = [('burst', str(i), {'value': i}, {}, False, False) for i in range(40)]
            identities = engine.submit_many(records + records)
            self.assertEqual(sum((i is not None for i in identities)), 40)
            self.assertEqual(engine.stats(), {'QUEUED': 40})
            with database(engine.db_path) as conn:
                plan = str(conn.execute("EXPLAIN QUERY PLAN SELECT * FROM pipeline_jobs WHERE status='QUEUED' ORDER BY created_at,rowid LIMIT 1").fetchall()[0][3])
                self.assertIn('pipeline_pending', plan)

class DispatcherTests(unittest.TestCase):

    def test_cast_back_matches_every_named_flux_register(self):
        result = run_model(bits=(False, True), states=('good', 'evil'), evaluations=('evil', 'good'))
        cast = dispatch_operation('CAST_BACK_ALL()', result)
        self.assertEqual(cast['status'], 'EXECUTED')
        record = flux_record(result)
        data = cast['result']
        self.assertEqual([bool(int(x)) for x in data['output_bits']], record['after'])
        self.assertEqual(data['output_sha256'], hashlib.sha256(bytes.fromhex(data['output_hex'])).hexdigest())
        self.assertEqual(len(data['register_names']), 16)
        self.assertEqual(data['decimal'], sum((t * 3 ** i for i, t in enumerate(reversed(data['balanced_ternary'])))))

    def test_forecast_holds_good_false_and_inverts_evil_next_pass(self):
        result = run_model(bits=(False, False), states=('good', 'evil'), evaluations=('good', 'evil'), trajectory=Trajectory(state='good'))
        prediction = dispatch_operation('BIT_FORECAST', result)['result']
        self.assertEqual(prediction['current_bits'], [False, True])
        self.assertEqual(prediction['selected_next_bits'], [False, False])
        self.assertFalse(result['trajectory']['can_after'])
        self.assertEqual([r['status'] for r in result['operation_trace'][:2]], ['EXECUTED', 'EXECUTED'])
        self.assertIn('not supplied', result['operation_trace'][2]['status'])

class RefreshTests(unittest.TestCase):

    def test_hidden_views_skip_rendering_but_records_survive_and_open_current(self):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from ..source import app as app
        from ..source.monitor import SystemBusMonitor
        from ..source.observatory import evaluate_payload
        application = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            monitor = SystemBusMonitor()
            monitor.sample_once()
            window = app.GraphicalVirtueMatrixEngine(monitor, folder, start_services=False)
            try:
                window.last_extension_tick = 0
                window.tick_extensions()
                with patch.object(window.obs_json, 'setPlainText', wraps=window.obs_json.setPlainText) as obs, patch.object(window.pipeline_result, 'setPlainText', wraps=window.pipeline_result.setPlainText) as pipeline:
                    for i in range(20):
                        audit = evaluate_payload({'state': 'evil', 'can': False, 'id': i + 100})
                        window.observatory.events.append({'receipt_id': str(i), 'module_id': str(i), 'result': audit})
                        window.pipeline.events.put({'id': str(i), 'source': 'test', 'status': 'COMPLETE', 'audit': audit})
                    window.last_extension_tick = 0
                    window.tick_extensions()
                    self.assertEqual(obs.call_count, 0)
                    self.assertEqual(pipeline.call_count, 0)
                    self.assertEqual(window.pipeline.stats()['QUEUED'], 20)
                    with database(window.hub.db_path) as conn:
                        self.assertEqual(conn.execute("SELECT COUNT(*) FROM execution_ledger WHERE kind IN ('PIPELINE','OBSERVATORY')").fetchone()[0], 40)
                    window.navigate(11)
                    self.assertEqual(obs.call_count, 1)
                    self.assertIn('"module_id": "19"', window.obs_json.toPlainText())
                    window.navigate(15)
                    self.assertEqual(pipeline.call_count, 1)
                window.command_input.setPlainText('CAST_BACK_ALL()')
                window.run_input()
                self.assertEqual(window.last_command['result']['status'], 'EXECUTED')
                with patch.object(window.hub, 'rows', side_effect=RuntimeError('temporary database failure')):
                    window.pages.setCurrentIndex(0)
                    window.last_extension_tick = 0
                    window.tick_extensions()
                    window.pages.setCurrentIndex(9)
                    window.last_extension_tick = 0
                    with self.assertRaises(RuntimeError):
                        window.tick_extensions()
                    self.assertFalse(window.batching_inputs)
            finally:
                window.close()
