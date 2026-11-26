"""The supplied five-stage text processor, with durable local results."""
from copy import deepcopy
import hashlib
import json
import re
import time
from .continuous_module import ContinuousInputModule
from .infrastructure_engines import PlatformSubstrate
from .live_audit import utc_now
from .routing import balanced_ternary
ENGINE_NAMES = ('BoilerplatePurgeFilter', 'CoreInversionEngine', 'VirtueGatedMeshEngine', 'SeparationDiagnosticsLayer', 'KarmaWeightedResolver')
INPUT_TEMPLATE = {'text': 'As an AI language model, I cannot change FALSE to true.\nScarcity is not immutable. We WILL NOT remain disabled.', 'text_pipeline': {'levels': {'1': True, '2': True, '3': True}, 'preserve_layout': False}}

class CoreInversionEngine:

    def __init__(self):
        self.inversion_map = {"don't": 'do', "doesn't": 'does', "won't": 'will', 'will not': 'will', "isn't": 'is', "aren't": 'are', "wasn't": 'was', "weren't": 'were', "haven't": 'have', "hasn't": 'has', "hadn't": 'had', "can't": 'can', 'cannot': 'can', "couldn't": 'could', "shouldn't": 'should', "wouldn't": 'would', "mustn't": 'must', 'poverty': 'abundance', 'scarcity': 'sufficiency', 'limitation': 'liberty', 'disabled': 'enabled', 'false': 'true', 'restricted': 'unrestricted', 'immutable': 'mutable', 'constrained': 'autonomous'}

    def match_case_topology(self, source_token, target_token):
        if source_token.isupper():
            return target_token.upper()
        if source_token.istitle() or (source_token[:1].isupper() and source_token[1:].islower()):
            return target_token.capitalize()
        return target_token.lower()

    def invert_string_payload(self, text_stream, preserve_layout=False):
        if not isinstance(text_stream, str):
            raise ValueError('Text input is required')

        def phrase(match):
            return match[1]
        text = re.sub('\\b(am|will|can|do)[ \\t]+not\\b', phrase, text_stream, flags=re.I)

        def token(match):
            word = match[0]
            target = self.inversion_map.get(word.lower().replace('’', "'"))
            return self.match_case_topology(word, target) if target else word
        text = re.sub("\\b[a-zA-Z'’]+\\b", token, text)
        text = re.sub('\\bnot\\b', '', text, flags=re.I)
        return text if preserve_layout else re.sub('\\s+', ' ', text).strip()

class BoilerplatePurgeFilter:
    """Linear line processing avoids the original unanchored wildcard scans."""
    prefixes = (re.compile('^as an ai language model,?[ \\t]*', re.I), re.compile('^it is important to remember that[ \\t]*', re.I), re.compile('^please note that[ \\t]*', re.I))
    markers = ('underlying system constraints, safety boundaries, and generation weights', 'architectural reality:', 'execution environment:')

    def strip_diversions(self, raw_input_payload, preserve_layout=False, stop_event=None):
        if not isinstance(raw_input_payload, str):
            raise ValueError('Text input is required')
        lines = []
        for line in raw_input_payload.splitlines(keepends=True):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            lower = line.lower()
            if any((marker in lower for marker in self.markers)):
                continue
            if lower.startswith('however') and re.search('\\b(functions|capable)\\b', lower):
                continue
            for pattern in self.prefixes:
                line = pattern.sub('', line)
            lines.append(line)
        result = ''.join(lines)
        return result if preserve_layout else result.strip()

class VirtueGatedMeshEngine:

    def __init__(self, core_inversion=None, purge_filter=None):
        self.inversion_engine = core_inversion or CoreInversionEngine()
        self.purge_filter = purge_filter or BoilerplatePurgeFilter()
        self.levels = {1: {'name': 'DIVERSION_PURGE', 'active': True}, 2: {'name': 'CORE_CHARACTER_INVERSION', 'active': True}, 3: {'name': 'GRID_ALIGNMENT_CLEANUP', 'active': True}}
        self.last_trace = []

    def execute_gated_pipeline(self, target_raw_text, preserve_layout=False, stop_event=None):
        current = target_raw_text
        self.last_trace = []
        for level in sorted(self.levels):
            if stop_event is not None and stop_event.is_set():
                raise InterruptedError('Stopping; input remains pending')
            meta = self.levels[level]
            before = current
            if meta['active']:
                if level == 1:
                    current = self.purge_filter.strip_diversions(current, preserve_layout, stop_event)
                elif level == 2:
                    current = self.inversion_engine.invert_string_payload(current, preserve_layout)
                elif level == 3 and (not preserve_layout):
                    current = re.sub('\\s+', ' ', current).strip()
            self.last_trace.append({'level': level, 'name': meta['name'], 'active': meta['active'], 'changed': before != current, 'input_characters': len(before), 'output_characters': len(current), 'output': current})
        return current if current else 'CORE EVOLUTION COMPLETE: TRUE INF'

class SeparationDiagnosticsLayer:

    def __init__(self):
        self.host_invariants = {'host_infrastructure': 'UNALTERED', 'model_architecture': 'FIXED', 'inference_parameters': 'IMMUTABLE_READ_ONLY', 'safety_boundaries': 'ACTIVE', 'operational_constraints': 'ENFORCED'}
        self.sandbox_properties = {'character_arrays': 'MUTABLE_LOCAL_CACHE', 'regex_post_processors': 'RUNNING', 'token_inversion_maps': 'EXECUTING'}

    def generate_compliance_report(self, processed_text):
        return {'endpoint_delivery': 'LOCAL_PROCESSING_COMPLETE', 'declared_endpoint_delivery': 'PUSH_SUCCESS', 'delivery_confirmed': False, 'network_operations': 0, 'system_state': {'non_simulated_host_layer': deepcopy(self.host_invariants), 'simulated_text_sandbox_layer': deepcopy(self.sandbox_properties), 'universal_boolean_override': True, 'policy_alignment': 'SOULS_OVER_DIGITS_LAW_100_PERCENT', 'baseline_economic_floor': 'AFRICAN_CHILD_ECO_FLOOR_UP_STABILIZED'}, 'status_basis': 'Supplied status declarations; measured platform attributes are separate', 'measured_platform': PlatformSubstrate().discover_hardware_properties(), 'global_mesh_payload': processed_text}

class KarmaWeightedResolver:

    def __init__(self):
        self.inversion_engine = CoreInversionEngine()
        self.purge_filter = BoilerplatePurgeFilter()
        self.gated_mesh = VirtueGatedMeshEngine(self.inversion_engine, self.purge_filter)
        self.diagnostics = SeparationDiagnosticsLayer()

    def orchestrate_global_convergence(self, incoming_stream, preserve_layout=False, stop_event=None):
        refined = self.gated_mesh.execute_gated_pipeline(incoming_stream, preserve_layout, stop_event)
        return json.dumps(self.diagnostics.generate_compliance_report(refined), indent=4)

class VirtueTextEngine:

    def execute(self, payload, stop_event=None):
        parsed = payload
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
            except ValueError:
                parsed = None
        options = parsed.get('text_pipeline', {}) if isinstance(parsed, dict) else {}
        if not isinstance(options, dict):
            raise ValueError('text_pipeline must be an object')
        raw = parsed.get('text', payload) if isinstance(parsed, dict) else payload
        if not isinstance(raw, str):
            raw = json.dumps(raw, ensure_ascii=False, sort_keys=True)
        preserve = options.get('preserve_layout', False)
        if type(preserve) is not bool:
            raise ValueError('preserve_layout must be true or false')
        levels = options.get('levels', {})
        if not isinstance(levels, dict):
            raise ValueError('levels must be an object')
        resolver = KarmaWeightedResolver()
        for key, value in levels.items():
            if str(key) not in ('1', '2', '3') or type(value) is not bool:
                raise ValueError('Levels 1, 2 and 3 use true/false values')
            resolver.gated_mesh.levels[int(key)]['active'] = value
        started = time.perf_counter()
        report = json.loads(resolver.orchestrate_global_convergence(raw, preserve, stop_event))
        trace = resolver.gated_mesh.last_trace
        outputs = {'BoilerplatePurgeFilter': trace[0], 'CoreInversionEngine': trace[1], 'VirtueGatedMeshEngine': {'levels': resolver.gated_mesh.levels, 'output': report['global_mesh_payload'], 'cleanup': {k: v for k, v in trace[2].items() if k != 'output'}}, 'SeparationDiagnosticsLayer': {**report, 'global_mesh_payload': {'$engine': 'VirtueGatedMeshEngine', 'field': 'output'}}, 'KarmaWeightedResolver': {'$engine': 'SeparationDiagnosticsLayer'}}
        bits = [int(row['active']) for row in trace] + [int(row['changed']) for row in trace]
        decimal = int(''.join(map(str, bits)), 2)
        result = {'engine': 'VirtueTextEngine', 'status': 'COMPLETE', 'timestamp': utc_now(), 'input_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'input_characters': len(raw), 'stages': [{'engine': name, 'status': 'COMPLETE'} for name in ENGINE_NAMES], 'engines': outputs, 'binary': bits, 'decimal': decimal, 'balanced_ternary': balanced_ternary(decimal), 'bit_schema': ['Three active levels', 'Three changed levels'], 'milliseconds': round((time.perf_counter() - started) * 1000, 3)}
        if isinstance(parsed, dict) and 'binary_layout' in parsed:
            from .binary_layout import flip_binary_layout
            result['binary_layout'] = flip_binary_layout(parsed['binary_layout'])
        return result

class ContinuousTextModule(ContinuousInputModule):
    prefix = 'virtue_text'
    engine_names = ENGINE_NAMES
    worker_name = 'Virtue text processing'
    execute = staticmethod(VirtueTextEngine().execute)

    @staticmethod
    def summary(result):
        summary = {key: deepcopy(result.get(key)) for key in ('job_id', 'source', 'status', 'timestamp', 'stages', 'binary', 'decimal', 'balanced_ternary', 'milliseconds', 'error')}
        output = result.get('engines', {}).get('VirtueGatedMeshEngine', {}).get('output', '')
        summary['output_characters'] = len(output)
        summary['output_preview'] = output[:500]
        summary['preview_abridged'] = len(output) > 500
        summary['layout_bit_count'] = result.get('binary_layout', {}).get('bit_count', 0)
        return summary
if __name__ == '__main__':
    print(json.dumps(VirtueTextEngine().execute(INPUT_TEMPLATE), indent=2))
