"""Typed native program synthesis from example contracts. Never eval/exec."""
import copy,hashlib,itertools,json,math,random,time
from collections import deque
OPS=('strip','lower','reverse','to-lines','join-lines','sort','unique','json-encode','json-decode','increment','double','absolute','upper','words','length','negate','sum','minimum','maximum','sort-numbers','unique-numbers')

def bounded(value):
 text=json.dumps(value,ensure_ascii=True,allow_nan=False)
 if len(text)>8192:raise ValueError('Experiment value exceeds 8192 encoded characters')
 if isinstance(value,(list,dict)) and len(value)>128:raise ValueError('Too many elements')
 return value

def apply(op,value):
 bounded(value)
 if op not in OPS:raise ValueError('Unregistered operation')
 if op in ('strip','lower','upper','words','reverse','to-lines','json-decode') and not isinstance(value,str):raise ValueError('Text required')
 if op=='strip':out=value.strip()
 elif op=='lower':out=value.lower()
 elif op=='upper':out=value.upper()
 elif op=='words':out=value.split()
 elif op=='length':
  if not isinstance(value,(str,list,dict)):raise ValueError('Text or collection required')
  out=len(value)
 elif op in ('sum','minimum','maximum','sort-numbers','unique-numbers'):
  if not isinstance(value,list) or not value or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1e100 for v in value):raise ValueError('Nonempty finite numeric list required')
  out=sum(value) if op=='sum' else min(value) if op=='minimum' else max(value) if op=='maximum' else sorted(value) if op=='sort-numbers' else list(dict.fromkeys(value))
 elif op=='reverse':out=value[::-1]
 elif op=='to-lines':out=value.splitlines()
 elif op=='json-decode':out=json.loads(value)
 elif op=='json-encode':out=json.dumps(value,ensure_ascii=True)
 elif op in ('join-lines','sort','unique'):
  if not isinstance(value,list) or not all(isinstance(x,str) for x in value):raise ValueError('Text list required')
  out='\n'.join(value) if op=='join-lines' else sorted(value) if op=='sort' else list(dict.fromkeys(value))
 else:
  if type(value) not in (int,float) or abs(value)>1e100 or not math.isfinite(value):raise ValueError('Bounded finite number required')
  out=value+1 if op=='increment' else value*2 if op=='double' else -value if op=='negate' else abs(value)
 return bounded(out)

def execute(operations,value):
 if not isinstance(operations,list) or len(operations)>4:raise ValueError('Use at most four operations')
 for op in operations:value=apply(op,value)
 return value

def validate(spec):
 if not isinstance(spec,dict):raise ValueError('Provide an example-contract object')
 examples=spec.get('examples',[]);holdout=spec.get('holdout',[]);ops=spec.get('operations',list(OPS))
 if not isinstance(examples,list) or not 2<=len(examples)<=16 or not isinstance(holdout,list) or not 2<=len(holdout)<=16:raise ValueError('Provide 2 to 16 training and held-out pairs each')
 for row in examples+holdout:
  if not isinstance(row,dict) or 'input' not in row or 'output' not in row:raise ValueError('Pairs require input and output')
  bounded(row['input']);bounded(row['output'])
 if not isinstance(ops,list) or not ops or len(ops)>32 or any(op not in OPS for op in ops):raise ValueError('Choose registered operations')
 depth=spec.get('max_depth',4)
 if type(depth)is not int or not 1<=depth<=4:raise ValueError('Depth must be 1 to 4')
 # Prevent literal test leakage between the two sets.
 train={json.dumps(r['input'],sort_keys=True) for r in examples}
 if any(json.dumps(r['input'],sort_keys=True) in train for r in holdout):raise ValueError('Held-out inputs must be distinct from training inputs')
 return {'examples':copy.deepcopy(examples),'holdout':copy.deepcopy(holdout),'operations':list(dict.fromkeys(ops)),'max_depth':depth}

def synthesize(spec):
 spec=validate(spec);start=time.perf_counter();training=spec['examples'];target=[r['output'] for r in training];queue=deque([([], [r['input'] for r in training])]);seen=set();tested=0;solutions=[];counterexamples=[];training_candidates=[]
 while queue and tested<1024 and time.perf_counter()-start<.15:
  program,outputs=queue.popleft();signature=json.dumps(outputs,sort_keys=True,ensure_ascii=True)
  repeated=signature in seen;tested+=1
  if outputs==target and program:
   training_candidates.append(program)
   checks=[]
   for row in spec['holdout']:
    try:actual=execute(program,copy.deepcopy(row['input']));passed=type(actual)==type(row['output']) and actual==row['output']
    except (ValueError,TypeError,OverflowError):actual=None;passed=False
    checks.append({'passed':passed,'input':row['input'],'expected':row['output'],'actual':actual})
   if all(x['passed'] for x in checks):solutions.append({'operations':program,'held_out':checks})
   else:counterexamples.append({'operations':program,'failures':[x for x in checks if not x['passed']]})
  if repeated or len(program)>=spec['max_depth']:continue
  seen.add(signature)
  for op in spec['operations']:
   try:values=[apply(op,copy.deepcopy(v)) for v in outputs]
   except (ValueError,TypeError,OverflowError,RecursionError):continue
   queue.append((program+[op],values))
  if solutions and len(program)>=len(solutions[0]['operations']):break
 winner=min(solutions,key=lambda x:(len(x['operations']),x['operations'])) if solutions else None
 diagnostics=[]
 for case in spec['holdout']:
  predictions=[]
  for program in training_candidates:
   try:predictions.append(json.dumps(execute(program,copy.deepcopy(case['input'])),sort_keys=True,ensure_ascii=True))
   except (ValueError,TypeError,OverflowError):predictions.append('<domain-error>')
  total=max(1,len(predictions));counts={v:predictions.count(v) for v in set(predictions)};entropy=-sum((n/total)*math.log2(n/total) for n in counts.values())
  diagnostics.append({'input':case['input'],'distinct_predictions':len(counts),'disagreement_bits':entropy})
 discriminating=max(diagnostics,key=lambda x:x['disagreement_bits']) if diagnostics else None
 return {'experiment_design':{'training_consistent_candidates':len(training_candidates),'most_discriminating_held_out_case':discriminating,'scope':'Uniform-candidate disagreement within the enumerated hypothesis set, not universal information gain.'},'type':'native-program-synthesis','tested_candidates':tested,'search_exhausted':not queue,'budget_reached':bool(queue) and not solutions,'solution':winner,'counterexamples':counterexamples[:8],'training_cases':len(training),'held_out_cases':len(spec['holdout']),'elapsed_ms':(time.perf_counter()-start)*1000,'scope':'Fits explicit example contracts with registered pure operations. Held-out tests establish this contract only; not unrestricted generalisation.'}

def question_spec(question):
 q=question.lower()
 if 'sort' in q and any(term in q for term in ('remove duplicates','deduplicate','unique lines')):
  data=['b\na\nb','Z\na\nZ\nb','γ\nα\nγ','9\n1\n9\n2'];return {'examples':[{'input':x,'output':'\n'.join(sorted(set(x.splitlines())))} for x in data[:2]],'holdout':[{'input':x,'output':'\n'.join(sorted(set(x.splitlines())))} for x in data[2:]],'operations':['to-lines','sort','unique','join-lines'],'max_depth':4}
 return None
