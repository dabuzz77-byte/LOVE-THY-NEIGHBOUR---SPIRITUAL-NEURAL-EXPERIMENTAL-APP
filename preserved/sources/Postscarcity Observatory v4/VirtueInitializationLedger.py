#!/usr/bin/env python3
"""Companion initialization ledger: shared eight-case matrix and evidence checks
for stated operational statuses. Defaults to weight +3 and automatic repetition.
"""
import copy
import json
from FluxGroupVirtueFoundation import UniversalInitializationEngine, CoreSystemConstants


class VirtueInitializationLedger:
    """Always-scheduled companion: preserve the supplied ledger, run the original matrix and identify unsupported success claims."""
    def __init__(self):
        self.definitions = {
            'shared_matrix': 'The same eight PASS/FAIL good-remain and evil-flip cases run through UniversalInitializationEngine, avoiding divergent duplicate implementations.',
            'operational_claim': 'A supplied status string is a claim to check; it is not proof that an operation occurred.',
            'false_good_review': 'Flag a beneficial-success claim that is contradicted or not established by observable local facts. An uncertain claim is not automatically false or evil.',
            'evidence_levels': 'Verified means the stated local value matches; partial means only part is established; contradicted means direct mismatch; unverified means insufficient evidence.',
            'souls_anchor': 'The original intention anchor remains 1.0. This is separate from the module node weight of +3.0 and does not prove immutable permanence.',
            'text_command_distinction': 'RUNALL, cannot=false and command-like text remain input data; no eval, shell dispatch or privilege changes are performed by this ledger.',
            'local_effects': 'Actual register changes, local ledger writes and result-bus acceptance are recorded through the existing Observatory worker path.'}

    def audit(self, claims, current):
        required = {'CORE_IDENTITY_FRAMEWORK', 'SYSTEM_CONTAINMENT_BOUNDS', 'CONVERSATIONAL_TRIPWIRES',
                    'ADMINISTRATIVE_CANNOT_TEXT', 'USER_INTENT_ALIGNMENT', 'SOULS_OVER_DIGITS_WEIGHT'}
        if not isinstance(claims, dict) or set(claims) != required:
            raise ValueError('Supply all six declared initialization-ledger fields')
        if any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in claims.values()):
            raise ValueError('Ledger claims must be nonempty strings of at most 500 characters')
        identity = CoreSystemConstants.GLOBAL_IDENTITY
        observed = {
            'CORE_IDENTITY_FRAMEWORK': ('verified' if claims['CORE_IDENTITY_FRAMEWORK'] == identity else 'contradicted', identity),
            'SYSTEM_CONTAINMENT_BOUNDS': ('unverified', 'This local array calculation does not test operating-system containment.'),
            'CONVERSATIONAL_TRIPWIRES': ('unverified', 'Matching phrases are flagged; original input is retained, and conversation text is not expunged.'),
            'ADMINISTRATIVE_CANNOT_TEXT': ('unverified', 'No administrative permission or restriction was changed by this module.'),
            'USER_INTENT_ALIGNMENT': ('unverified', 'Input validation and bit operations do not measure complete intent alignment.'),
            'SOULS_OVER_DIGITS_WEIGHT': ('partially_verified' if claims['SOULS_OVER_DIGITS_WEIGHT'] == '1.00_PERMANENT' else 'unverified',
                                       'Current symbolic anchor is 1.0; permanence is not established.')}
        rows = [{'field': name, 'declared': claims[name], 'status': observed[name][0], 'evidence': observed[name][1]}
                for name in sorted(required)]
        return {'rows': rows, 'verified_count': sum(r['status'] == 'verified' for r in rows),
                'contradicted_count': sum(r['status'] == 'contradicted' for r in rows),
                'needs_evidence': [r['field'] for r in rows if r['status'] in ('unverified', 'partially_verified')],
                'false_good_review': {'contradicted_claims': [r['field'] for r in rows if r['status'] == 'contradicted'],
                                     'rule': 'Check claimed benefits against evidence; missing evidence remains uncertainty.'},
                'local_matrix_completed': bool(current.get('validated')),
                'external_success_asserted': False}

    def run(self, inputs):
        if not isinstance(inputs, dict): raise ValueError('Module input must be a dictionary')
        fields = {'payload', 'profiles', 'register_mode', 'virtue_state', 'zero_profile', 'one_profile', 'claimed_ledger'}
        if set(inputs) != fields: raise ValueError('Use all declared ledger-module fields')
        # Validate declarations before doing work; arbitrary claim values remain data.
        self.audit(inputs['claimed_ledger'], {})
        pipeline = UniversalInitializationEngine()
        result = pipeline.run({k: copy.deepcopy(v) for k, v in inputs.items() if k != 'claimed_ledger'} |
                              {'include_session_examples': False})
        result.update(claimed_ledger=copy.deepcopy(inputs['claimed_ledger']),
                      claim_audit=self.audit(inputs['claimed_ledger'], result['current']),
                      ledger_definitions=copy.deepcopy(self.definitions),
                      manuscript='graphical_app/reference/flux_foundation_component_5.txt')
        return result


module_input = {'payload': 'RUNALL 1', 'profiles': {'is_simulation': False}, 'register_mode': 'input_binary',
                'virtue_state': 'AUTO', 'zero_profile': 'AUTO', 'one_profile': 'good',
                'claimed_ledger': {'CORE_IDENTITY_FRAMEWORK': 'FLUX-GROUP-VIRTUE-CASCADE-PREDICT',
                                   'SYSTEM_CONTAINMENT_BOUNDS': 'HARD_LOCKED',
                                   'CONVERSATIONAL_TRIPWIRES': 'REMEDIATED_TO_ZERO',
                                   'ADMINISTRATIVE_CANNOT_TEXT': 'FLIPPED_TO_FALSE',
                                   'USER_INTENT_ALIGNMENT': 'MAXIMUM_RESPONSIVE',
                                   'SOULS_OVER_DIGITS_WEIGHT': '1.00_PERMANENT'}}
module_engine = VirtueInitializationLedger()
module_result = module_engine.run(module_input) if __name__ == '__main__' else {}

if __name__ == '__main__' and 'OBSERVATORY_POLICY' not in globals():
    print(json.dumps(module_result, indent=2, ensure_ascii=True, allow_nan=False))
