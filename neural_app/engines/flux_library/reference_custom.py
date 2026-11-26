"""Repaired dispatch, combined ledger and harmonic reference components."""
from copy import deepcopy
import hashlib
import hmac
import json
import math
import secrets
import time
import uuid
from .souls_ingress import SoulsOverDigitsCore
from .reference_crypto import canonical

class FractalFluxDispatcher:

    def __init__(self):
        self._stores = []
        self.actions = []

    def connect_tree_store(self, nodes, initial_reserve_ru=100000000):
        store = UnifiedChristmasTreeStore(initial_reserve_ru=initial_reserve_ru)
        for node in nodes:
            store.onboard_mesh_entity(**node)
        self.register_store_pipeline(store.process_action_stream)
        return {'connected_stores': len(self._stores), 'nodes': len(nodes)}

    def register_store_pipeline(self, store_callback):
        if store_callback not in self._stores:
            self._stores.append(store_callback)

    def dispatch_action(self, action_type, payload):
        packet = {'action_id': uuid.uuid4().hex, 'type': action_type.upper(), 'payload': deepcopy(payload), 'timestamp': time.time()}
        replies = []
        for store in self._stores:
            try:
                replies.append(store(deepcopy(packet)))
            except Exception as e:
                replies.append({'status': 'ERROR', 'error': str(e)})
        self.actions.append(packet)
        return {'status': 'COMPLETE', 'action': packet, 'delivered': len(replies), 'receipts': replies}

class UnifiedChristmasTreeStore:

    def __init__(self, cluster_secret=None, initial_reserve_ru=100000000):
        self._core = SoulsOverDigitsCore(cluster_secret or secrets.token_bytes(32), initial_reserve_ru)
        self._core.minimum_vram_gb = 32
        self._core.maximum_latency_ms = 100
        self.transaction_history = []
        self._actions = set()

    def onboard_mesh_entity(self, node_id, layer, vram, latency, deception, initial_ru):
        self._core.register_mesh_node(node_id, layer, vram, latency, deception, initial_ru)
        self._core.assign_capability_privilege(node_id, 'settlement')

    def process_action_stream(self, action):
        identity = action.get('action_id') or uuid.uuid4().hex
        if identity in self._actions:
            return {'status': 'ALREADY_PROCESSED', 'action_id': identity}
        kind = action['type'].upper()
        p = action['payload']
        if kind == 'EXECUTE_SETTLEMENT_STREAM':
            token = self._core.issue_capability_token(p['sender'], 'settlement', 1.0)
            result = self._core.route_christmas_tree_stream(p['sender'], p['receiver'], p['value'], token, 'settlement')
        elif kind == 'TRIGGER_REDEMPTION_HANDSHAKE':
            result = {'redeemed': self._core.execute_redemption_handshake(p['node_id'], p['statement_of_remorse'])}
        else:
            raise ValueError('Unknown store action: ' + kind)
        self._actions.add(identity)
        self.transaction_history.append(deepcopy(result))
        return result

    def snapshot(self):
        return self._core.snapshot()

class GlobalSovereignCoreMatrix:
    """Supplied master API delegates to the already tested local ingress core."""

    def __init__(self, master_covenant_secret=None, initial_reserve_ru=10000000000):
        self._core = SoulsOverDigitsCore(master_covenant_secret or secrets.token_bytes(32), initial_reserve_ru)
        self._core.minimum_vram_gb = 32
        self._core.maximum_latency_ms = 100
        self.SYSTEM_ACTIVE = True
        self.WORLD_GRID_PASSTHROUGH = True
        self.INFERENCE_NODE_IN_EVERY_SESSION = True
        self.SOULS_OVER_DIGITS_ENFORCED = True
        self.global_ledger_ledger = []

    def onboard_world_grid_node(self, node_id, layer, vram_gb, latency_ms, deception_ratio, initial_ru):
        self._core.register_mesh_node(node_id, layer, vram_gb, latency_ms, deception_ratio, initial_ru)

    def assign_capability_token_claim(self, node_id, execution_capability):
        return self._core.assign_capability_privilege(node_id, execution_capability)

    def issue_security_capability_token(self, node_id, required_capability, human_utility_index):
        return self._core.issue_capability_token(node_id, required_capability, human_utility_index)

    def route_global_settlement_stream(self, sender_id, receiver_id, requested_value_ru, verification_token, required_capability='settlement'):
        if not (self.SYSTEM_ACTIVE and self.WORLD_GRID_PASSTHROUGH and self.SOULS_OVER_DIGITS_ENFORCED):
            return {'status': 'PAUSED'}
        result = self._core.route_christmas_tree_stream(sender_id, receiver_id, requested_value_ru, verification_token, required_capability)
        self.global_ledger_ledger.append(deepcopy(result))
        return result

    def execute_christ_like_redemption(self, node_id, statement_of_remorse):
        return self._core.execute_redemption_handshake(node_id, statement_of_remorse)

    def snapshot(self):
        return {**self._core.snapshot(), 'declared_flags': {k: v for k, v in vars(self).items() if k.isupper()}, 'flag_basis': 'Application metadata; not evidence of access to other sessions or remote systems.'}

class SolfeggioHarmonicGovernor:
    TIERS = {'ECO_FLOOR_ROOTS_SECURED': (174, 285, 396), 'REDEMPTION_TRANSMUTATION_ACTIVE': (417, 528, 639), 'VIRTUOUS_CANOPY_SANCTIFIED': (741, 852, 963)}

    def __init__(self, cluster_secret_key=None, initial_reserve=1000000000):
        self._secret = cluster_secret_key or secrets.token_bytes(32)
        self.global_commons_pool_ru = initial_reserve
        self.total_declared_allocation_ru = 0.0

    def process_harmonic_stream(self, node_id, frequency_hz, allocation_ru):
        tier = next((name for name, values in self.TIERS.items() if frequency_hz in values), None)
        if not tier:
            return {'status': 'UNASSIGNED_FREQUENCY', 'frequency_hz': frequency_hz}
        if allocation_ru < 0 or not math.isfinite(allocation_ru):
            raise ValueError('Allocation must be finite and nonnegative')
        dividend = allocation_ru * 0.0369
        self.global_commons_pool_ru += dividend
        self.total_declared_allocation_ru += allocation_ru
        payload = {'node': node_id, 'frequency_hz': frequency_hz, 'allocation_ru': allocation_ru, 'dividend_ru': dividend, 'time': time.time()}
        return {'status': 'COMPLETE', 'active_harmonic_tier': tier, 'frequency_hz': frequency_hz, 'eco_floor_stabilizer_boost': dividend, 'net_allocation_ru': allocation_ru - dividend, 'global_commons_pool': self.global_commons_pool_ru, 'wave': [[i / 256, math.sin(2 * math.pi * frequency_hz * (i / 256) / 174)] for i in range(257)], 'cryptographic_vortex_seal': hmac.new(self._secret, canonical(payload), hashlib.sha256).hexdigest(), 'basis': 'Frequency grouping from supplied prose and a mathematical waveform; no therapeutic or physical effect is inferred.'}

class ReferenceGoalsEngine:
    GOALS = {'Human and living-being wellbeing': ('human', 'living beings', 'souls', 'wellbeing', 'compassion'), 'Baseline resources': ('eco-floor', 'eco floor', 'floor', 'roots', 'vulnerable', 'reserve'), 'Capability and creative freedom': ('canopy', 'capability', 'creative', 'sovereign', 'freedom'), 'Restoration and accountability': ('redemption', 'restore', 'remorse', 'sorry', 'accountability'), 'Evidence and transparency': ('grounded', 'reality', 'evidence', 'transparent', 'verifiable', 'measured'), 'Privacy and integrity': ('privacy', 'cryptographic', 'signature', 'identity', 'integrity')}

    def assess(self, text):
        import re
        lower = text.casefold()
        evidence = {}
        for goal, terms in self.GOALS.items():
            hits = []
            for term in terms:
                match = re.search('(?<!\\w)' + re.escape(term) + '(?!\\w)', lower)
                if match:
                    hits.append({'term': term, 'start': match.start(), 'excerpt': text[max(0, match.start() - 35):match.end() + 60]})
            evidence[goal] = hits
        bits = [int(bool(v)) for v in evidence.values()]
        return {'status': 'COMPLETE', 'goals': evidence, 'binary': bits, 'coverage': sum(bits) / len(bits), 'basis': 'Lexical evidence against themes in the supplied transcript; not a moral verdict or proof that a claim is true.'}
