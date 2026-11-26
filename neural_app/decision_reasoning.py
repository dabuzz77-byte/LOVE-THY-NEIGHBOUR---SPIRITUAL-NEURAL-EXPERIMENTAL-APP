"""Unit-labelled interval/Pareto comparisons without inventing missing ratings."""
import re
from .linear_reasoning import rational

def label(value):
 if not isinstance(value,str) or not value.strip() or len(value)>80:raise ValueError('Use short nonempty labels')
 return value.strip().casefold()

def compare(body):
 raw_criteria=body.get('criteria');options=body.get('options');constraints=body.get('constraints',[])
 if not isinstance(raw_criteria,list) or not 1<=len(raw_criteria)<=8 or not isinstance(options,list) or not 2<=len(options)<=12 or not isinstance(constraints,list) or len(constraints)>16:raise ValueError('Use 1–8 criteria, 2–12 options and up to 16 constraints')
 criteria={}
 for row in raw_criteria:
  if not isinstance(row,dict):raise ValueError('Each criterion needs name and direction')
  name=label(row.get('name'));direction=row.get('direction');unit=row.get('unit','')
  if name in criteria or direction not in ('min','max') or not isinstance(unit,str) or len(unit)>40:raise ValueError('Criteria need distinct names, min/max direction and a bounded unit label')
  criteria[name]={'direction':direction,'unit':unit.strip()}
 limits=[]
 for row in constraints:
  if not isinstance(row,dict):raise ValueError('Each constraint must be an object')
  name=label(row.get('criterion'))
  if name not in criteria or not any(k in row for k in ('min','max')):raise ValueError('Constraints need a declared criterion and min or max')
  minimum=rational(row['min']) if 'min' in row else None;maximum=rational(row['max']) if 'max' in row else None
  if minimum is not None and maximum is not None and minimum>maximum:raise ValueError('Constraint bounds conflict')
  limits.append((name,minimum,maximum))
 records=[];names=set();missing=[]
 for row in options:
  if not isinstance(row,dict) or not isinstance(row.get('values'),dict):raise ValueError('Each option needs a name and value mapping')
  name=label(row.get('name'));values={};normalised={}
  if name in names:raise ValueError('Option names must be distinct')
  names.add(name)
  for raw_name,value in row['values'].items():
   metric=label(raw_name)
   if metric not in criteria or metric in normalised:raise ValueError('Every metric must uniquely match a declared criterion')
   normalised[metric]=value
  for metric,criterion in criteria.items():
   if metric not in normalised:missing.append({'option':name,'criterion':metric});continue
   value=normalised[metric]
   if isinstance(value,dict):
    if not isinstance(value.get('unit',criterion['unit']),str) or value.get('unit',criterion['unit']).strip().casefold()!=criterion['unit'].casefold():raise ValueError('Metric units do not match; convert explicitly before comparing')
    if 'value' in value and ('low' in value or 'high' in value):raise ValueError('Use a point value or an interval, not both')
    low=high=rational(value['value']) if 'value' in value else None
    if low is None:
     if 'low' not in value or 'high' not in value:raise ValueError('An interval needs low and high')
     low,high=rational(value['low']),rational(value['high'])
   else:low=high=rational(value)
   if low>high:raise ValueError('Measurement interval bounds must be ordered')
   values[metric]=(low,high)
  checks=[]
  for metric,minimum,maximum in limits:
   if metric not in values:outcome='unknown'
   else:
    low,high=values[metric]
    if minimum is not None and high<minimum or maximum is not None and low>maximum:outcome='fail'
    elif minimum is not None and low<minimum or maximum is not None and high>maximum:outcome='unknown'
    else:outcome='pass'
   checks.append({'criterion':metric,'result':outcome})
  feasibility='excluded' if any(r['result']=='fail' for r in checks) else 'uncertain' if any(r['result']=='unknown' for r in checks) else 'feasible'
  records.append({'name':name,'values':values,'constraints':checks,'feasibility':feasibility,'complete_metrics':len(values)==len(criteria)})
 eligible=[r for r in records if r['feasibility']=='feasible' and r['complete_metrics']];edges=[]
 for a in eligible:
  for b in eligible:
   if a is b:continue
   comparisons=[]
   for metric,criterion in criteria.items():
    low_a,high_a=a['values'][metric];low_b,high_b=b['values'][metric]
    comparisons.append((high_a<=low_b,high_a<low_b) if criterion['direction']=='min' else (low_a>=high_b,low_a>high_b))
   if all(v[0] for v in comparisons) and any(v[1] for v in comparisons):edges.append({'better':a['name'],'worse':b['name']})
 dominated={e['worse'] for e in edges};frontier=[r['name'] for r in eligible if r['name'] not in dominated]
 unresolved=[r['name'] for r in records if r['feasibility']=='uncertain' or r['feasibility']!='excluded' and not r['complete_metrics']]
 best=[r['name'] for r in eligible if not unresolved and all(other is r or {'better':r['name'],'worse':other['name']} in edges for other in eligible)]
 for row in records:row['values']={metric:{'low':str(pair[0]),'high':str(pair[1]),'unit':criteria[metric]['unit']} for metric,pair in row['values'].items()}
 status='needs-evidence' if unresolved else 'no-feasible-option' if not eligible else 'compared'
 next_question='Supply the missing measurements or resolve intervals that cross a requirement.' if unresolved else 'Revise an explicitly failing requirement or consider another option.' if not eligible else 'Choose a priority or further evidence to resolve remaining trade-offs.' if len(frontier)>1 else 'Check whether the declared criteria, bounds and measurements cover the actual decision.'
 return {'status':status,'options':records,'criteria':criteria,'missing_data':missing,'unresolved_options':unresolved,'robust_dominance':edges,'pareto_frontier':frontier,'robust_best_under_declared_criteria':best,'next_step':next_question,'scope':'Exact comparisons of supplied values and intervals under declared units, criteria and requirements. Missing values are unknown, not zero. Robust dominance requires no worse at every criterion and guaranteed strict improvement on at least one. No inferred ratings, currency conversion, universal recommendation or external action.'}

def compile_frame(frame):
 """Compile only explicitly declared directions, measurements and requirements."""
 criteria=[];unparsed=[]
 for text in frame['criteria']:
  match=re.fullmatch(r'(min|max|minimise|minimize|maximise|maximize)\s+([\w-]+)',text.strip(),re.I)
  if not match:unparsed.append(text);continue
  criteria.append({'name':match[2].casefold(),'direction':'min' if match[1].lower().startswith('min') else 'max'})
 if not criteria:return None
 if unparsed:return {'clarification':'Express each criterion explicitly as min NAME or max NAME before combining them.'}
 if len(frame['options'])<2:return {'clarification':'Which two or more named options should I compare on those criteria?'}
 if len({row['name'] for row in criteria})!=len(criteria):return {'clarification':'A criterion has repeated or conflicting directions; correct or replace the criteria list.'}
 number=r'[-+]?\d{1,12}(?:\.\d{1,6}|/\d{1,12})?';units={};observations={};selected={row['name'] for row in criteria};options=frame['options']
 for source in frame['facts']:
  for option in sorted(options,key=len,reverse=True):
   prefix=re.match(re.escape(option)+r'\s+',source,re.I)
   if not prefix:continue
   match=re.fullmatch(r'([\w-]+)\s*=\s*([£$€]?)\s*('+number+r')\s*([\w%/-]+)?',source[prefix.end():].strip())
   if not match:continue
   metric,symbol,value,unit=match.groups();metric=metric.casefold()
   if metric not in selected:continue
   symbol_unit={'£':'GBP','$':'USD','€':'EUR'}.get(symbol,'');unit=unit or symbol_unit
   if not unit or symbol_unit and symbol_unit.casefold()!=unit.casefold():return {'clarification':'Supply one explicit, consistent unit for '+metric+'.'}
   if metric in units and units[metric].casefold()!=unit.casefold():return {'clarification':'The '+metric+' measurements use different units. Convert them explicitly before comparison.'}
   units[metric]=unit;key=(option.casefold(),metric);exact=rational(value)
   if key in observations and rational(observations[key]['value'])!=exact:return {'clarification':'Conflicting '+metric+' measurements for '+option+' need an explicit correction.'}
   observations[key]={'value':value,'unit':unit,'source':source};break
 for row in criteria:
  if row['name'] not in units:return {'clarification':'What measured values and common unit should I use for '+row['name']+'?'}
  row['unit']=units[row['name']]
 constraints=[]
 for text in frame['constraints']:
  match=re.fullmatch(r'([\w-]+)\s*(<=|>=)\s*('+number+r')\s+([\w%/-]+)',text.strip())
  if not match:return {'clarification':'The requirement “'+text+'” is not quantified. Specify how to check it before declaring an option feasible.'}
  metric,operator,value,unit=match.groups();metric=metric.casefold()
  if metric not in units or unit.casefold()!=units[metric].casefold():return {'clarification':'The requirement must name a declared criterion with the same unit as its measurements.'}
  constraints.append({'criterion':metric,'max' if operator=='<=' else 'min':value})
 return {'model':{'mode':'decision','criteria':criteria,'options':[{'name':option,'values':{metric:observations[(option.casefold(),metric)] for metric in selected if (option.casefold(),metric) in observations}} for option in options],'constraints':constraints},'provenance':'Compiled exclusively from explicit user-supplied option labels, min/max directions, measurement statements and quantified requirements.'}
