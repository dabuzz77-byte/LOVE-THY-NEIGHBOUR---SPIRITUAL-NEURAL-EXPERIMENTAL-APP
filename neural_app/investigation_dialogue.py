"""Evidence-seeking native conversations over explicit deterministic hypotheses."""
import copy,json,re
from fractions import Fraction
from .diagnostic_reasoning import diagnose,token

def amount(value):
    if type(value) not in (int,float,str) or len(str(value))>40:raise ValueError('Test costs must be short nonnegative numbers')
    try:result=Fraction(str(value))
    except (ValueError,ZeroDivisionError):raise ValueError('Test costs must be finite nonnegative numbers') from None
    if not 0<=result<=10**9:raise ValueError('Test costs must be between zero and 10^9')
    return result

def analyse(body):
    if not isinstance(body,dict):raise ValueError('Provide an investigation object with hypotheses and observations')
    report=diagnose(body)
    costs=body.get('probe_costs',{});blocked=body.get('blocked_probes',[]);budget=body.get('max_probe_cost')
    if not isinstance(costs,dict) or len(costs)>64 or not isinstance(blocked,list) or len(blocked)>64 or any(not isinstance(p,str) for p in blocked):raise ValueError('Use a probe-cost object and list of blocked probe names')
    known={p for h in body['hypotheses'] for p in h.get('predictions',{})}|set(body.get('observations',{}))
    if (set(costs)|set(blocked))-known:raise ValueError('Cost and blocked-probe names must refer to known predictions or observations')
    costs={p:amount(v) for p,v in costs.items()};maximum=amount(budget) if budget is not None else None
    ranked=[]
    for row in report['candidate_probes']:
        item=copy.deepcopy(row);cost=costs.get(row['probe']);reason=None
        if row['probe'] in blocked:reason='blocked by supplied test constraints'
        elif maximum is not None and cost is None:reason='cost unknown under supplied budget'
        elif maximum is not None and cost>maximum:reason='exceeds supplied per-test budget'
        item.update(cost=str(cost) if cost is not None else None,eligible=reason is None,exclusion_reason=reason)
        ranked.append(item)
    # Prioritise the strongest guaranteed distinction, then declared lower cost.
    # Unknown cost is never presented as free; no probabilities are invented.
    ranked.sort(key=lambda r:(not r['eligible'],-r['guaranteed_eliminations'],r['cost'] is None,Fraction(r['cost']) if r['cost'] is not None else 0,r['probe']))
    choices=[r for r in ranked if r['eligible'] and r['guaranteed_eliminations']>0]
    report['test_plan']=ranked;report['recommended_probe']=choices[0]['probe'] if choices else None
    report['selection_rule']='Maximise guaranteed eliminations among eligible tests; break ties by lower declared cost. Costs use supplied units. This is not an optimal multi-step policy.'
    report['action_scope']='A suggested observation only. No test, command, device or network operation is executed.'
    return report

def render(report):
    lines=['Compatible or unresolved explanations: '+(', '.join(report['remaining']) or 'none')+'.']
    for h in report['hypotheses']:
        if h['mismatches']:lines.append(h['name']+' conflicts with '+', '.join(h['mismatches'])+'.')
        if h['missing_predictions']:lines.append(h['name']+' has no prediction for '+', '.join(h['missing_predictions'])+'; it remains unresolved on those observations.')
    choice=report['recommended_probe']
    if choice:
        row=next(r for r in report['test_plan'] if r['probe']==choice)
        lines.append('Next useful observation: '+choice+'. Guaranteed eliminations under the supplied model: '+str(row['guaranteed_eliminations'])+'; worst-case survivors: '+str(row['worst_case_remaining'])+'. Declared cost: '+(row['cost'] if row['cost'] is not None else 'unknown')+'.')
        lines += [json.dumps(o['outcome'],ensure_ascii=False)+' would retain '+', '.join(o['hypotheses']+row['unknown_predictions'])+'.' for o in row['outcomes']]
    else:lines.append('No eligible test is guaranteed to distinguish the remaining explanations. Add a distinguishing prediction or revise the test constraints; do not treat a surviving explanation as a proven cause.')
    lines += ['Excluded '+r['probe']+': '+r['exclusion_reason']+'.' for r in report['test_plan'] if not r['eligible']]
    return '\n\n'.join(lines+[report['selection_rule'],report['scope'],report['action_scope']])

def respond(text,state):
    text=text.strip();key=text.casefold().rstrip('?.!');old=state.get('investigation');body=None;history=[]
    if key.startswith('investigate:'):
        body=json.loads(text.split(':',1)[1]);history=[]
    elif old and (state.get('focus_kind')=='investigation' or key=='resume investigation'):
        if key in ('what next','what should we test next','which explanations remain','why','explain that','resume investigation'):
            state['focus_kind']='investigation'
            return {'status':'complete','answer':render(old['report']),'investigation':copy.deepcopy(old['report']),'model_calls':0}
        m=re.fullmatch(r'(observation|correct observation):\s*([^=]{1,120})\s*=\s*(.+)',text,re.I|re.S)
        if not m:return None
        body=copy.deepcopy(old['input']);probe=m[2].strip();value=json.loads(m[3]);token(value)
        known={p for h in body['hypotheses'] for p in h.get('predictions',{})}
        if probe not in known:raise ValueError('This observation has no prediction in the current hypothesis catalogue')
        observed=body.setdefault('observations',{})
        if probe in observed and token(observed[probe])!=token(value) and m[1].casefold()!='correct observation':raise ValueError('An observation already exists; use correct observation: to replace it explicitly')
        history=copy.deepcopy(old['history']);history.append({'probe':probe,'before':copy.deepcopy(observed.get(probe)),'after':value,'correction':m[1].casefold()=='correct observation'})
        observed[probe]=value
    else:return None
    report=analyse(body)
    stored={'input':copy.deepcopy(body),'report':report,'history':history[-32:]}
    if len(json.dumps(stored,allow_nan=False))>100000:raise ValueError('Investigation exceeds its retained-data budget')
    state['investigation']=stored;state['focus_kind']='investigation'
    return {'status':'complete','answer':render(report),'investigation':copy.deepcopy(report),'model_calls':0}
