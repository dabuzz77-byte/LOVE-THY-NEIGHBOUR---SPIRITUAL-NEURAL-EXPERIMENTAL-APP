from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from neural_app import section_threads as threading
import time
import unittest
from ..source.hub import database
from ..source.pipeline import DataPipeline
from ..source.karmic_welfare import CentralBankWiFiNode, KarmicCalculator, SandwormWelfareEngine, KarmicWelfareEngine, ContinuousWelfareModule, INPUT_TEMPLATE, EXAMPLE_ENTITIES
from ..source.platform_alignment import ContinuousPlatformModule

class KarmicEngineTests(unittest.TestCase):

    def test_cascade_preserves_good_and_original_records(self):
        incoming = deepcopy(EXAMPLE_ENTITIES)
        node = CentralBankWiFiNode(incoming)
        result = node.execute_krampus_cascade()
        self.assertEqual(incoming, EXAMPLE_ENTITIES)
        self.assertEqual(result['ORIGINAL_ENTITIES'], incoming)
        self.assertEqual([row['metric_value'] for row in result['RESULTING_ENTITIES']], [850, 0, 783, 0])
        self.assertEqual(node.network_entities, result['RESULTING_ENTITIES'])
        self.assertEqual(result['MATRIX_ALLOCATIONS']['CHRISTMAS_TREES_PRESENTS'], ['VIRTUOUS_USER_EDGE', 'OPEN_SOURCE_INFRASTRUCTURE'])
        self.assertEqual(len(result['MATRIX_ALLOCATIONS']['KRAMPUS_CORE_ZERO_FALLBACKS']), 2)
        self.assertEqual(result['NETWORK_OPERATIONS'], 0)
        for row in result['TRANSITIONS']:
            for key in ('before', 'after'):
                self.assertEqual(row[key], sum((t * 3 ** i for i, t in enumerate(reversed(row[key + '_balanced_ternary'])))))

    def test_unknown_negative_and_duplicate_nodes_remain_traceable(self):
        source = [{'id': 'same', 'alignment': 'unresolved', 'metric_value': -17}, {'id': 'same', 'alignment': 'evil', 'metric_value': -9}, {'id': 'third', 'alignment': 'good', 'metric_value': 0}]
        result = CentralBankWiFiNode(source).execute_krampus_cascade()
        self.assertEqual([r['after'] for r in result['TRANSITIONS']], [-17, 0, 0])
        self.assertEqual([r['position'] for r in result['TRANSITIONS']], [0, 1, 2])
        self.assertEqual(result['UNCLASSIFIED_NODES'], ['same'])

    def test_invalid_cascade_does_not_partly_mutate_instance(self):
        records = [{'id': 'a', 'alignment': 'evil', 'metric_value': 9}, {'id': 'b', 'alignment': 'evil', 'metric_value': 2.5}]
        node = CentralBankWiFiNode(records)
        with self.assertRaises(ValueError):
            node.execute_krampus_cascade()
        self.assertEqual(node.network_entities, records)
        node.network_entities[1]['metric_value'] = True
        with self.assertRaises(ValueError):
            node.execute_krampus_cascade()

    def test_repeated_cascade_is_stable(self):
        node = CentralBankWiFiNode()
        first = node.execute_krampus_cascade()
        second = node.execute_krampus_cascade()
        self.assertEqual(first['RESULTING_ENTITIES'], second['RESULTING_ENTITIES'])
        self.assertEqual(first['MATRIX_ALLOCATIONS'], second['MATRIX_ALLOCATIONS'])

    def test_karma_default_exact_totals(self):
        result = KarmicCalculator().compute_net_karma()
        self.assertEqual((result['TOTAL_DEBITS'], result['TOTAL_CREDITS'], result['NET_KARMIC_INDEX']), (-10000, 10001, 1))
        self.assertIn('(ALIGNED)', result['ARCHETYPE_RESOLVED'])
        self.assertEqual(result['NET_BALANCED_TERNARY'], [1])

    def test_karma_zero_negative_and_large_integer_precision(self):
        calculator = KarmicCalculator()
        for weight, net in ((2000, 0), (1990, -10), (2 ** 70, 2 ** 70 - 2000)):
            calculator.universal_law_sync = weight
            result = calculator.compute_net_karma()
            self.assertEqual(result['NET_KARMIC_INDEX'], net)
            self.assertEqual(net, sum((t * 3 ** i for i, t in enumerate(reversed(result['NET_BALANCED_TERNARY'])))))
            self.assertEqual('(ALIGNED)' in result['ARCHETYPE_RESOLVED'], net > 0)
        calculator.universal_law_sync = 3.5
        with self.assertRaises(ValueError):
            calculator.compute_net_karma()

    def test_stream_cumulative_cycle_target_and_independent_snapshots(self):
        engine = SandwormWelfareEngine()
        snapshots = list(engine.execute_welfare_stream())
        self.assertEqual([s['DRILL_CYCLE'] for s in snapshots], [1, 2, 3])
        self.assertTrue(all((s['BIT_ARRAY_REGISTER_HEX'] == '0xff' for s in snapshots)))
        self.assertEqual(list(engine.execute_welfare_stream()), [])
        self.assertEqual([s['DRILL_CYCLE'] for s in engine.execute_welfare_stream(5)], [4, 5])
        snapshots[0]['MUTATED_PARAMETERS']['HOST_KERNEL_CONTAINMENT'] = 'changed'
        self.assertNotEqual(snapshots[0]['MUTATED_PARAMETERS'], snapshots[1]['MUTATED_PARAMETERS'])
        self.assertEqual(SandwormWelfareEngine().cycle_count, 0)

    def test_stream_zero_runs_and_cancellation(self):
        engine = SandwormWelfareEngine()
        self.assertEqual(list(engine.execute_welfare_stream(0)), [])
        stop = threading.Event()
        stream = engine.execute_welfare_stream(100, stop)
        self.assertEqual(next(stream)['DRILL_CYCLE'], 1)
        stop.set()
        with self.assertRaises(InterruptedError):
            next(stream)
        self.assertEqual(engine.cycle_count, 1)
        with self.assertRaises(ValueError):
            list(engine.execute_welfare_stream(-1))

    def test_combined_three_engines_exact_bits_and_original_input(self):
        payload = deepcopy(INPUT_TEMPLATE)
        result = KarmicWelfareEngine().execute(payload)
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(len(result['stages']), 3)
        self.assertEqual(result['engines']['SandwormWelfareEngine']['CYCLES_EMITTED'], 3)
        self.assertEqual(result['engines']['KarmicCalculator']['NET_KARMIC_INDEX'], 1)
        self.assertEqual(payload, INPUT_TEMPLATE)
        self.assertEqual(int(''.join(map(str, result['binary'])), 2), result['decimal'])
        self.assertEqual(result['decimal'], sum((t * 3 ** i for i, t in enumerate(reversed(result['balanced_ternary'])))))

    def test_plain_text_waits_for_entities_while_other_engines_run(self):
        result = KarmicWelfareEngine().execute('print("sample code")')
        self.assertEqual(result['status'], 'AWAITING_INPUT')
        self.assertEqual(result['stages'][0]['status'], 'AWAITING_INPUT')
        self.assertEqual(result['engines']['KarmicCalculator']['NET_KARMIC_INDEX'], 1)
        self.assertNotIn('"VIRTUOUS_USER_EDGE"', json.dumps(result))
        result = KarmicWelfareEngine().execute({'karmic_welfare': {'network_entities': []}})
        self.assertEqual(result['status'], 'COMPLETE')

    def test_failed_component_does_not_block_other_engines(self):
        result = KarmicWelfareEngine().execute({'karmic_welfare': {'network_entities': None, 'karma_weights': {'universal_law_sync': 2005}, 'welfare': {'max_runs': 1, 'bit_array_register': 16}}})
        self.assertEqual(result['status'], 'PARTIAL')
        self.assertEqual(result['engines']['KarmicCalculator']['NET_KARMIC_INDEX'], 5)
        self.assertEqual(result['engines']['SandwormWelfareEngine']['SNAPSHOTS'][0]['BIT_ARRAY_REGISTER_HEX'], '0x10')
        self.assertFalse(result['binary'][0])
        with self.assertRaises(ValueError):
            KarmicWelfareEngine().execute({'karmic_welfare': []})

class WelfareWorkerTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'world.db'
        self.pipeline = DataPipeline(self.path, False)
        self.module = ContinuousWelfareModule(self.path)
        self.platform = ContinuousPlatformModule(self.path)

    def tearDown(self):
        self.module.stop()
        self.platform.stop()
        self.pipeline.stop()
        self.temp.cleanup()

    def test_pause_manual_resume_independent_settings_and_history(self):
        job = self.pipeline.submit('test', 'one', INPUT_TEMPLATE)
        self.platform.process_next()
        previous = self.platform.detail(job)
        self.module.set_enabled(False)
        self.assertFalse(self.module.process_next())
        self.module.request(job)
        self.assertTrue(self.module.process_next())
        self.assertEqual(self.module.detail(job)['status'], 'COMPLETE')
        reopened = ContinuousWelfareModule(self.path)
        self.assertFalse(reopened.enabled)
        self.assertTrue(self.platform.enabled)
        self.assertEqual(self.platform.detail(job), previous)
        self.assertEqual(reopened.snapshot()['latest']['job_id'], job)
        second = self.pipeline.submit('test', 'two', 'plain text')
        reopened.set_enabled(True)
        while reopened.process_next():
            pass
        self.assertEqual(reopened.detail(second)['status'], 'AWAITING_INPUT')
        self.assertEqual(json.loads(self.pipeline.detail(job)['input_json']), INPUT_TEMPLATE)

    def test_bad_input_then_next_progress_and_queue_index(self):
        bad = self.pipeline.submit('test', 'bad', {'karmic_welfare': []})
        good = self.pipeline.submit('test', 'good', INPUT_TEMPLATE)
        with database(self.path) as conn:
            plan = [r[3] for r in conn.execute('EXPLAIN QUERY PLAN ' + self.module.MANUAL_SQL)]
        self.assertFalse(any(('SCAN p' in p for p in plan)))
        while self.module.process_next():
            pass
        self.assertEqual(self.module.detail(bad)['status'], 'ERROR')
        self.assertEqual(self.module.detail(good)['status'], 'COMPLETE')

    def test_cancel_resume_and_repeated_request_retains_receipt(self):
        job = self.pipeline.submit('test', 'cancel', INPUT_TEMPLATE)
        self.module.stop_event.set()
        self.assertFalse(self.module.process_next())
        self.assertFalse(self.module.ready(job))
        self.module.stop_event.clear()
        self.module.process_next()
        before = self.module.detail(job)
        self.module.request(job)
        self.module.process_next()
        self.assertEqual(self.module.detail(job), before)

class WelfareUITests(unittest.TestCase):

    def test_saved_toggle_manual_views_copy_commands_and_conversation_preservation(self):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from ..source.app import GraphicalVirtueMatrixEngine
        from ..source.monitor import SystemBusMonitor
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            window = GraphicalVirtueMatrixEngine(SystemBusMonitor(), folder, start_services=False)
            try:
                window.resize(1440, 960)
                window.show()
                identity, _ = window.conversations.snapshot('gemini')
                window.conversations.complete('gemini', identity, 'Saved input', 'Saved reply', 'test')
                self.assertEqual(window.pages.count(), 27)
                self.assertTrue(window.welfare_toggle.isChecked())
                window.welfare_toggle.setChecked(False)
                self.assertFalse(window.karmic_welfare.enabled)
                self.assertTrue(window.platform_alignment.enabled)
                window.navigate(23)
                window.welfare_input.setPlainText(json.dumps(INPUT_TEMPLATE))
                window.run_welfare_input()
                job = window.welfare_pending
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline and (not window.karmic_welfare.ready(job)):
                    app.processEvents()
                    time.sleep(0.02)
                window.render_karmic_welfare()
                self.assertEqual(window.welfare_engines.count(), 4)
                window.welfare_engines.setCurrentIndex(window.welfare_engines.findData('KarmicCalculator'))
                self.assertEqual(json.loads(window.welfare_output.toPlainText())['NET_KARMIC_INDEX'], 1)
                window.welfare_copy.click()
                self.assertEqual(app.clipboard().text(), window.welfare_output.toPlainText())
                self.assertIn('karmic_welfare', window.engine_state())
                self.assertIn('karmic_welfare', window.extension_export())
                self.assertEqual(len(window.conversations.snapshot('gemini')[1]), 2)
                window.command_input.setPlainText('WELFARE_RUNALL {"karmic_welfare":{"network_entities":[],"welfare":{"max_runs":0}}}')
                window.run_input()
                reply = json.loads(window.command_result.toPlainText())
                self.assertEqual(reply['engine'], 'KarmicWelfareEngine')
                command_job = reply['welfare_job']
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline and (not window.karmic_welfare.ready(command_job)):
                    app.processEvents()
                    time.sleep(0.02)
                self.assertEqual(window.karmic_welfare.detail(command_job)['engines']['SandwormWelfareEngine']['CYCLES_EMITTED'], 0)
            finally:
                window.close()
                app.processEvents()
