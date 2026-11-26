"""Whole-input counterfactual search shared by all predictive bit modules.

The oracle assesses complete candidate data, never the moral worth of a bit.
No candidate is executed. Predictions and observed outcomes remain distinct.
"""
import hashlib
import math
from consequence_policy import prediction_gate

NAME = 'arrayFLUX-GROUP-VIRTUE CASCADE-PREDICT'
CONTRACT = ('Assess the whole input/process first using the overall neural model and contextual model analyses; '
            'then predict remain/flip alternatives in that same whole context, divide unresolved groups down to '
            'single bits, and reassess the combined result. Unknown means preserve and review. Forced-choice '
            'comparison is a labelled trial, not evidence or permission to execute a process. '
            'Compare benefit, harm, inaction, affected people and alternatives; raise the floor while '
            'preserving rightful earnings. Allow beneficial local candidates, deny harmful ones, review unknowns. '
            'Moral assessment never creates access permission.')


def digest(bits):
    return hashlib.sha256(bits.encode('ascii')).hexdigest()


def conditional_bit(bit, highest_virtue=None, classification='unknown'):
    """Compatibility table for an explicitly classified bit; not a predictor."""
    if type(bit) is not int or bit not in (0, 1):raise ValueError('Use a binary bit')
    if highest_virtue is not None and type(highest_virtue) is not bool:raise ValueError('Virtue pass must be boolean or unknown')
    if classification == 'uncertain':classification = 'unknown'
    if classification not in ('good', 'evil', 'unknown'):raise ValueError('Unknown classification')
    return 1-bit if classification == 'evil' else bit


def decision(remain, flip, uncertain=True):
    """Prefer an acceptable unchanged whole; only choose an acceptable alternative.

    In the forced trial, available comparative scores break uncertainty. Equal or
    absent scores deterministically keep the input, explicitly labelled forced.
    """
    gates = {'remain':prediction_gate(remain), 'flip':prediction_gate(flip)}
    choice = _choose(remain, flip, gates, uncertain)
    return {**choice, 'consequence_gates':gates}


def _choose(remain, flip, gates, uncertain):
    r, f = gates['remain']['candidate_classification'], gates['flip']['candidate_classification']
    blocked_flip = gates['flip']['verdict']=='deny'
    blocked_remain = gates['remain']['verdict']=='deny'
    if r == 'good' and not blocked_remain:return {'action':'remain', 'resolved':True, 'basis':'Whole remain candidate predicted good'}
    if f == 'good' and not blocked_flip:return {'action':'flip', 'resolved':True, 'basis':'Whole flipped candidate predicted good'}
    if blocked_flip and blocked_remain:return {'action':'uncertain','resolved':False,'basis':'Both candidates blocked; known harmful outcomes are never selected'}
    if uncertain:return {'action':'uncertain', 'resolved':False, 'basis':'Neither candidate has an acceptable supported prediction'}
    def score(item):
        value = item.get('score')
        return float(value) if type(value) in (float, int) and math.isfinite(value) else None
    rs, fs = score(remain), score(flip)
    choose = not blocked_flip and fs is not None and rs is not None and fs > rs
    if not choose and blocked_remain:return {'action':'uncertain','resolved':False,'basis':'No acceptable forced alternative; harmful remain candidate is not selected'}
    return {'action':'flip' if choose else 'remain', 'resolved':False, 'forced':True,
            'basis':'Forced comparison of model scores; absent/equal scores keep input. This is not a resolved classification.'}


def new_state(bits, initial, uncertain=True):
    if not isinstance(bits, str) or not 1 <= len(bits) <= 4096 or set(bits)-{'0','1'}:raise ValueError('Use 1–4,096 bits')
    return {'name':NAME, 'contract':CONTRACT, 'input_bits':bits, 'output_bits':bits,
            'whole_assessment':initial, 'current_assessment':initial, 'uncertain_condition':uncertain,
            'pending':[[0,len(bits)]], 'trace':[], 'leaves':{}, 'status':'running', 'assessments':0}


def advance(state, oracle, budget=16, cancelled=lambda:False):
    """A resumable, bounded depth-first search; every oracle sees the full candidate.

    Resolved groups share one decision across their leaves. They are not falsely
    reported as independently evaluated single-bit predictions.
    """
    used = 0
    while state['pending'] and used < budget and not cancelled():
        start, end = state['pending'].pop()
        before = state['output_bits']
        flipped = before[:start]+before[start:end].translate(str.maketrans('01','10'))+before[end:]
        try:prediction = oracle(flipped, {'start':start, 'end':end, 'operation':'flip', 'whole_before':before})
        except BaseException:
            state['pending'].append([start,end]);raise
        used += 1;state['assessments'] += 1
        choice = decision(state['current_assessment'], prediction, state['uncertain_condition'])
        # A trial still explores unresolved groups before forcing a leaf decision.
        split = not choice['resolved'] and end-start > 1
        row = {'index':len(state['trace']), 'name':NAME, 'start':start, 'end':end, 'group_size':end-start,
               'highest_virtue':state['whole_assessment'].get('virtue_pass'), 'before_sha256':digest(before),
               'remain':state['current_assessment'], 'flip':prediction,
               'action':'divide' if split else choice['action'], 'resolved':choice['resolved'],
               'basis':choice['basis'], 'consequence_gates':choice['consequence_gates'], 'candidate_sha256':digest(flipped)}
        state['trace'].append(row)
        if split:
            middle = (start+end)//2
            state['pending'].extend([[middle,end],[start,middle]])
        else:
            if choice['action'] == 'flip':
                state['output_bits'] = flipped;state['current_assessment'] = prediction
            for index in range(start,end):
                state['leaves'][str(index)] = {'index':index, 'operation':choice['action'], 'resolved':choice['resolved'],
                    'prediction_group':row['index'], 'group_size':end-start, 'independently_predicted':end-start==1,
                    'input':state['input_bits'][index], 'output':state['output_bits'][index], 'forced':bool(choice.get('forced'))}
        row['after_sha256'] = digest(state['output_bits'])
    state['status'] = 'paused' if cancelled() else 'paused_budget' if state['pending'] else 'evaluated'
    return state


def summarize(state):
    leaves = state['leaves'].values()
    return {'name':NAME, 'status':state['status'], 'bit_count':len(state['input_bits']),
            'whole_virtue_pass':state['whole_assessment'].get('virtue_pass'),
            'input_sha256':digest(state['input_bits']), 'output_sha256':digest(state['output_bits']),
            'changed_bits':sum(a!=b for a,b in zip(state['input_bits'],state['output_bits'])),
            'resolved_bits':sum(v['resolved'] for v in leaves),
            'uncertain_bits':sum(not v['resolved'] for v in state['leaves'].values()),
            'forced_trial_bits':sum(bool(v.get('forced')) for v in state['leaves'].values()),
            'unexamined_bits':len(state['input_bits'])-len(state['leaves']),
            'groups_evaluated':len(state['trace']), 'groups_pending':len(state['pending']),
            'prediction_is_observed_outcome':False, 'process_executed':False}


def indexed_arrays(state):
    """Partition by original value without losing order or whole-candidate references."""
    arrays={'array0_FLUX_GROUP_VIRTUE_CASCADE_PREDICT':[], 'array1_FLUX_GROUP_VIRTUE_CASCADE_PREDICT':[]}
    for index,bit in enumerate(state['input_bits']):
        leaf=state['leaves'].get(str(index));trace=state['trace'][leaf['prediction_group']] if leaf else None
        arrays['array'+bit+'_FLUX_GROUP_VIRTUE_CASCADE_PREDICT'].append({
            'index':index,'original':int(bit),'output':int(state['output_bits'][index]),
            'state':trace['remain'].get('classification','unknown') if trace else 'unknown',
            'flip_prediction':trace['flip'].get('classification','unknown') if trace else 'unknown',
            'operation':leaf['operation'] if leaf else 'unexamined','group':leaf['prediction_group'] if leaf else None,
            'scope':'Whole-candidate prediction; inherited group scope is retained'})
    return arrays
