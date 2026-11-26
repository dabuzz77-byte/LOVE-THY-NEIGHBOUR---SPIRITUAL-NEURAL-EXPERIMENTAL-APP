"""CentralBankMeshController with actual signed local settlement requests."""
import hashlib
import hmac
import json
import secrets
import time
import uuid
from .souls_ingress import SoulsOverDigitsCore, number

class CentralBankMeshController:

    def __init__(self, mesh_secret_key, commons_reserve=1000000000.0):
        self.core = SoulsOverDigitsCore(mesh_secret_key, commons_reserve)
        self.core.minimum_vram_gb = 32
        self.core.maximum_latency_ms = 100
        self.secret = mesh_secret_key
        self.used_signatures = set()
        self.mesh_nodes = self.core.node_registry

    @property
    def global_commons_pool(self):
        return self.core.global_root_reserve_ru

    @property
    def quarantine_zone(self):
        return list(self.core.quarantine_zone)

    def onboard_central_bank_node(self, node_id, layer, vram_gb, latency_ms, deception_ratio, initial_ru):
        self.core.register_mesh_node(node_id, layer, vram_gb, latency_ms, deception_ratio, initial_ru)
        self.core.assign_capability_privilege(node_id, 'mesh_settlement')

    def sign_settlement(self, sender_id, receiver_id, amount_ru):
        amount_ru = number(amount_ru, 'Amount')
        payload = json.dumps(dict(sender=sender_id, receiver=receiver_id, amount=amount_ru, exp=int(time.time()) + 300, nonce=uuid.uuid4().hex), sort_keys=True, separators=(',', ':'))
        return payload + '||sig:' + hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()

    def process_mesh_settlement(self, sender_id, receiver_id, amount_ru, auth_sig):
        with self.core.lock:
            try:
                amount_ru = number(amount_ru, 'Amount')
                if amount_ru <= 0:
                    raise ValueError('Amount must be positive')
                raw, sig = auth_sig.rsplit('||sig:', 1)
                if not hmac.compare_digest(sig, hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()):
                    raise ValueError('Invalid signature')
                fields = json.loads(raw)
                if (fields['sender'], fields['receiver'], fields['amount']) != (sender_id, receiver_id, amount_ru):
                    raise ValueError('Request signature scope mismatch')
                if time.time() >= fields['exp'] or fields['nonce'] in self.used_signatures:
                    raise ValueError('Expired or already used request')
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                return {'status': 'BLOCKED', 'reason': str(error)}
            if sender_id not in self.mesh_nodes or receiver_id not in self.mesh_nodes:
                return {'status': 'BLOCKED', 'reason': 'Invalid node mapping signatures.'}
            if sender_id in self.quarantine_zone or receiver_id in self.quarantine_zone:
                return {'status': 'BLOCKED', 'reason': 'Endpoint quarantined'}
            if not self.core._evaluate_node_purity(sender_id):
                self.used_signatures.add(fields['nonce'])
                return {'status': 'EVICTED_AND_REBALANCED', 'target': sender_id}
            token = self.core.issue_capability_token(sender_id, 'mesh_settlement', 1.0)
            result = self.core.route_christmas_tree_stream(sender_id, receiver_id, amount_ru, token, 'mesh_settlement')
            if result['status'] == 'STREAM_SUCCESSFULLY_SANCTIFIED':
                self.used_signatures.add(fields['nonce'])
                result.update(status='SETTLEMENT_MESH_SANCTIFIED', eco_floor_dividend_yield=result['root_stabilizer_dividend'], global_commons_pool_status=result['global_commons_reserve_pool'])
                result['cryptographic_seal'] = result['cryptographic_seal'].replace('369-TREE-SIG:', 'CB-MESH-369:')
            return result

    def _evict_node_to_quarantine(self, node_id, reason):
        self.core._trigger_quarantine_eviction(node_id, reason)
INPUT_TEMPLATE = {'commons_reserve': 1000000000, 'nodes': [dict(node_id='interbank_clearing_shard_01', layer='CANOPY', vram_gb=144, latency_ms=12, deception_ratio=0.1, initial_ru=1000000), dict(node_id='african_child_educational_grid', layer='ROOTS', vram_gb=48, latency_ms=8, deception_ratio=0, initial_ru=5000), dict(node_id='deceptive_leveraged_brokerage_co', layer='CANOPY', vram_gb=24, latency_ms=150, deception_ratio=14.5, initial_ru=500000)], 'settlements': [dict(sender_id='deceptive_leveraged_brokerage_co', receiver_id='interbank_clearing_shard_01', amount_ru=100000), dict(sender_id='interbank_clearing_shard_01', receiver_id='african_child_educational_grid', amount_ru=250000)]}

def execute_bank_mesh(spec, stop_event=None):
    import math
    if not isinstance(spec, dict):
        raise ValueError('central_bank_mesh must be an object')
    core = CentralBankMeshController(secrets.token_bytes(32), spec.get('commons_reserve', 1000000000))
    for node in spec.get('nodes', []):
        core.onboard_central_bank_node(**node)
    before = core.core.snapshot()
    receipts = []
    for supplied in spec.get('settlements', []):
        if stop_event and stop_event.is_set():
            raise InterruptedError()
        action = dict(supplied)
        signature = action.pop('auth_sig', None)
        if signature is None:
            signature = core.sign_settlement(**action)
        receipts.append(core.process_mesh_settlement(**action, auth_sig=signature))
    after = core.core.snapshot()
    return dict(status='COMPLETE', before=before, after=after, receipts=receipts, resource_conserved=math.isclose(before['total_ru'], after['total_ru'], rel_tol=1e-12), basis='Real local HMAC and RU ledger operations; supplied node metrics do not establish remote bank connectivity')
