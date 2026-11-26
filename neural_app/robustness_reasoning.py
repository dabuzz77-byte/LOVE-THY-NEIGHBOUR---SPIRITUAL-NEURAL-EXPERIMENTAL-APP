"""Explicit scenario audits of supported pure reasoning models, not universal proof."""
import copy,json,time
from .reasoning_case import path_get,accepted

MODES={'deduction','equations','units','decision','scenarios','reading','relations','probability','planning','constraints','causal','counterfactual','causal_probability'}

def signature(report,focus=None):
 if focus is not None:return copy.deepcopy(path_get(report,focus))
 mode=report['mode'];value={'status':report['status']}
 fields={'deduction':(), 'equations':('determined_values',),'units':('base_value','dimensions'),'decision':('robust_best_under_declared_criteria','pareto_frontier','unresolved_options'),'scenarios':('minimax_regret_options','expected_outcome_options','undominated_options'),'reading':('answers','counter_supporting_fact_ids'),'relations':('answers','counter_supporting_fact_ids'),'probability':('posterior',),'planning':('plan','total_cost'),'constraints':('assignment','objective_value'),'causal':('baseline','intervened'),'counterfactual':('baseline_outcome','interventions'),'causal_probability':('posterior_outcome_probability','interventions')}
 for field in fields.get(mode,()):
  item=copy.deepcopy(report.get(field))
  if field=='determined_values':item={name:item.get(name) for name in report.get('requested_variables',item or {})} if item is not None else None
  if field=='answers' and item is not None:item=sorted([{'bindings':row['bindings'],'conflicted':row.get('has_conflicted_support',False)} for row in item],key=lambda r:json.dumps(r,sort_keys=True))
  if field=='counter_supporting_fact_ids':item=bool(item)
  if field=='posterior' and item is not None:item=[{'name':r['name'],'posterior':r['posterior']} for r in item]
  if field=='interventions' and item is not None:item=sorted([{k:r[k] for k in ('set','outcome','counterfactual_probability_given_evidence') if k in r} for r in item],key=lambda r:json.dumps(r,sort_keys=True))
  value[field]=item
 return value

def change(task,edits):
 if not isinstance(edits,list) or not 1<=len(edits)<=8:raise ValueError('Each variant needs 1–8 explicit changes')
 touched=[]
 for edit in edits:
  if not isinstance(edit,dict):raise ValueError('Use change objects')
  path=edit.get('path')
  if not isinstance(path,list) or not 1<=len(path)<=8 or any(type(p)not in (str,int) for p in path) or not isinstance(path[0],str) or path[0] in ('mode','query','question','question_expected_value','select','requested_variables','variables','outcome','goal','objective'):raise ValueError('Use bounded existing assumption paths without changing the question, variable identities, goal or reasoning mode')
  if ('value' in edit)==('remove' in edit) or 'remove' in edit and edit['remove'] is not True:raise ValueError('Choose a replacement value or remove: true')
  for prior in touched:
   if path[:len(prior)]==prior or prior[:len(path)]==path:raise ValueError('Changes cannot overlap or shift the same list in one variant')
  try:
   parent=path_get(task,path[:-1]) if len(path)>1 else task;key=path[-1];path_get(task,path)
  except (KeyError,IndexError,TypeError):raise ValueError('A change path does not exist in the original task') from None
  if edit.get('remove'):
   if not isinstance(parent,list) or type(key)is not int:raise ValueError('Removal is supported only for an existing list item')
   parent.pop(key);touched.append(path[:-1])
  else:parent[key]=copy.deepcopy(edit['value']);touched.append(path)
 return task

def audit(body):
 from .general_reasoning import reason
 task=body.get('task');variants=body.get('variants');focus=body.get('focus')
 if not isinstance(task,dict) or task.get('mode','deduction') not in MODES or not isinstance(variants,list) or not 1<=len(variants)<=8:raise ValueError('Provide one supported base task and 1–8 named variants')
 if focus is not None and (not isinstance(focus,list) or not 1<=len(focus)<=8 or any(type(p)not in (str,int) for p in focus)):raise ValueError('Focus must be a bounded path in the result')
 seen=set();prepared=[]
 for variant in variants:
  if not isinstance(variant,dict) or not isinstance(variant.get('name'),str) or not variant['name'].strip() or len(variant['name'])>120 or variant['name'] in seen:raise ValueError('Use distinct short variant names')
  seen.add(variant['name']);prepared.append((variant,change(copy.deepcopy(task),variant.get('changes'))))
 baseline=reason(copy.deepcopy(task));base_signature=signature(baseline,focus);base_usable=accepted(baseline);rows=[];deadline=time.monotonic()+3
 for variant,modified in prepared:
  if time.monotonic()>deadline:
   rows.append({'name':variant['name'],'comparison':'unresolved','error':'Audit computation budget reached'});continue
  try:
   report=reason(modified);value=signature(report,focus);usable=accepted(report)
   settled=report.get('complete',True) is True and report.get('status') not in ('incomplete','undetermined')
   comparison=('unchanged' if json.dumps(value,sort_keys=True,allow_nan=False)==json.dumps(base_signature,sort_keys=True,allow_nan=False) else 'changed') if settled else 'unresolved'
   rows.append({'name':variant['name'],'comparison':comparison,'usable_conclusion':usable,'changes':copy.deepcopy(variant['changes']),'signature':value,'result':report})
  except (ValueError,TypeError,KeyError,IndexError,SyntaxError,OverflowError,ZeroDivisionError) as exc:rows.append({'name':variant['name'],'comparison':'unresolved','changes':copy.deepcopy(variant['changes']),'error':str(exc)[:400]})
 changed=[r['name'] for r in rows if r['comparison']=='changed'];unresolved=[r['name'] for r in rows if r['comparison']=='unresolved' or not r.get('usable_conclusion',False)]
 status='sensitive' if base_usable and changed else 'stable-in-tested-variants' if base_usable and not unresolved else 'inconclusive'
 return {'status':status,'complete':baseline.get('complete',True) is True and not any(r['comparison']=='unresolved' for r in rows),'baseline':baseline,'baseline_usable':base_usable,'baseline_signature':base_signature,'variants':rows,'changed_variants':changed,'unresolved_variants':unresolved,'focus':focus,'automatic_probe_scope':body.get('automatic_probe_scope'),'next_step':'Review the specific changed assumptions and outputs; resolve invalid or incomplete variants before making a broader claim.','scope':'Comparison of explicitly specified finite model variants only. Unchanged results do not prove universal robustness, independent corroboration or real-world safety. Invalid models remain unresolved; losing support is not proof of the opposite.'}

def probes(task):
 if not isinstance(task,dict):raise ValueError('Supply a reasoning task first')
 mode=task.get('mode','deduction');variants=[];scope=''
 if mode in ('deduction','relations'):
  field='premises' if mode=='deduction' else 'facts';rows=task.get(field,[])
  for i in range(min(8,len(rows))):variants.append({'name':'omit_'+field+'_'+str(i+1),'changes':[{'path':[field,i],'remove':True}]})
  scope='Single-entry omissions for the first '+str(min(8,len(rows)))+' of '+str(len(rows))+' '+field+' only.'
 elif mode=='equations':
  from .linear_reasoning import rational
  rows=task.get('equations',[])
  for i,row in enumerate(rows[:4]):
   for delta in (-1,1):variants.append({'name':'rhs_'+str(i+1)+'_'+str(delta),'changes':[{'path':['equations',i,'equals'],'value':str(rational(row['equals'])+delta)}]})
  scope='Plus/minus one in the supplied right-hand-side number, for at most four equations; no measurement scale or empirical likelihood is assumed.'
 else:raise ValueError('Provide explicit variants with check robustness: for this reasoning mode')
 if not variants:raise ValueError('No supported omission or nearby-value probes are available')
 return {'mode':'robustness','task':copy.deepcopy(task),'variants':variants,'automatic_probe_scope':scope}
