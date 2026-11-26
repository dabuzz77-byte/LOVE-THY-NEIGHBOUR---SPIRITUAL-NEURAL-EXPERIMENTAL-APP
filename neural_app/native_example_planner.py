"""Infer short parameterised native workflows; validation never selects candidates."""
import copy,json,time
from collections import deque
from .native_synthesis import bounded
from .reasoning_engine import pipeline
from .workflow_contracts import equivalent

def signature(values):return json.dumps(values,sort_keys=True,ensure_ascii=True,allow_nan=False)

def solve(body):
 if not isinstance(body,dict):raise ValueError('Supply name, examples and validation')
 name=body.get('name','');train=body.get('examples');validation=body.get('validation')
 if not isinstance(name,str) or not name.strip() or len(name)>80:raise ValueError('Use a short procedure name')
 if not isinstance(train,list) or not 2<=len(train)<=8 or not isinstance(validation,list) or not 2<=len(validation)<=8:raise ValueError('Supply 2–8 examples and 2–8 separate validation pairs')
 for row in train+validation:
  if not isinstance(row,dict) or 'input' not in row or 'output' not in row:raise ValueError('Each pair needs input and output')
  bounded(row['input']);bounded(row['output'])
 if len(signature([train,validation]))>32768:raise ValueError('Example collection exceeds storage budget')
 if len({signature(r['input']) for r in train+validation})!=len(train+validation):raise ValueError('Training and validation inputs must all be distinct')
 depth=body.get('max_depth',3)
 if type(depth)is not int or not 1<=depth<=3:raise ValueError('Use depth 1–3')
 ops=[{'op':op} for op in ('strip','lower','upper','lines','words','unique','sort','sum','count','minimum','maximum','mean','reverse','join')]
 # Derive table schemas from training inputs only. Validation remains untouched.
 tables=[r['input'] for r in train]
 if all(isinstance(table,list) and table and all(isinstance(row,dict) for row in table) for table in tables):
  rows=[row for table in tables for row in table]
  fields=sorted(field for field in set.intersection(*(set(row) for row in rows)) if isinstance(field,str))[:8]
  field_ops=[{'op':'field','name':field} for field in fields]
  keys=[field for field in fields if all(isinstance(row[field],str) for row in rows)][:4]
  measures=[field for field in fields if all(type(row[field]) in (int,float) for row in rows)][:4]
  grouping=[{'op':'group','field':field,'aggregate':'count'} for field in keys]
  grouping.extend({'op':'group','field':key,'value_field':measure,'aggregate':aggregate} for key in keys for measure in measures for aggregate in ('sum','mean','minimum','maximum'))
  ops=field_ops+grouping[:32]+ops
 constants=[2,-1,.5]
 scalar=[r for r in train if type(r['input']) in (int,float) and type(r['output']) in (int,float)]
 if len(scalar)>=2:
  a,b=scalar[:2];dx=b['input']-a['input']
  if dx:
   slope=(b['output']-a['output'])/dx;constants.extend([slope,a['output']-slope*a['input']])
 # Candidate parameters use training examples only.
 for row in train:
  x,y=row['input'],row['output']
  if type(x) in (int,float) and type(y) in (int,float):
   constants.append(y-x)
   if x:constants.append(y/x)
 for op in ('scale','add'):
  for v in list(dict.fromkeys(constants))[:8]:
   if abs(v)<=1e6:ops.append({'op':op,'value':v})
 queue=deque([([], [copy.deepcopy(r['input']) for r in train])]);seen=set();tested=0;winner=None;started=time.perf_counter()
 while queue and tested<512 and time.perf_counter()-started<.25:
  steps,values=queue.popleft();tested+=1
  if steps and all(equivalent(v,r['output']) for v,r in zip(values,train)):winner=steps;break
  key=signature(values)
  if key in seen or len(steps)>=depth:continue
  seen.add(key)
  for op in ops:
   try:outputs=[pipeline(copy.deepcopy(v),[op])['result'] for v in values]
   except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError):continue
   queue.append((steps+[op],outputs))
   if len(queue)>=2048:break
 report={'name':name.strip().casefold(),'tested':tested,'elapsed_ms':round((time.perf_counter()-started)*1000,3),'model_calls':0,'candidate_operations':len(ops),'search_scope':'Bounded native operations, depth at most three; parameters and table schemas derived only from training examples','validation_used_for_selection':False}
 if winner is None:return {**report,'status':'unresolved','reason':'No candidate found within this search budget; this does not prove the task impossible.'}
 checks=[]
 for row in validation:
  try:actual=pipeline(copy.deepcopy(row['input']),winner)['result'];passed=equivalent(actual,row['output']);error=None
  except (ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as exc:actual=None;passed=False;error=str(exc)[:200]
  checks.append({'input':copy.deepcopy(row['input']),'expected':copy.deepcopy(row['output']),'actual':actual,'passed':passed,'error':error})
 passed=all(c['passed'] for c in checks)
 return {**report,'status':'validated-candidate' if passed else 'validation-failed','steps':winner,'validation':checks,'training_cases':len(train),'source_input':copy.deepcopy(train[0]['input']),'source_output':copy.deepcopy(train[0]['output']),'scope':'A procedure consistent with finite examples, not a guarantee for all future inputs. A rejected candidate is not replaced using validation data.'}
