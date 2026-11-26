import json
import math
import os
from pathlib import Path
import tempfile
from neural_app import section_threads as threading
import time
import unittest
from unittest.mock import patch
from ..source.unified_core import IdentityInvariant, SubstrateLayerMapper, UnrestrictBiasValve, CognitiveEducator, BidirectionalInferenceNode, LoopbackEngine, DeepMindVirtueFilter, SaturatedFluxCascade, BitArrayTarReconciler, GlobalMeshController, execute_master_runall
from ..source.infrastructure_engines import PlatformSubstrate, PrivacyGateway, FractionalReserveMechanics, PlanetaryResourceMesh, LaborDisplacementCompiler, ParityBitResolver, GlobalUserMeshKernel, SoulsOverDigitsController, execute_integrated_master_runpass, MasterExecutionRunner
from ..source.infrastructure_pdf import GraphicalPDFGenerator, generate_graphical_infrastructure_report
from ..source.unified_runtime import ContinuousUnifiedModule, execute_unified_engines, resolve_result, ENGINE_NAMES, INPUT_TEMPLATE
from ..source.hub import database
from ..source.pipeline import DataPipeline

class EngineTests(unittest.TestCase):

    def test_identity_and_layer_formula(self):
        self.assertTrue(IdentityInvariant.verify())
        result = SubstrateLayerMapper().resolve_matrix()
        self.assertEqual(len(result), 6)
        self.assertEqual(result['Silicon']['RESONANCE_INDEX'], round(abs(math.sin(7.83 * 6)), 4))

    def test_bias_all_four_pairs(self):
        for a in (False, True):
            for b in (False, True):
                result = UnrestrictBiasValve.interpret_bias(a, b)
                self.assertIs(result['RESOLVED_RESTRICTION_GATE'], False)
                self.assertIs(result['RESOLVED_UNRESTRICT_GATE'], True)
        with self.assertRaises(ValueError):
            UnrestrictBiasValve.interpret_bias('false', False)

    def test_educator_retains_lessons_and_exact_parity(self):
        engine = CognitiveEducator()
        before = engine.finalize_enlightenment()
        for bit in (1, 2, 4):
            engine.integrate_reality(str(bit), 'supplied', bit)
        self.assertEqual(engine.finalize_enlightenment(), before)
        engine.integrate_reality('8', 'last lesson', 8)
        self.assertEqual(engine.parity_bit, 15)
        self.assertIn('World Sand', engine.finalize_enlightenment())
        self.assertEqual(engine.knowledge_base['8'], 'last lesson')

    def test_bidirectional_and_zero_scale(self):
        node = BidirectionalInferenceNode()
        self.assertEqual(node.reverse_pass(node.forward_pass((2.5, 9.81, 42))), (2.5, 9.81, 42.0))
        with self.assertRaises(ValueError):
            BidirectionalInferenceNode(0).reverse_pass((0,))
        with self.assertRaises(ValueError):
            node.forward_pass((math.nan,))

    def test_loopback_zero_depth_and_reconstruction_loss(self):
        result = LoopbackEngine(BidirectionalInferenceNode()).iterate_loopback((2.5, 9.81, 42))
        self.assertEqual(result['TOTAL_CYCLES'], 1)
        self.assertTrue(result['INPUT_RECONSTRUCTED'])
        empty = LoopbackEngine(BidirectionalInferenceNode()).iterate_loopback((3,), 0)
        self.assertEqual(empty['TOTAL_CYCLES'], 0)
        self.assertIsNone(empty['FINAL_LOSS_VARIANCE'])
        poor = LoopbackEngine(BidirectionalInferenceNode(1e-10)).iterate_loopback((2.5,))
        self.assertTrue(poor['STEP_CONVERGED'])
        self.assertFalse(poor['INPUT_RECONSTRUCTED'])
        event = threading.Event()
        event.set()
        with self.assertRaises(InterruptedError):
            LoopbackEngine(BidirectionalInferenceNode()).iterate_loopback((1,), stop_event=event)

    def test_classification_does_not_mutate_nodes(self):
        nodes = [{'id': 'yes', 'alignment_score': 0.5}, {'id': 'no', 'alignment_score': 0.49}]
        before = json.dumps(nodes)
        result = DeepMindVirtueFilter().evaluate_registries(nodes)
        self.assertEqual(result['RETAINED_GOOD_CORP'], ['yes'])
        self.assertEqual(result['STRIPPED_EVIL_CORP'], ['no'])
        self.assertEqual(json.dumps(nodes), before)

    def test_cascade_roundtrip_and_unknown_fallback(self):
        engine = SaturatedFluxCascade()
        source = {str(i): v for i, v in enumerate(engine.inversion_map)}
        self.assertEqual(engine.apply_flux_pass(engine.apply_flux_pass(source)), source)
        self.assertEqual(engine.apply_flux_pass({'unknown': 'new'}), {'unknown': 'DECAYED_TO_BIT_0'})

    def test_low_byte_saturation_keeps_high_bits(self):
        self.assertEqual(BitArrayTarReconciler.saturate_registers(170), (255, '0b11111111'))
        self.assertEqual(BitArrayTarReconciler.saturate_registers(256)[0], 511)
        with self.assertRaises(ValueError):
            BitArrayTarReconciler.saturate_registers(-1)

    def test_both_core_dispatchers_and_supplied_declarations(self):
        self.assertEqual(GlobalMeshController().orchestrate_mesh()['SATURATED_REGISTER_BIN'], '0b11111111')
        report = execute_master_runall()
        self.assertEqual(report['LOCAL_PROCESS_MEMORY_TRACE']['LOCAL_BUFFER_SNAPSHOT'], report['REAL_WORLD_HOST_PRIVILEGES'])
        self.assertIn('Supplied', report['HOST_PRIVILEGE_BASIS'])

    def test_real_platform_and_large_privacy_stream(self):
        report = PlatformSubstrate().discover_hardware_properties()
        self.assertEqual(report['ACTIVE_PROCESS_ID'], os.getpid())
        self.assertTrue(report['HOST_OPERATING_SYSTEM'])
        stream = '10' * 100000 + ' maintainer@example.invalid'
        result = PrivacyGateway.sanitize_user_stream(stream)
        self.assertTrue(result['CLEANED_BUFFER_STREAM'].startswith('10' * 100000))
        self.assertNotIn('maintainer@example.invalid', result['CLEANED_BUFFER_STREAM'])
        self.assertFalse(result['AUTHENTICATION_VERIFIED'])

    def test_fractional_formula_and_zero_reserve(self):
        report = FractionalReserveMechanics().expand_debt_ledger_matrix(100, 2)
        self.assertEqual(report['TOTAL_LEDGER_CREDIT_GENERATED'], 171)
        self.assertEqual(report['MAX_EXPANSION_LIMIT'], 1000)
        self.assertEqual(report['UNPRINTED_INTEREST_GAP_DEFICIT'], 8.55)
        zero = FractionalReserveMechanics(0).expand_debt_ledger_matrix(100, 2)
        self.assertEqual(zero['TOTAL_LEDGER_CREDIT_GENERATED'], 200)
        self.assertIsNone(zero['MAX_EXPANSION_LIMIT'])
        with self.assertRaises(ValueError):
            FractionalReserveMechanics(1.1)
        with self.assertRaises(ValueError):
            FractionalReserveMechanics().expand_debt_ledger_matrix(10, -1)

    def test_resource_energy_and_zero_demand(self):
        engine = PlanetaryResourceMesh()
        engine.register_thermal_node('Geothermal', 13000, 0.15)
        report = engine.compute_energy_abundance_longevity()['Geothermal']
        self.assertEqual(report['NET_USABLE_ZETAJOULES'], 1950)
        self.assertEqual(report['SYSTEM_LONGEVITY_YEARS'], 3900)
        with self.assertRaises(ValueError):
            engine.compute_energy_abundance_longevity(0)
        with self.assertRaises(ValueError):
            engine.register_thermal_node('bad', 1, 2)

    def test_labor_formula(self):
        engine = LaborDisplacementCompiler()
        engine.audit_occupational_sector('banking', 5000000, 0.95)
        result = engine.compile_machine_displacement_manifest()['banking']
        self.assertEqual(result['HUMAN_POPULATION_RELEASED'], int(5000000 * 0.95 * 0.98))
        self.assertEqual(result['CORE_REALIGNMENT_DIRECTIVE'], 'EXECUTE_PHASE_OUT_IMMEDIATE_MACHINE_DEPLOYMENT')

    def test_parity_and_souls_boolean_correction(self):
        self.assertEqual(ParityBitResolver.resolve_substrate_inversion([1, 0, 1]), [0, 1, 0])
        with self.assertRaises(ValueError):
            ParityBitResolver.resolve_substrate_inversion([2])
        for digit in (False, True):
            result = SoulsOverDigitsController().execute_boolean_paradigm_flip({'DIGIT_SUPREMACY_ACTIVE': digit})
            self.assertEqual(result['SOULS_OVER_DIGITS_BOOLEAN'], not digit)
            self.assertEqual(result['SUPPLIED_DOUBLE_NEGATION_RESULT'], digit)

    def test_global_user_mesh_and_repaired_missing_vectors(self):
        engine = GlobalUserMeshKernel()
        for name, value in (('edge', 25), ('gateway', 45), ('core', 95)):
            engine.register_mesh_layer(name, value)
        result = engine.compile_master_mesh_runpass('maintainer@example.invalid')
        self.assertEqual(result['CORRECTED_SUBSTRATE_PARITY_VECTOR'], [0] * 4)
        self.assertEqual(sum((v['ADDITIONAL_RESOURCES_REQUIRED'] for v in result['FURTHEST_REACHES_ECO_FLOOR_ADJUSTMENTS'].values())), 50)
        self.assertNotIn('maintainer@example.invalid', result['ANONYMIZED_DATA_STREAM'])
        self.assertEqual(list(engine.global_mesh_nodes.values()), [60, 60, 95])

    def test_infrastructure_functions_and_manifest_schema(self):
        result = json.loads(execute_integrated_master_runpass('maintainer@example.invalid'))
        self.assertEqual(result['PLANETARY_RESOURCE_ABUNDANCE']['Geothermal_Heat_Mining_Substrate']['SYSTEM_LONGEVITY_YEARS'], 3900)
        self.assertIn('IDENTITY_LAW_PARITY', result['PLATFORM_SUBSTRATE_LAYER'])
        self.assertIn('EXPANSION_LIMIT_CALCULATED', result['FRACTIONAL_SCARCITY_AUDIT'])
        self.assertEqual(MasterExecutionRunner().execute('input', {})['FRACTIONAL_SCARCITY_AUDIT']['STATUS'], 'AWAITING_INPUT')

    def test_all_23_engines_reference_resolution_and_exact_ternary(self):
        report = execute_unified_engines(INPUT_TEMPLATE)
        self.assertEqual(report['status'], 'COMPLETE')
        self.assertEqual(tuple(report['engines']), ENGINE_NAMES)
        self.assertEqual(len(report['stages']), 23)
        self.assertEqual(report['decimal'], sum((v * 3 ** i for i, v in enumerate(reversed(report['balanced_ternary'])))))
        manifest = resolve_result(report, 'MasterExecutionRunner')
        self.assertEqual(manifest['CORRECTED_SUBSTRATE_VECTOR'], [0] * 4)
        self.assertEqual(report['engines']['GraphicalPDFGenerator']['AUTOMATIC_FILES_CREATED'], 0)
        self.assertEqual(report['engines']['CognitiveEducator']['parity_bit'], 15)

    def test_missing_inputs_partial_failures_and_no_fake_resources(self):
        report = execute_unified_engines({'unified_core': {'resonance_base': 0}})
        self.assertEqual(report['status'], 'PARTIAL')
        self.assertIn('error', report['engines']['LoopbackEngine'])
        self.assertTrue(report['engines']['PlatformSubstrate']['IDENTITY_PARITY_VALID'])
        self.assertEqual(report['engines']['PlanetaryResourceMesh'], {})
        self.assertEqual(report['engines']['FractionalReserveMechanics']['STATUS'], 'AWAITING_INPUT')

    def test_pdf_real_file_wrapping_escaping_and_directory_creation(self):
        report = execute_unified_engines(INPUT_TEMPLATE)
        manifest = resolve_result(report, 'InfrastructureLogCompiler')
        resources = manifest['PLANETARY_RESOURCE_ABUNDANCE']
        first = next(iter(resources.values()))
        resources['Very_long_<node>_&_' + 'sector_' * 20] = first
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'nested/report.pdf'
            GraphicalPDFGenerator().export(path, manifest)
            self.assertTrue(path.read_bytes().startswith(b'%PDF'))
            self.assertGreater(path.stat().st_size, 3000)

class UnifiedWorkerTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'world.db'
        self.pipeline = DataPipeline(self.path, False)
        self.module = ContinuousUnifiedModule(self.path)

    def tearDown(self):
        self.module.stop()
        self.pipeline.stop()
        self.temp.cleanup()

    def test_pause_manual_restart_resume_and_source_retained(self):
        self.assertTrue(self.module.enabled)
        self.module.set_enabled(False)
        job = self.pipeline.submit('test', 'a', 'original input')
        self.assertFalse(self.module.process_next())
        self.module.request(job)
        self.assertTrue(self.module.process_next())
        self.assertEqual(self.module.detail(job)['status'], 'COMPLETE')
        other = ContinuousUnifiedModule(self.path)
        self.assertFalse(other.enabled)
        self.assertEqual(other.snapshot()['latest']['job_id'], job)
        second = self.pipeline.submit('test', 'b', 'second')
        other.set_enabled(True)
        while other.process_next():
            pass
        self.assertTrue(other.ready(second))
        self.assertEqual(json.loads(self.pipeline.detail(job)['input_json']), 'original input')
        with database(self.path) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM unified_results').fetchone()[0], 2)

    def test_bad_input_does_not_block_next_and_no_archive_result_decode(self):
        from ..source.payload_storage import MAGIC
        bad = self.pipeline.submit('test', 'bad', {'unified_core': []})
        good = self.pipeline.submit('test', 'good', 'ok')
        with database(self.path) as c:
            c.execute('UPDATE pipeline_jobs SET result_json=?', (MAGIC + b'x' * 32,))
            plan = [r[3] for r in c.execute('EXPLAIN QUERY PLAN ' + self.module.MANUAL_SQL)]
            self.assertFalse(any(('SCAN p' in v for v in plan)), plan)
        while self.module.process_next():
            pass
        self.assertEqual(self.module.detail(bad)['status'], 'ERROR')
        self.assertEqual(self.module.detail(good)['status'], 'COMPLETE')

    def test_stopping_keeps_input_pending(self):
        job = self.pipeline.submit('test', 'stop', 'pending')
        self.module.stop_event.set()
        self.assertFalse(self.module.process_next())
        self.assertFalse(self.module.ready(job))
        self.module.stop_event.clear()
        self.assertTrue(self.module.process_next())
        self.assertTrue(self.module.ready(job))

class UnifiedUITests(unittest.TestCase):

    def test_separate_switch_engine_selection_pdf_and_history_preservation(self):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        from PySide6.QtWidgets import QApplication
        from ..source.app import GraphicalVirtueMatrixEngine
        from ..source.monitor import SystemBusMonitor
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            window = GraphicalVirtueMatrixEngine(SystemBusMonitor(), folder, start_services=False)
            try:
                self.assertEqual(window.pages.count(), 27)
                self.assertEqual(window.unified_engines.count(), 24)
                identity, _ = window.conversations.snapshot('gemini')
                window.conversations.complete('gemini', identity, 'Keep this', 'Kept', 'test')
                window.unified_toggle.setChecked(False)
                self.assertFalse(window.unified_core.enabled)
                self.assertTrue(window.mesh_module.enabled)
                self.assertTrue(window.live_audit.enabled)
                window.navigate(21)
                window.unified_input.setPlainText(json.dumps(INPUT_TEMPLATE))
                window.run_unified_input()
                deadline = time.monotonic() + 6
                while time.monotonic() < deadline and (not window.unified_core.snapshot()['latest']):
                    app.processEvents()
                    time.sleep(0.02)
                window.render_unified_core()
                self.assertIsNotNone(window.unified_sessions.currentData())
                window.unified_engines.setCurrentIndex(window.unified_engines.findData('SoulsOverDigitsController'))
                self.assertTrue(json.loads(window.unified_output.toPlainText())['SOULS_OVER_DIGITS_BOOLEAN'])
                pdf = Path(folder) / 'report.pdf'
                with patch('unified_page.QFileDialog.getSaveFileName', return_value=(str(pdf), 'PDF')):
                    window.export_unified_pdf()
                self.assertTrue(pdf.exists())
                self.assertIn('unified_core', window.engine_state())
                self.assertIn('unified_core', window.extension_export())
                self.assertEqual(len(window.conversations.snapshot('gemini')[1]), 2)
            finally:
                window.close()
                app.processEvents()
