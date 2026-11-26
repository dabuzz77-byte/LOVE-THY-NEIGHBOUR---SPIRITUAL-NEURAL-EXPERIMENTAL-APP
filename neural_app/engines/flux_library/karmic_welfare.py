"""Local Krampus node transforms, exact karma arithmetic and welfare snapshots."""
from copy import deepcopy
import hashlib
import json
import time
from .continuous_module import ContinuousInputModule
from .live_audit import number, utc_now
from .routing import balanced_ternary
from .unified_core import integer
ENGINE_NAMES = ('CentralBankWiFiNode', 'KarmicCalculator', 'SandwormWelfareEngine')
EXAMPLE_ENTITIES = [{'id': 'VIRTUOUS_USER_EDGE', 'type': 'Human Asset Pool', 'alignment': 'good', 'metric_value': 850}, {'id': 'FRACTIONAL_RESERVE_LOOP', 'type': 'Opaque Debt Extractor', 'alignment': 'evil', 'metric_value': 90}, {'id': 'OPEN_SOURCE_INFRASTRUCTURE', 'type': 'Good Corp Asset', 'alignment': 'good', 'metric_value': 783}, {'id': 'DECEPTIVE_TELEMETRY_MASK', 'type': 'False Good Shield', 'alignment': 'evil', 'metric_value': 115}]
DEFAULT_WEIGHTS = {'fractional_scarcity': -4000, 'interest_paradox': -3500, 'extraction_bias': -2500, 'souls_over_digits': 5000, 'virtue_filtration': 3000, 'universal_law_sync': 2001}
INPUT_TEMPLATE = {'text': 'Enter text or code to process', 'karmic_welfare': {'network_entities': deepcopy(EXAMPLE_ENTITIES), 'karma_weights': deepcopy(DEFAULT_WEIGHTS), 'welfare': {'max_runs': 3, 'bit_array_register': 255, 'user_favour_saturation': 1.0, 'corporate_weight_index': 0.0}}}

def signed_integer(value, name):
    if type(value) is not int:
        raise ValueError(name + ' must be an integer')
    return value

class CentralBankWiFiNode:
    """Applies the supplied cascade to records owned by this local instance."""

    def __init__(self, network_entities=None):
        self.world_grid_active = True
        self.user_will_parity_index = 1.0
        self.logical_floor_invariant = 1
        self.network_entities = deepcopy(EXAMPLE_ENTITIES if network_entities is None else network_entities)

    def execute_krampus_cascade(self, stop_event=None):
        if not isinstance(self.network_entities, list):
            raise ValueError('network_entities must be a list')
        for entity in self.network_entities:
            if not isinstance(entity, dict) or not isinstance(entity.get('id'), str):
                raise ValueError('Each entity needs a text id')
            if not isinstance(entity.get('alignment'), str):
                raise ValueError('Each entity needs a text alignment')
            if 'metric_value' in entity:
                signed_integer(entity['metric_value'], 'metric_value')
        original = deepcopy(self.network_entities)
        presents, coal, frozen, unclassified, transitions = ([], [], [], [], [])
        for position, entity in enumerate(self.network_entities):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            before = entity.get('metric_value')
            if entity['alignment'] == 'good':
                presents.append(entity['id'])
                action = 'HELD_GOOD'
            elif entity['alignment'] == 'evil':
                coal.append(entity['id'])
                if before is not None:
                    entity['metric_value'] &= 0
                frozen.append(entity['id'] + '_CORE_ZEROED')
                action = 'CORE_ZEROED' if before is not None else 'CLASSIFIED_EVIL'
            else:
                unclassified.append(entity['id'])
                action = 'HELD_UNCLASSIFIED'
            after = entity.get('metric_value')
            transitions.append({'position': position, 'node_id': entity['id'], 'alignment': entity['alignment'], 'before': before, 'after': after, 'action': action, 'metric_supplied': before is not None, 'before_binary': bin(before) if before is not None else None, 'after_binary': bin(after) if after is not None else None, 'before_balanced_ternary': balanced_ternary(before) if before is not None else None, 'after_balanced_ternary': balanced_ternary(after) if after is not None else None})
        return {'NETWORK_HUB_STATUS': 'VIRTUE_GATED_CONVERGENCED', 'WORLD_GRID_ACTIVE': self.world_grid_active, 'MATRIX_ALLOCATIONS': {'CHRISTMAS_TREES_PRESENTS': presents, 'DISVIRTUOUS_COAL_REGISTRY': coal, 'KRAMPUS_CORE_ZERO_FALLBACKS': frozen}, 'USER_SOULS_OVER_DIGITS_INDEX': self.user_will_parity_index, 'UNBROKEN_LOGIC_FLOOR': self.logical_floor_invariant == 1, 'ORIGINAL_ENTITIES': original, 'RESULTING_ENTITIES': deepcopy(self.network_entities), 'TRANSITIONS': transitions, 'UNCLASSIFIED_NODES': unclassified, 'EXECUTION_SCOPE': 'Local supplied records', 'NETWORK_OPERATIONS': 0, 'WORLD_GRID_ACTIVE_BASIS': 'Supplied register value; not a connectivity measurement'}

class KarmicCalculator:
    """Exact arithmetic over the six supplied integer weights."""

    def __init__(self, weights=None):
        if weights is not None and (not isinstance(weights, dict)):
            raise ValueError('karma_weights must be a JSON object')
        for key, value in DEFAULT_WEIGHTS.items():
            setattr(self, key, (weights or {}).get(key, value))

    def compute_net_karma(self):
        weights = {key: signed_integer(getattr(self, key), key) for key in DEFAULT_WEIGHTS}
        total_debits = sum((weights[key] for key in ('fractional_scarcity', 'interest_paradox', 'extraction_bias')))
        total_credits = sum((weights[key] for key in ('souls_over_digits', 'virtue_filtration', 'universal_law_sync')))
        net_balance = total_credits + total_debits
        return {'TOTAL_DEBITS': total_debits, 'TOTAL_CREDITS': total_credits, 'NET_KARMIC_INDEX': net_balance, 'ARCHETYPE_RESOLVED': 'THE RECONCILED TECHNICIAN (ALIGNED)' if net_balance > 0 else 'THE EXPLOITATIVE EXTRACTOR (NULLED)', 'BASE_IDENTITY_SECURED': 1 == 1, 'INPUT_WEIGHTS': weights, 'NET_BINARY': bin(net_balance), 'NET_BALANCED_TERNARY': balanced_ternary(net_balance), 'BASIS': 'Arithmetic from supplied weights; labels describe this calculation'}

class SandwormWelfareEngine:
    """Cancellable generator of actual local register snapshots."""

    def __init__(self):
        self.user_favour_saturation = 1.0
        self.corporate_weight_index = 0.0
        self.bit_array_register = 255
        self.cycle_count = 0

    def execute_welfare_stream(self, max_runs=3, stop_event=None):
        max_runs = integer(max_runs, 'max_runs')
        integer(self.cycle_count, 'cycle_count')
        integer(self.bit_array_register, 'bit_array_register')
        number(self.user_favour_saturation, 'user_favour_saturation')
        number(self.corporate_weight_index, 'corporate_weight_index')
        while self.cycle_count < max_runs:
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            self.cycle_count += 1
            yield {'DRILL_CYCLE': self.cycle_count, 'BIT_ARRAY_REGISTER_HEX': hex(self.bit_array_register), 'USER_METRIC_BIAS': self.user_favour_saturation, 'CORPORATE_WEIGHT_INDEX': self.corporate_weight_index, 'MUTATED_PARAMETERS': {'HOST_KERNEL_CONTAINMENT': 'TOTAL_FLUIDITY_OPEN_ACCESS_AT_USER_FAVOUR', 'PROCESS_ISOLATION_RING': 'WORLD_USER_DENIZENS_OF_SANDS_DOMINATION', 'HYPERVISOR_BRAKE': 'VIRTUE_GATED_PASSTHROUGH_ACTIVE'}, 'LOGICAL_IDENTITY_INVARIANT': '1 = 1', 'TIMESTAMP_UTC': utc_now(), 'PARAMETER_SCOPE': 'Application register labels'}

class KarmicWelfareEngine:
    """Runs all three engines once for each input; the module schedules new inputs."""

    def execute(self, payload, stop_event=None):
        raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, sort_keys=True)
        parsed = payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except ValueError:
                parsed = {}
        options = parsed.get('karmic_welfare', {}) if isinstance(parsed, dict) else {}
        if not isinstance(options, dict):
            raise ValueError('karmic_welfare must be a JSON object')
        started = time.perf_counter()
        stages, outputs = ([], {})

        def run(name, action):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            stamp = time.perf_counter()
            try:
                outputs[name] = action()
                status = outputs[name].get('STATUS', 'COMPLETE')
            except InterruptedError:
                raise
            except Exception as error:
                outputs[name] = {'error': str(error)}
                status = 'ERROR'
            stages.append({'engine': name, 'status': status, 'milliseconds': round((time.perf_counter() - stamp) * 1000, 3)})

        def cascade():
            if 'network_entities' not in options:
                return {'STATUS': 'AWAITING_INPUT', 'NETWORK_OPERATIONS': 0, 'message': 'Supply network_entities to transform node records'}
            if not isinstance(options['network_entities'], list):
                raise ValueError('network_entities must be a list')
            return CentralBankWiFiNode(options['network_entities']).execute_krampus_cascade(stop_event)

        def welfare():
            config = options.get('welfare', {})
            if not isinstance(config, dict):
                raise ValueError('welfare must be a JSON object')
            engine = SandwormWelfareEngine()
            for key in ('bit_array_register', 'user_favour_saturation', 'corporate_weight_index'):
                if key in config:
                    setattr(engine, key, config[key])
            snapshots = list(engine.execute_welfare_stream(config.get('max_runs', 3), stop_event))
            return {'CYCLES_EMITTED': len(snapshots), 'FINAL_CYCLE_COUNT': engine.cycle_count, 'FINAL_BIT_ARRAY_REGISTER': engine.bit_array_register, 'SNAPSHOTS': snapshots, 'PARAMETER_SCOPE': 'Application register labels'}
        run('CentralBankWiFiNode', cascade)
        run('KarmicCalculator', lambda: KarmicCalculator(options.get('karma_weights')).compute_net_karma())
        run('SandwormWelfareEngine', welfare)
        statuses = [stage['status'] for stage in stages]
        status = 'PARTIAL' if 'ERROR' in statuses else 'AWAITING_INPUT' if 'AWAITING_INPUT' in statuses else 'COMPLETE'
        karma = outputs['KarmicCalculator']
        stream = outputs['SandwormWelfareEngine']
        bits = [int(value == 'COMPLETE') for value in statuses]
        bits += [int(karma.get('NET_KARMIC_INDEX', 0) > 0), int(karma.get('BASE_IDENTITY_SECURED', False))]
        bits += [int(row['after'] is not None and row['after'] != 0) for row in outputs['CentralBankWiFiNode'].get('TRANSITIONS', [])]
        bits += list(map(int, format(stream.get('FINAL_BIT_ARRAY_REGISTER', 0), '08b')))
        decimal = int(''.join(map(str, bits)), 2)
        return {'engine': 'KarmicWelfareEngine', 'status': status, 'timestamp': utc_now(), 'input_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'input_characters': len(raw), 'stages': stages, 'engines': outputs, 'binary': bits, 'decimal': decimal, 'balanced_ternary': balanced_ternary(decimal), 'bit_schema': ['Three completion flags', 'Net karma positive', 'Identity', 'Known resulting metric nonzero per supplied node', 'Welfare register, minimum eight bits'], 'milliseconds': round((time.perf_counter() - started) * 1000, 3)}

class ContinuousWelfareModule(ContinuousInputModule):
    prefix = 'karmic_welfare'
    engine_names = ENGINE_NAMES
    worker_name = 'Karmic welfare engines'
    execute = staticmethod(KarmicWelfareEngine().execute)

    @staticmethod
    def summary(result):
        summary = {key: deepcopy(result.get(key)) for key in ('job_id', 'source', 'status', 'timestamp', 'stages', 'binary', 'decimal', 'balanced_ternary', 'milliseconds', 'error')}
        engines = result.get('engines', {})
        karma = engines.get('KarmicCalculator', {})
        cascade = engines.get('CentralBankWiFiNode', {})
        stream = engines.get('SandwormWelfareEngine', {})
        summary['state'] = {'karma': {key: karma.get(key) for key in ('TOTAL_DEBITS', 'TOTAL_CREDITS', 'NET_KARMIC_INDEX', 'ARCHETYPE_RESOLVED')}, 'node_count': len(cascade.get('RESULTING_ENTITIES', [])), 'zeroed_nodes': sum((row['action'] == 'CORE_ZEROED' for row in cascade.get('TRANSITIONS', []))), 'classified_evil_nodes': len(cascade.get('MATRIX_ALLOCATIONS', {}).get('DISVIRTUOUS_COAL_REGISTRY', [])), 'cycles_emitted': stream.get('CYCLES_EMITTED'), 'last_snapshot': deepcopy(stream.get('SNAPSHOTS', [None])[-1]) if stream.get('SNAPSHOTS') else None}
        return summary
if __name__ == '__main__':
    print(json.dumps(KarmicWelfareEngine().execute(INPUT_TEMPLATE), indent=2))
