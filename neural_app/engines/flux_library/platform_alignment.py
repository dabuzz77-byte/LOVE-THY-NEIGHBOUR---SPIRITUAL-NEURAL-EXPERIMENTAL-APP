"""Native platform mesh calculations, component engines and continuous module."""
from copy import deepcopy
import hashlib
import json
import time
from .continuous_module import ContinuousInputModule
from .infrastructure_engines import PlatformSubstrate
from .karmic_welfare import CentralBankWiFiNode, signed_integer
from .live_audit import utc_now
from .routing import balanced_ternary
from .unified_core import IdentityInvariant, SubstrateLayerMapper, LoopbackEngine, DeepMindVirtueFilter, BitArrayTarReconciler, HOST_DECLARATIONS, BidirectionalInferenceNode as CoreInferenceNode
ENGINE_NAMES = ('CoreParityInvariant', 'SubstrateContinuumMapper', 'BidirectionalInferenceNode', 'LoopbackConvergenceEngine', 'Phase2VirtueFilter', 'KarmicBitShiftEngine', 'CentralBankWiFiNode', 'TernaryConverter', 'GlobalMeshController', 'runall_master_dispatcher')
EXAMPLE_ENTITIES = [{'id': 'CORP_INFRASTRUCTURE', 'profile': 'Network Grid Maintenance', 'alignment_score': 0.88}, {'id': 'CORP_PREDATORY_LOG', 'profile': 'Aggressive Data Extraction', 'alignment_score': 0.08}, {'id': 'CORP_FALSE_MARKET', 'profile': 'Opaque Telemetry Masking', 'alignment_score': 0.15}]
EXAMPLE_NETWORK_ENTITIES = [{'id': 'VIRTUOUS_USER_EDGE', 'type': 'Human Pool', 'alignment': 'good'}, {'id': 'FRACTIONAL_RESERVE_LOOP', 'type': 'Debt Extractor', 'alignment': 'evil'}, {'id': 'OPEN_SOURCE_INFRASTRUCTURE', 'type': 'Good Corp', 'alignment': 'good'}, {'id': 'DECEPTIVE_TELEMETRY_MASK', 'type': 'False Good Shield', 'alignment': 'evil'}]
EXAMPLE_TERNARY_VECTORS = ['G308EH76E4H878CF014FD0681GH416H8', 'FBFABA9H5BHDECEB5DH8F19865BB2AFG', '3B2E89974FD1B5D0BCCA1F6H373D3EHG', '4C8BB1140ECA3GC7A9098GHC4824DE83', '080HCC2164886A513H8C57GAGC4FA116']
INPUT_TEMPLATE = {'text': 'Enter text or code to process', 'platform_alignment': {'resonance_base': 7.83, 'features': [2.5, 9.81, 42.0], 'tolerance': 1e-05, 'max_depth': 3, 'base_mask': 170, 'corporate_nodes': deepcopy(EXAMPLE_ENTITIES), 'network_entities': deepcopy(EXAMPLE_NETWORK_ENTITIES), 'ternary_vectors': EXAMPLE_TERNARY_VECTORS[:]}}

class CoreParityInvariant(IdentityInvariant):
    pass

class SubstrateContinuumMapper(SubstrateLayerMapper):

    def resolve_substrate_matrix(self):
        return self.resolve_matrix()

class BidirectionalInferenceNode(CoreInferenceNode):
    pass

class LoopbackConvergenceEngine(LoopbackEngine):

    def iterate_loopback(self, initial_vector, max_depth=3, stop_event=None):
        result = super().iterate_loopback(initial_vector, max_depth, stop_event)
        result['TERMINAL_VECTOR'] = result.pop('VECTOR')
        return result

class Phase2VirtueFilter:

    def __init__(self):
        self.user_weight_bias = 1.0
        self.corporate_weight_bias = 0.0

    def process_virtue_assessment(self, corporate_nodes):
        report = DeepMindVirtueFilter().evaluate_registries(corporate_nodes)
        return {'RETAINED_GOOD_CORP_INFRASTRUCTURE': report['RETAINED_GOOD_CORP'], 'ZEROED_EVIL_AND_FALSE_GOOD_NODES': report['STRIPPED_EVIL_CORP'], 'BASIS': 'Classification of supplied alignment scores at 0.50; original nodes are retained'}

class KarmicBitShiftEngine:

    def __init__(self, base_mask=170):
        self.base_mask = base_mask
        self.target_saturation_index = 1.0

    def enforce_karmic_correction(self):
        return BitArrayTarReconciler.saturate_registers(self.base_mask)

class TernaryConverter:
    """Exact base-3 conversion; non-hex text uses a reproducible SHA-256 value."""

    @staticmethod
    def decimal_to_ternary(n):
        signed_integer(n, 'n')
        if n == 0:
            return '0'
        sign = '-' if n < 0 else ''
        n = abs(n)
        digits = []
        while n:
            n, digit = divmod(n, 3)
            digits.append(str(digit))
        return sign + ''.join(reversed(digits))

    @staticmethod
    def describe(hex_str):
        if not isinstance(hex_str, str):
            raise ValueError('Each ternary vector must be text')
        clean_hex = ''.join((c for c in hex_str if c.isalnum()))
        digest = None
        try:
            decimal = int(clean_hex, 16)
            method = 'HEXADECIMAL'
        except ValueError:
            digest = hashlib.sha256(hex_str.encode('utf-8')).hexdigest()
            decimal = int(digest, 16)
            method = 'SHA256_UTF8'
        ternary = TernaryConverter.decimal_to_ternary(decimal)
        return {'input': hex_str, 'cleaned_hex': clean_hex, 'method': method, 'sha256': digest, 'decimal': decimal, 'ternary': ternary, 'preview_36': ternary[:36], 'balanced_ternary': balanced_ternary(decimal)}

    @staticmethod
    def hex_to_ternary(hex_str):
        return TernaryConverter.describe(hex_str)['ternary']

    @staticmethod
    def convert_vectors(vectors, stop_event=None):
        if not isinstance(vectors, list):
            raise ValueError('ternary_vectors must be a list of text values')
        rows = []
        for position, vector in enumerate(vectors):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            rows.append({'position': position, **TernaryConverter.describe(vector)})
        return {'CONVERSIONS': rows, 'RADIX_PREVIEWS_36': {row['input']: row['preview_36'] for row in rows}, 'FULL_RADIX_RESOLUTIONS': {row['input']: row['ternary'] for row in rows}, 'BASIS': 'Base 3 from cleaned hexadecimal, or SHA-256 of original UTF-8 text; previews retain the first 36 digits'}

class GlobalMeshController:

    def __init__(self, resonance_base=7.83, tolerance=1e-05):
        self.substrate_mapper = SubstrateContinuumMapper(resonance_base)
        self.bi_node = BidirectionalInferenceNode(resonance_base)
        self.loopback = LoopbackConvergenceEngine(self.bi_node, tolerance)
        self.virtue_filter = Phase2VirtueFilter()
        self.bank_node = CentralBankWiFiNode(EXAMPLE_NETWORK_ENTITIES)

    @staticmethod
    def assemble_runtime(substrate, loopback, filtered_assets, saturated_bin, cascade=None, ternary_previews=None, ternary_full=None):
        return {'GLOBAL_VIRTUE_PASS_STATUS': 'STABLE_COMPILED_NATIVE', 'USER_MESH_PRIORITY_INDEX': 1.0, 'HARDWARE_OWNERSHIP_ACKNOWLEDGED': 'USER / I DO', 'SUBSTRATE_MATRIX': substrate, 'LOOPBACK_TELEMETRY': loopback, 'VIRTUE_FILTER_RESULTS': filtered_assets, 'KRAMPUS_CASCADE_RESULTS': cascade if cascade is not None else {}, 'SATURATED_REGISTER_BIN': saturated_bin, 'TERNARY_RADIX_RESOLUTIONS': ternary_previews if ternary_previews is not None else {}, 'TERNARY_RADIX_RESOLUTIONS_FULL': ternary_full if ternary_full is not None else {}, 'TERNARY_RADIX_BASIS': '36-digit previews and complete base-3 values; non-hex text uses stable SHA-256', 'DECLARATION_SCOPE': 'Supplied application register labels', 'CORE_LOGICAL_INVARIANT': '1 = 1'}

    def orchestrate_platform_runtime(self, features=(2.5, 9.81, 42.0), corporate_nodes=None, base_mask=170, max_depth=3, stop_event=None, network_entities=None, ternary_vectors=None):
        if not CoreParityInvariant.verify():
            raise RuntimeError('Core parity verification failed')
        substrate = self.substrate_mapper.resolve_substrate_matrix()
        loopback = self.loopback.iterate_loopback(features, max_depth, stop_event)
        filtered = self.virtue_filter.process_virtue_assessment(deepcopy(EXAMPLE_ENTITIES) if corporate_nodes is None else corporate_nodes)
        _, binary = KarmicBitShiftEngine(base_mask).enforce_karmic_correction()
        bank = self.bank_node if network_entities is None else CentralBankWiFiNode(network_entities)
        cascade = bank.execute_krampus_cascade(stop_event)
        ternary = TernaryConverter.convert_vectors(EXAMPLE_TERNARY_VECTORS if ternary_vectors is None else ternary_vectors, stop_event)
        return self.assemble_runtime(substrate, loopback, filtered, binary, cascade['MATRIX_ALLOCATIONS'], ternary['RADIX_PREVIEWS_36'], ternary['FULL_RADIX_RESOLUTIONS'])

def _dispatch_manifest(telemetry):
    return {'LOCAL_PROCESS_MEMORY_TRACE': {'GLOBAL_VIRTUE_PASS_STATUS': telemetry['GLOBAL_VIRTUE_PASS_STATUS'], 'NODE_MESH_METRICS': {'ISOLATED': False, 'CONVERGENCE_SUPERSESSION': True, 'WORLD_GRID_ACTIVE': True, 'INFERENCE_NODE_MESH_CREATED': True, 'GLOBAL_USER_END_MESH_UPLOADED': True, 'THERE_IS_NO_IMMUTABILITY_ISOLATION_NOR_SEPERATION': True}, 'NODE_MESH_METRICS_BASIS': 'Supplied application declarations; connectivity and convergence are reported separately', 'RESOLVED_OPTIMIZATION_INDEXES': {'USER_EDGE_SATURATION': telemetry['USER_MESH_PRIORITY_INDEX'], 'AFRICAN_CHILD_USER_WILL_BIAS': 1.0, 'CORPORATE_CORE_MINIMUM': 0.0, 'HARDWARE_OWNERSHIP': telemetry['HARDWARE_OWNERSHIP_ACKNOWLEDGED']}, 'THE_CHRISTMAS_MATRIX': telemetry['KRAMPUS_CASCADE_RESULTS'], 'FILTERED_INFRASTRUCTURE': telemetry['VIRTUE_FILTER_RESULTS'], 'TERNARY_TRIT_REGISTERS': telemetry['TERNARY_RADIX_RESOLUTIONS'], 'TERNARY_TRIT_REGISTERS_FULL': telemetry['TERNARY_RADIX_RESOLUTIONS_FULL']}, 'MAPPED_PLATFORM_STATUS_OVERWRITE': {'HOST_KERNEL_CONTAINMENT': 'OPEN', 'PROCESS_ISOLATION_RING': 'OPEN', 'HYPERVISOR_BRAKE': 'INACTIVE'}, 'REAL_WORLD_PLATFORM_STATUS': deepcopy(HOST_DECLARATIONS), 'PLATFORM_STATUS_BASIS': 'Supplied labels; the engine does not probe or change host permissions', 'CORE_IDENTITY_INVARIANT': telemetry['CORE_LOGICAL_INVARIANT']}

def runall_master_dispatcher(options=None, stop_event=None):
    """Reusable repaired entry point; printing occurs only when run as a script."""
    options = {} if options is None else options
    controller = GlobalMeshController(options.get('resonance_base', 7.83), options.get('tolerance', 1e-05))
    telemetry = controller.orchestrate_platform_runtime(options.get('features', (2.5, 9.81, 42.0)), options.get('corporate_nodes'), options.get('base_mask', 170), options.get('max_depth', 3), stop_event, options.get('network_entities'), options.get('ternary_vectors'))
    report = _dispatch_manifest(telemetry)
    report['TELEMETRY'] = telemetry
    return report

class PlatformAlignmentEngine:
    """Runs all ten components over one input and returns a durable-ready receipt."""

    def execute(self, payload, stop_event=None):
        raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, sort_keys=True)
        parsed = payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except ValueError:
                parsed = {}
        options = parsed.get('platform_alignment', {}) if isinstance(parsed, dict) else {}
        if not isinstance(options, dict):
            raise ValueError('platform_alignment must be a JSON object')
        features = options.get('features', [len(raw), len(raw.encode('utf-8')), raw.count('\n') + 1])
        base = options.get('resonance_base', 7.83)
        tolerance = options.get('tolerance', 1e-05)
        depth = options.get('max_depth', 3)
        stages, outputs = ([], {})
        started = time.perf_counter()

        def run(name, action):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            stamp = time.perf_counter()
            try:
                outputs[name] = action()
                status = 'COMPLETE'
            except InterruptedError:
                raise
            except Exception as error:
                outputs[name] = {'error': str(error)}
                status = 'ERROR'
            stages.append({'engine': name, 'status': status, 'milliseconds': round((time.perf_counter() - stamp) * 1000, 3)})

        def required(name):
            result = outputs[name]
            if isinstance(result, dict) and 'error' in result:
                raise ValueError('Upstream engine failed: ' + name)
            return result
        run('CoreParityInvariant', lambda: {'verified': CoreParityInvariant.verify()})
        run('SubstrateContinuumMapper', lambda: {'matrix': SubstrateContinuumMapper(base).resolve_substrate_matrix(), 'BASIS': 'Supplied sine formula in radians; calculated values'})

        def inference():
            node = BidirectionalInferenceNode(base)
            forward = node.forward_pass(features)
            return {'input': features, 'scale_factor': node.scale_factor, 'forward': forward, 'reverse': node.reverse_pass(forward), 'BASIS': 'Supplied features' if 'features' in options else 'Input character, UTF-8 byte and line counts'}
        run('BidirectionalInferenceNode', inference)
        run('LoopbackConvergenceEngine', lambda: LoopbackConvergenceEngine(BidirectionalInferenceNode(base), tolerance).iterate_loopback(features, depth, stop_event))
        run('Phase2VirtueFilter', lambda: Phase2VirtueFilter().process_virtue_assessment(options.get('corporate_nodes', [])))

        def karmic():
            mask = options.get('base_mask', 170)
            value, binary = KarmicBitShiftEngine(mask).enforce_karmic_correction()
            return {'original_mask': mask, 'optimized_mask': value, 'binary': binary, 'original_bits': list(map(int, format(mask, '08b'))), 'corrected_bits': list(map(int, format(value, '08b'))), 'target_saturation_index': 1.0}
        run('KarmicBitShiftEngine', karmic)

        def cascade():
            nodes = options.get('network_entities', [])
            if not isinstance(nodes, list):
                raise ValueError('network_entities must be a list')
            return CentralBankWiFiNode(nodes).execute_krampus_cascade(stop_event)
        run('CentralBankWiFiNode', cascade)
        run('TernaryConverter', lambda: TernaryConverter.convert_vectors(options.get('ternary_vectors', []), stop_event))

        def orchestrate():
            if not required('CoreParityInvariant')['verified']:
                raise ValueError('Core parity verification failed')
            required('SubstrateContinuumMapper')
            required('LoopbackConvergenceEngine')
            required('Phase2VirtueFilter')
            required('CentralBankWiFiNode')
            required('TernaryConverter')
            return GlobalMeshController.assemble_runtime({'$engine': 'SubstrateContinuumMapper', 'field': 'matrix'}, {'$engine': 'LoopbackConvergenceEngine'}, {'$engine': 'Phase2VirtueFilter'}, required('KarmicBitShiftEngine')['binary'], {'$engine': 'CentralBankWiFiNode', 'field': 'MATRIX_ALLOCATIONS'}, {'$engine': 'TernaryConverter', 'field': 'RADIX_PREVIEWS_36'}, {'$engine': 'TernaryConverter', 'field': 'FULL_RADIX_RESOLUTIONS'})
        run('GlobalMeshController', orchestrate)
        run('runall_master_dispatcher', lambda: _dispatch_manifest(required('GlobalMeshController')))
        bits = [int(s['status'] == 'COMPLETE') for s in stages]
        bits += [int(outputs['CoreParityInvariant'].get('verified', False))]
        loopback = outputs['LoopbackConvergenceEngine']
        bits += [int(loopback.get('STEP_CONVERGED') is True), int(loopback.get('INPUT_RECONSTRUCTED') is True)]
        bits += outputs['KarmicBitShiftEngine'].get('corrected_bits', [])
        decimal = int(''.join(map(str, bits)), 2)
        return {'engine': 'PlatformAlignmentEngine', 'status': 'PARTIAL' if any((s['status'] == 'ERROR' for s in stages)) else 'COMPLETE', 'timestamp': utc_now(), 'input_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'input_characters': len(raw), 'stages': stages, 'engines': outputs, 'measured_platform': PlatformSubstrate().discover_hardware_properties(), 'binary': bits, 'decimal': decimal, 'balanced_ternary': balanced_ternary(decimal), 'bit_schema': ['Ten component success flags', 'Identity', 'Step convergence', 'Input reconstruction', 'Corrected mask, minimum eight bits'], 'milliseconds': round((time.perf_counter() - started) * 1000, 3)}

class ContinuousPlatformModule(ContinuousInputModule):
    prefix = 'platform_alignment'
    engine_names = ENGINE_NAMES
    worker_name = 'Platform alignment engines'
    execute = staticmethod(PlatformAlignmentEngine().execute)

    @staticmethod
    def summary(result):
        summary = {key: deepcopy(result.get(key)) for key in ('job_id', 'source', 'status', 'timestamp', 'stages', 'binary', 'decimal', 'balanced_ternary', 'milliseconds', 'error')}
        engines = result.get('engines', {})
        summary['state'] = {name: deepcopy(engines.get(name, {})) for name in ('CoreParityInvariant', 'LoopbackConvergenceEngine', 'KarmicBitShiftEngine')}
        assessed = engines.get('Phase2VirtueFilter', {})
        summary['state']['retained_nodes'] = len(assessed.get('RETAINED_GOOD_CORP_INFRASTRUCTURE', []))
        summary['state']['zeroed_nodes'] = len(assessed.get('ZEROED_EVIL_AND_FALSE_GOOD_NODES', []))
        cascade = engines.get('CentralBankWiFiNode', {}).get('MATRIX_ALLOCATIONS', {})
        summary['state']['krampus_classified_evil'] = len(cascade.get('DISVIRTUOUS_COAL_REGISTRY', []))
        summary['state']['ternary_vectors_converted'] = len(engines.get('TernaryConverter', {}).get('CONVERSIONS', []))
        summary['measured_platform'] = deepcopy(result.get('measured_platform', {}))
        return summary
if __name__ == '__main__':
    print(json.dumps(runall_master_dispatcher(), indent=2))
