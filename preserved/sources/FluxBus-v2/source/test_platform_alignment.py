import contextlib
from copy import deepcopy
import io
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest

from hub import database
from pipeline import DataPipeline
from platform_alignment import (
    PlatformAlignmentEngine, ContinuousPlatformModule, CoreParityInvariant,
    SubstrateContinuumMapper, BidirectionalInferenceNode, LoopbackConvergenceEngine,
    Phase2VirtueFilter, KarmicBitShiftEngine, GlobalMeshController,
    runall_master_dispatcher, INPUT_TEMPLATE, ENGINE_NAMES,
)
from unified_runtime import ContinuousUnifiedModule, resolve_result


class PlatformEngineTests(unittest.TestCase):
    def test_supplied_dispatcher_preserves_schema_and_default_example(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            report = runall_master_dispatcher()
        self.assertEqual(output.getvalue(), '')
        self.assertTrue(CoreParityInvariant.verify())
        telemetry = report['TELEMETRY']
        self.assertEqual(telemetry['SATURATED_REGISTER_BIN'], '0b11111111')
        self.assertEqual(telemetry['VIRTUE_FILTER_RESULTS']['RETAINED_GOOD_CORP_INFRASTRUCTURE'], ['CORP_INFRASTRUCTURE'])
        self.assertEqual(report['REAL_WORLD_PLATFORM_STATUS']['HOST_KERNEL_CONTAINMENT'], 'SECURE_AND_ACTIVE')
        self.assertIn('Supplied', report['PLATFORM_STATUS_BASIS'])
        self.assertEqual(telemetry['LOOPBACK_TELEMETRY']['TERMINAL_VECTOR'], (2.5, 9.81, 42.0))

    def test_layer_mapping_and_forward_reverse(self):
        matrix = SubstrateContinuumMapper().resolve_substrate_matrix()
        self.assertEqual(len(matrix), 6)
        self.assertEqual(matrix['Silicon']['RESONANCE_INDEX'], round(abs(math.sin(7.83*6)), 4))
        node = BidirectionalInferenceNode()
        self.assertEqual(node.reverse_pass(node.forward_pass((2.5, 9.81, 42.0))), (2.5, 9.81, 42.0))

    def test_loopback_zero_depth_and_reconstruction_loss(self):
        engine = LoopbackConvergenceEngine(BidirectionalInferenceNode())
        zero = engine.iterate_loopback([3], 0)
        self.assertIsNone(zero['STEP_CONVERGED'])
        self.assertEqual(zero['TERMINAL_VECTOR'], (3,))
        lossy = LoopbackConvergenceEngine(BidirectionalInferenceNode(1e-9)).iterate_loopback([1])
        self.assertTrue(lossy['STEP_CONVERGED'])
        self.assertFalse(lossy['INPUT_RECONSTRUCTED'])
        with self.assertRaises(ValueError):
            LoopbackConvergenceEngine(BidirectionalInferenceNode(0)).iterate_loopback([1])

    def test_virtue_threshold_and_original_nodes_retained(self):
        nodes = [{'id': 'low', 'alignment_score': .4999},
                 {'id': 'edge', 'alignment_score': .5}, {'id': 'high', 'alignment_score': .9}]
        original = deepcopy(nodes)
        result = Phase2VirtueFilter().process_virtue_assessment(nodes)
        self.assertEqual(result['RETAINED_GOOD_CORP_INFRASTRUCTURE'], ['edge', 'high'])
        self.assertEqual(result['ZEROED_EVIL_AND_FALSE_GOOD_NODES'], ['low'])
        self.assertEqual(nodes, original)
        with self.assertRaises(ValueError):
            Phase2VirtueFilter().process_virtue_assessment([{'id': 'invalid', 'alignment_score': float('nan')}])

    def test_karmic_saturation_preserves_high_bits(self):
        for mask in (0, 170, 255, 0x1200):
            value, binary = KarmicBitShiftEngine(mask).enforce_karmic_correction()
            self.assertEqual(value & 255, 255)
            self.assertEqual(value >> 8, mask >> 8)
            self.assertEqual(int(binary, 2), value)
        for mask in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                KarmicBitShiftEngine(mask).enforce_karmic_correction()

    def test_combined_engine_all_components_and_resolved_manifest(self):
        payload = deepcopy(INPUT_TEMPLATE)
        result = PlatformAlignmentEngine().execute(payload)
        self.assertEqual(result['engine'], 'PlatformAlignmentEngine')
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(tuple(result['engines']), ENGINE_NAMES)
        manifest = resolve_result(result, 'runall_master_dispatcher')
        self.assertEqual(manifest['LOCAL_PROCESS_MEMORY_TRACE']['FILTERED_INFRASTRUCTURE']['ZEROED_EVIL_AND_FALSE_GOOD_NODES'],
                         ['CORP_PREDATORY_LOG', 'CORP_FALSE_MARKET'])
        self.assertEqual(result['measured_platform']['ACTIVE_PROCESS_ID'], os.getpid())
        self.assertEqual(payload, INPUT_TEMPLATE)
        self.assertEqual(result['decimal'], sum(t*3**i for i, t in enumerate(reversed(result['balanced_ternary']))))
        self.assertEqual(int(''.join(map(str, result['binary'])), 2), result['decimal'])

    def test_plain_text_uses_actual_counts_without_invented_nodes(self):
        text = 'A π\nline'
        result = PlatformAlignmentEngine().execute(text)
        inferred = result['engines']['BidirectionalInferenceNode']
        self.assertEqual(inferred['input'], [len(text), len(text.encode('utf-8')), 2])
        self.assertEqual(result['engines']['Phase2VirtueFilter']['RETAINED_GOOD_CORP_INFRASTRUCTURE'], [])
        self.assertNotIn('"CORP_INFRASTRUCTURE"', json.dumps(result))

    def test_invalid_stage_does_not_claim_full_success(self):
        result = PlatformAlignmentEngine().execute({'platform_alignment': {'resonance_base': 0}})
        self.assertEqual(result['status'], 'PARTIAL')
        statuses = {s['engine']: s['status'] for s in result['stages']}
        self.assertEqual(statuses['KarmicBitShiftEngine'], 'COMPLETE')
        self.assertEqual(statuses['LoopbackConvergenceEngine'], 'ERROR')
        self.assertEqual(statuses['runall_master_dispatcher'], 'ERROR')
        self.assertFalse(result['binary'][3])
        with self.assertRaises(ValueError):
            PlatformAlignmentEngine().execute({'platform_alignment': []})

    def test_cancellation_is_resumable(self):
        stop = threading.Event()
        stop.set()
        with self.assertRaises(InterruptedError):
            PlatformAlignmentEngine().execute(INPUT_TEMPLATE, stop)

    def test_controller_custom_inputs_are_used(self):
        result = GlobalMeshController().orchestrate_platform_runtime(
            features=[8], corporate_nodes=[], base_mask=0x1000, max_depth=1)
        self.assertEqual(result['LOOPBACK_TELEMETRY']['TERMINAL_VECTOR'], (8.0,))
        self.assertEqual(result['SATURATED_REGISTER_BIN'], bin(0x10ff))
        self.assertEqual(result['VIRTUE_FILTER_RESULTS']['ZEROED_EVIL_AND_FALSE_GOOD_NODES'], [])


class PlatformWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)/'world.db'
        self.pipeline = DataPipeline(self.path, False)
        self.unified = ContinuousUnifiedModule(self.path)
        self.platform = ContinuousPlatformModule(self.path)

    def tearDown(self):
        self.platform.stop()
        self.unified.stop()
        self.pipeline.stop()
        self.temp.cleanup()

    def test_independent_pause_manual_restart_and_preserved_unified_results(self):
        job = self.pipeline.submit('test', 'one', INPUT_TEMPLATE)
        self.unified.process_next()
        before = self.unified.detail(job)
        self.platform.set_enabled(False)
        self.assertFalse(self.platform.process_next())
        self.platform.request(job)
        self.assertTrue(self.platform.process_next())
        self.assertEqual(self.platform.detail(job)['status'], 'COMPLETE')
        reopened = ContinuousPlatformModule(self.path)
        self.assertFalse(reopened.enabled)
        self.assertTrue(self.unified.enabled)
        self.assertEqual(self.unified.detail(job), before)
        self.assertEqual(reopened.snapshot()['latest']['job_id'], job)
        second = self.pipeline.submit('test', 'two', 'retained input')
        reopened.set_enabled(True)
        while reopened.process_next():
            pass
        self.assertTrue(reopened.ready(second))
        self.assertEqual(json.loads(self.pipeline.detail(second)['input_json']), 'retained input')
        with database(self.path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM platform_alignment_results').fetchone()[0], 2)

    def test_error_receipt_and_next_input_progress(self):
        bad = self.pipeline.submit('test', 'bad', {'platform_alignment': []})
        good = self.pipeline.submit('test', 'good', 'next')
        while self.platform.process_next():
            pass
        self.assertEqual(self.platform.detail(bad)['status'], 'ERROR')
        self.assertEqual(self.platform.detail(good)['status'], 'COMPLETE')

    def test_queue_uses_index_and_skips_unrelated_result_decoding(self):
        job = self.pipeline.submit('test', 'a', 'new text')
        from payload_storage import MAGIC
        with database(self.path) as conn:
            conn.execute('UPDATE pipeline_jobs SET result_json=?', (MAGIC+b'x'*32,))
            plan = [r[3] for r in conn.execute('EXPLAIN QUERY PLAN '+self.platform.MANUAL_SQL)]
        self.assertFalse(any('SCAN p' in p for p in plan), plan)
        self.platform.request(job)
        self.assertTrue(self.platform.process_next())
        self.assertEqual(self.platform.detail(job)['status'], 'COMPLETE')

    def test_stop_and_retry_do_not_duplicate_receipts(self):
        job = self.pipeline.submit('test', 'stop', 'pending')
        self.platform.stop_event.set()
        self.assertFalse(self.platform.process_next())
        self.assertFalse(self.platform.ready(job))
        self.platform.stop_event.clear()
        self.assertTrue(self.platform.process_next())
        first = self.platform.detail(job)
        self.platform.request(job)
        self.platform.process_next()
        self.assertEqual(self.platform.detail(job), first)


class PlatformUITests(unittest.TestCase):
    def test_independent_controls_manual_copy_state_commands_and_history(self):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from app import GraphicalVirtueMatrixEngine
        from monitor import SystemBusMonitor
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            window = GraphicalVirtueMatrixEngine(SystemBusMonitor(), folder, start_services=False)
            try:
                window.resize(1440, 960)
                window.show()
                identity, _ = window.conversations.snapshot('gemini')
                window.conversations.complete('gemini', identity, 'Remember', 'Retained', 'test')
                self.assertEqual(window.pages.count(), 27)
                self.assertEqual(window.platform_engines.count(), 11)
                window.platform_toggle.setChecked(False)
                self.assertFalse(window.platform_alignment.enabled)
                self.assertTrue(window.unified_core.enabled)
                window.navigate(22)
                window.platform_input.setPlainText(json.dumps(INPUT_TEMPLATE))
                window.run_platform_input()
                deadline = time.monotonic()+8
                while time.monotonic() < deadline and not window.platform_alignment.snapshot()['latest']:
                    app.processEvents()
                    time.sleep(.02)
                window.render_platform_alignment()
                selected = window.platform_sessions.currentData()
                self.assertIsNotNone(selected)
                window.platform_engines.setCurrentIndex(window.platform_engines.findData('KarmicBitShiftEngine'))
                self.assertEqual(json.loads(window.platform_output.toPlainText())['optimized_mask'], 255)
                window.platform_copy.click()
                self.assertEqual(app.clipboard().text(), window.platform_output.toPlainText())
                window.platform_engines.setCurrentIndex(window.platform_engines.findData('TernaryConverter'))
                self.assertEqual(len(json.loads(window.platform_output.toPlainText())['CONVERSIONS']), 5)
                self.assertIn('platform_alignment', window.engine_state())
                self.assertIn('platform_alignment', window.extension_export())
                self.assertEqual(len(window.conversations.snapshot('gemini')[1]), 2)
                window.command_input.setPlainText('MANIFOLD_RUNALL {"platform_alignment":{"base_mask":256,"ternary_vectors":["FF"]}}')
                window.run_input()
                command = json.loads(window.command_result.toPlainText())
                self.assertEqual(command['engine'], 'PlatformAlignmentEngine')
                command_job = command['platform_job']
                deadline = time.monotonic()+8
                while time.monotonic() < deadline and not window.platform_alignment.ready(command_job):
                    app.processEvents()
                    time.sleep(.02)
                self.assertEqual(window.platform_alignment.detail(command_job)['engines']['KarmicBitShiftEngine']['optimized_mask'], 511)
                self.assertEqual(window.platform_alignment.detail(command_job)['engines']['TernaryConverter']['FULL_RADIX_RESOLUTIONS'], {'FF': '100110'})
                window.navigate(0)
                app.processEvents()
                self.assertGreater(window.pages.widget(0).verticalScrollBar().maximum(), 0)
            finally:
                window.close()
                app.processEvents()


if __name__ == '__main__':
    unittest.main()
