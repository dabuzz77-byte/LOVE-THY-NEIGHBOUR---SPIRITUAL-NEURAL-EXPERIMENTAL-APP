"""Native-first goal attention and bounded experiment selection; sparse local model advice."""
import copy,hashlib,json,re,threading,time,urllib.request
QUESTIONS={'data-preservation':'Does encoding preserve data exactly?','sort-properties':'Does sorting retain duplicate lines?','retry-effects':'Do duplicate network retries repeat effects?','resource-scheduling':'Does resource scheduling back off under pressure?','exact-arithmetic':'Does exact integer arithmetic avoid rounding?'}
class SelfController:
 def __init__(self,circuit,saved=None):
  self.c=circuit;self.lock=threading.RLock();self.next_at=time.monotonic()+5;self.started=time.monotonic();self.last_progress=self.started;self.last_helper=0;self.busy=False;self.closed=False;self.sequence=0;self.last={};self.stats=copy.deepcopy((saved or {}).get('stats',{}));self.cache=copy.deepcopy((saved or {}).get('cache',{}));self.calls=0;self.errors=0;self.next_advice=None;self.learned_tasks=copy.deepcopy((saved or {}).get("learned_tasks",{}))
 def checkpoint(self):
  with self.lock:return {'stats':copy.deepcopy(self.stats),'cache':copy.deepcopy(self.cache),'learned_tasks':copy.deepcopy(self.learned_tasks)}
 def advise(self,goal,choices,key,investigation_id=None):
  try:
   model=self.c.thin_inference.model_for()
   if not model:return
   payload={'model':model,'stream':False,'format':'json','keep_alive':'30s','messages':[{'role':'system','content':'Select a relevant choice ID and return JSON {"choice":"ID"}. For a specific unsupported data transformation you may instead return {"spec":{"examples":[{"input":...,"output":...}],"holdout":[{"input":...,"output":...}],"operations":[...],"max_depth":4}} with 2 distinct examples and 2 different held-out inputs. Allowed operations: strip, lower, reverse, to-lines, join-lines, sort, unique, json-encode, json-decode, increment, double, absolute. A proposed example contract is not verified world knowledge. Do not propose system commands.'},{'role':'user','content':json.dumps({'goal':goal[:500],'choices':choices})}],'options':{'num_ctx':2048,'num_predict':256 if investigation_id else 64,'temperature':0}}
   req=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
   with self.lock:self.calls+=1
   answer=self.c.thin_inference.run(payload,{'retained_sources':len(self.c.sources),'native_experiments':self.sequence,'learned_procedures':len(self.learned_tasks)})
   result=json.loads(answer['message']['content'])
   if investigation_id and result.get('spec'):
    from .native_synthesis import validate
    spec=validate(result['spec'])
    if self.closed:return
    self.c.thin_inference.mark('Proposal schema validated; native experiment pending',{'investigation':investigation_id})
    self.c.investigations.set_spec(investigation_id,spec);row=self.c.investigations.get(investigation_id);row['experiment_spec_origin']='Local-model-proposed example contract; not independently established domain truth';self.c.investigations.save(row)
    with self.lock:self.cache[key]={'investigation':investigation_id,'status':'proposed-contract'}
    return
   choice=result.get('choice')
   if choice not in choices:raise ValueError('Helper returned an unregistered choice')
   self.c.thin_inference.mark('Choice identifier validated; native test pending',{'choice':choice})
   with self.lock:
    if not self.closed:self.cache[key]=choice;self.next_advice=(goal,choice)
    while len(self.cache)>64:self.cache.pop(next(iter(self.cache)))
  except Exception as exc:
   self.c.thin_inference.reject(exc)
   with self.lock:self.errors+=1
  finally:
   with self.lock:self.busy=False
 def tick(self):
  now=time.monotonic()
  if now<self.next_at or self.closed:return
  self.next_at=now+5
  from .investigation_models import choose
  goal=self.c.goal
  from .native_synthesis import question_spec
  task_key=hashlib.sha256(goal.encode()).hexdigest()[:20]
  if question_spec(goal) and task_key not in self.learned_tasks:
   record=self.c.investigations.create(goal);result=self.c.investigations.test(record['id']);self.learned_tasks[task_key]={'question':goal,'investigation':record['id'],'procedure':result.get('learned_procedure')};self.last={'goal':goal,'basis':'native compositional synthesis','result':result['conclusion']};self.last_progress=now;return
  relevant=choose(goal);choices=list(QUESTIONS)
  # Prefer untested hypotheses and task relevance; no model required for these decisions.
  scores={k:(.2 if k==relevant else 0)+1/(1+self.stats.get(k,{}).get('runs',0))-(1 if self.stats.get(k,{}).get('runs',0)>=2 else 0) for k in choices}
  selected=max(choices,key=lambda k:scores[k]);basis='native relevance and coverage'
  with self.lock:
   if self.next_advice and self.next_advice[0]==goal:selected=self.next_advice[1];self.next_advice=None;basis='validated local model choice'
  state=self.stats.get(selected,{})
  if state.get('runs',0)<2 or basis=='validated local model choice':
   record=self.c.investigations.create(QUESTIONS[selected]);result=self.c.investigations.test(record['id']);obs=result['experiments'][-1]['observations'];rejected=sum(o['passed']<o['cases'] for o in obs)
   self.stats[selected]={'runs':state.get('runs',0)+1,'rejected_hypotheses':state.get('rejected_hypotheses',0)+rejected,'last_investigation':record['id']};self.last_progress=now
   if basis=='validated local model choice':self.c.thin_inference.mark('Native test completed',{'test_cases':sum(o['cases'] for o in obs),'passed_cases':sum(o['passed'] for o in obs),'investigation':record['id']})
   with self.lock:self.sequence+=1;self.last={'goal':goal,'selected':selected,'basis':basis,'investigation':record['id'],'result':result['conclusion'],'rejected_hypotheses':rejected,'scope':'Isolated experiment and retained result; not a general task completion claim'}
  elif self.c.investigations.pending_models() and now-self.last_progress>120 and now-self.last_helper>300 and not self.busy and not self.c.r.user_active:
   pending=self.c.investigations.pending_models()[0];question=pending['question'];key=hashlib.sha256(json.dumps([question,choices],sort_keys=True).encode()).hexdigest()
   with self.lock:
    if key in self.cache:self.last={'goal':goal,'selected':self.cache[key],'basis':'cached helper advice; no repeat call','status':'awaiting new evidence'}
    else:
     self.busy=True;self.last_helper=now;threading.Thread(target=self.advise,args=(question,choices,key,pending['id']),daemon=True,name='sparse-llama-advice').start()
  with self.c.lock:
   if relevant:
    for layer in self.c.element_thinking.layers.values():
     if layer['id'] in ('generationthought','recursivemind','expressionsphere'):layer['attention']=max(layer['attention'],scores[selected])
 def view(self):
  with self.lock:return {'sequence':self.sequence,'latest':copy.deepcopy(self.last),'learned_tasks':copy.deepcopy(self.learned_tasks),'native_experiments':copy.deepcopy(self.stats),'helper_calls':self.calls,'helper_errors':self.errors,'helper_busy':self.busy,'cached_advice':len(self.cache),'policy':'Native decisions first; configured lightweight Llama/Qwen route only after 120 seconds without progress, at most once per five minutes; bounded choices, 2048 context and 64 choice-output tokens or 256 for a typed experiment proposal. Model route is selected through the lightweight Llama/Qwen node; generated proposals require native validation.'}
 def close(self):self.closed=True
