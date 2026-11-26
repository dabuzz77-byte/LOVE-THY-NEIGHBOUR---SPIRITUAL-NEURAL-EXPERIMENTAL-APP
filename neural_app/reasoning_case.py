"""Checked, provenance-preserving composition of pure reasoning models."""
import copy,time,math
from fractions import Fraction

MODES={'deduction','explanation','probability','planning','equations','units','decision','relations','reading','diagnostic','scenarios','constraints','causal'}
MODES.add('counterfactual')
MODES.add('causal_probability')
MODES.add('written_quantities')

def path_get(value,path):
 if not isinstance(path,list) or not 1<=len(path)<=8:raise ValueError('Bindings need paths with 1–8 keys or indices')
 for part in path:
  if isinstance(value,dict) and isinstance(part,str):value=value[part]
  elif isinstance(value,list) and type(part)is int and 0<=part<len(value):value=value[part]
  else:raise ValueError('Binding path does not match the actual model result')
 return value

def accepted(result):
 mode=result['mode'];status=result.get('status')
 if mode=='equations':return status in ('unique-solution','underdetermined') and result.get('requested_values_resolved') is True and result.get('all_equations_substitution_checked') is True
 if mode=='deduction':return status in ('entailed','refuted') and result.get('complete') is True
 if mode=='explanation':return False # A hypothetical explanation is not a derived measurement.
 if mode=='probability':return status=='updated'
 if mode=='planning':return status=='planned' and result.get('plan_replayed') is True
 if mode=='decision':return status=='compared'
 if mode=='scenarios':return status=='compared' and result.get('complete') is True
 if mode in ('units','written_quantities'):return status=='calculated' and result.get('complete') is True
 if mode=='counterfactual':return status=='model-evaluated' and result.get('complete') is True
 if mode=='causal_probability':return status=='updated' and result.get('complete') is True
 if mode=='diagnostic':return False # Compatibility is not a verified causal conclusion.
 if mode in ('reading','relations'):return status in ('answered','refuted') and result.get('complete') is True and not any(a.get('has_conflicted_support') for a in result.get('answers',[]))
 if mode=='constraints':return status in ('feasible','optimal') and result.get('verified') is True
 return mode=='causal' and status=='model-evaluated'

def source_number(result,path):
 mode=result['mode']
 allowed=(mode=='equations' and len(path)==2 and path[0]=='determined_values' or mode=='causal' and len(path)==2 and path[0] in ('baseline','intervened','difference') or mode=='planning' and path==['total_cost'] or mode=='probability' and len(path)==3 and path[0]=='posterior' and type(path[1])is int and path[2]=='posterior' or mode=='causal_probability' and path in (['prior_outcome_probability'],['posterior_outcome_probability'],['evidence_probability']) or mode=='constraints' and len(path)==2 and path[0]=='assignment')
 if not allowed:raise ValueError('Bindings use explicit numeric model outputs, not assumptions, witness worlds or arbitrary result text')
 value=path_get(result,path)
 if type(value)not in (str,int,float) or type(value)is float and not math.isfinite(value):raise ValueError('Binding source must be a finite numeric result')
 return Fraction(str(value))

def bind(task,path,value):
 mode=task.get('mode','deduction')
 if mode=='equations':valid=len(path)==3 and path[0]=='equations' and path[2]=='equals' or len(path)==4 and path[0]=='equations' and path[2]=='terms'
 elif mode=='decision':valid=len(path)in (4,5) and path[0]=='options' and path[2]=='values' and (len(path)==4 or path[4]in ('value','low','high')) or len(path)==3 and path[0]=='constraints' and path[2]in ('min','max')
 elif mode=='causal':valid=len(path)==2 and path[0]in ('values','intervention')
 elif mode=='probability':valid=len(path)==3 and path[0]=='hypotheses' and path[2]=='prior' or len(path)==4 and path[0]=='hypotheses' and path[2]=='likelihoods'
 elif mode=='planning':valid=len(path)==3 and path[0]=='actions' and path[2]=='cost'
 elif mode=='constraints':valid=len(path)==3 and path[0]=='domains' or len(path)==3 and path[0]=='constraints' and path[2]=='value'
 else:valid=False
 if not valid:raise ValueError('Binding destination must be an explicit numeric model parameter')
 # Do not create hidden fields, variables, options or facts while binding.
 path_get(task,path);parent=path_get(task,path[:-1]);last=path[-1]
 converted=int(value) if value.denominator==1 else str(value) if mode in ('equations','decision') else float(value)
 if isinstance(converted,float) and not math.isfinite(converted):raise ValueError('Binding exceeds the numeric model range')
 parent[last]=converted
 return {'exact_value':str(value),'bound_value':converted,'representation':'integer' if value.denominator==1 else 'exact rational' if isinstance(converted,str) else 'finite floating point'}

def run(body):
 stages=body.get('stages')
 if not isinstance(stages,list) or not 1<=len(stages)<=8:raise ValueError('A reasoning case needs 1–8 stages')
 names=[s.get('id') for s in stages if isinstance(s,dict)]
 if len(names)!=len(stages) or any(not isinstance(n,str) or not n.isidentifier() or len(n)>40 for n in names) or len(set(names))!=len(names):raise ValueError('Stages need distinct identifier names')
 dependencies={}
 for stage in stages:
  task=stage.get('task');bindings=stage.get('bindings',[])
  if not isinstance(task,dict) or task.get('mode','deduction') not in MODES or not isinstance(bindings,list) or len(bindings)>8:raise ValueError('Stages need a supported pure reasoning task and up to eight bindings')
  refs=set();destinations=set()
  for item in bindings:
   if not isinstance(item,dict) or item.get('from') not in names or not isinstance(item.get('path'),list) or not isinstance(item.get('to'),list):raise ValueError('Each binding needs a known stage, source path and destination path')
   if not 1<=len(item['path'])<=8 or not 2<=len(item['to'])<=8 or any(type(p)not in (str,int) for p in item['path']+item['to']):raise ValueError('Binding paths must use bounded text keys or integer indices')
   destination=tuple(item['to'])
   if destination in destinations:raise ValueError('Multiple bindings cannot overwrite the same parameter')
   destinations.add(destination);refs.add(item['from'])
  dependencies[stage['id']]=refs
 remaining=set(names);ordered=[]
 while remaining:
  ready=[n for n in names if n in remaining and not dependencies[n]&remaining]
  if not ready:raise ValueError('Reasoning case contains a dependency cycle')
  ordered.extend(ready);remaining.difference_update(ready)
 from .general_reasoning import reason
 results={};receipts=[];deadline=time.monotonic()+2;status='complete';blocked=None
 for name in ordered:
  if time.monotonic()>deadline:status='incomplete';blocked=name;break
  stage=next(s for s in stages if s['id']==name);task=copy.deepcopy(stage['task']);records=[]
  try:
   for binding in stage.get('bindings',[]):
    source=results[binding['from']]
    if not accepted(source):raise ValueError('The dependency remains unresolved or hypothetical')
    value=source_number(source,binding['path']);record=bind(task,binding['to'],value)
    records.append({'from':binding['from'],'source_path':binding['path'],'destination_path':binding['to'],**record,'source_scope':source['scope'],'source_input_sha256':source['input_sha256']})
   result=reason(task);results[name]=result;receipts.append({'id':name,'task':task,'bindings':records,'result':result})
   if not accepted(result):status='needs-review';blocked=name;break
  except (ValueError,TypeError,KeyError,IndexError,OverflowError,ZeroDivisionError) as exc:
   status='blocked';blocked=name;receipts.append({'id':name,'bindings':records,'error':str(exc)[:400]});break
 return {'status':status,'stages':receipts,'blocked_stage':blocked,'remaining_stages':[n for n in ordered if n not in results],'model_calls':0,'next_step':'Review each model assumption and the provenance of values passed between stages.' if status=='complete' else 'Resolve the incomplete or invalid stage before using its output downstream.','scope':'Composition of explicit pure models, not corroborating independent evidence. A derived value retains its source assumptions. No hypotheses, arbitrary text, uncertain witness worlds or real-world actions are promoted to facts or executed.'}
