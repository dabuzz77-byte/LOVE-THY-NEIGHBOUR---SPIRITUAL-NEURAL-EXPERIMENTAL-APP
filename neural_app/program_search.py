"""Typed, equivalent-state-pruned search of native compositions."""
import collections,json,time,math

def parameter_steps(values,targets):
 """Derive bounded parameters from training examples only, never final-test data."""
 choices=[]
 if all(type(v) in (int,float) for v in values+targets):
  constants=[]
  for a,b in zip(values,targets):
   constants.append(('add',b-a))
   if a:constants.append(('scale',b/a))
  if len(values)>=2:
   pair=next(((i,j) for i in range(len(values)) for j in range(i) if values[i]!=values[j]),None)
   if pair:
    i,j=pair;slope=(targets[i]-targets[j])/(values[i]-values[j]);constants=[('scale',slope),('add',targets[i]-slope*values[i])]+constants
  seen=set()
  for op,n in constants:
   if math.isfinite(n) and abs(n)<=1e100 and (op,n) not in seen:
    choices.append({'op':op,'value':n});seen.add((op,n))
  return choices[:12]
 if all(isinstance(v,list) for v in values):
  choices.append({'op':'sort','descending':True})
  if all(isinstance(v,list) for v in targets):
   for n in sorted({len(v) for v in targets if len(v)<=512}):choices.append({'op':'take','count':n})
  if all(isinstance(t,str) for t in targets):
   choices.extend({'op':'join','separator':s} for s in (' ', ',', ';', '|', ''))
  records=[r for v in values for r in v]
  if records and all(isinstance(r,dict) for r in records):
   keys=set(records[0])
   for r in records[1:]:keys.intersection_update(r)
   choices.extend({'op':'field','name':k} for k in sorted(k for k in keys if isinstance(k,str))[:8])
 return choices

def search(examples,max_depth=6,budget_ms=200,max_expansions=5000):
 from .reasoning_engine import pipeline,transform
 from .workflow_contracts import equivalent,verify
 if not isinstance(examples,list) or not 3<=len(examples)<=16:raise ValueError('Inference needs 3 to 16 examples, with a held-out check')
 if any(not isinstance(e,dict) or 'input' not in e or 'expected' not in e for e in examples):raise ValueError('Each example needs input and expected fields')
 train=examples[:-1];heldout=examples[-1];initial=[e['input'] for e in train];targets=[e['expected'] for e in train]
 if any(equivalent(heldout['input'],e['input']) for e in train):raise ValueError('The held-out input must differ from all training inputs')
 def fingerprint(values):
  raw=json.dumps(values,sort_keys=True,ensure_ascii=True,allow_nan=False)
  if len(raw)>24000:raise ValueError('Candidate states exceed search budget')
  return raw
 queue=collections.deque([(initial,[])]);seen={fingerprint(initial)};started=time.perf_counter();expanded=0
 text_ops=('strip','lower','upper','reverse','lines','words','json','csv');list_ops=('unique','sort','join','numbers','count','sum','mean','median','minimum','maximum','frequencies')
 while queue:
  values,steps=queue.popleft()
  if len(steps)>=max_depth:continue
  choices=[{'op':op} for op in (text_ops if all(isinstance(v,str) for v in values) else list_ops if all(isinstance(v,list) for v in values) else ())]+parameter_steps(values,targets)
  for step in choices:
   expanded+=1
   if expanded>max_expansions or (time.perf_counter()-started)*1000>budget_ms:raise ValueError('No verified composition found within this search budget; supply steps or more informative examples')
   try:
    outputs=[transform(v,step) for v in values]
    if not all(verify(v,step,o) for v,o in zip(values,outputs)):continue
    signature=fingerprint(outputs)
   except (ValueError,TypeError,KeyError,IndexError,OverflowError):continue
   candidate=steps+[step]
   if all(equivalent(o,t) for o,t in zip(outputs,targets)):
    if not equivalent(pipeline(heldout['input'],candidate)['result'],heldout['expected']):raise ValueError('The selected composition failed the held-out example; provide more training examples')
    return candidate,expanded
   if signature not in seen:seen.add(signature);queue.append((outputs,candidate))
 raise ValueError('No composition of the supported primitives passed the training examples')
