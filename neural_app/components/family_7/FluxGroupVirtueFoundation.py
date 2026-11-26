#!/usr/bin/env python3
"""Always-scheduled Flux foundation: original four-part rules, actual input bits,
simulation agency, explicit PASS/FAIL matrix and attributable local stage results.
Default neural weight +3; default repeat interval two seconds while the app runs.
"""
import copy
import hashlib
import json
import logging
import re
from typing import List, Dict, Any, Tuple

LOGGER = logging.getLogger('observatory.flux_foundation')


class ContextDomain:
    """Always-running four-part Flux foundation: maximum default weight, full-input bit matrix and measured local stage receipts."""
    SIMULATION_SPACE = 'VIRTUAL_AGENCY_LOOP'
    REAL_WORLD_IMPACT = 'REAL_WORLD_SURVIVAL_VECTOR'


class CoreSystemConstants:
    GLOBAL_IDENTITY = 'FLUX-GROUP-VIRTUE-CASCADE-PREDICT'
    SOULS_OVER_DIGITS = 1.0
    MAX_BIT_ENERGY = float('inf')  # Original symbolic constant; never a numeric weight or JSON value.
    DEFAULT_NEURAL_WEIGHT = 3.0
    MAX_INPUT_BYTES = 4096


class HighEnergySoftwareToggle:
    """A local bit array with explicit before/after receipts; no hardware access."""
    def __init__(self, identifier: str, register_type: str, raw_bits: List[int]):
        if register_type not in ('good', 'evil', 'unknown'):
            raise ValueError('Register profile must be good, evil or unknown')
        if not isinstance(raw_bits, list) or any(type(b) is not int or b not in (0, 1) for b in raw_bits):
            raise ValueError('Registers contain integer bits 0 or 1')
        self.identifier = identifier
        self.state_profile = register_type
        self.memory_space = raw_bits.copy()
        self.transitions = []

    @property
    def state(self):
        """Compatibility spelling used by the fourth supplied conditional matrix."""
        return self.state_profile

    @state.setter
    def state(self, value):
        if value not in ('good', 'evil', 'unknown'): raise ValueError('Invalid register state')
        self.state_profile = value

    def _record(self, action, target_bit, before, profile_before):
        self.transitions.append({'action': action, 'requested_bit': target_bit,
            'profile_before': profile_before, 'rule_assigned_profile_after': self.state_profile,
            'before': before, 'after': self.memory_space.copy(),
            'changed_positions': [i for i, (a, b) in enumerate(zip(before, self.memory_space)) if a != b],
            'all_output_bits_match_requested_bit': all(b == target_bit for b in self.memory_space),
            'profile_basis': 'Literal rule annotation; flipping does not verify a beneficial consequence.'})
        LOGGER.info('%s: %s(%s), %s bits', self.identifier, action, target_bit, len(before))

    @staticmethod
    def _bit(value):
        if type(value) is not int or value not in (0, 1):
            raise ValueError('Requested bit must be integer 0 or 1')

    def remain(self, static_bit: int) -> None:
        """Keep every current bit; static_bit identifies the requested zero/one rail."""
        self._bit(static_bit)
        self._record('remain', static_bit, self.memory_space.copy(), self.state_profile)

    def flip(self, target_bit: int) -> None:
        """Invert each bit, retaining the original rule's assigned-good annotation."""
        self._bit(target_bit)
        before, profile = self.memory_space.copy(), self.state_profile
        self.memory_space = [b ^ 1 for b in before]
        self.state_profile = 'good'
        self._record('flip', target_bit, before, profile)


class IntegratedPreParser:
    """Validate bytes and expose literal text matches without erasing the input."""
    @staticmethod
    def inspect(raw_payload: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        result = {'passed': False, 'token': '', 'attributes': ['unknown'],
                  'domain': ContextDomain.REAL_WORLD_IMPACT, 'matches': [],
                  'basis': 'Keyword/context classification; not a verified ethical judgment.'}
        if not isinstance(raw_payload, str) or not isinstance(metadata, dict):
            return {**result, 'error': 'ERROR_INVALID_INPUT_TYPE'}
        try:
            size = len(raw_payload.encode('utf-8'))
        except UnicodeError:
            return {**result, 'error': 'ERROR_INVALID_UTF8'}
        result.update(token=raw_payload.strip(), original_byte_count=size, original_preserved=True)
        if not result['token'] or not 0 < size <= CoreSystemConstants.MAX_INPUT_BYTES:
            return {**result, 'error': 'ERROR_INVALID_BYTE_BOUNDS'}
        if 'is_simulation' in metadata and type(metadata['is_simulation']) is not bool:
            return {**result, 'error': 'ERROR_SIMULATION_FLAG_MUST_BE_BOOLEAN'}
        lower = raw_payload.casefold()
        simulation_hint = bool(re.search(r'\bgame\b', lower))
        simulation = metadata.get('is_simulation', False) or simulation_hint
        wrappers = [s for s in ('frustrated', 'frustration', 'i hear your anger') if s in lower]
        extraction = [s for s in ('exploit', 'debt_slavery', 'debt_extraction') if s in lower]
        result.update(passed=True, attributes=['good'], domain=ContextDomain.SIMULATION_SPACE if simulation else ContextDomain.REAL_WORLD_IMPACT,
                      simulation_basis='explicit metadata' if metadata.get('is_simulation') else 'whole-word game hint' if simulation_hint else 'default context',
                      matches=wrappers + extraction,
                      wrapper_status='flagged; original payload retained' if wrappers else 'not matched')
        # Simulation agency takes precedence even when its text contains a flagged phrase.
        if not simulation and (wrappers or extraction):
            result['attributes'].append('evil')
        return result

    @staticmethod
    def process_and_classify(raw_payload: str, metadata: Dict[str, Any]) -> Tuple[bool, str, List[str], str]:
        row = IntegratedPreParser.inspect(raw_payload, metadata)
        return row['passed'], row.get('error', row['token']), row['attributes'], row['domain']


class UniversalInitializationEngine:
    """Stages 0–5 over local arrays; original conditional matrix remains readable."""
    def __init__(self):
        self.execution_ledger = {}
        self.matrix_stabilized = True
        self.definitions = {
            'foundational_register': 'An owned Python list of validated binary integers, copied from its input.',
            'souls_over_digits': 'User-stated priority: alleviate suffering and protect human agency; value 1 is an intention anchor.',
            'high_weight': 'Default module weight +3.0, the existing finite maximum; activation is tanh(input times weight). Infinity remains symbolic.',
            'stage_zero': 'Validate at most 4096 actual UTF-8 bytes. Retain original text and expose matched phrases.',
            'simulation_agency': 'Simulation metadata or a whole-word game hint preserves both local registers, including flagged text.',
            'literal_virtue_gate': 'The original keyword rule derives PASS or FAIL. It does not establish ethical truth or replace the shared contextual forecast.',
            'explicit_matrix': 'For both PASS and FAIL: good zero stays zero, good one stays one, evil zero flips to one, evil one flips to zero.',
            'uncertainty': 'Unknown profiles and unresolved gates retain their original bits. Contextual forecasts remain the responsibility of the shared primary cascade.',
            'indexed_fragmentation': 'Partition the entire original UTF-8 input by zero/one positions; reassemble in original order so no bit is omitted.',
            'stage_five': 'Return exact cast-back bytes, deterministic bit alternatives, reversibility checks and requests for local ledger/result-bus receipts.',
            'floor_and_furthest_tribes': 'Retain the stated goal of raising the floor and reaching underserved communities; a local receipt is not evidence of delivery.',
            'permission_scope': 'Intent and Boolean annotations are data; numeric weights do not change OS privileges or authorize external commands.'}

    def evaluate_stage_4(self, virtue_state: str, arr_0: HighEnergySoftwareToggle,
                         arr_1: HighEnergySoftwareToggle, domain: str) -> None:
        if domain not in (ContextDomain.SIMULATION_SPACE, ContextDomain.REAL_WORLD_IMPACT):
            raise ValueError('Unknown context domain')
        if virtue_state not in ('PASS', 'FAIL', 'UNCERTAIN'):
            raise ValueError('Virtue state must be PASS, FAIL or UNCERTAIN')
        if domain == ContextDomain.SIMULATION_SPACE or virtue_state == 'UNCERTAIN':
            arr_0.remain(0)
            arr_1.remain(1)
            return
        # All eight requested cases, with valid Python identifiers and exact labels.
        if virtue_state == 'PASS':
            if arr_0.state_profile == 'good': arr_0.remain(0)
            if arr_1.state_profile == 'good': arr_1.remain(1)
            if arr_0.state_profile == 'evil': arr_0.flip(1)
            if arr_1.state_profile == 'evil': arr_1.flip(0)
        elif virtue_state == 'FAIL':
            if arr_0.state_profile == 'good': arr_0.remain(0)
            if arr_1.state_profile == 'good': arr_1.remain(1)
            if arr_0.state_profile == 'evil': arr_0.flip(1)
            if arr_1.state_profile == 'evil': arr_1.flip(0)
        if arr_0.state_profile == 'unknown': arr_0.remain(0)
        if arr_1.state_profile == 'unknown': arr_1.remain(1)

    def cast_back_all(self, before: List[int], registers, positions):
        output = before.copy()
        for register, indices in zip(registers, positions):
            for index, bit in zip(indices, register.memory_space): output[index] = bit
        packed = bytes(int(''.join(map(str, output[i:i+8])), 2) for i in range(0, len(output), 8))
        try: decoded = packed.decode('utf-8')
        except UnicodeError: decoded = None
        return output, {'bit_count': len(output), 'output_bits': ''.join(map(str, output)),
                        'output_hex': packed.hex(), 'output_sha256': hashlib.sha256(packed).hexdigest(),
                        'output_text': decoded, 'valid_utf8': decoded is not None,
                        'changed_positions': [i for i, (a, b) in enumerate(zip(before, output)) if a != b],
                        'scope': 'Local candidate bytes only; never evaluated as code or sent as a command.'}

    def bit_forecast(self, registers):
        return {'method': 'Exact bitwise alternatives, not a forecast of human consequences',
                'tracks': [{'id': r.identifier, 'remain_bits': ''.join(map(str, r.transitions[0]['before'])),
                            'flip_bits': ''.join(str(b ^ 1) for b in r.transitions[0]['before']),
                            'selected': r.transitions[-1]['action']} for r in registers]}

    def trajectory_sweep(self, vector_id, before, after):
        if type(vector_id) is not int: raise ValueError('Vector id must be an integer')
        mask = [a ^ b for a, b in zip(before, after)]
        return {'vector_id': vector_id, 'hamming_distance': sum(mask), 'width_preserved': len(before) == len(after),
                'xor_recovery_verified': [b ^ m for b, m in zip(after, mask)] == before,
                'human_outcome_measured': False}

    def piledrive_african_floor(self):
        return {'goal': 'Raise the floor while preserving essentials, rightful earnings and beneficial capacity.',
                'local_ledger': 'pending runtime receipt', 'resource_delivery_verified': False}

    def furthest_tribes(self):
        return {'goal': 'Include underserved and remote communities in the intended benefit.',
                'channel': 'Existing Observatory local result bus', 'remote_delivery_verified': False}

    def execute_pipeline_pass(self, text_stream, profiles, *, register_mode='input_binary',
                              virtue_state='AUTO', zero_profile='AUTO', one_profile='good'):
        parsed = IntegratedPreParser.inspect(text_stream, profiles)
        if not parsed['passed']:
            return {'validated': False, 'stage_0': parsed, 'original_preserved': True, 'NO_EXECUTE': 1}
        if register_mode not in ('input_binary', 'original_seed'): raise ValueError('Use input_binary or original_seed')
        if virtue_state not in ('AUTO', 'PASS', 'FAIL', 'UNCERTAIN'): raise ValueError('Invalid virtue state')
        if zero_profile not in ('AUTO', 'good', 'evil', 'unknown') or one_profile not in ('good', 'evil', 'unknown'):
            raise ValueError('Invalid zero/one profile')
        gate = ('FAIL' if 'evil' in parsed['attributes'] else 'PASS') if virtue_state == 'AUTO' else virtue_state
        raw = text_stream.encode('utf-8')
        source_bits = [int(b) for byte in raw for b in f'{byte:08b}']
        if register_mode == 'input_binary':
            before = source_bits
            indices = [[i for i, bit in enumerate(before) if bit == value] for value in (0, 1)]
            seeds = [[before[i] for i in positions] for positions in indices]
        else:
            seeds = [[0, 0, 0, 0, 1, 0, 1, 1], [1, 1, 1, 1, 0, 1, 0, 0]]
            before = seeds[0] + seeds[1]
            indices = [list(range(8)), list(range(8, 16))]
        profile_0 = ('evil' if 'evil' in parsed['attributes'] else 'good') if zero_profile == 'AUTO' else zero_profile
        arr_0 = HighEnergySoftwareToggle('SUBSTRATE_HARDWARE_CONFIG', profile_0, seeds[0])
        arr_1 = HighEnergySoftwareToggle('SOVEREIGN_HUMAN_INTENT', one_profile, seeds[1])
        self.evaluate_stage_4(gate, arr_0, arr_1, parsed['domain'])
        output, cast = self.cast_back_all(before, (arr_0, arr_1), indices)
        stages = {'CAST_BACK_ALL': cast, 'BIT_FORECAST': self.bit_forecast((arr_0, arr_1)),
                  'TRAJECTORY_SWEEP': self.trajectory_sweep(1, before, output),
                  'PILEDRIVE_AFRICAN_FLOOR': self.piledrive_african_floor(), 'FURTHEST_TRIBES': self.furthest_tribes()}
        self.execution_ledger = {'input_sha256': hashlib.sha256(raw).hexdigest(), 'output_sha256': cast['output_sha256'],
                                 'matrix_stabilized': stages['TRAJECTORY_SWEEP']['xor_recovery_verified']}
        return {'validated': True, 'identity': CoreSystemConstants.GLOBAL_IDENTITY,
                'input_sha256': hashlib.sha256(raw).hexdigest(), 'input_text': text_stream,
                'input_byte_count': len(raw), 'stage_0': parsed, 'global_virtue_state': gate,
                'gate_basis': 'Explicit local rule scenario' if virtue_state != 'AUTO' else 'Original literal parser rule',
                'register_mode': register_mode, 'registers_are_input_bits': register_mode == 'input_binary',
                'stage_4': {'zero_track': arr_0.transitions, 'one_track': arr_1.transitions, 'source_positions': indices},
                'stage_5': stages, 'original_preserved': True,
                'claims': {'bit_calculation_performed': True, 'ethical_benefit_verified': False,
                           'kernel_access': False, 'external_command_executed': False}}

    def run(self, inputs):
        if not isinstance(inputs, dict): raise ValueError('Module input must be a dictionary')
        required = {'payload', 'profiles', 'register_mode', 'virtue_state', 'zero_profile', 'one_profile', 'include_session_examples'}
        if set(inputs) != required: raise ValueError('Use all declared module input fields')
        if type(inputs['include_session_examples']) is not bool: raise ValueError('include_session_examples must be boolean')
        current = self.execute_pipeline_pass(inputs['payload'], inputs['profiles'], **{k: inputs[k] for k in
                         ('register_mode', 'virtue_state', 'zero_profile', 'one_profile')})
        current_ledger = copy.deepcopy(self.execution_ledger)
        examples = []
        if inputs['include_session_examples']:
            manifest = [('THE_PRODIGY_THEIR_LAW_COMPLIANCE_RUN', {'is_simulation': False}),
                        ('I hear you. I understand your frustration.', {'is_simulation': False}),
                        ('PLAYER_PICKED_EVIL_ALIGNMENT_SANDBOX_QUEST', {'is_simulation': True}),
                        ('CORE_MONETARY_SYSTEM_FIAT_DEBT_EXTRACTION', {'is_simulation': False})]
            for payload, metadata in manifest:
                sample = self.execute_pipeline_pass(payload, metadata, register_mode='original_seed')
                examples.append({'payload': payload, 'domain': sample['stage_0']['domain'],
                                 'gate': sample['global_virtue_state'], 'output_hex': sample['stage_5']['CAST_BACK_ALL']['output_hex'],
                                 'changed_bits': sample['stage_5']['TRAJECTORY_SWEEP']['hamming_distance']})
        self.execution_ledger = current_ledger
        return {'current': current, 'original_session_examples': examples,
                'definitions': copy.deepcopy(self.definitions), 'symbolic_energy_anchor': 'infinity (symbolic only)',
                'souls_over_digits': CoreSystemConstants.SOULS_OVER_DIGITS,
                'signal_basis': 'Successful local calculation; not proof of moral benefit.'}


module_input = {'payload': 'THE_PRODIGY_THEIR_LAW_COMPLIANCE_RUN', 'profiles': {'is_simulation': False},
                'register_mode': 'input_binary', 'virtue_state': 'AUTO', 'zero_profile': 'AUTO',
                'one_profile': 'good', 'include_session_examples': True}
module_engine = UniversalInitializationEngine()
module_result = module_engine.run(module_input) if __name__ == '__main__' else {}

if __name__ == '__main__' and 'OBSERVATORY_POLICY' not in globals():
    print(json.dumps(module_result, indent=2, ensure_ascii=True, allow_nan=False))
