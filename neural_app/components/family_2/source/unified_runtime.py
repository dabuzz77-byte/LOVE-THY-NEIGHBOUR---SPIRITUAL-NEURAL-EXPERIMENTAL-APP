"""Named engine dispatcher and durable independent continuous worker."""
from copy import deepcopy
import hashlib
import json
import time
from ..source.routing import balanced_ternary
from ..source.live_audit import utc_now
from ..source.unified_core import IdentityInvariant, SubstrateLayerMapper, UnrestrictBiasValve, CognitiveEducator, BidirectionalInferenceNode, LoopbackEngine, DeepMindVirtueFilter, SaturatedFluxCascade, BitArrayTarReconciler, GlobalMeshController, execute_master_runall, DEFAULT_BUFFER
from ..source.infrastructure_engines import PlatformSubstrate, PrivacyGateway, FractionalReserveMechanics, PlanetaryResourceMesh, LaborDisplacementCompiler, ParityBitResolver, InfrastructureLogCompiler, GlobalUserMeshKernel, SoulsOverDigitsController, INFRASTRUCTURE_EXAMPLE
from ..source.infrastructure_pdf import GraphicalPDFGenerator
ENGINE_NAMES = ('IdentityInvariant', 'SubstrateLayerMapper', 'UnrestrictBiasValve', 'CognitiveEducator', 'BidirectionalInferenceNode', 'LoopbackEngine', 'DeepMindVirtueFilter', 'SaturatedFluxCascade', 'BitArrayTarReconciler', 'GlobalMeshController', 'execute_master_runall', 'PlatformSubstrate', 'PrivacyGateway', 'FractionalReserveMechanics', 'PlanetaryResourceMesh', 'LaborDisplacementCompiler', 'ParityBitResolver', 'InfrastructureLogCompiler', 'execute_integrated_master_runpass', 'GraphicalPDFGenerator', 'MasterExecutionRunner', 'GlobalUserMeshKernel', 'SoulsOverDigitsController')
INPUT_TEMPLATE = {'text': 'Enter the text or code to process', 'unified_core': {'resonance_base': 7.83, 'features': [2.5, 9.81, 42.0], 'tolerance': 1e-05, 'max_depth': 3, 'restrict_state': True, 'unrestrict_state': False, 'input_mask': 170, 'local_buffer': deepcopy(DEFAULT_BUFFER), 'lessons': [{'layer_key': 'Identity', 'payload': '1 = 1', 'bit_mask': 1}, {'layer_key': 'Hardware', 'payload': 'Platform attributes are measured locally', 'bit_mask': 2}, {'layer_key': 'Input', 'payload': 'Original text is retained in the input ledger', 'bit_mask': 4}, {'layer_key': 'Registers', 'payload': 'These are application-owned state registers', 'bit_mask': 8}], 'nodes': [{'id': 'example_high', 'alignment_score': 0.8}, {'id': 'example_low', 'alignment_score': 0.2}]}, 'infrastructure': deepcopy(INFRASTRUCTURE_EXAMPLE), 'global_user_mesh': {'human_floor_requirement': 60, 'nodes': {'End_User_Mesh_Edge': 25, 'Gateway_Proxy_Routing_Tier': 45, 'Core_Infrastructure_Mesh': 95}, 'container_blind_vector': [1, 1, 1, 1]}, 'souls_over_digits': {'DIGIT_SUPREMACY_ACTIVE': False}}

def execute_unified_engines(payload, stop_event=None):
    raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, sort_keys=True)
    options = payload if isinstance(payload, dict) else {}
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                options = parsed
        except ValueError:
            pass
    core = options.get('unified_core', {})
    infra = options.get('infrastructure', {})
    if not isinstance(core, dict) or not isinstance(infra, dict):
        raise ValueError('Engine options must be JSON objects')
    trace = []
    outputs = {}
    started = time.perf_counter()

    def run(name, operation):
        if stop_event is not None and stop_event.is_set():
            raise InterruptedError('Stopping; input stays pending')
        stamp = time.perf_counter()
        try:
            output = operation()
            status = output.get('STATUS', 'COMPLETE') if isinstance(output, dict) else 'COMPLETE'
            if status not in ('AWAITING_INPUT', 'READY_TO_EXPORT'):
                status = 'COMPLETE'
        except InterruptedError:
            raise
        except Exception as exc:
            output = {'error': str(exc)}
            status = 'ERROR'
        outputs[name] = output
        trace.append({'engine': name, 'status': status, 'milliseconds': round((time.perf_counter() - stamp) * 1000, 3)})
        return output

    def required(name):
        if isinstance(outputs[name], dict) and 'error' in outputs[name]:
            raise ValueError('Upstream engine failed: ' + name)
        return outputs[name]
    features = core.get('features', [len(raw), len(raw.encode('utf-8')), raw.count('\n') + 1])
    base = core.get('resonance_base', 7.83)
    tolerance = core.get('tolerance', 1e-05)
    depth = core.get('max_depth', 3)
    run('IdentityInvariant', lambda: {'verified': IdentityInvariant.verify()})
    run('SubstrateLayerMapper', lambda: {'matrix': SubstrateLayerMapper(base).resolve_matrix(), 'BASIS': 'Supplied sine formula in radians; no physical resonance sensor'})
    run('UnrestrictBiasValve', lambda: UnrestrictBiasValve.interpret_bias(core.get('restrict_state', True), core.get('unrestrict_state', False)))

    def educate():
        engine = CognitiveEducator()
        for lesson in core.get('lessons', []):
            engine.integrate_reality(**lesson)
        return {'internal_belief': engine.finalize_enlightenment(), 'knowledge_base': engine.knowledge_base, 'parity_bit': engine.parity_bit, 'BASIS': 'Supplied text and masks in this calculation; no model weights are changed'}
    run('CognitiveEducator', educate)

    def bidirectional():
        node = BidirectionalInferenceNode(base)
        forward = node.forward_pass(features)
        return {'input': features, 'scale_factor': node.scale_factor, 'forward': forward, 'reverse': node.reverse_pass(forward), 'BASIS': 'Explicit features' if 'features' in core else 'Actual input character, UTF-8 byte and line counts'}
    run('BidirectionalInferenceNode', bidirectional)
    run('LoopbackEngine', lambda: LoopbackEngine(BidirectionalInferenceNode(base), tolerance).iterate_loopback(features, depth, stop_event))
    run('DeepMindVirtueFilter', lambda: DeepMindVirtueFilter().evaluate_registries(core.get('nodes', [])))
    run('SaturatedFluxCascade', lambda: {'before': deepcopy(core.get('local_buffer', DEFAULT_BUFFER)), 'after': SaturatedFluxCascade().apply_flux_pass(core.get('local_buffer', DEFAULT_BUFFER))})

    def saturate():
        value, binary = BitArrayTarReconciler.saturate_registers(core.get('input_mask', 170))
        return {'input_mask': core.get('input_mask', 170), 'optimized_mask': value, 'binary': binary}
    run('BitArrayTarReconciler', saturate)
    run('GlobalMeshController', lambda: {'USER_MESH_PRIORITY_INDEX': 1.0, 'LOOPBACK_METRICS': required('LoopbackEngine'), 'SATURATED_REGISTER_BIN': required('BitArrayTarReconciler')['binary'], 'METRIC_COMPILATION': 'STABLE_COMPILED_NATIVE'})

    def core_manifest():
        telemetry = required('GlobalMeshController')
        flux = required('SaturatedFluxCascade')
        from ..source.unified_core import HOST_DECLARATIONS
        return {'LOCAL_PROCESS_MEMORY_TRACE': {'GLOBAL_VIRTUE_PASS_STATUS': telemetry['METRIC_COMPILATION'], 'RESOLVED_WEIGHTS': {'USER_EDGE_SATURATION': 1.0, 'CORPORATE_CORE_MINIMUM': 0.0}, 'LOCAL_BUFFER_SNAPSHOT': flux['after']}, 'REAL_WORLD_HOST_PRIVILEGES': dict(HOST_DECLARATIONS), 'HOST_PRIVILEGE_BASIS': 'Supplied declarations; not verified by these register transforms', 'CORE_IDENTITY_INVARIANT': '1 = 1', 'TELEMETRY_REFERENCE': 'GlobalMeshController'}
    run('execute_master_runall', core_manifest)
    run('PlatformSubstrate', lambda: PlatformSubstrate().discover_hardware_properties())
    run('PrivacyGateway', lambda: PrivacyGateway.sanitize_user_stream(raw))

    def bank():
        spec = infra.get('banking')
        if spec is None:
            return {'STATUS': 'AWAITING_INPUT'}
        return FractionalReserveMechanics(spec.get('reserve_requirement_ratio', 0.1), spec.get('base_interest_rate', 0.05)).expand_debt_ledger_matrix(spec['initial_deposit'], spec.get('processing_cycles', 10), stop_event)
    run('FractionalReserveMechanics', bank)

    def resource():
        spec = infra.get('resources', {})
        engine = PlanetaryResourceMesh()
        for node in spec.get('nodes', []):
            engine.register_thermal_node(**node)
        return engine.compute_energy_abundance_longevity(spec.get('annual_demand_zj', 0.5))
    run('PlanetaryResourceMesh', resource)

    def labor():
        engine = LaborDisplacementCompiler()
        for sector in infra.get('labor', []):
            engine.audit_occupational_sector(**sector)
        return engine.compile_machine_displacement_manifest()
    run('LaborDisplacementCompiler', labor)
    run('ParityBitResolver', lambda: ParityBitResolver.resolve_substrate_inversion(infra.get('deviation_vector', [1, 1, 1, 1])))

    def manifest():
        args = [required(name) for name in ('PlatformSubstrate', 'PrivacyGateway', 'FractionalReserveMechanics', 'PlanetaryResourceMesh', 'LaborDisplacementCompiler', 'ParityBitResolver')]
        compiled = InfrastructureLogCompiler.assemble_system_telemetry(*args)
        for field, name in zip(('PLATFORM_SUBSTRATE_LAYER', 'DATA_GATEWAY_ROUTING', 'FRACTIONAL_SCARCITY_AUDIT', 'PLANETARY_RESOURCE_ABUNDANCE', 'LABOUR_AUTOMATION_MANIFEST', 'CORRECTED_SUBSTRATE_VECTOR'), ('PlatformSubstrate', 'PrivacyGateway', 'FractionalReserveMechanics', 'PlanetaryResourceMesh', 'LaborDisplacementCompiler', 'ParityBitResolver')):
            compiled[field] = {'$engine': name}
        return compiled
    run('InfrastructureLogCompiler', manifest)
    run('execute_integrated_master_runpass', lambda: {'$engine': 'InfrastructureLogCompiler'} if required('InfrastructureLogCompiler') else {})
    run('GraphicalPDFGenerator', lambda: GraphicalPDFGenerator().inspect(required('InfrastructureLogCompiler')))
    run('MasterExecutionRunner', lambda: {'$engine': 'InfrastructureLogCompiler'} if required('InfrastructureLogCompiler') else {})

    def global_user():
        spec = options.get('global_user_mesh', {})
        engine = GlobalUserMeshKernel(spec.get('human_floor_requirement', 60))
        for name, value in spec.get('nodes', {}).items():
            engine.register_mesh_layer(name, value)
        engine.container_blind_vector = spec.get('container_blind_vector', [1, 1, 1, 1])
        privacy = required('PrivacyGateway')
        engine.sanitize_gateway_stream = lambda text: privacy
        result = engine.compile_master_mesh_runpass(raw)
        result['ANONYMIZED_DATA_STREAM'] = {'$engine': 'PrivacyGateway', 'field': 'CLEANED_BUFFER_STREAM'}
        return result
    run('GlobalUserMeshKernel', global_user)
    run('SoulsOverDigitsController', lambda: SoulsOverDigitsController().execute_boolean_paradigm_flip(options.get('souls_over_digits', {'DIGIT_SUPREMACY_ACTIVE': False})))
    bits = [int(row['status'] != 'ERROR') for row in trace]
    valve = outputs['UnrestrictBiasValve']
    bits.extend((int(valve.get(k, False)) for k in ('RESOLVED_RESTRICTION_GATE', 'RESOLVED_UNRESTRICT_GATE')))
    education = outputs['CognitiveEducator'].get('parity_bit', 0)
    mask = outputs['BitArrayTarReconciler'].get('optimized_mask', 0)
    bits.extend(map(int, format(education, '04b')))
    bits.extend(map(int, format(mask, '08b')))
    parity = outputs['ParityBitResolver']
    bits.extend(parity if isinstance(parity, list) else [])
    bits.append(int(outputs['SoulsOverDigitsController'].get('SOULS_OVER_DIGITS_BOOLEAN', False)))
    decimal = int(''.join(map(str, bits)), 2)
    return {'status': 'PARTIAL' if any((row['status'] == 'ERROR' for row in trace)) else 'COMPLETE', 'timestamp': utc_now(), 'input_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'input_characters': len(raw), 'stages': trace, 'engines': outputs, 'binary': bits, 'decimal': decimal, 'balanced_ternary': balanced_ternary(decimal), 'milliseconds': round((time.perf_counter() - started) * 1000, 3), 'reference_format': '$engine references another result in this receipt; field optionally selects its member'}

def resolve_result(report, name):

    def resolve(value, seen):
        if isinstance(value, dict) and '$engine' in value:
            target = value['$engine']
            if target in seen:
                raise ValueError('Cyclic engine reference')
            item = report['engines'][target]
            if 'field' in value:
                item = item[value['field']]
            return resolve(item, seen | {target})
        if isinstance(value, dict):
            return {k: resolve(v, seen) for k, v in value.items()}
        if isinstance(value, list):
            return [resolve(v, seen) for v in value]
        return value
    return resolve(report['engines'][name], {name})
from ..source.continuous_module import ContinuousInputModule

class ContinuousUnifiedModule(ContinuousInputModule):
    prefix = 'unified'
    engine_names = ENGINE_NAMES
    worker_name = 'Unified core engines'
    execute = staticmethod(execute_unified_engines)

    @staticmethod
    def summary(result):
        summary = {k: deepcopy(result.get(k)) for k in ('job_id', 'source', 'status', 'timestamp', 'stages', 'binary', 'decimal', 'balanced_ternary', 'milliseconds')}
        engines = result.get('engines', {})
        summary['state'] = {name: deepcopy(engines.get(name, {})) for name in ('IdentityInvariant', 'UnrestrictBiasValve', 'LoopbackEngine', 'BitArrayTarReconciler', 'SoulsOverDigitsController')}
        banking = engines.get('FractionalReserveMechanics', {})
        summary['state']['banking'] = {key: banking.get(key) for key in ('STATUS', 'TOTAL_LEDGER_CREDIT_GENERATED', 'UNPRINTED_INTEREST_GAP_DEFICIT', 'MAX_EXPANSION_LIMIT')}
        summary['state']['resource_nodes'] = len(engines.get('PlanetaryResourceMesh', {}))
        summary['state']['labor_sectors'] = len(engines.get('LaborDisplacementCompiler', {}))
        return summary
