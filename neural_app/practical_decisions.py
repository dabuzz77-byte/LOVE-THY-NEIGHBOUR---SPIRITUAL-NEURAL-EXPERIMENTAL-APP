"""Conversational comparison of explicit cost/time evidence, with exact units.

This is a language compiler into a small decision model, not a world-knowledge
generator. Unparsed statements remain visible, and absent ratings stay unknown.
"""
import copy,re
from fractions import Fraction

NUM=r'(\d{1,12}(?:\.\d{1,8})?)'
NAME=r'([\w][\w -]{0,55}?)'
MONEY=r'([£$€])\s*'+NUM
TIME=NUM+r'\s*(minutes?|mins?|hours?|hrs?|days?|weeks?)'

def amount(number):return Fraction(number)
def duration(number,unit):
    multiplier=Fraction(1,60) if unit.lower().startswith(('min',)) else 24*7 if unit.lower().startswith('week') else 24 if unit.lower().startswith('day') else 1
    return amount(number)*multiplier
def shown(value):return str(value.numerator) if value.denominator==1 else str(value)

def split(text):
    return [v.strip().rstrip('.!?') for v in re.split(r'[;\n]+|(?<=[.!?])\s+(?=[^\W\d_])',text) if v.strip()]

def parse(text):
    clauses=split(text);measurements=[];requirements=[];unknown=[];priority=None;question=None
    for raw in clauses:
        clause=re.sub(r'^(?:actually[, ]+|correct(?:ion)?[: ]+|update[: ]+)','',raw,flags=re.I).strip()
        clause=re.sub(r'^what if\s+','',clause,flags=re.I)
        if re.search(r'\b(?:might|maybe|perhaps|approximately|estimated|roughly)\b',clause,re.I):
            unknown.append(raw);continue
        requirement_count=len(requirements)
        # Common combined option description; expand the second verb with its subject.
        combined=re.fullmatch(NAME+r'\s+(costs?\s+.+?)\s+and\s+(takes?\s+.+)',clause,re.I)
        pieces=[combined[1]+' '+combined[2],combined[1]+' '+combined[3]] if combined else [clause]
        for piece in pieces:
            cost=re.fullmatch(NAME+r'\s+(?:costs?|is priced at)\s*'+MONEY,piece,re.I)
            time=re.fullmatch(NAME+r'\s+(?:takes?|needs?|requires?)\s+'+TIME,piece,re.I)
            if cost:
                measurements.append({'name':cost[1].strip(),'metric':'cost','value':shown(amount(cost[3])),'unit':{'£':'GBP','$':'USD','€':'EUR'}[cost[2]],'source':raw});continue
            if time:
                measurements.append({'name':time[1].strip(),'metric':'time','value':shown(duration(time[2],time[3])),'unit':'hours','source':raw});continue
            if re.search(r'\b(?:which|choose|compare|cheapest|cheaper|fastest|quicker|better|best|recommend|should)\b',piece,re.I):
                question=piece
                cheap=bool(re.search(r'\b(?:cheapest|cheaper|lowest cost|lowest price)\b',piece,re.I))
                fast=bool(re.search(r'\b(?:fastest|quicker|quickest|least time)\b',piece,re.I))
                priority='cost' if cheap and not fast else 'time' if fast and not cheap else None
                # Constraints are parsed below from the entire clause as well.
                if re.search(r'\b(?:reliable|safe|quality|warranty|durable|carbon|efficient|ethical|business|working|excluding|except|unless|before|after)\b|\bat least\b|\bno less than\b',piece,re.I):unknown.append(raw)
                continue
            if re.fullmatch(r'(?:my )?budget(?: is| of|:)?\s*'+MONEY,piece,re.I):continue
            if re.fullmatch(r'(?:I (?:need|want) (?:it|this) )?(?:within|no more than|at most)\s+'+TIME,piece,re.I):continue
            unknown.append(raw)
        for match in re.finditer(r'\b(?:budget(?: is| of|:)?|cost(?:s)? (?:at most|under|no more than)|spend (?:at most|no more than))\s*'+MONEY,clause,re.I):
            requirements.append({'metric':'cost','max':shown(amount(match[2])),'unit':{'£':'GBP','$':'USD','€':'EUR'}[match[1]],'source':raw})
        for match in re.finditer(r'\b(?:within|at most|no more than)\s+'+TIME,clause,re.I):
            requirements.append({'metric':'time','max':shown(duration(match[1],match[2])),'unit':'hours','source':raw})
        for match in re.finditer(r'\b(?:under|below)\s*'+MONEY,clause,re.I):
            requirements.append({'metric':'cost','max':shown(amount(match[2])),'unit':{'£':'GBP','$':'USD','€':'EUR'}[match[1]],'strict':True,'source':raw})
        if re.search(r'\b(?:within|budget|deadline|must|by Friday|by Monday)\b',clause,re.I) and len(requirements)==requirement_count:unknown.append(raw)
    return {'measurements':measurements,'requirements':requirements,'unknown':list(dict.fromkeys(unknown)),'priority':priority,'question':question}

def evaluate(model):
    options=model['options'];priority=model.get('priority');requirements=model['requirements']
    metrics=({priority} if priority else {m for row in options.values() for m in row['values']})|{r['metric'] for r in requirements}
    units={m:{row['values'][m]['unit'] for row in options.values() if m in row['values']} for m in metrics}
    for requirement in requirements:units.setdefault(requirement['metric'],set()).add(requirement['unit'])
    incompatible=[metric for metric,values in units.items() if len(values)>1]
    rows=[]
    for name,row in options.items():
        failures=[];missing=sorted(metrics-set(row['values']))
        for requirement in requirements:
            value=row['values'].get(requirement['metric'])
            if value and value['unit']==requirement['unit'] and (Fraction(value['value'])>Fraction(requirement['max']) or requirement.get('strict') and Fraction(value['value'])==Fraction(requirement['max'])):
                failures.append({'metric':requirement['metric'],'value':value['value'],'maximum':requirement['max'],'unit':value['unit'],'strict':requirement.get('strict',False)})
        rows.append({'name':name,'display_name':row['name'],'values':copy.deepcopy(row['values']), 'failures':failures,'missing':missing,
                     'feasibility':'excluded' if failures else 'unknown' if missing else 'feasible'})
    eligible=[row for row in rows if row['feasibility']=='feasible'];unresolved=[row['name'] for row in rows if row['feasibility']=='unknown']
    selected=[];frontier=[];dominance=[]
    if not incompatible:
        for a in eligible:
            for b in eligible:
                if a is b:continue
                av=[Fraction(a['values'][m]['value']) for m in metrics];bv=[Fraction(b['values'][m]['value']) for m in metrics]
                if all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv)):dominance.append({'better':a['name'],'worse':b['name']})
        frontier=[row['name'] for row in eligible if not any(d['worse']==row['name'] for d in dominance)]
        if eligible and not unresolved and not model['unparsed']:
            if priority:
                minimum=min(Fraction(r['values'][priority]['value']) for r in eligible)
                selected=[r['name'] for r in eligible if Fraction(r['values'][priority]['value'])==minimum]
            elif len(frontier)==1:selected=frontier
    status='needs-clarification' if incompatible or model['unparsed'] else 'needs-evidence' if unresolved or len(options)<2 else 'no-feasible-option' if not eligible else 'selected' if selected else 'trade-off'
    return {'status':status,'rows':rows,'selected':selected,'frontier':frontier,'dominance':dominance,'priority':priority,
            'requirements':copy.deepcopy(requirements),'incompatible_units':incompatible,'unresolved':unresolved,'unparsed':model['unparsed'],
            'scope':'Exact comparison under supplied cost/time figures and requirements. Time is converted to hours; currencies are never converted. A selection is conditional on the stated criteria, not a complete real-world recommendation.','model_calls':0}

def render(report):
    names={r['name']:r['display_name'] for r in report['rows']}
    lines=[]
    if report['selected']:lines.append('Under your stated requirements, '+', '.join(names[n] for n in report['selected'])+(' ties for the best '+report['priority']+'.' if len(report['selected'])>1 and report['priority'] else ' is selected'+(' for the lowest '+report['priority'] if report['priority'] else ' on the stated cost/time criteria')+'.'))
    elif report['status']=='trade-off':lines.append('There is a trade-off: '+', '.join(names[n] for n in report['frontier'])+'. Which matters more: cost or time?')
    elif report['status']=='no-feasible-option':lines.append('None of the supplied options meets all the stated requirements.')
    else:lines.append('I need to resolve the missing or incompatible information before selecting an option.')
    for row in report['rows']:
        facts=', '.join(metric+' '+v['value']+' '+v['unit'] for metric,v in row['values'].items())
        detail='; '.join(f"{f['metric']} {f['value']} "+('is not below ' if f['strict'] else 'exceeds ')+f"{f['maximum']} {f['unit']}" for f in row['failures'])
        if row['missing']:detail+='; missing '+', '.join(row['missing'])
        lines.append('- '+row['display_name']+': '+facts+' — '+row['feasibility']+(' ('+detail.strip('; ')+')' if detail else ''))
    if report['incompatible_units']:lines.append('Supply a common currency for '+', '.join(report['incompatible_units'])+'.')
    if report['unparsed']:lines.append('These details still need an explicit interpretation: '+' / '.join(report['unparsed']))
    lines.append(report['scope'])
    return '\n\n'.join(lines)

def respond(text,state):
    if len(text)>16000:return None
    old=state.get('practical_decision');focused=state.get('focus_kind')=='practical-decision'
    key=text.strip().casefold().rstrip('?.!')
    if focused and key in ('what could change that conclusion','what would change that result','how robust is that choice'):
        report=old['report'];model=old['model'];lines=[]
        for row in report['rows']:
            for requirement in model['requirements']:
                value=row['values'].get(requirement['metric'])
                if value and value['unit']==requirement['unit']:
                    margin=Fraction(requirement['max'])-Fraction(value['value'])
                    lines.append(row['display_name']+': '+requirement['metric']+' margin '+shown(margin)+' '+value['unit']+' before the maximum is exceeded.')
        if report['priority'] and report['selected']:
            best=next(r for r in report['rows'] if r['name']==report['selected'][0]);metric=report['priority'];best_value=Fraction(best['values'][metric]['value'])
            for other in report['rows']:
                if other['name']!=best['name'] and other['feasibility']=='feasible':
                    difference=Fraction(other['values'][metric]['value'])-best_value
                    lines.append(best['display_name']+' could increase '+metric+' by '+shown(difference)+' '+best['values'][metric]['unit']+' to tie '+other['display_name']+', if other figures and requirements stay fixed.')
        return {'status':'complete','answer':'\n\n'.join(lines) if lines else 'Supply comparable figures and a priority before a numeric sensitivity check.','model_calls':0}
    if focused and key in ('why','why that choice','explain that','show comparison','explain your choice'):
        return {'status':old['report']['status'],'answer':render(old['report']),'decision':copy.deepcopy(old['report']),'model_calls':0}
    why_not=re.fullmatch(r'why not (.+)',key) if focused else None
    if why_not:
        row=next((r for r in old['report']['rows'] if r['name']==why_not[1]),None)
        if row is None:return {'status':'needs-input','answer':'That name is not one of the retained options.','model_calls':0}
        reasons=[f"{r['metric']} is {r['value']} {r['unit']}, "+('not below the strict maximum ' if r.get('strict') else 'above the stated maximum ')+r['maximum'] for r in row['failures']]
        if row['missing']:reasons.append('missing '+', '.join(row['missing']))
        if not reasons:
            reasons.append('It remains feasible. Selection depends on the stated priority and competing figures.')
        return {'status':'complete','answer':row['display_name']+': '+'; '.join(reasons)+'.\n\n'+render(old['report']),'model_calls':0}
    parsed=parse(text)
    is_new=bool(parsed['question'] and len({m['name'].casefold() for m in parsed['measurements']})>=2)
    if not is_new and not (focused and (parsed['measurements'] or parsed['requirements'] or parsed['question'])):return None
    model={'options':{},'requirements':[],'priority':None,'question':parsed['question'],'unparsed':[],'revision':0,'changes':[]} if is_new else copy.deepcopy(old['model'])
    hypothetical=bool(re.match(r'^what if\b',text,re.I))
    explicit_correction=hypothetical or bool(re.match(r'^(?:actually|correct|correction|update)\b',text,re.I))
    for item in parsed['measurements']:
        name=item['name'].casefold();option=model['options'].setdefault(name,{'name':item['name'],'values':{}})
        prior=option['values'].get(item['metric'])
        if prior and (prior['value']!=item['value'] or prior['unit']!=item['unit']) and not explicit_correction:
            return {'status':'needs-clarification','answer':f"The new {item['metric']} for {item['name']} conflicts with the retained figure. Say “actually, {item['source']}” to replace it explicitly. The previous comparison is retained.",'model_calls':0}
        if prior and prior!=item:model['changes'].append({'option':name,'metric':item['metric'],'before':prior,'after':item})
        option['values'][item['metric']]={k:item[k] for k in ('value','unit','source')}
    for req in parsed['requirements']:
        model['requirements']=[r for r in model['requirements'] if r['metric']!=req['metric']]+[req]
    if parsed['priority']:model['priority']=parsed['priority']
    elif parsed['question'] and re.search(r'\b(?:best|better|compare)\b',parsed['question'],re.I):model['priority']=None
    if parsed['question']:model['question']=parsed['question']
    model['unparsed']=parsed['unknown'];model['revision']+=1;model['changes']=model['changes'][-24:]
    if len(model['options'])>12:raise ValueError('Compare at most 12 named options in one topic')
    report=evaluate(model)
    if hypothetical and old:
        state['last_decision_scenario']={'model':model,'report':report}
        return {'status':report['status'],'answer':'Hypothetical comparison — the original figures remain unchanged.\n\n'+render(report),'decision':copy.deepcopy(report),'hypothetical':True,'model_calls':0}
    state['practical_decision']={'model':model,'report':report};state['focus_kind']='practical-decision'
    return {'status':report['status'],'answer':render(report),'decision':copy.deepcopy(report),'model_calls':0}
