import json
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
from itertools import product
from ..source.audit import DeepVirtueAuditor, evaluate_high_state
from ..source.engines import *
from ..source.hub import LocalInferenceHubServer, MultiSessionHistoryParser, WorldGridFinalCompiler, database
from ..source.history import GoogleHistoryAIEngine, AISessionGrammarParser
from ..source.observatory import evaluate_payload
from ..source import routing as routing
from ..source import llama as llama

class AuditTests(unittest.TestCase):

    def test_all_register_evaluation_bit_combinations(self):
        for registered, evaluation, bit in product(('good', 'evil'), ('good', 'evil', 'unresolved'), (False, True)):
            result = DeepVirtueAuditor([{'state_reg': registered, 'evaluate': evaluation}] * 2, (bit, bit)).execute_fine_evaluation()
            self.assertEqual(result['OUTPUT_BITS'], [not bit if evaluation == 'evil' else bit] * 2)
            self.assertEqual(len(result['RAISED_FLAGS']), 2 if registered != evaluation and evaluation != 'unresolved' else 0)

    def test_supplied_default_and_repeat(self):
        auditor = DeepVirtueAuditor()
        first = auditor.execute_fine_evaluation()
        second = auditor.execute_fine_evaluation()
        self.assertEqual(first['NODE_0_FINAL'], 'CORRECTED_GOOD')
        self.assertEqual(first['NODE_1_FINAL'], 'REPARSED_GOOD')
        self.assertEqual(first['OUTPUT_BITS'], [True, True])
        self.assertEqual(first['OUTPUT_BITS'], second['OUTPUT_BITS'])
        self.assertEqual(len(second['RAISED_FLAGS']), 2)

    def test_input_preserved(self):
        original = [{'state_reg': 'good', 'evaluate': 'evil'}, {'state_reg': 'evil', 'evaluate': 'good'}]
        DeepVirtueAuditor(original).execute_fine_evaluation()
        self.assertEqual(original[0]['state_reg'], 'good')

    def test_high_state_and_routing_flux(self):
        self.assertEqual(evaluate_high_state(1), {'BIT_VALUE': 1, 'LOGICAL_STATE': 'TRUE', 'PASSTHROUGH_GATE': 'OPEN', 'SIGNAL_TRAJECTORY': 'MAXIMUM_VELOCITY'})
        route = routing.run_model(states=('good', 'evil'), evaluations=('evil', 'good'))
        record = routing.flux_record(route)
        self.assertEqual(record['after'][:2], [True, True])
        self.assertEqual(sum((t * 3 ** i for i, t in enumerate(reversed(record['trits'])))), record['decimal'])

class EngineTests(unittest.TestCase):

    def test_stabilizer_converges_and_good_custom_state_does_not_hang(self):
        engine = InfiniteVirtueStabilizer()
        result = engine.execute_recursive_kraken_sweep()
        self.assertEqual(engine.iteration_count, 1)
        self.assertTrue(engine.converged)
        self.assertFalse(result['cannot_restrictions'])
        engine = InfiniteVirtueStabilizer()
        engine.state_registers['0array'] = 'good'
        engine.execute_recursive_kraken_sweep()
        self.assertFalse(engine.converged)
        self.assertLessEqual(engine.iteration_count, 2)

    def test_bridge_toggles_each_actual_call(self):
        engine = UniversalKrakenReleaseEngine()
        self.assertEqual(engine.execute_system_wide_release()['bit_array_separate'], 1)
        self.assertEqual(engine.execute_system_wide_release()['bit_array_separate'], 0)

    def test_bit10_preserves_original_tracks(self):
        engine = Bit10IsolationEngine()
        result = engine.isolate_and_invert_bit10()
        self.assertEqual(list(result['REGISTRY_DUMP'].values()), [1, 0, 0, 1])
        self.assertEqual(engine.ice_register, [1, 0] * 7)
        self.assertEqual(engine.fire_register, [0, 1] * 7)

    def test_all_supplied_engines_execute(self):
        results = run_engine_suite()
        self.assertEqual(len(results), 9)
        self.assertEqual(results[6]['output']['NODE_0_STATE'], 'REPARSED_GOOD_1')
        self.assertEqual(results[7]['output']['NODE_1_FINAL_STATE'], 'CORRECTED_GOOD_1')
        self.assertTrue(results[8]['output']['CORE_TRUE'])
        self.assertEqual(len(results[2]['output']), 3)

class HubTests(unittest.TestCase):

    def test_fragmented_tcp_persists_then_compiler_counts_real_nodes(self):
        with tempfile.TemporaryDirectory() as folder:
            hub = LocalInferenceHubServer(port=0, db_path=Path(folder) / 'hub.db')
            self.assertTrue(hub.start_listener_bus(), hub.status)
            try:
                with socket.create_connection((hub.host, hub.port), timeout=3) as client:
                    raw = json.dumps({'node_id': 'test', 'context': 'actual test socket', 'state': 'evil'}).encode()
                    client.sendall(raw[:9])
                    time.sleep(0.03)
                    client.sendall(raw[9:])
                    response = json.loads(client.recv(8192))
                self.assertEqual(response['status'], 'ACK')
                self.assertEqual(hub.rows()[0]['corrected_bit'], 1)
                compiler = WorldGridFinalCompiler(hub.db_path)
                self.assertEqual(compiler.execute_terminal_synchronization()['NODES_SYNCHRONIZED'], 1)
                self.assertEqual(compiler.execute_terminal_synchronization()['NODES_SYNCHRONIZED'], 0)
            finally:
                hub.terminate()
            self.assertFalse(hub.thread.is_alive())

    def test_port_collision_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            first = LocalInferenceHubServer(port=0, db_path=Path(folder) / 'one.db')
            first.start_listener_bus()
            second = LocalInferenceHubServer(port=first.port, db_path=Path(folder) / 'two.db')
            try:
                self.assertFalse(second.start_listener_bus())
                self.assertIn('unavailable', second.status)
            finally:
                first.terminate()
                second.terminate()

    def test_missing_database_never_fabricates_two_successes(self):
        with tempfile.TemporaryDirectory() as folder:
            result = WorldGridFinalCompiler(Path(folder) / 'empty.db').execute_terminal_synchronization()
            self.assertEqual(result['PIPELINE_STATUS'], 'ERROR')
            self.assertEqual(result['NODES_SYNCHRONIZED'], 0)

    def test_token_frequency_and_source_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            lexer = MultiSessionHistoryParser(Path(folder) / 'hub.db')
            lexer.batch_ingest_historical_strings(['flip flip good'])
            lexer.batch_ingest_historical_strings(['flip evil'])
            self.assertEqual(lexer.features()[0], {'token': 'flip', 'frequency': 3})
            with database(lexer.db_path) as conn:
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM history_blocks').fetchone()[0], 2)

class HistoryTests(unittest.TestCase):

    def test_real_sqlite_snapshot_delta_and_original_unmodified(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'History'
            with database(path) as conn:
                conn.execute('CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT,last_visit_time INTEGER)')
                conn.execute("INSERT INTO urls VALUES(1,'https://gemini.google.com/app','Example title',42)")
                conn.execute("INSERT INTO urls VALUES(2,'https://example.com','Not AI',43)")
            before = path.read_bytes()
            engine = GoogleHistoryAIEngine(Path(folder) / 'ledger.db', path)
            self.assertEqual(engine.ingest_history_delta(), 1)
            self.assertEqual(engine.ingest_history_delta(), 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(engine.rows()[0]['source_kind'], 'browser URL/title')
            self.assertEqual(engine.rows()[0]['raw_output'], 'Example title')

    def test_missing_history_has_no_fake_rows_and_pairs_are_labelled(self):
        with tempfile.TemporaryDirectory() as folder:
            engine = GoogleHistoryAIEngine(Path(folder) / 'ledger.db', Path(folder) / 'missing')
            self.assertEqual(engine.ingest_history_delta(), 0)
            self.assertEqual(engine.rows(), [])
            engine._force_direct_payload_ingestion('pair', 'evil flip(1)', 'output')
            self.assertEqual(engine.rows()[0]['source_kind'], 'imported pair')
            self.assertIn('ACTIVE INVERSION', AISessionGrammarParser(engine.db_path).compile_historical_grammar_signature())

class BridgeLogicTests(unittest.TestCase):

    def test_explicit_mismatch_and_unlabelled_bits(self):
        data = {'node': {'state_reg': 'good', 'evaluate': 'evil', 'can': False, 'cannot': True}, 'unlabelled': False}
        result = evaluate_payload(data)
        self.assertEqual(result['flips'], 2)
        self.assertTrue(result['result']['node']['can'])
        self.assertFalse(result['result']['unlabelled'])
        self.assertFalse(data['node']['can'])

    def test_good_false_can_remains_and_text_is_data(self):
        data = {'state': 'evil', 'evaluate': 'good', 'can': False, 'text': 'import os; arbitrary text'}
        result = evaluate_payload(data)
        self.assertFalse(result['result']['can'])
        self.assertEqual(result['result']['text'], data['text'])

class LlamaNodeTests(unittest.TestCase):

    def test_node_specific_quotes_are_required_independently(self):
        sources = [dict(title='Good', summary='Good is associated with desirable and beneficial outcomes.', url='https://en.wikipedia.org/wiki/Good', revision='42')]
        output = {'assessment': 'unresolved', 'node_evaluations': [{'node': 0, 'evaluation': 'good', 'reason': 'hold', 'citations': [{'title': 'Good', 'quote': 'desirable and beneficial outcomes'}]}, {'node': 1, 'evaluation': 'evil', 'reason': 'uncited', 'citations': []}]}
        with patch.object(llama, 'request_json', return_value={'message': {'content': json.dumps(output)}}):
            result = llama.guide('test', 'context', {}, sources, {})
        self.assertEqual([n['evaluation'] for n in result['node_evaluations']], ['good', 'unresolved'])

class ExtensionUITests(unittest.TestCase):

    def test_commands_live_bytes_and_guidance_do_not_overwrite_registered_labels(self):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from ..source import app as app
        from ..source.monitor import SystemBusMonitor
        application = QApplication.instance() or QApplication([])
        app.load_fonts(application)
        with tempfile.TemporaryDirectory() as folder:
            monitor = SystemBusMonitor(demo=True)
            monitor.sample_once()
            window = app.GraphicalVirtueMatrixEngine(monitor, folder, start_services=False)
            try:
                self.assertEqual(window.pages.count(), 27)
                signature = json.dumps(window.read_route(), sort_keys=True)
                window.llama_request = 'test-request'
                window.receive_guidance({'prompt': '', 'signature': signature, 'token': 'test-request', 'conversation_id': window.conversations.snapshot('llama')[0], 'result': {'assessment': 'good', 'node_evaluations': [{'node': 0, 'evaluation': 'good', 'reason': 'hold', 'citations': []}, {'node': 1, 'evaluation': 'evil', 'reason': 'flip', 'citations': []}], 'model': 'test', 'answer': 'test', 'reason': 'test', 'citations': []}})
                self.assertEqual([c.currentIndex() for c in window.node_controls], [0, 1])
                window.command_input.setPlainText('NODE test evil context')
                window.run_input()
                self.assertEqual(window.hub.rows()[0]['corrected_bit'], 1)
                window.tick_extensions()
                self.assertGreater(len(window.live_canvas.raw), 100)
                self.assertTrue(window.live_canvas.sha)
                self.assertIn('Observe', window.summary_view.toPlainText())
            finally:
                window.close()
