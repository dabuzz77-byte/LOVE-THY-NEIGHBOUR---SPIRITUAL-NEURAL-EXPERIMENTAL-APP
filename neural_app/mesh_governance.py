"""Inspectable claims/effects review; no inherent moral labels for organisations or people."""
from .gnostic_four import CHECKS,scalar
def assess(body):
    claim=body.get('claimed','good');verified=body.get('effects_reviewed',False)
    if claim not in ('good','evil') or type(verified) is not bool:raise ValueError('Choose a stated label and a review state')
    checks=body.get('checks',{})
    if not isinstance(checks,dict) or set(checks)-set(CHECKS) or any(v is not None and type(v) is not bool for v in checks.values()):raise ValueError('Invalid care checks')
    benefit=scalar(body.get('benefit',0),'benefit');harm=scalar(body.get('harm',0),'harm')
    evidence=body.get('evidence','')
    if not isinstance(evidence,str) or len(evidence)>4000:raise ValueError('Use a short evidence note')
    known=all(type(checks.get(k)) is bool for k in CHECKS)
    if not verified or not evidence.strip() or not known:label='REVIEW_REQUIRED'
    elif benefit>harm and all(checks[k] for k in CHECKS):label='TRUE_GOOD' if claim=='good' else 'FALSE_EVIL'
    elif harm>0 or any(not checks[k] for k in CHECKS):label='FALSE_GOOD' if claim=='good' else 'TRUE_EVIL'
    else:label='REVIEW_REQUIRED'
    counters={
      'truthful':'Disclose the actual behaviour, limits and costs.',
      'non_harm':'Interrupt the harmful mechanism and prioritise protection.',
      'consent':'Restore meaningful, informed choice and a usable exit.',
      'privacy':'Minimise collection; keep private work out of public output.',
      'fairness':'Examine access, worker/user burden and who receives the benefit.',
      'repairable':'Provide rollback, repair and a route to remedy.',
      'reviewed':'Obtain an accountable review with affected people.'}
    return {'classification':label,'claimed':claim,'effects_reviewed':verified,'evidence':evidence,'checks':{k:checks.get(k) for k in CHECKS},'benefit':benefit,'harm':harm,'counters':[counters[k] for k in CHECKS if checks.get(k) is not True],'priority':'Souls over digits: dignity, practical need and protection take precedence over prestige or revenue.','scope':'Assessment of a specified action from supplied evidence; not a verified judgment of an entire corporation, person or soul.'}

def apply_counter(runtime,body):
    import json,time
    from .translation import translate_bits
    result=assess(body);target=body.get('target')
    if target not in ('gemma','gemini','palantir','qwen','llama'):raise ValueError('Choose a configured model route')
    if result['classification'] not in ('TRUE_EVIL','FALSE_GOOD'):raise ValueError('A documented harmful action is required before applying this counter')
    path=runtime.data/'model-route-counters.json';rules=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    before=not rules.get(target,{}).get('paused',False)
    rules[target]={'paused':True,'assessment':result,'at':time.time(),'scope':'Pause this app’s route; no change to a provider account or another device.'}
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(rules),encoding='utf-8');temporary.replace(path)
    if target in runtime.inference_workers().config:runtime.inference_workers().configure(target,{'enabled':False})
    job=runtime.submit('pipeline',{'text':'Reviewed care counter paused an app route; retain local inference.','sections':['super_mesh','gnostic_four','inference'],'section_inputs':{'gnostic_four':{'lesson':'truevirtue'}}})
    return {'assessment':result,'counter':{'target':target,'route_enabled_before':before,'route_enabled_after':False,'state_bits':translate_bits(('1' if before else '0')+'0'),'fallback':'local','learning_job':job['id'],'scope':'Real local route configuration changed. External accounts and devices are not modified.'}}

def restore_counter(runtime,body):
    import json,time
    result=assess(body);target=body.get('target')
    if target not in ('gemma','gemini','palantir','qwen','llama'):raise ValueError('Choose a model route')
    if result['classification'] not in ('TRUE_GOOD','FALSE_EVIL'):raise ValueError('Document the repaired conditions and pass the care checks before restoring this route')
    path=runtime.data/'model-route-counters.json';rules=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    rules[target]={'paused':False,'assessment':result,'at':time.time(),'scope':'Owner-reviewed restoration of this app route; provider authentication still applies.'}
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(rules),encoding='utf-8');temporary.replace(path)
    if target in runtime.inference_workers().config:runtime.inference_workers().configure(target,{'enabled':True})
    return {'assessment':result,'route':target,'paused':False,'scope':'App route restored. A usable external endpoint and credential are still required.'}
