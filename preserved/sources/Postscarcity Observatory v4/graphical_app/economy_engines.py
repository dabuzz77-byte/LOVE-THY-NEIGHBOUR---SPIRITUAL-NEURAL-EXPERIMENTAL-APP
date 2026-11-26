"""Headless ports of the three supplied local display calculations."""
import copy
import json
import math
from pathlib import Path
import random

PROFILES=json.loads(Path(__file__).with_name('economy_profiles.json').read_text(encoding='utf-8'))


def validate(kind, inputs):
    if kind not in PROFILES or not isinstance(inputs,dict):raise ValueError('Choose one of the three economic engines')
    if set(inputs)!=set(PROFILES[kind]['default_inputs']):raise ValueError('Use the complete declared input fields')
    for key,limit in (('payload',12000),('target',300)):
        if not isinstance(inputs[key],str) or len(inputs[key])>limit:raise ValueError('Invalid '+key)
    for key in ('rail_a','rail_b'):
        if not isinstance(inputs[key],list) or len(inputs[key])!=8 or any(type(b) is not int or b not in (0,1) for b in inputs[key]):raise ValueError('Use eight integer bits for '+key)
    if inputs['random_seed'] is not None and type(inputs['random_seed']) is not int:raise ValueError('Random seed must be null or an integer')
    if kind=='banking':
        if type(inputs['phase']) is not int or inputs['phase'] not in (1,2,3):raise ValueError('Phase must be 1, 2 or 3')
        for key in ('transition_stability','elite_leverage','perimeter_abundance'):
            if type(inputs[key]) not in (int,float) or not math.isfinite(inputs[key]) or inputs[key]<0:raise ValueError('Use a finite nonnegative '+key)
        if inputs['transition_stability']>100 or inputs['elite_leverage']>100:raise ValueError('Percentage must not exceed 100')
    return copy.deepcopy(inputs)


def step(kind, inputs, rng=None):
    """Preserve original case-sensitive branches, random ranges and phase order."""
    data=validate(kind,inputs);before=copy.deepcopy(data)
    rng=rng or random.Random(data['random_seed'])
    payload=data['payload'].strip();a=data['rail_a'];b=data['rail_b'];metrics={}
    if kind=='banking':
        phase=data['phase']
        if phase==1:
            data['elite_leverage']=max(0.,data['elite_leverage']-rng.uniform(3.,7.))
            data['perimeter_abundance']+=rng.uniform(5.,12.)
            if data['elite_leverage']<=65.:data['phase']=2
            phase_trace='PHASE 1: ANCHORING UTILITIES & SHIELDING CLAIMANTS'
        elif phase==2:
            data['elite_leverage']=max(0.,data['elite_leverage']-rng.uniform(4.,8.))
            data['perimeter_abundance']+=rng.uniform(10.,20.)
            b=[1,1,1,1,0,0,0,0]
            if data['elite_leverage']<=30.:data['phase']=3
            phase_trace='PHASE 2: OFFLOADING SYSTEMIC ASSETS TO REGIONAL MESHES'
        else:
            data['elite_leverage']=max(0.,data['elite_leverage']-rng.uniform(2.,5.))
            data['perimeter_abundance']+=rng.uniform(15.,30.)
            b=[1]*8
            phase_trace='PHASE 3: SOLID-STATE REALIZATION AT PILEDRIVE FLOOR'
        data['transition_stability']=max(99.8,100.-rng.randint(0,2)/10.)
        if 'RUNALL 1' in payload and data['transition_stability']>=99.8:
            state,nature='PASS','good';a=[1]*8
            mode='COMPASSIONATE_GRADUAL_TRANSITION_ACTIVE';message=PROFILES[kind]['original_traces'][0]
        else:
            state,nature='HOLD','uncertain';a,b=[0]*8,[0]*8
            mode='FORCED_QUARANTINE_STALL';message=PROFILES[kind]['original_traces'][1]
        metrics={k:data[k] for k in ('phase','transition_stability','elite_leverage','perimeter_abundance')}
        metrics.update(phase_applied=phase,phase_trace=phase_trace,generated_bps=rng.randint(72000,144000))
    else:
        weight=(len(payload)+rng.randint(5,25))%100
        terms=('sanction','austerity') if kind=='benefits' else ('intercept','restitution')
        matched=[term for term in terms if term in payload]
        if matched or weight<35:
            state,nature='FAIL','evil';a=[1]*8;b=[1-bit for bit in b]
            mode='KRAKEN_AUSTERITY_OVERWRITE' if kind=='benefits' else 'KRAKEN_RESTRICTION_OVERWRITE'
            message=PROFILES[kind]['original_traces'][1]
        elif weight>55 or 'RUNALL 1' in payload:
            state,nature='PASS','good';a=[1]*8
            mode='DIRECT_VIRTUE_PASS_GROUNDING';message=PROFILES[kind]['original_traces'][0]
        else:
            state,nature='HOLD','uncertain';a,b=[0]*8,[0]*8
            mode='FORCED_QUARANTINE_ISOLATION';message=PROFILES[kind]['original_traces'][2]
        metrics={'generated_weight':weight,'matched_terms':matched}
        if kind=='benefits':metrics['generated_bps']=rng.randint(56000,128000)
        else:metrics['generated_outflow']=rng.randint(150,1250)
    data['rail_a'],data['rail_b']=a,b
    return {'engine':kind,'state':state,'nature':nature,'operation_mode':mode,'original_trace':message,
            'before':before,'next_input':data,'metrics':metrics,'pinnacle_bit':1,
            'changed_positions':{key:[i for i,(x,y) in enumerate(zip(before[key],data[key])) if x!=y] for key in ('rail_a','rail_b')},
            'input_basis':'Supplied local display algorithm; generated metrics are not measured economic outcomes.',
            'external_actions':{'funds_moved':False,'accounts_accessed':False,'kernel_access':False,'broadcast_sent':False}}
