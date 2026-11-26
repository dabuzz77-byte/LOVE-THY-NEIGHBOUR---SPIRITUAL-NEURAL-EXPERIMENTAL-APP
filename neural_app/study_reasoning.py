"""Native two-group evidence analysis; supplied counts, not world verification.

Wilson per-group intervals: https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm
No pooled inference across non-independent observations; no automatic causality.
"""
import copy,json,math,re
from fractions import Fraction

def group(row):
    if not isinstance(row,dict):raise ValueError('Each group needs name, events and total')
    name=row.get('name');events=row.get('events');total=row.get('total');missing=row.get('missing',0)
    if not isinstance(name,str) or not 1<=len(name.strip())<=60:raise ValueError('Give each group a short name')
    if any(type(v)is not int for v in (events,total,missing)) or not 0<=events<=total or not 1<=total<=10**9 or not 0<=missing<=10**9:raise ValueError('Use integer counts: 0 <= events <= total, total positive, missing nonnegative')
    p=events/total;z=1.959963984540054;den=1+z*z/total
    centre=(p+z*z/(2*total))/den;half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return {'name':name.strip(),'events':events,'total':total,'missing':missing,'rate':p,'exact_rate':str(Fraction(events,total)),
            'wilson_95':[max(0,centre-half),min(1,centre+half)],
            'missing_outcome_bounds':[events/(total+missing),(events+missing)/(total+missing)]}

def comparison(rows):
    a,b=rows;difference=Fraction(a['events'],a['total'])-Fraction(b['events'],b['total'])
    return {'difference':float(difference),'exact_difference':str(difference),'rate_ratio':str(Fraction(a['events'],a['total'])/Fraction(b['events'],b['total'])) if b['events'] else None,
            'direction':(difference>0)-(difference<0),'missing_difference_bounds':[a['missing_outcome_bounds'][0]-b['missing_outcome_bounds'][1],a['missing_outcome_bounds'][1]-b['missing_outcome_bounds'][0]]}

def analyse(body):
    if not isinstance(body,dict) or not isinstance(body.get('groups'),list) or len(body['groups'])!=2:raise ValueError('Supply exactly two groups with name, events and total')
    rows=[group(r) for r in body['groups']]
    if rows[0]['name'].casefold()==rows[1]['name'].casefold():raise ValueError('Group names must differ')
    design=body.get('design','unspecified')
    if design not in ('randomized','observational','unspecified'):raise ValueError('Design is randomized, observational or unspecified')
    if type(body.get('independent',True))is not bool:raise ValueError('Independent must be a boolean')
    result={'groups':rows,'comparison':comparison(rows),'design':design,'independent':body.get('independent',True),'strata':[],'aggregation_reversal':False}
    strata=body.get('strata',[])
    if not isinstance(strata,list) or len(strata)>16:raise ValueError('Use up to 16 disjoint strata')
    for s in strata:
        if not isinstance(s,dict) or not isinstance(s.get('groups'),list) or len(s['groups'])!=2:raise ValueError('Each stratum needs both groups')
        sub=[group(r) for r in s['groups']]
        if [r['name'].casefold() for r in sub]!=[r['name'].casefold() for r in rows]:raise ValueError('Stratum groups must match the same names and order')
        result['strata'].append({'name':str(s.get('name','unnamed'))[:60],'groups':sub,'comparison':comparison(sub)})
    if strata:
        for i in range(2):
            for field in ('events','total','missing'):
                if sum(s['groups'][i][field] for s in result['strata'])!=rows[i][field]:raise ValueError('Disjoint stratum counts must sum to the overall '+field)
        directions={s['comparison']['direction'] for s in result['strata']}
        result['aggregation_reversal']=len(directions)==1 and 0 not in directions and result['comparison']['direction']==-next(iter(directions))
    result['scope']='Descriptive analysis of supplied counts. Events are not assumed beneficial. Per-group Wilson intervals assume independent binomial observations; they are not an interval or significance test for the between-group difference. Neither association nor a randomized label alone verifies a causal effect or predicts an individual outcome.'
    return result

def explain(report,mode='summary'):
    a,b=report['groups'];c=report['comparison'];direction='higher' if c['direction']>0 else 'lower' if c['direction']<0 else 'equal'
    lines=[f"{a['name']}: {a['events']}/{a['total']} ({a['rate']:.2%}). {b['name']}: {b['events']}/{b['total']} ({b['rate']:.2%}).",
           f"The recorded event rate for {a['name']} is {direction}; A minus B is {100*c['difference']:.2f} percentage points (exactly {c['exact_difference']})."]
    if mode=='why':lines += ['Each rate divides events by that group’s own denominator. The exact difference subtracts those fractions; absolute event counts alone can reverse a comparison.']
    if report['aggregation_reversal']:lines += ['Aggregation reversal: every supplied stratum points in the opposite direction from the overall comparison. Group composition must be investigated before choosing an explanation.']
    if any(r['missing'] for r in report['groups']):
        lo,hi=c['missing_difference_bounds'];lines += [f'Including all missing outcomes, the descriptive difference can range from {100*lo:.2f} to {100*hi:.2f} percentage points. These are worst-case missing-data bounds, not sampling confidence limits.']
    if not report['independent']:lines += ['Repeated or clustered observations were declared: ordinary binomial uncertainty intervals are withheld.']
    else:
        for row in report['groups']:lines += [f"{row['name']} per-group 95% Wilson interval: {row['wilson_95'][0]:.2%} to {row['wilson_95'][1]:.2%}."]
    if mode in ('causal','next','uncertainty'):
        lines += ['What remains unresolved: selection effects, confounding, measurement consistency, missing outcomes, independence and whether the groups represent the intended population.']
        lines += ['Next: check allocation and baseline differences; inspect disjoint subgroups and missing outcomes; repeat on separately collected observations. Define whether the event is desirable before recommending an action.']
        if report['design']=='randomized':lines += ['Random allocation can support causal analysis, but the supplied label does not check allocation integrity, adherence, attrition or outcome measurement.']
        else:lines += ['The supplied comparison does not establish causation. A controlled design or explicit defensible causal assumptions are needed.']
    return '\n\n'.join(lines+[report['scope']])

def respond(text,state):
    raw=text.strip();key=raw.casefold().rstrip('?.!');body=None;mode='summary'
    if key in ('write python for this study','export study as python') and state.get('study_input'):
        import ast,inspect,hashlib
        # Only installed pure analysis functions are exported; user text stays JSON data.
        data=json.dumps(state['study_input'],ensure_ascii=True,allow_nan=False)
        code='import json, math\nfrom fractions import Fraction\n\n'+'\n\n'.join(inspect.getsource(f) for f in (group,comparison,analyse))+'\n\ndata = json.loads('+repr(data)+')\nprint(json.dumps(analyse(data), indent=2))\n'
        ast.parse(code)
        return {'status':'complete','answer':'Standalone Python reproducing the supplied-count analysis:\n```python\n'+code+'```','code':code,'code_sha256':hashlib.sha256(code.encode()).hexdigest(),'verification':'Syntax checked; exports the installed pure analysis functions with the supplied input serialized as data. No model, host-control or network code.','model_calls':0}
    if re.match(r'^(?:analyse|analyze|compare) study:\s*',raw,re.I):body=json.loads(raw.split(':',1)[1])
    elif re.match(r'^study:\s*',raw,re.I):
        passage=raw.split(':',1)[1];matches=list(re.finditer(r'(?:Group\s+)?([A-Za-z][\w -]{0,40}?):\s*(\d+)\s+(?:of|out of)\s+(\d+)\s+(?:events|improved|passed|failed|responded)',passage,re.I))
        if len(matches)!=2:raise ValueError('Use study: Group A: 12 of 100 events. Group B: 8 of 100 events. Or analyse study: JSON')
        remainder=passage
        for m in reversed(matches):remainder=remainder[:m.start()]+remainder[m.end():]
        if remainder.strip(' .;\n\t'):raise ValueError('Unparsed qualifications remain; use analyse study: JSON to preserve design, missing outcomes or strata explicitly')
        body={'groups':[{'name':m[1].strip(),'events':int(m[2]),'total':int(m[3])} for m in matches]}
    elif key=='resume study analysis' and state.get('study_analysis'):pass
    elif state.get('focus_kind')=='study-analysis' and state.get('study_analysis'):
        if key in ('why','explain that','explain the comparison','how did you calculate that'):mode='why'
        elif key in ('does that prove causation','is that causal','did it cause that','does that prove it'):mode='causal'
        elif key in ('what should we check next','what next','what evidence is missing','what would change that conclusion'):mode='next'
        elif key in ('how certain is that','what are the limitations','what about uncertainty'):mode='uncertainty'
        elif key in ('show study data','show the original counts'):return {'status':'complete','answer':json.dumps(state['study_input'],indent=2),'model_calls':0}
        elif key.startswith('actually, study:'):return respond(raw[len('actually, '):],state)
        else:return None
    else:return None
    if body is not None:
        report=analyse(body)
        # Mutate only after complete validation.
        state['study_analysis']=report;state['study_input']=copy.deepcopy(body)
    report=copy.deepcopy(state['study_analysis']);state['focus_kind']='study-analysis'
    if not report['independent']:
        for row in report['groups']:row['wilson_95']=None
    return {'status':'complete','answer':explain(report,mode),'study_analysis':report,'model_calls':0}
