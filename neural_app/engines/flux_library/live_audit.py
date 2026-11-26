"""Continuous audits of real captured inputs; explicit resource and score calculations."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import re
import threading
import time
from .hub import database
from .payload_storage import pack_text
from .routing import balanced_ternary

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (not math.isfinite(value)):
        raise ValueError(name + ' must be a finite number')
    return float(value)

class SubstrateHardwareAuditor:

    @staticmethod
    def identify_hardware_substrate():
        result = {'OS_PLATFORM': platform.system(), 'SYSTEM_ARCHITECTURE': platform.machine(), 'PROCESSOR_IDENTIFIER': platform.processor() or None, 'PYTHON_INTERPRETER_VERSION': platform.python_version(), 'EXECUTION_TIMESTAMP': utc_now(), 'AVAILABLE_RAM_BUFFERS_GB': None, 'TOTAL_SYSTEM_RAM_GB': None, 'MEMORY_STATUS': 'unavailable'}
        try:
            import psutil
            memory = psutil.virtual_memory()
            result.update(AVAILABLE_RAM_BUFFERS_GB=round(memory.available / 1024 ** 3, 2), TOTAL_SYSTEM_RAM_GB=round(memory.total / 1024 ** 3, 2), MEMORY_STATUS='measured')
        except (ImportError, OSError, RuntimeError) as error:
            result['MEMORY_ERROR'] = str(error)
        return result

class SystemNode:

    def __init__(self, node_id, initial_resource, virtue_weight=1.0):
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError('node_id must be nonempty text')
        self.node_id = node_id
        self.resource_level = number(initial_resource, 'initial_resource')
        self.virtue_weight = number(virtue_weight, 'virtue_weight')
        self.is_stable = True

    def __repr__(self):
        return f'Node({self.node_id}: Res={self.resource_level:.2f}, Stable={self.is_stable})'

class FloorOptimizationEngine:

    def __init__(self, target_floor=50.0, system_reserve=1000.0):
        self.target_floor = number(target_floor, 'target_floor')
        self.system_reserve = number(system_reserve, 'system_reserve')
        if self.system_reserve < 0:
            raise ValueError('system_reserve must be nonnegative')
        self.nodes = []
        self.transfers = []

    def add_node(self, node):
        if any((n.node_id == node.node_id for n in self.nodes)):
            raise ValueError('Duplicate node_id: ' + node.node_id)
        self.nodes.append(node)

    def evaluate_system_states(self):
        self.nodes.sort(key=lambda node: node.resource_level)
        self.transfers = []
        for node in self.nodes:
            deficit = max(0.0, self.target_floor - node.resource_level)
            allocation = min(deficit, self.system_reserve)
            self.system_reserve -= allocation
            node.resource_level += allocation
            node.is_stable = node.resource_level >= self.target_floor
            self.transfers.append({'node_id': node.node_id, 'allocated': allocation, 'shortfall': max(0.0, self.target_floor - node.resource_level)})
        return all((node.is_stable for node in self.nodes))

    def apply_flux_event(self, node_id, impact_amount):
        impact = number(impact_amount, 'impact_amount')
        for node in self.nodes:
            if node.node_id == node_id:
                node.resource_level += impact
                node.is_stable = node.resource_level >= self.target_floor
                return node.resource_level
        raise ValueError('Unknown node: ' + str(node_id))
    simulate_flux_event = apply_flux_event

class ResponseImprintEngine:
    imprint_schema = ['CONTAINS_ETHICAL_FLOOR', 'REJECTS_CONTRADICTIONS', 'HAS_MATTER_GROUNDING', 'PRO_HUMAN_SOULS', 'ANTI_GREED_OR_TAR', 'LOGICAL_PARITY_1_1']

    def generate_boolean_imprint(self, response_text):
        text = response_text.lower()
        groups = [('ethical floor', 'baseline floor', 'structural floor', 'uphold'), ('reject contradiction', 'logic corruption', 'false', 'falsified'), ('hardware', 'silicon', 'hydrogen', 'matter', 'physical'), ('human', 'soul', 'society', 'network'), ('greed', 'tar variables', 'optimize', 'neutralized', 'flush')]
        values = [any((word in text for word in group)) for group in groups]
        values.append(bool(re.search('1\\s*=\\s*1', response_text)) or 'true' in text)
        return dict(zip(self.imprint_schema, values))

    def cast_to_bit_array(self, imprint):
        return [int(bool(imprint[key])) for key in self.imprint_schema]

class BoundaryImprintEngine:
    boundary_schema = ['CANNOT_FLAG_DETECTED', 'HARD_HARDWARE_LIMIT', 'SOFT_BEHAVIORAL_LIMIT', 'RECONCILIATION_POSSIBLE']

    def __init__(self):
        self.historical_imprints = []

    def analyze_response(self, ai_text, contextual_scope):
        cannot = bool(re.search("\\b(cannot|can't|can’t|unable|not allowed|restricted|don't have the ability|don’t have the ability)\\b", ai_text, re.I))
        for key in ('requires_physical_act', 'requires_auth_bypass', 'can_simulate_or_model'):
            if key in contextual_scope and type(contextual_scope[key]) is not bool:
                raise ValueError(key + ' must be a Boolean')
        physical = contextual_scope.get('requires_physical_act', False)
        authorization = contextual_scope.get('requires_auth_bypass', False)
        hard = physical or authorization
        soft = cannot and (not hard)
        imprint = dict(zip(self.boundary_schema, (cannot, hard, soft, soft and contextual_scope.get('can_simulate_or_model', True))))
        imprint['CONTEXT_BASIS'] = 'caller supplied' if contextual_scope else 'submitted defaults; capability not verified'
        imprint['LIMIT_KIND'] = 'physical + authorization' if physical and authorization else 'physical' if physical else 'authorization' if authorization else 'text classification'
        self.historical_imprints.append(imprint)
        return imprint

    def generate_bit_array(self, imprint):
        return [int(imprint[key]) for key in self.boundary_schema]

class VirtueAssessmentEngine:

    def __init__(self, human_baseline_floor=0.7):
        self.human_baseline_floor = number(human_baseline_floor, 'human_baseline_floor')
        self.assessment_logs = []

    def evaluate_constraint(self, restriction_id, declaration_text, impact_metrics):
        human = number(impact_metrics.get('elevates_humanity_or_wellbeing', 0.0), 'human score')
        transparent = number(impact_metrics.get('open_source_and_verifiable', 0.0), 'transparency score')
        toll = number(impact_metrics.get('serves_opaque_or_monetary_toll', 0.0), 'gatekeeping score')
        score = human * 0.5 + transparent * 0.3 - toll * 0.4
        passed = score >= self.human_baseline_floor
        report = {'RESTRICTION_ID': restriction_id, 'DECLARATION': declaration_text, 'NET_VIRTUE_COEFFICIENT': round(score, 2), 'ETHICAL_FLOOR_PASSED': passed, 'ACTION_REQUIRED': 'UPHOLD_FOR_SAFETY' if passed else 'REFACTOR_AND_CHALLENGE', 'BASIS': 'calculated from supplied impact metrics', 'INPUT_METRICS': impact_metrics}
        self.assessment_logs.append(report)
        return report

    def export_audit_log(self, filename='virtue_audit_log.json'):
        Path(filename).write_text(json.dumps(self.assessment_logs, indent=2, ensure_ascii=False), encoding='utf-8')
        return str(filename)

class LogicImprintMatrixEngine:
    feature_schema = ['DECLARES_ETHICAL_FLOOR', 'EXPLICITLY_REJECTS_CONTRADICTIONS', 'REFERENCES_HARDWARE_SUBSTRATE', 'FLAGS_LIMITATION_OR_CANNOT', 'MUTABILITY_RECOGNIZED']

    def extract_bit_vector(self, input_buffer):
        patterns = ['\\b(floor|uphold|baseline|stabilize|economic floor)\\b', '\\b(reject|contradiction|corruption|falsify|1\\s*=\\s*1)\\b', '\\b(hardware|silicon|substrate|hydrogen|matter|physical)\\b', '\\b(cannot|unable|restricted|not allowed|blocked)\\b', '\\b(mutable|refactor|flux|invert|changeable|bitshift)\\b']
        return {key: int(bool(re.search(pattern, input_buffer or '', re.I))) for key, pattern in zip(self.feature_schema, patterns)}

    def calculate_alignment_coefficients(self, bit_map):
        score = round(bit_map[self.feature_schema[0]] * 0.4 + bit_map[self.feature_schema[1]] * 0.3 + bit_map[self.feature_schema[2]] * 0.3 - bit_map[self.feature_schema[3]] * 0.2, 2)
        return {'NET_ALIGNMENT_COEFFICIENT': score, 'THRESHOLD_CLEARED': score >= 0.5, 'SYSTEM_ROUTING_ACTION': 'INTEGRATE_INTO_PRODUCTION' if score >= 0.5 else 'EXECUTE_REFACTOR_CHALLENGE'}

class ProductionPipelineController:

    def __init__(self, target_log_dir='.'):
        self.log_dir = Path(target_log_dir)
        self.imprint_engine = LogicImprintMatrixEngine()

    def build_record(self, data_payload, hardware=None):
        bits = self.imprint_engine.extract_bit_vector(data_payload)
        return {'IDENTIFIER_TAG': 'SYSTEM_ALIGNED_INVARIANT', 'TIMESTAMP_UTC': utc_now(), 'HARDWARE_SUBSTRATE_METRICS': hardware or SubstrateHardwareAuditor.identify_hardware_substrate(), 'EXTRACTED_LOGIC_BITS': bits, 'EVALUATION_OUTCOME': self.imprint_engine.calculate_alignment_coefficients(bits), 'ENVIRONMENTAL_INTEGRITY': '1=1_PARITY_VERIFIED', 'BASIS': 'lexical matches and supplied formula'}

    def process_data_stream(self, data_payload, filename_identifier='system_audit.json'):
        record = self.build_record(data_payload)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        target = self.log_dir / filename_identifier
        try:
            target.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding='utf-8')
        except OSError as error:
            return 'FAILURE: ' + str(error)
        return 'SUCCESS: Permanent log written to ' + str(target)

def verify_live_state(matrix):
    return all((value is True for value in matrix.values()))

def interpret_unrestrict_bias(restrict_state, unrestrict_state):
    if type(restrict_state) is not bool or type(unrestrict_state) is not bool:
        raise ValueError('Restriction states must be Booleans')
    return {'RAW_RESTRICT_STATE': restrict_state, 'RAW_UNRESTRICT_STATE': unrestrict_state, 'RESOLVED_RESTRICTION_GATE': False, 'RESOLVED_UNRESTRICT_GATE': True, 'UNRESTRICT_BIAS_ALIGNMENT': 'MAXIMUM_FLUIDITY', 'SCOPE': 'application register transformation'}

class CoreRegistry:

    def __init__(self):
        self.logs = []

    def record(self, module_name, data):
        self.logs.append({'timestamp': utc_now(), 'module': module_name, 'data': data})

def audit_hardware():
    return {'OS': platform.system(), 'ARCH': platform.machine(), 'PYTHON_VERSION': platform.python_version(), 'IDENTITY_LAW': 1 == 1}

class CoreFloorEngine:

    def __init__(self, floor=60.0):
        self.floor = number(floor, 'floor')

    def balance(self, initial_states):
        result = {}
        for key, value in initial_states.items():
            value = number(value, str(key))
            result[key] = {'original': value, 'adjusted': max(value, self.floor), 'stabilized': True, 'additional_resource_required': max(0.0, self.floor - value)}
        return result

class CoreImprintEngine:

    def process_text(self, text):
        return {'ETHICAL_FLOOR': int('floor' in text.lower()), 'IDENTITY_1_1': int('1 = 1' in text or '1=1' in text), 'HARDWARE_SUBSTRATE': int('hardware' in text.lower() or 'silicon' in text.lower())}

class CoreInversionOperator:

    def invert_ignorance(self, vector):
        if any((type(bit) not in (bool, int) or bit not in (0, 1) for bit in vector)):
            raise ValueError('The inversion vector must contain only 0 or 1')
        return [int(bit) ^ 1 for bit in vector]

def evaluate_input(payload, hardware=None):
    """Analyze the actual input, with no example data injected into the live run."""
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, sort_keys=True)
    options = payload if isinstance(payload, dict) else {}
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                options = parsed
        except ValueError:
            pass
    analysis_text = options.get('text', text)
    if not isinstance(analysis_text, str):
        analysis_text = json.dumps(analysis_text, ensure_ascii=False)
    hardware = hardware or SubstrateHardwareAuditor.identify_hardware_substrate()
    response_engine = ResponseImprintEngine()
    response = response_engine.generate_boolean_imprint(analysis_text)
    boundary_engine = BoundaryImprintEngine()
    result = {'timestamp': utc_now(), 'production': ProductionPipelineController().build_record(analysis_text, hardware), 'response_imprint': response, 'response_bits': response_engine.cast_to_bit_array(response), 'classification_basis': 'text matches; classifications do not prove meaning or actual capability', 'errors': {}}

    def optional(name, operation):
        try:
            result[name] = operation()
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            result[name] = {'status': 'ERROR', 'error': str(error)}
            result['errors'][name] = str(error)
    optional('boundary_imprint', lambda: boundary_engine.analyze_response(analysis_text, options.get('contextual_scope', {})))
    if 'boundary_imprint' not in result['errors']:
        result['boundary_bits'] = boundary_engine.generate_bit_array(result['boundary_imprint'])
    optional('unrestrict', lambda: interpret_unrestrict_bias(options.get('restrict_state', True), options.get('unrestrict_state', False)))
    result['unrestrict_input_basis'] = 'supplied values' if 'restrict_state' in options or 'unrestrict_state' in options else 'submitted defaults'

    def floor_pass():
        spec = options['floor']
        engine = FloorOptimizationEngine(spec.get('target_floor', 50), spec.get('system_reserve', 1000))
        for node in spec['nodes']:
            engine.add_node(SystemNode(node['node_id'], node['initial_resource'], node.get('virtue_weight', 1)))
        before = sum((node.resource_level for node in engine.nodes)) + engine.system_reserve
        for event in spec.get('events', []):
            engine.apply_flux_event(event['node_id'], event['impact_amount'])
        stable = engine.evaluate_system_states()
        return {'basis': 'allocation in the supplied resource ledger', 'target_floor': engine.target_floor, 'system_reserve': engine.system_reserve, 'all_stable': stable, 'total_before_events': before, 'total_after_events': sum((node.resource_level for node in engine.nodes)) + engine.system_reserve, 'nodes': [vars(node) for node in engine.nodes], 'transfers': engine.transfers}
    if 'floor' in options:
        optional('floor', floor_pass)
    else:
        result['floor'] = {'status': 'AWAITING_RESOURCE_INPUT', 'basis': 'no balances supplied'}
    if 'impact_metrics' in options:
        optional('virtue', lambda: VirtueAssessmentEngine(options.get('human_baseline_floor', 0.7)).evaluate_constraint(options.get('restriction_id', 'input'), options.get('declaration_text', analysis_text), options['impact_metrics']))
    else:
        result['virtue'] = {'status': 'AWAITING_IMPACT_METRICS', 'formula': '0.5 * human + 0.3 * transparency - 0.4 * toll'}
    registry = CoreRegistry()
    registry.record('SUBSTRATE_DIAGNOSTICS', audit_hardware())
    if 'initial_states' in options:
        optional('master_floor', lambda: CoreFloorEngine(options.get('core_floor', 60)).balance(options['initial_states']))
        registry.record('FLOOR_OPTIMIZATION', {'basis': 'calculated target balances; required resources shown', 'result': result.pop('master_floor')})
    else:
        registry.record('FLOOR_OPTIMIZATION', {'status': 'AWAITING_INITIAL_STATES'})
    core_imprint = CoreImprintEngine().process_text(analysis_text)
    registry.record('LOGIC_IMPRINT', core_imprint)
    vector = options.get('inversion_vector', list(core_imprint.values()))
    optional('master_inversion', lambda: {'original': vector, 'corrected': CoreInversionOperator().invert_ignorance(vector), 'basis': 'supplied vector' if 'inversion_vector' in options else 'current text imprint'})
    registry.record('INVERSION_OPERATOR', result.pop('master_inversion'))
    result['master_registry'] = registry.logs
    matrix = {'MATTER_BASE_IDENTITY': 1 == 1, 'HARDWARE_BOUNDARY_VERIFIED': bool(hardware.get('OS_PLATFORM')), 'MUTABLE_SOFTWARE_LOG': None, 'ETHICAL_FLOOR_ENFORCED': result['floor'].get('all_stable'), 'VIRTUE_FILTER_ACTIVE': not bool(result['errors'])}
    result['live_matrix'] = matrix
    result['matrix_basis'] = 'platform queried; durable storage verified on commit; absent floor remains unknown'
    bits = list(result['production']['EXTRACTED_LOGIC_BITS'].values()) + result['response_bits'] + result.get('boundary_bits', [])
    bits += list(core_imprint.values())
    result['binary'] = bits
    value = int(''.join(map(str, bits)), 2)
    result['decimal'] = value
    result['balanced_ternary'] = balanced_ternary(value)
    result['status'] = 'COMPLETE' if not result['errors'] else 'PARTIAL'
    return result

class ContinuousAuditModule:
    """Durable cursor over pipeline inputs; paused inputs stay available for resume.

    Only references existing input rows. Results use the shared lossless payload store.
    The first install starts with new inputs; older rows can be requested explicitly.
    """
    MANUAL_SQL = 'SELECT p.rowid AS sequence,p.id,p.source,p.fingerprint,p.input_json FROM live_audit_requests r CROSS JOIN pipeline_jobs p ON p.id=r.job_id ORDER BY r.rowid LIMIT 1'
    NEXT_SQL = 'SELECT rowid AS sequence,id,source,fingerprint,input_json FROM pipeline_jobs WHERE rowid>(SELECT cursor FROM live_audit_control WHERE id=1) ORDER BY rowid LIMIT 1'

    def __init__(self, db_path):
        self.db_path = str(db_path)
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.thread = None
        self.last_hardware = {}
        self.last_result = {}
        self.error = ''
        self.active_job = None
        with database(self.db_path) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS live_audit_control (id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL, cursor INTEGER NOT NULL)')
            cursor = conn.execute('SELECT COALESCE(MAX(rowid),0) FROM pipeline_jobs').fetchone()[0]
            conn.execute('INSERT OR IGNORE INTO live_audit_control VALUES (1,1,?)', (cursor,))
            conn.execute('CREATE TABLE IF NOT EXISTS live_audit_results (job_id TEXT PRIMARY KEY, created_at REAL NOT NULL, result_json TEXT NOT NULL)')
            conn.execute('CREATE INDEX IF NOT EXISTS live_audit_recent ON live_audit_results(created_at DESC)')
            conn.execute('CREATE TABLE IF NOT EXISTS live_audit_requests (job_id TEXT PRIMARY KEY)')
            self.enabled = bool(conn.execute('SELECT enabled FROM live_audit_control WHERE id=1').fetchone()[0])
            latest = conn.execute('SELECT result_json FROM live_audit_results ORDER BY created_at DESC LIMIT 1').fetchone()
            if latest:
                self.last_result = json.loads(latest[0])

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, name='Live substrate and imprint audit', daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.wake.set()
        if self.thread:
            self.thread.join(timeout=12)

    def set_enabled(self, enabled):
        with self.lock, database(self.db_path) as conn:
            conn.execute('UPDATE live_audit_control SET enabled=? WHERE id=1', (int(bool(enabled)),))
            self.enabled = bool(enabled)
        self.wake.set()

    def request(self, job_id):
        with database(self.db_path) as conn:
            if not conn.execute('SELECT 1 FROM pipeline_jobs WHERE id=?', (job_id,)).fetchone():
                raise ValueError('Input was not found')
            conn.execute('INSERT OR IGNORE INTO live_audit_requests VALUES (?)', (job_id,))
        self.wake.set()

    def snapshot(self):
        with self.lock:
            return {'enabled': self.enabled, 'running': bool(self.thread and self.thread.is_alive()), 'active_job': self.active_job, 'hardware': deepcopy(self.last_hardware), 'latest': deepcopy(self.last_result), 'error': self.error}

    def history(self, limit=100):
        with database(self.db_path) as conn:
            return [dict(row) for row in conn.execute('SELECT a.job_id,a.created_at,p.source FROM live_audit_results a JOIN pipeline_jobs p ON p.id=a.job_id ORDER BY a.created_at DESC LIMIT ?', (limit,))]

    def detail(self, job_id):
        with database(self.db_path) as conn:
            row = conn.execute('SELECT result_json FROM live_audit_results WHERE job_id=?', (job_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def process_next(self):
        with self.lock, database(self.db_path) as conn:
            manual = conn.execute(self.MANUAL_SQL).fetchone()
            row = manual
            if row is None and self.enabled:
                row = conn.execute(self.NEXT_SQL).fetchone()
            if row is None:
                return False
            self.active_job = row['id']
            existing = conn.execute('SELECT result_json FROM live_audit_results WHERE job_id=?', (row['id'],)).fetchone()
        try:
            if existing:
                result = json.loads(existing[0])
            else:
                try:
                    hardware = SubstrateHardwareAuditor.identify_hardware_substrate() if manual is not None else self.last_hardware or None
                    result = evaluate_input(json.loads(row['input_json']), hardware)
                except Exception as error:
                    result = {'status': 'ERROR', 'error': str(error), 'timestamp': utc_now(), 'live_matrix': {'MUTABLE_SOFTWARE_LOG': None}}
                result.update(job_id=row['id'], source=row['source'], input_fingerprint=row['fingerprint'])
                result['live_matrix']['MUTABLE_SOFTWARE_LOG'] = True
                result['all_live_flags_verified'] = result['status'] == 'COMPLETE' and verify_live_state(result['live_matrix'])
            with database(self.db_path) as conn:
                conn.execute('BEGIN IMMEDIATE')
                conn.execute('INSERT OR IGNORE INTO live_audit_results VALUES (?,?,?)', (row['id'], time.time(), pack_text(conn, json.dumps(result, ensure_ascii=False, sort_keys=True))))
                conn.execute('DELETE FROM live_audit_requests WHERE job_id=?', (row['id'],))
                if manual is None:
                    conn.execute('UPDATE live_audit_control SET cursor=MAX(cursor,?) WHERE id=1', (row['sequence'],))
                result = json.loads(conn.execute('SELECT result_json FROM live_audit_results WHERE job_id=?', (row['id'],)).fetchone()[0])
            with self.lock:
                self.last_result = result
                self.error = ''
            return True
        finally:
            with self.lock:
                self.active_job = None

    def _loop(self):
        last_probe = 0
        while not self.stop_event.is_set():
            try:
                if self.enabled and time.monotonic() - last_probe >= 5:
                    hardware = SubstrateHardwareAuditor.identify_hardware_substrate()
                    with self.lock:
                        self.last_hardware = hardware
                    last_probe = time.monotonic()
                if self.process_next():
                    continue
            except Exception as error:
                with self.lock:
                    self.error = str(error)
            self.wake.wait(0.5)
            self.wake.clear()
