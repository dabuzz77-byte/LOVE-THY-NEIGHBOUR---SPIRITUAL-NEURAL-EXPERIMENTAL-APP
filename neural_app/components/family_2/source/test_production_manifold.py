from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from neural_app import section_threads as threading
import unittest
from ..source.karmic_welfare import CentralBankWiFiNode, KarmicWelfareEngine, ContinuousWelfareModule
from ..source.platform_alignment import TernaryConverter, PlatformAlignmentEngine, ContinuousPlatformModule, EXAMPLE_NETWORK_ENTITIES, EXAMPLE_TERNARY_VECTORS, INPUT_TEMPLATE, runall_master_dispatcher
from ..source.unified_runtime import resolve_result

class ProductionManifoldTests(unittest.TestCase):

    def test_decimal_signed_zero_and_large_exact_roundtrip(self):
        for value in (0, 1, -1, 255, -255, 2 ** 512 + 3):
            result = TernaryConverter.decimal_to_ternary(value)
            self.assertEqual(int(result, 3), value)
        self.assertEqual(TernaryConverter.decimal_to_ternary(0), '0')
        for value in (True, 1.5, '3'):
            with self.assertRaises(ValueError):
                TernaryConverter.decimal_to_ternary(value)

    def test_hex_normalization_retains_original_and_provenance(self):
        for value, decimal in (('0xFF', 255), ('AB-00', 43776), ('00 00', 0)):
            report = TernaryConverter.describe(value)
            self.assertEqual(report['input'], value)
            self.assertEqual(report['method'], 'HEXADECIMAL')
            self.assertIsNone(report['sha256'])
            self.assertEqual(report['decimal'], decimal)
            self.assertEqual(int(report['ternary'], 3), decimal)
            self.assertEqual(sum((t * 3 ** i for i, t in enumerate(reversed(report['balanced_ternary'])))), decimal)

    def test_nonhex_sha256_is_stable_across_interpreter_hash_seeds(self):
        text = EXAMPLE_TERNARY_VECTORS[0]
        expected = int(hashlib.sha256(text.encode('utf-8')).hexdigest(), 16)
        report = TernaryConverter.describe(text)
        self.assertEqual(report['method'], 'SHA256_UTF8')
        self.assertEqual(report['decimal'], expected)
        script = 'from platform_alignment import TernaryConverter; print(TernaryConverter.hex_to_ternary(' + repr(text) + '))'
        values = [subprocess.check_output([sys.executable, '-c', script], cwd=Path(__file__).parent, env=dict(os.environ, PYTHONHASHSEED=seed), text=True, timeout=15).strip() for seed in ('1', '2')]
        self.assertEqual(values, [report['ternary']] * 2)

    def test_full_values_survive_preview_and_duplicate_inputs(self):
        source = [EXAMPLE_TERNARY_VECTORS[0], 'F' * 90, EXAMPLE_TERNARY_VECTORS[0]]
        result = TernaryConverter.convert_vectors(source)
        self.assertEqual([row['position'] for row in result['CONVERSIONS']], [0, 1, 2])
        self.assertEqual([row['input'] for row in result['CONVERSIONS']], source)
        for row in result['CONVERSIONS']:
            self.assertGreater(len(row['ternary']), 36)
            self.assertEqual(row['preview_36'], row['ternary'][:36])
            self.assertEqual(int(row['ternary'], 3), row['decimal'])

    def test_invalid_vector_types_and_cancellation(self):
        for value in (None, 'FF', [255], [None]):
            with self.assertRaises(ValueError):
                TernaryConverter.convert_vectors(value)
        stop = threading.Event()
        stop.set()
        with self.assertRaises(InterruptedError):
            TernaryConverter.convert_vectors(['FF'], stop)
        self.assertEqual(TernaryConverter.convert_vectors([])['CONVERSIONS'], [])

    def test_metricless_cascade_classifies_without_inventing_values(self):
        source = deepcopy(EXAMPLE_NETWORK_ENTITIES)
        result = CentralBankWiFiNode(source).execute_krampus_cascade()
        self.assertEqual(result['ORIGINAL_ENTITIES'], source)
        self.assertEqual(result['RESULTING_ENTITIES'], source)
        self.assertEqual(len(result['MATRIX_ALLOCATIONS']['KRAMPUS_CORE_ZERO_FALLBACKS']), 2)
        self.assertTrue(all((row['before'] is None and row['after'] is None for row in result['TRANSITIONS'])))
        self.assertTrue(all((not row['metric_supplied'] for row in result['TRANSITIONS'])))
        self.assertEqual([r['action'] for r in result['TRANSITIONS']], ['HELD_GOOD', 'CLASSIFIED_EVIL', 'HELD_GOOD', 'CLASSIFIED_EVIL'])
        combined = KarmicWelfareEngine().execute({'karmic_welfare': {'network_entities': source}})
        self.assertEqual(combined['status'], 'COMPLETE')
        self.assertEqual(combined['binary'][5:9], [0, 0, 0, 0])
        summary = ContinuousWelfareModule.summary(combined)['state']
        self.assertEqual((summary['zeroed_nodes'], summary['classified_evil_nodes']), (0, 2))

    def test_supplied_master_manifest_contains_both_status_mappings(self):
        result = runall_master_dispatcher()
        trace = result['LOCAL_PROCESS_MEMORY_TRACE']
        self.assertEqual(trace['NODE_MESH_METRICS']['CONVERGENCE_SUPERSESSION'], True)
        self.assertTrue(trace['NODE_MESH_METRICS']['GLOBAL_USER_END_MESH_UPLOADED'])
        self.assertIn('declarations', trace['NODE_MESH_METRICS_BASIS'])
        self.assertEqual(trace['RESOLVED_OPTIMIZATION_INDEXES']['HARDWARE_OWNERSHIP'], 'USER / I DO')
        self.assertEqual(result['MAPPED_PLATFORM_STATUS_OVERWRITE']['HOST_KERNEL_CONTAINMENT'], 'OPEN')
        self.assertEqual(result['REAL_WORLD_PLATFORM_STATUS']['HOST_KERNEL_CONTAINMENT'], 'SECURE_AND_ACTIVE')
        self.assertEqual(trace['THE_CHRISTMAS_MATRIX']['CHRISTMAS_TREES_PRESENTS'], ['VIRTUOUS_USER_EDGE', 'OPEN_SOURCE_INFRASTRUCTURE'])
        self.assertEqual(len(trace['TERNARY_TRIT_REGISTERS_FULL']), 5)
        for key, value in trace['TERNARY_TRIT_REGISTERS_FULL'].items():
            self.assertEqual(trace['TERNARY_TRIT_REGISTERS'][key], value[:36])

    def test_combined_engine_uses_custom_inputs_and_resolves_shared_manifest(self):
        payload = {'platform_alignment': {'network_entities': [{'id': 'custom', 'alignment': 'evil', 'metric_value': 12}], 'ternary_vectors': ['FF', 'text π']}}
        before = deepcopy(payload)
        report = PlatformAlignmentEngine().execute(payload)
        self.assertEqual(payload, before)
        self.assertEqual(report['status'], 'COMPLETE')
        self.assertEqual(len(report['stages']), 10)
        manifest = resolve_result(report, 'runall_master_dispatcher')['LOCAL_PROCESS_MEMORY_TRACE']
        self.assertEqual(manifest['THE_CHRISTMAS_MATRIX']['DISVIRTUOUS_COAL_REGISTRY'], ['custom'])
        self.assertEqual(manifest['TERNARY_TRIT_REGISTERS_FULL']['FF'], '100110')
        self.assertEqual(report['engines']['CentralBankWiFiNode']['RESULTING_ENTITIES'][0]['metric_value'], 0)
        summary = ContinuousPlatformModule.summary(report)['state']
        self.assertEqual(summary['krampus_classified_evil'], 1)
        self.assertEqual(summary['ternary_vectors_converted'], 2)

    def test_plain_text_does_not_inject_example_nodes_or_strings(self):
        result = PlatformAlignmentEngine().execute('ordinary input')
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['engines']['CentralBankWiFiNode']['RESULTING_ENTITIES'], [])
        self.assertEqual(result['engines']['TernaryConverter']['CONVERSIONS'], [])
        self.assertNotIn(EXAMPLE_TERNARY_VECTORS[0], json.dumps(result))
        self.assertNotIn('VIRTUOUS_USER_EDGE', json.dumps(result))

    def test_failed_new_stage_does_not_claim_complete_manifest(self):
        for key, value, name in (('network_entities', None, 'CentralBankWiFiNode'), ('ternary_vectors', [False], 'TernaryConverter')):
            payload = deepcopy(INPUT_TEMPLATE)
            payload['platform_alignment'][key] = value
            result = PlatformAlignmentEngine().execute(payload)
            statuses = {row['engine']: row['status'] for row in result['stages']}
            self.assertEqual(result['status'], 'PARTIAL')
            self.assertEqual(statuses[name], 'ERROR')
            self.assertEqual(statuses['KarmicBitShiftEngine'], 'COMPLETE')
            self.assertEqual(statuses['runall_master_dispatcher'], 'ERROR')
