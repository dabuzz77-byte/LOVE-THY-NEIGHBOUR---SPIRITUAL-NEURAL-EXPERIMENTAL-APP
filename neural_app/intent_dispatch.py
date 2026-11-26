"""Need-first routing proposals; deterministic and bounded exploratory strategies."""
import math,random

def resolve(body):
    tasks=body.get('tasks',[])
    if not isinstance(tasks,list) or len(tasks)>256:raise ValueError('Use up to 256 tasks')
    mode=body.get('mode','roadrunner')
    if mode not in ('roadrunner','taz'):raise ValueError('Use roadrunner or taz')
    seed=body.get('seed',0)
    if type(seed) is not int:raise ValueError('Seed must be an integer')
    ready=[];blocked=[];seen=set()
    for i,t in enumerate(tasks):
        if not isinstance(t,dict):raise ValueError('Each task must be an object')
        ident=t.get('id',str(i))
        if not isinstance(ident,str) or not 1<=len(ident)<=100 or ident in seen:raise ValueError('Use unique short task IDs')
        seen.add(ident);values={}
        for k in ('need','urgency','severity','benefit','confidence','cost'):
            v=t.get(k,0)
            if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1:raise ValueError(k+' must be between 0 and 1')
            values[k]=v
        reasons=[]
        for key in ('life_protecting','authorized','reachable','capable'):
            if t.get(key) is not True:reasons.append(key+' not confirmed')
        checks=t.get('checks',{})
        if not isinstance(checks,dict):raise ValueError('Checks must be an object')
        for key in ('truthful','non_harm','consent','privacy','fairness','repairable','reviewed'):
            if checks.get(key) is not True:reasons.append(key+' check not passed')
        if values['benefit']<=0:reasons.append('No positive benefit declared')
        if values['confidence']<.5:reasons.append('Needs stronger information')
        danger=values['severity']*values['urgency']
        emergency=t.get('emergency') is True
        harm_review=None
        if emergency:
            intervention=t.get('intervention',{})
            if not isinstance(intervention,dict):raise ValueError('Intervention must be an object')
            if intervention.get('kind')!='immediate_safety' or intervention.get('actionable') is not True or intervention.get('minimal') is not True:reasons.append('Emergency requires a minimal actionable immediate-safety intervention')
            review=t.get('harm_review',{})
            if not isinstance(review,dict):raise ValueError('Harm review must be an object')
            if danger<.64:reasons.append('Emergency requires immediate severe danger')
            if review.get('resources_available') is not True:reasons.append('Emergency resources not confirmed')
            for key in ('harm_prevented','harm_caused','confidence'):
                n=review.get(key)
                if type(n) not in (int,float) or not math.isfinite(n) or not 0<=n<=1:reasons.append('Harm review '+key+' missing or invalid')
            if not any('missing or invalid' in r for r in reasons):
                if review['confidence']<.8:reasons.append('Emergency harm review needs confidence of at least 0.8')
                if review['harm_caused']>=review['harm_prevented']*review['confidence']:reasons.append('Projected harm does not justify the proposal')
            harm_review=review
        cost_factor=0 if emergency and not reasons else values['cost']
        score=(danger+values['benefit']*values['confidence'])*(1+values['need'])/(1+cost_factor)
        entry={'id':ident,**values,'danger':danger,'priority':round(score,6),'app_law_checks':checks,'emergency':emergency,'harm_review':harm_review,'cost_factor_used':cost_factor}
        if reasons:blocked.append({**entry,'reasons':reasons})
        else:ready.append(entry)
    # Urgent life-safety tasks precede nonurgent tasks in both strategies.
    # Taz explores within equivalent urgency/need bands, never bypassing eligibility.
    rng=random.Random(seed)
    for r in ready:r['exploration']=rng.random() if mode=='taz' else 0
    if mode=='taz':ready.sort(key=lambda r:(-int(r['danger']>=.64),-int(r['danger']*10),-int(r['priority']*4),-r['exploration'],r['id']))
    else:ready.sort(key=lambda r:(-int(r['danger']>=.64),-r['priority'],r['id']))
    return {'status':'PLAN_READY' if ready else 'AWAITING_ELIGIBLE_TASKS','strategy':mode,'seed':seed,'ordered_tasks':ready,'blocked_tasks':blocked,'equation':'(severity * urgency + benefit * confidence) * (1 + need) / (1 + cost)', 'decision_rule':'All seven app-law checks pass, then confirmed life-protecting purpose, authorization, reachability and capability; prioritize reported urgency and need. Taz explores within priority bands.','meaning':'Routing proposal, not a guarantee of moral correctness or a remote delivery receipt.','emergency_rule':'Only with all ordinary checks passed, immediate severe danger, available resources and a high-confidence harm review showing less caused than prevented harm; waive ordinary cost penalty only. Estimates remain reviewable.','external_deliveries':0,'learning_features':[len(ready)/max(1,len(tasks)),sum(r['need'] for r in ready)/max(1,len(ready))]}
