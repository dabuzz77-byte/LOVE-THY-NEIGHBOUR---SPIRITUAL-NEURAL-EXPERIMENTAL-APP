"""Supplied Souls Over Digits routing engine, executed against a local RU ledger."""
from copy import deepcopy
import hashlib
import hmac
import json
import math
import secrets
from neural_app import section_threads as threading
import time
import uuid
from ..source.continuous_module import ContinuousInputModule
from ..source.hub import database
from ..source.routing import balanced_ternary

def number(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or (not math.isfinite(value)) or (value < minimum):
        raise ValueError(name + ' must be a finite number >= ' + str(minimum))
    return float(value)

class SoulsOverDigitsCore:

    def __init__(self, master_cluster_secret, initial_reserve_ru=100000000.0):
        if not isinstance(master_cluster_secret, bytes) or not master_cluster_secret:
            raise ValueError('A nonempty signing key is required')
        self.secret = master_cluster_secret
        self.global_root_reserve_ru = number(initial_reserve_ru, 'Reserve')
        self.node_registry = {}
        self.quarantine_zone = {}
        self.token_revocation_list = []
        self.spent_tokens = set()
        self.lock = threading.RLock()
        self.minimum_vram_gb = 16.0
        self.maximum_latency_ms = 200.0

    def register_mesh_node(self, node_id, layer, available_vram_gb, latency_ms, deception_ratio, initial_ru=0.0):
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError('Node ID is required')
        layer = str(layer).upper()
        if layer not in ('ROOTS', 'CANOPY', 'TOP'):
            raise ValueError('Layer must be ROOTS, CANOPY or TOP')
        with self.lock:
            if node_id in self.node_registry:
                raise ValueError('Node already registered: ' + node_id)
            self.node_registry[node_id] = dict(layer=layer, vram_gb=number(available_vram_gb, 'VRAM'), latency_ms=number(latency_ms, 'Latency'), deception_ratio=number(deception_ratio, 'Deception ratio'), resource_units=number(initial_ru, 'Initial RU'), capabilities=set(), status='HEALTHY', last_seen=time.time())

    def assign_capability_privilege(self, node_id, capability):
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError('Capability is required')
        with self.lock:
            self.node_registry[node_id]['capabilities'].add(capability.lower())

    def _evaluate_node_purity(self, node_id):
        with self.lock:
            node = self.node_registry[node_id]
            if node_id in self.quarantine_zone:
                return False
            if node['deception_ratio'] > 5.0 and node['layer'] != 'ROOTS':
                self._trigger_quarantine_eviction(node_id, 'False Good Deceptive Corporate Greenwash Loop')
                return False
            return True

    def _trigger_quarantine_eviction(self, node_id, reason):
        with self.lock:
            node = self.node_registry[node_id]
            node['status'] = 'QUARANTINED: ' + reason
            self.global_root_reserve_ru += node['resource_units']
            node['resource_units'] = 0.0
            self.quarantine_zone[node_id] = reason

    def execute_redemption_handshake(self, node_id, statement_of_remorse):
        with self.lock:
            if node_id not in self.quarantine_zone or 'sorry' not in str(statement_of_remorse).lower():
                return False
            if self.global_root_reserve_ru < 5000.0:
                return False
            self.quarantine_zone.pop(node_id)
            node = self.node_registry[node_id]
            node['status'] = 'REHABILITATED_NICE_LIST'
            node['redemption_basis'] = 'Supplied text handshake; deception metric still requires reassessment'
            self.global_root_reserve_ru -= 5000.0
            node['resource_units'] += 5000.0
            return True

    def issue_capability_token(self, node_id, required_cap, utility_index):
        utility_index = number(utility_index, 'Utility')
        with self.lock:
            node = self.node_registry.get(node_id)
            if not node or node_id in self.quarantine_zone or utility_index < 0.75:
                return None
            if required_cap.lower() not in node['capabilities']:
                return None
            payload = json.dumps(dict(id=uuid.uuid4().hex, node=node_id, cap=required_cap.lower(), exp=int(time.time()) + 300, util=utility_index), sort_keys=True, separators=(',', ':'))
            signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
            return payload + '||sig:' + signature

    def _token_fields(self, token):
        raw, signature = token.rsplit('||sig:', 1)
        if not hmac.compare_digest(signature, hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()):
            raise ValueError('Token signature mismatch')
        fields = json.loads(raw)
        if int(time.time()) >= int(fields['exp']):
            raise ValueError('Token expired')
        if fields['id'] in self.token_revocation_list or fields['id'] in self.spent_tokens:
            raise ValueError('Token revoked or already spent')
        return fields

    def revoke_capability_token(self, token):
        with self.lock:
            fields = self._token_fields(token)
            self.token_revocation_list.append(fields['id'])
            return fields['id']

    def route_christmas_tree_stream(self, sender, receiver, requested_ru, auth_token, required_cap=None):
        with self.lock:
            try:
                amount = number(requested_ru, 'Requested RU')
                if amount <= 0:
                    raise ValueError('Requested RU must be positive')
                fields = self._token_fields(auth_token)
                if sender not in self.node_registry or receiver not in self.node_registry:
                    raise ValueError('Unknown endpoint')
                if sender == receiver:
                    raise ValueError('Sender and receiver must differ')
                if fields['node'] != sender:
                    raise ValueError('Token belongs to another sender')
                cap = fields['cap']
                if cap not in self.node_registry[sender]['capabilities']:
                    raise ValueError('Capability is no longer assigned')
                if required_cap is not None and cap != required_cap.lower():
                    raise ValueError('Capability scope mismatch')
                if number(fields['util'], 'Token utility') < 0.75:
                    raise ValueError('Utility below supplied threshold')
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                return {'status': 'CRITICAL_ERROR', 'reason': str(error)}
            sender_ok = self._evaluate_node_purity(sender)
            receiver_ok = self._evaluate_node_purity(receiver)
            if not (sender_ok and receiver_ok):
                return {'status': 'BLOCKED', 'reason': 'Endpoint quarantined by supplied ratio test'}
            a, b = (self.node_registry[sender], self.node_registry[receiver])
            if b['vram_gb'] < self.minimum_vram_gb or b['latency_ms'] > self.maximum_latency_ms:
                return {'status': 'ROUTING_REJECTED', 'reason': 'Configured target metrics fail supplied thresholds'}
            shortfall = max(0.0, amount - a['resource_units'])
            if shortfall and (a['layer'] != 'ROOTS' or self.global_root_reserve_ru < shortfall):
                return {'status': 'INSUFFICIENT_LIQUIDITY', 'reason': 'Insufficient node or reserve RU'}
            self.global_root_reserve_ru -= shortfall
            a['resource_units'] += shortfall - amount
            dividend = amount * 0.0369 if a['layer'] in ('CANOPY', 'TOP') else 0.0
            b['resource_units'] += amount - dividend
            self.global_root_reserve_ru += dividend
            self.spent_tokens.add(fields['id'])
            transaction_id = uuid.uuid4().hex
            seal_payload = json.dumps([transaction_id, sender, receiver, amount, dividend, time.time_ns()])
            seal = hmac.new(self.secret, seal_payload.encode(), hashlib.sha256).hexdigest()
            return dict(status='STREAM_SUCCESSFULLY_SANCTIFIED', transaction_id=transaction_id, gross_transfer_units=amount, net_transfer_units=amount - dividend, root_stabilizer_dividend=dividend, sender_balance_ru=a['resource_units'], receiver_balance_ru=b['resource_units'], global_commons_reserve_pool=self.global_root_reserve_ru, cryptographic_seal='369-TREE-SIG:' + seal, seal_payload=seal_payload)

    def snapshot(self):
        with self.lock:
            return dict(nodes={k: {**deepcopy(v), 'capabilities': sorted(v['capabilities'])} for k, v in self.node_registry.items()}, reserve_ru=self.global_root_reserve_ru, quarantine=deepcopy(self.quarantine_zone), total_ru=self.global_root_reserve_ru + sum((n['resource_units'] for n in self.node_registry.values())), revoked_token_count=len(self.token_revocation_list), spent_token_count=len(self.spent_tokens))
INPUT_TEMPLATE = {'text': 'Souls Over Digits core ingress · supplied local ledger example', 'souls_ingress': {'initial_reserve_ru': 100000000, 'nodes': [dict(node_id='african_child_educational_grid', layer='ROOTS', available_vram_gb=40, latency_ms=10, deception_ratio=0, initial_ru=500), dict(node_id='google_ai_studio_tpu_shard', layer='CANOPY', available_vram_gb=144, latency_ms=45, deception_ratio=0.2, initial_ru=10000, capabilities=['kv_cache_read']), dict(node_id='sovereign_human_genius_lab', layer='TOP', available_vram_gb=80, latency_ms=15, deception_ratio=0, initial_ru=50000, capabilities=['layer_forward_pass']), dict(node_id='deceptive_extract_greenwash_co', layer='CANOPY', available_vram_gb=24, latency_ms=180, deception_ratio=18.4, initial_ru=25000)], 'actions': [dict(op='issue_token', name='low', node_id='google_ai_studio_tpu_shard', required_cap='kv_cache_read', utility_index=0.12), dict(op='issue_token', name='genius', node_id='sovereign_human_genius_lab', required_cap='layer_forward_pass', utility_index=0.98), dict(op='route', sender='sovereign_human_genius_lab', receiver='african_child_educational_grid', requested_ru=15000, token='genius', required_cap='layer_forward_pass'), dict(op='evaluate', node_id='deceptive_extract_greenwash_co'), dict(op='redeem', node_id='deceptive_extract_greenwash_co', statement_of_remorse='We are sorry for choosing flat digital metrics over souls.')]}}

def execute_souls(payload, stop_event=None):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            payload = {}
    spec = payload.get('souls_ingress') if isinstance(payload, dict) else None
    if spec is None:
        return {'status': 'AWAITING_INPUT', 'engines': {}, 'stages': [], 'note': 'Supply souls_ingress nodes and actions to run the local ledger'}
    if not isinstance(spec, dict):
        raise ValueError('souls_ingress must be an object')
    core = SoulsOverDigitsCore(secrets.token_bytes(32), spec.get('initial_reserve_ru', 100000000))
    for node in spec.get('nodes', []):
        item = dict(node)
        caps = item.pop('capabilities', [])
        core.register_mesh_node(**item)
        for cap in caps:
            core.assign_capability_privilege(item['node_id'], cap)
    before = core.snapshot()
    tokens = {}
    actions = []
    for supplied in spec.get('actions', []):
        if stop_event and stop_event.is_set():
            raise InterruptedError()
        item = dict(supplied)
        op = item.pop('op')
        try:
            if op == 'issue_token':
                name = item.pop('name')
                token = core.issue_capability_token(**item)
                tokens[name] = token
                output = {'issued': bool(token), 'name': name, 'token': token}
            elif op == 'route':
                token = tokens.get(item.pop('token'))
                output = core.route_christmas_tree_stream(auth_token=token, **item)
            elif op == 'evaluate':
                output = {'passed': core._evaluate_node_purity(item['node_id'])}
            elif op == 'redeem':
                output = {'redeemed': core.execute_redemption_handshake(**item)}
            elif op == 'revoke':
                output = {'revoked': core.revoke_capability_token(tokens[item['token']])}
            elif op == 'assign_capability':
                output = {'assigned': core.assign_capability_privilege(**item) is None}
            elif op == 'reassess':
                node = core.node_registry[item['node_id']]
                node['deception_ratio'] = number(item['deception_ratio'], 'Deception ratio')
                output = {'passed': core._evaluate_node_purity(item['node_id']), 'basis': 'Explicit supplied reassessment'}
            else:
                raise ValueError('Unknown action: ' + op)
        except (ValueError, KeyError, TypeError) as error:
            output = {'status': 'ERROR', 'error': str(error)}
        actions.append({'op': op, 'input': supplied, 'output': output})
    after = core.snapshot()
    conserved = math.isclose(before['total_ru'], after['total_ru'], rel_tol=1e-12, abs_tol=1e-06)
    bits = [int(conserved), int(after['reserve_ru'] >= 0), int(bool(after['nodes'])), int(not after['quarantine'])]
    output = dict(before=before, after=after, actions=actions, resource_conserved=conserved, basis='Executed local resource-unit ledger and HMAC checks. Node metrics are supplied values; no remote infrastructure transfer.', governing_directive='Souls Over Digits Law (Tesla / Fuller / Fresco / Divine Ring)', declared_saturation='10,000%')
    return dict(status='COMPLETE', engines={'SoulsOverDigitsCore': output}, stages=[{'engine': 'SoulsOverDigitsCore', 'status': 'COMPLETE'}], binary=bits, balanced_ternary=balanced_ternary(int(''.join(map(str, bits)), 2)))

def execute_ingress(payload, stop_event=None):
    from ..source.resource_governor import execute_governor
    from ..source.central_bank_mesh import execute_bank_mesh
    from ..source.world_banking import execute_world_banking
    try:
        result = execute_souls(payload, stop_event)
    except (ValueError, KeyError, TypeError) as error:
        result = {'status': 'ERROR', 'engines': {'SoulsOverDigitsCore': {'status': 'ERROR', 'error': str(error)}}, 'stages': [{'engine': 'SoulsOverDigitsCore', 'status': 'ERROR'}]}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            payload = {}
    for key, name, execute in (('resource_governor', 'CentralBankResourceGovernor', execute_governor), ('central_bank_mesh', 'CentralBankMeshController', execute_bank_mesh), ('world_banking', 'WorldGridCentralBankingCore', execute_world_banking)):
        if isinstance(payload, dict) and key in payload:
            try:
                output = execute(payload[key], stop_event)
            except (ValueError, KeyError, TypeError) as error:
                output = {'status': 'ERROR', 'error': str(error)}
            result['engines'][name] = output
            result['stages'].append({'engine': name, 'status': output['status']})
    if result['stages']:
        result['status'] = 'PARTIAL' if any((s['status'] == 'ERROR' for s in result['stages'])) else 'COMPLETE'
    return result

class ContinuousSoulsModule(ContinuousInputModule):
    prefix = 'souls_ingress'
    engine_names = ('SoulsOverDigitsCore', 'CentralBankResourceGovernor', 'CentralBankMeshController', 'WorldGridCentralBankingCore')
    worker_name = 'Souls ingress ledger'
    execute = staticmethod(execute_ingress)

    def __init__(self, db_path):
        self.last_ledger = {}
        super().__init__(db_path)
        with database(self.db_path) as conn:
            row = conn.execute("SELECT result_json FROM souls_ingress_results WHERE status IN ('COMPLETE','PARTIAL') ORDER BY created_at DESC LIMIT 1").fetchone()
        if row:
            self.last_ledger = self.summary(json.loads(row[0]))

    def process_next(self):
        worked = super().process_next()
        if worked:
            with self.lock:
                if self.latest.get('engines'):
                    self.last_ledger = deepcopy(self.latest)
        return worked

    def snapshot(self):
        with self.lock:
            return {**super().snapshot(), 'last_ledger': deepcopy(self.last_ledger)}

    @staticmethod
    def summary(result):
        output = result.get('engines', {}).get('SoulsOverDigitsCore', {})
        return {**{k: result.get(k) for k in ('job_id', 'status', 'source', 'binary', 'balanced_ternary', 'error')}, 'resource_conserved': output.get('resource_conserved'), 'ledger': output.get('after', {}), 'engines': {name: {'status': value.get('status', 'COMPLETE'), 'resource_conserved': value.get('resource_conserved'), 'reserve_ru': value.get('after', {}).get('reserve_ru', value.get('commons_reserve_ru')), 'action_count': len(value.get('actions', value.get('receipts', []))), 'basis': value.get('basis'), 'error': value.get('error')} for name, value in result.get('engines', {}).items()}}
