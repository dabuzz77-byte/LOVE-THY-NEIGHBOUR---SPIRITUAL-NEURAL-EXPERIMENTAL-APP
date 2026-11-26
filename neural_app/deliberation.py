"""Persistent, task-directed deliberation over registered pure operations.

Predictions and branch experiments are inspectable computation records, not a
claim of sentience. Nothing in this module executes generated source or tools.
"""
import collections,copy,hashlib,json,math,os,tempfile,threading,time,uuid
from pathlib import Path
from .native_synthesis import execute,validate,bounded,OPS,question_spec

TERMINAL={'verified','unresolved','budget-exhausted','cancelled','needs-input','stalled'}

def fingerprint(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()).hexdigest()

def task_spec(question):
 spec=question_spec(question)
 if spec:return spec
 from .teacher_intake import TASKS
 value=question.strip().lower().rstrip('.?!')
 additional={
  'sum numbers':(['sum'],[([1,2],3),([3,1],4),([-1,1],0),([0],0)]),
  'maximum number':(['maximum'],[([1,2],2),([3,1],3),([-7,-2],-2),([0],0)]),
  'minimum number':(['minimum'],[([1,2],1),([3,1],1),([-7,-2],-7),([0],0)]),
  'sort numbers':(['sort-numbers'],[([2,1],[1,2]),([3,0],[0,3]),([-2,-5],[-5,-2]),([4,4],[4,4])]),
  'uppercase text':(['upper'],[('abc','ABC'),('one','ONE'),('β','Β'),('','')]),
  'count words':(['words','length'],[('one two',2),('one',1),('  α  β  γ ',3),('',0)]),
  'negate number':(['negate'],[(1,-1),(2,-2),(-3,3),(0,0)])}
 if value in additional:
  operations,rows=additional[value]
  return {'examples':[{'input':a,'output':b} for a,b in rows[:2]],'holdout':[{'input':a,'output':b} for a,b in rows[2:]],'operations':operations,'max_depth':4}
 aliases={'reverse text':'reverse-text','trim and lowercase text':'trim-lower-text','lowercase text':'lowercase-text','sort lines':'sorted-lines','sort and deduplicate lines':'sorted-unique-lines','increment a number':'increment-number','double a number':'double-number','absolute value':'absolute-number'}
 name=aliases.get(value,value)
 if name not in TASKS:return None
 rows=TASKS[name]
 return {'examples':[{'input':a,'output':b} for a,b in rows['cases'][:2]],'holdout':[{'input':a,'output':b} for a,b in rows['cases'][2:]],'operations':rows['operations'],'max_depth':4}

class Deliberation:
 def __init__(self,data=None):
  self.lock=threading.RLock();self.path=Path(data)/'task-deliberation.json' if data else None
  self.library=collections.OrderedDict();self.tasks=collections.OrderedDict();self.sequence=0;self.round_robin=0;self.helper_running=False;self.closed=False;self.load_error=None;self.last_save=0
  if self.path and self.path.exists():
   try:
    if self.path.stat().st_size>2_000_000:raise ValueError('Deliberation checkpoint exceeds limit')
    saved=json.loads(self.path.read_text(encoding='utf-8'))
    if not isinstance(saved,dict):raise ValueError('Task checkpoint must be an object')
    for item in saved.get('library',[])[-64:]:
     if isinstance(item,dict) and isinstance(item.get('operations'),list) and len(item['operations'])<=4 and all(op in OPS for op in item['operations']) and isinstance(item.get('contracts'),list) and type(item.get('verified_contracts'))is int and type(item.get('replays'))is int:self.library[fingerprint(item['operations'])]=item
    for row in saved.get('tasks',[])[-8:]:
     if not isinstance(row,dict) or not isinstance(row.get('id'),str):continue
     if any(k not in row for k in ('question','status','helper','constraints','branches','counterexamples','tested','cpu_ms','candidate_limit','cpu_budget_ms','operation_failures','revision','stagnant','best_score','source')):raise ValueError('Incomplete task checkpoint')
     if row.get('spec'):row['spec']=validate(row['spec'])
     if row.get('status') not in TERMINAL:row['status']='running'
     row['frontier']=row.get('frontier',[[]])[:1024];row['seen']=row.get('seen',[])[:4096];row['trace']=row.get('trace',[])[-40:]
     self.tasks[row['id']]=row
    self.sequence=int(saved.get('sequence',0))
   except (OSError,ValueError,TypeError,KeyError) as exc:self.load_error=str(exc)[:200];self.tasks.clear()
 def submit(self,body):
  if not isinstance(body,dict):raise ValueError('Provide a task object')
  question=str(body.get('question','')).strip()
  if not question or len(question)>4000:raise ValueError('Provide a question under 4000 characters')
  spec=body['spec'] if 'spec' in body else task_spec(question)
  spec=validate(spec) if spec is not None else None
  if spec and len(json.dumps(spec,ensure_ascii=True))>32768:raise ValueError('Use a contract under 32 KB')
  limit=body.get('candidate_limit',1024);cpu=body.get('cpu_budget_ms',1500)
  if type(limit)is not int or not 16<=limit<=4096:raise ValueError('Candidate limit must be 16–4096')
  if type(cpu) not in (int,float) or not math.isfinite(cpu) or not 10<=cpu<=5000:raise ValueError('Computation budget must be 10–5000 ms')
  if 'input' in body:bounded(body['input'])
  with self.lock:
   if self.closed:raise ValueError('Deliberation engine is closing')
   ident=uuid.uuid4().hex
   task={'id':ident,'question':question,'spec':spec,'status':'running' if spec else 'needs-input','phase':'observe','created':time.time(),'updated':time.time(),'frontier':[[]],'seen':[],'tested':0,'cpu_ms':0.,'candidate_limit':limit,'cpu_budget_ms':cpu,'branches':[],'trace':[],'constraints':[],'counterexamples':[],'rejected':0,'best_score':-1,'stagnant':0,'solution':None,'result':None,'allow_helper':body.get('allow_helper') is True,'helper':{'status':'not needed','calls':0},'source':str(body.get('source','user task'))[:120],'source_observations':[],'acceptance_reveals':0,'revision':0,'operation_failures':{}}
   if 'input' in body:task['application_input']=copy.deepcopy(body['input'])
   if spec:
    task['constraints']=[{'id':kind+'/'+str(i),'meaning':'Exact type and value match','state':0,'basis':'not tested','input_digest':fingerprint(row['input'])} for kind in ('examples','holdout') for i,row in enumerate(spec[kind])]
   else:task['conclusion']='Needs explicit input/output examples and acceptance checks, or a supported named task. No result was invented.'
   prior=next((t for t in reversed(list(self.tasks.values())) if spec and t['status']=='verified' and t.get('spec')==spec),None)
   if prior:
    task['frontier']=[copy.deepcopy(prior['solution']),[]];task['reused_procedure_from']=prior['id'];task['preferred_programs']=[fingerprint(prior['solution'])]
   if spec:
    transfers=[row for row in self.library.values() if len(row['operations'])<=spec['max_depth'] and all(op in spec['operations'] for op in row['operations'])]
    if transfers:
     programs=[copy.deepcopy(row['operations']) for row in sorted(transfers,key=lambda r:(-r.get('verified_contracts',1),len(r['operations'])))[:8]]
     task['frontier']=programs+task['frontier'];task['preferred_programs']=list(dict.fromkeys([*task.get('preferred_programs',[]),*[fingerprint(p) for p in programs]]));task['transfer_candidates']=len(programs)
   self.tasks[ident]=task
   while len(self.tasks)>8:
    old=next((key for key,t in self.tasks.items() if t['status'] in TERMINAL and key!=ident),None)
    if old is None:del self.tasks[ident];raise ValueError('Eight tasks are active; cancel or finish one first')
    self.tasks.pop(old)
   self._event(task,'observe','Task retained with explicit completion conditions',{'supported':bool(spec)})
   self.save();return self._public(task)
 def _event(self,task,phase,message,data=None):
  if data and len(json.dumps(data,ensure_ascii=True,default=str))>2048:data={'record_preview':json.dumps(data,ensure_ascii=True,default=str)[:768],'truncated_for_display':True}
  self.sequence+=1;task['phase']=phase;task['updated']=time.time()
  task['trace']=(task['trace']+[{'sequence':self.sequence,'time':time.time(),'phase':phase,'summary':message,'data':copy.deepcopy(data or {})}])[-24:]
 def observe(self,rows):
  # Source references inform attention; they never replace acceptance criteria.
  with self.lock:
   for task in self.tasks.values():
    if task['status'] not in TERMINAL:
     task['source_observations']=[{'source':r.get('source'),'digest':r.get('digest'),'parent_event':r.get('parent_event')} for r in rows[-8:]]
 def cancel(self,ident):
  with self.lock:
   task=self.tasks.get(ident)
   if task is None:raise ValueError('Unknown deliberation task')
   if task['status'] not in TERMINAL:task['status']='cancelled';self._event(task,'stop','Cancelled; no host action was performed')
   self.save();return self._public(task)
 def _trial(self,task,program):
  spec=task['spec'];predictions=[];checks=[];train_pass=True;accept_pass=False
  # Branch input is copied; the live task inputs remain unchanged.
  for kind in ('examples','holdout'):
   if kind=='holdout' and not train_pass:break
   for index,row in enumerate(spec[kind]):
    try:actual=execute(program,copy.deepcopy(row['input']));error=None
    except (ValueError,TypeError,OverflowError,RecursionError) as exc:actual=None;error=str(exc)[:140]
    predictions.append({'check':kind+'/'+str(index),'predicted':copy.deepcopy(actual),'error':error})
   # Store the prediction record BEFORE comparing with the expected results.
   self._event(task,'predict','Predicted outputs for copied '+kind+' inputs',{'program':program,'predictions':predictions[-len(spec[kind]):]})
   for index,row in enumerate(spec[kind]):
    prediction=next(p for p in predictions if p['check']==kind+'/'+str(index));actual=prediction['predicted']
    passed=not prediction['error'] and type(actual)==type(row['output']) and actual==row['output']
    check={'id':kind+'/'+str(index),'state':1 if passed else -1,'passed':passed,'expected':copy.deepcopy(row['output']),'actual':actual,'error':prediction['error'],'basis':'registered pure executor compared with supplied acceptance value'}
    checks.append(check)
   if kind=='examples':train_pass=all(c['passed'] for c in checks)
   else:task['acceptance_reveals']+=1;accept_pass=all(c['passed'] for c in checks)
  score=sum(c['passed'] for c in checks)
  branch={'id':fingerprint(program)[:16],'program':program,'predictions':predictions,'checks':checks,'score':score,'verified':accept_pass,'input_state_unchanged':True,'experimental_only':True,'task_revision':task['revision']}
  task['tested']+=1
  if len(json.dumps(branch,ensure_ascii=True))>32768:
   branch={**branch,'predictions':[{'check':p['check'],'predicted_preview':str(p['predicted'])[:256],'error':p['error']} for p in predictions],'checks':[{'id':c['id'],'state':c['state'],'passed':c['passed'],'actual_preview':str(c['actual'])[:256],'expected_preview':str(c['expected'])[:256]} for c in checks],'display_truncated':True}
  task['branches']=(task['branches']+[branch])[-8:]
  latest={c['id']:c for c in checks}
  task['constraints']=[{**c,**latest[c['id']]} if c['id'] in latest else {**c,'state':0,'basis':'not tested on the current branch'} for c in task['constraints']]
  for constraint in task['constraints']:
   if len(json.dumps(constraint,ensure_ascii=True))>2048:
    for field in ('expected','actual'):
     if field in constraint:
      value=constraint.pop(field);constraint[field+'_preview']=str(value)[:256];constraint[field+'_sha256']=fingerprint(value)
    constraint['display_truncated']=True
  self._event(task,'check','Compared predictions with named acceptance checks',{'branch':branch['id'],'passed':score,'tested':len(checks),'total':len(task['constraints'])})
  if score>task['best_score']:task['best_score']=score;task['stagnant']=0
  else:task['stagnant']+=1
  if accept_pass:
   task['status']='verified';task['solution']=copy.deepcopy(program);task['result']={'operations':program,'checks_passed':len(checks),'checks_total':len(task['constraints']),'validation_scope':'Supplied finite example contract. Acceptance cases revealed during revision are not an independent benchmark.'}
   if 'application_input' in task:
    try:task['result']['output']=execute(program,copy.deepcopy(task['application_input']))
    except (ValueError,TypeError,OverflowError) as exc:task['result']['application_error']=str(exc);task['result']['application_verified']=False
    else:task['result']['application_verified']=False;task['result']['application_scope']='Executed learned pure procedure; no separate expected value was provided for this new input.'
   key=fingerprint(program);entry=self.library.setdefault(key,{'operations':copy.deepcopy(program),'contracts':[],'verified_contracts':0,'replays':0})
   contract=fingerprint(spec)
   if contract not in entry['contracts']:entry['contracts']=(entry['contracts']+[contract])[-32:];entry['verified_contracts']+=1
   entry['replays']+=1;entry['updated']=time.time();self.library.move_to_end(key)
   while len(self.library)>64:self.library.popitem(last=False)
   task['result']['transfer_candidates']=task.get('transfer_candidates',0)
   self._event(task,'conclude','All supplied checks passed; retained the shortest discovered passing branch',task['result']);return
  task['rejected']+=1;task['revision']+=1
  failures=[c for c in checks if not c['passed']]
  task['counterexamples']=(task['counterexamples']+[{'program':program,'failures':[{'id':c['id'],'expected_preview':str(c['expected'])[:256],'actual_preview':str(c['actual'])[:256],'error':c['error']} for c in failures[:2]]}])[-8:]
  for op in program:task['operation_failures'][op]=task['operation_failures'].get(op,0)+len(failures)
  self._event(task,'revise','Rejected this branch; retained counterexamples to guide later choices',{'program':program,'failed_checks':[c['id'] for c in failures]})
  # A suffix cannot repair a prefix that already raised in the pure executor.
  # Prune only these impossible-to-extend branches, not merely wrong outputs.
  if len(program)<spec['max_depth'] and not any(p['error'] for p in predictions):
   ops=sorted(spec['operations'],key=lambda op:(task['operation_failures'].get(op,0),spec['operations'].index(op)))
   for op in ops:
    candidate=program+[op]
    if len(task['frontier'])<1024:task['frontier'].append(candidate)
 def advance(self,slice_ms=8):
  start=time.perf_counter();changed=False
  with self.lock:
   if self.closed:return False
   active=[t for t in self.tasks.values() if t['status']=='running']
   if not active:return False
   priority=[t for t in active if t['source']!='bundled demonstration contract'] or active
   task=priority[self.round_robin%len(priority)];self.round_robin+=1
   while task['status']=='running' and (time.perf_counter()-start)*1000<slice_ms:
    if task['tested']>=task['candidate_limit'] or task['cpu_ms']>=task['cpu_budget_ms']:
     task['status']='budget-exhausted';task['conclusion']='Computation budget reached. No conclusion of impossibility follows.';self._event(task,'stop',task['conclusion']);changed=True;break
    if not task['frontier']:
     task['status']='unresolved';task['conclusion']='No passing branch found within the registered operation set and explored depth.';self._event(task,'stop',task['conclusion']);changed=True;break
    if task['stagnant']>=256 and (not task['allow_helper'] or task['helper']['calls']):
     task['status']='stalled';task['conclusion']='No improvement in 256 tested branches. Retained findings; more examples or a different operation set are needed.';self._event(task,'stop',task['conclusion']);changed=True;break
    task['frontier'].sort(key=lambda p:(0 if fingerprint(p) in task.get('preferred_programs',[]) else 1,len(p),sum(task['operation_failures'].get(op,0) for op in p)))
    program=task['frontier'].pop(0);key=fingerprint(program)
    if key in task['seen']:continue
    task['seen'].append(key)
    before=time.perf_counter();self._trial(task,program);task['cpu_ms']+=(time.perf_counter()-before)*1000;changed=True
    if task['stagnant']>=128 and task['allow_helper'] and task['helper']['calls']==0:
     task['status']='awaiting-critique';self._event(task,'critique','Native search stalled; one compact model proposal may be requested');break
   if changed and (task['status'] in TERMINAL or time.monotonic()-self.last_save>5):self.save()
  return changed
 def start_helper(self,node,user_active=False):
  with self.lock:
   if self.closed or self.helper_running or user_active:return
   task=next((t for t in self.tasks.values() if t['allow_helper'] and t['helper']['calls']==0 and t['status'] in ('awaiting-critique','unresolved','budget-exhausted','stalled')),None)
   if task is None or not task.get('spec'):return
   task['helper']={'status':'pending','calls':1};ident=task['id'];self.helper_running=True
   payload={'messages':[{'role':'system','content':'Propose a pure program as JSON {"operations":[...]}. Use only allowed operations, at most four. No commands or other text.'},{'role':'user','content':json.dumps({'examples':task['spec']['examples'],'allowed':task['spec']['operations'],'counterexamples':task['counterexamples'][-2]})}], 'options':{'num_predict':128},'format':{'type':'object','properties':{'operations':{'type':'array','items':{'type':'string','enum':task['spec']['operations']},'maxItems':task['spec']['max_depth']}},'required':['operations'],'additionalProperties':False}}
  def work():
   try:
    result=node.run(payload,{'task':ident,'purpose':'one compact critique'});proposal=json.loads(result['message']['content']);program=proposal.get('operations')
    if not isinstance(program,list) or not 1<=len(program)<=task['spec']['max_depth'] or any(op not in task['spec']['operations'] for op in program):raise ValueError('Helper proposed unsupported operations')
    with self.lock:
     if self.closed or task['status'] in ('cancelled','verified'):return
     if fingerprint(program) in task['seen']:raise ValueError('Helper repeated an already tested branch')
     task['frontier'].insert(0,program);task.setdefault('preferred_programs',[]).append(fingerprint(program));task['candidate_limit']=max(task['candidate_limit'],task['tested']+1);task['cpu_budget_ms']=max(task['cpu_budget_ms'],task['cpu_ms']+50);task['status']='running';task['helper']['status']='proposal awaits native verification';self._event(task,'critique','Received a bounded program proposal; no conclusion accepted',{'program':program});self.save()
   except Exception as exc:
    with self.lock:
     task['helper']['status']='unavailable or rejected';task['helper']['error']=str(exc)[:200]
     if task['status']=='awaiting-critique':task['status']='running'
   finally:
    with self.lock:self.helper_running=False
  threading.Thread(target=work,daemon=True,name='deliberation-compact-critique').start()
 def _public(self,task):
  return copy.deepcopy({k:v for k,v in task.items() if k not in ('frontier','seen','operation_failures')})|{'queued_branches':len(task['frontier']),'scope':'Task-specific bounded pure-operation deliberation. No OS or network action is executed by candidate programs.'}
 def view(self,compact=False):
  with self.lock:
   if compact:
    tasks=[]
    for task in self.tasks.values():
     row={k:copy.deepcopy(task[k]) for k in ('id','question','status','phase','tested','revision','best_score','solution','result')}
     row['constraints']=[{k:c.get(k) for k in ('id','state','basis')} for c in task['constraints']]
     row['trace']=[{k:e[k] for k in ('sequence','phase','summary')} for e in task['trace'][-6:]]
     row['branches']=[{k:b[k] for k in ('id','program','score','verified')} for b in task['branches']]
     tasks.append(row)
    return {'sequence':self.sequence,'tasks':tasks,'model_calls':sum(t['helper']['calls'] for t in self.tasks.values())}
  with self.lock:return {'sequence':self.sequence,'tasks':[self._public(t) for t in self.tasks.values()],'procedure_library':copy.deepcopy(list(self.library.values())),'helper_running':self.helper_running,'load_error':self.load_error,'ternary':{'-1':'a named check failed','0':'not checked or unresolved','1':'a named check passed'},'model_calls':sum(t['helper']['calls'] for t in self.tasks.values()),'policy':'No harmonic or visual score is used as proof of task correctness.'}
 def save(self):
  if not self.path:return
  self.path.parent.mkdir(exist_ok=True,parents=True)
  self.write_json(self.path,{'sequence':self.sequence,'tasks':list(self.tasks.values()),'library':list(self.library.values())});self.last_save=time.monotonic()
 @staticmethod
 def write_json(path,value):
  raw=json.dumps(value,ensure_ascii=True,allow_nan=False).encode()
  if len(raw)>2_000_000:raise ValueError('Deliberation checkpoint exceeds limit')
  descriptor,name=tempfile.mkstemp(prefix='deliberation-',suffix='.tmp',dir=path.parent)
  try:
   with os.fdopen(descriptor,'wb') as output:output.write(raw);output.flush();os.fsync(output.fileno())
   os.replace(name,path)
  finally:
   if os.path.exists(name):os.unlink(name)
 def close(self):
  with self.lock:self.closed=True;self.save()
