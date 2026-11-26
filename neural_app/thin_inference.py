"""Resident native bridge; local models invoked sparsely, one at a time."""
import copy,hashlib,json,threading,time,urllib.request
class ThinInference:
 def __init__(self,data):
  from .native_student import NativeStudent
  self.student=NativeStudent(data)
  from .teacher_intake import TeacherIntake
  self.skills=TeacherIntake(data);self.teaching=False;self.next_teaching=time.monotonic()+90;self.teaching_last={}
  self.path=data/'thin-inference-settings.json';self.lock=threading.RLock();self.gate=threading.Lock();self.route='auto';self.selected_model=None;self.route_revision=0;self.cache={};self.events=[];self.states={'llama':{'calls':0,'status':'available on demand'},'qwen':{'calls':0,'status':'available on demand'}};self.registry_at=0;self.registry=[];self.last={};self.failures=0;self.probing=False;self.next_probe=0;self.closed=False;self.availability={'status':'not yet checked'}
  try:saved=json.loads(self.path.read_text(encoding='utf-8'));self.route=saved.get('route','auto');self.selected_model=saved.get('model')
  except (OSError,ValueError):pass
  if self.route not in ('auto','llama','qwen','off'):self.route='auto'
 def tick(self,c=None):
  self.student.tick(c)
  if self.route!='off' and not self.closed and not self.teaching and time.monotonic()>=self.next_teaching and not (c and c.r.user_active):
   self.next_teaching=time.monotonic()+300;self.teaching=True
   threading.Thread(target=self.teach_next,daemon=True,name='native-skill-inheritance').start()
  if self.closed or self.probing or time.monotonic()<self.next_probe:return
  self.next_probe=time.monotonic()+60;self.probing=True
  threading.Thread(target=self.probe,daemon=True,name='local-inference-availability').start()
 def probe(self):
  try:
   with urllib.request.urlopen('http://127.0.0.1:11434/api/tags',timeout=3) as response:
    raw=response.read(262145)
   if len(raw)>262144:raise ValueError('Local registry response exceeds limit')
   rows=json.loads(raw).get('models',[])
   with self.lock:self.availability={'status':'local Ollama responding','checked':time.time(),'models':[row.get('name') for row in rows[:128]],'model_loaded_by_probe':False}
  except Exception as e:
   with self.lock:self.availability={'status':'local service unavailable','checked':time.time(),'error':str(e)[:160],'model_loaded_by_probe':False}
  finally:self.probing=False
 def close(self):self.closed=True
 def teach_next(self,transport=None):
  """Transfer tested procedures, rather than claiming neural weight copying."""
  try:
   from .teacher_intake import TASKS
   known={r['task'] for r in self.skills.view()['skills']}
   task=next((t for t in TASKS if t not in known),None)
   if task is None:
    self.teaching_last={'status':'Registered lessons retained; no model call needed','skills':len(known)};return self.teaching_last
   payload={'format':{'type':'object','properties':{'operations':{'type':'array','items':{'type':'string','enum':['strip','lower','reverse','to-lines','join-lines','sort','unique','increment','double','absolute']},'minItems':1,'maxItems':4}},'required':['operations'],'additionalProperties':False},'messages':[{'role':'system','content':'Return JSON {"operations":[...]}. Select 1 to 4 pure operations implementing the named task. Operations: strip, lower, reverse, to-lines, join-lines, sort, unique, increment, double, absolute. No commands or explanations.'},{'role':'user','content':task}],'options':{'num_predict':96}}
   answer=self.run(payload,{'retained_skills':len(known),'task':task},transport=transport)
   candidate=json.loads(answer['message']['content'])
   if self.closed:raise RuntimeError('Teaching stopped before retention')
   result=self.skills.submit({'task':task,'operations':candidate.get('operations'),'teacher':self.last.get('model','local teacher')})
   if not result['retained']:
    self.reject('Independent skill fixtures failed');self.teaching_last=result;return result
   value=-(time.time()%997)/7 if task.endswith('number') else '  Fresh βeta\nALPHA\nFresh βeta  '+str(time.time_ns())
   replay=self.skills.run(result['id'],value)
   self.teaching_last={'status':'Native skill retained and independently replayed','lesson':result,'replay':replay,'weights_copied':False,'reuse_requires_model':False}
   self.mark('Native skill retained',self.teaching_last)
   return copy.deepcopy(self.teaching_last)
  except Exception as exc:
   self.reject(exc)
   self.teaching_last={'status':'Teaching deferred; native engine continues','error':str(exc)[:240]};return copy.deepcopy(self.teaching_last)
  finally:self.teaching=False
 def models(self):
  if time.monotonic()-self.registry_at>60 or not self.registry:
   from .assistant_models import installed
   self.registry=installed();self.registry_at=time.monotonic()
  return self.registry
 def model_for(self,rows=None):
  if self.route=='off':return None
  if self.selected_model:
   available=self.models() if rows is None else rows
   return self.selected_model if any(r['name']==self.selected_model for r in available) else None
  rows=self.models() if rows is None else rows;rows=sorted(rows,key=lambda r:(0 if any(t in r['name'].lower() for t in ('uncensored','abliterated','heretic')) else 1,r.get('size_bytes') or float('inf'),0 if 'hauhau' in r['name'].lower() else 1));llama=next((r['name'] for r in rows if 'llama3.2_1b_2025' in r['name'].lower()),None) or next((r['name'] for r in rows if 'llama3.2' in r['name'].lower()),None);qwen=next((r['name'] for r in rows if 'qwen' in r['name'].lower()),None)
  return qwen if self.route=='qwen' else llama if self.route=='llama' else (qwen if self.failures>=2 and qwen else llama or qwen)
 def configure(self,b):
  route=b.get('route')
  if route not in ('auto','llama','qwen','off'):raise ValueError('Choose auto, llama, qwen or off')
  model=b.get('model') or None
  if model and (not isinstance(model,str) or len(model)>200 or not any(r['name']==model for r in self.models())):raise ValueError('Choose an installed model from the registry')
  if model and not any(f in model.casefold() for f in ('llama','qwen')):raise ValueError('This compact bridge supports Llama and Qwen; use Chat & Work for other model families')
  if model and route in ('llama','qwen') and route not in model.casefold():raise ValueError('Selected model does not match the chosen family')
  with self.lock:self.route=route;self.selected_model=model;self.route_revision+=1;self.failures=0;self.cache.clear();self.path.write_text(json.dumps({'route':route,'model':model}),encoding='utf-8')
  return self.view()
 def run(self,payload,before=None,transport=None):
  revision=self.route_revision;model=self.model_for()
  if not model:raise ValueError('No installed Llama 3.2 or Qwen route found')
  family='qwen' if 'qwen' in model.lower() else 'llama';payload=copy.deepcopy(payload);payload.update(model=model,stream=False,format=payload.get('format','json'),keep_alive='30s');payload['options']={**payload.get('options',{}),'num_ctx':2048,'num_predict':min(256,max(16,int(payload.get('options',{}).get('num_predict',64)))),'temperature':0};payload['think']=False
  if len(json.dumps(payload))>14000:raise ValueError('Use a compact structured task for this node')
  key=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
  with self.lock:
   if self.closed:raise RuntimeError('Inference node is closed')
   if key in self.cache:
    self.last={**copy.deepcopy(self.cache[key]),'before':copy.deepcopy(before or {}),'cache_hit':True,'status':'cached proposal returned; native validation required'}
    return copy.deepcopy(self.cache[key]['answer'])
  if not self.gate.acquire(blocking=False):raise RuntimeError('The single inference slot is occupied; native processing continues')
  started=time.monotonic()
  with self.lock:self.states[family]['status']='waiting for shared model slot';self.last={'model':model,'family':family,'status':'queued','before':before or {},'started':time.time()}
  try:
   from .shared_inference import SHARED
   with SHARED.slot('compact native reasoning helper',True,lambda:self.closed):
    if self.closed:raise RuntimeError('Inference node is closed')
    if revision!=self.route_revision:raise RuntimeError('Model route changed while queued; no old-route request was sent')
    with self.lock:self.states[family]['status']='active';self.states[family]['calls']+=1;self.last['status']='active'
    if transport:answer=transport(payload)
    else:
     request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
     with urllib.request.urlopen(request,timeout=60) as response:answer=json.load(response)
   if self.closed:raise RuntimeError('Discarded late model response after shutdown')
   if revision!=self.route_revision:raise RuntimeError('Discarded response from the previous model route')
   parsed=json.loads(answer['message']['content'])
   if not isinstance(parsed,dict):raise ValueError('Model response must be a structured object')
   record={'cache_key':key,'model':model,'family':family,'status':'returned; native validation required','before':before or {},'elapsed_ms':round((time.monotonic()-started)*1000),'prompt_tokens':answer.get('prompt_eval_count'),'output_tokens':answer.get('eval_count'),'answer':answer,'cache_hit':False,'scope':'Structured model proposal; not a verified action or intelligence score.'}
   with self.lock:self.failures=0;self.cache[key]=record;self.last=record;self.states[family]['status']='available on demand';self.events=(self.events+[record])[-12:]
   while len(self.cache)>32:self.cache.pop(next(iter(self.cache)))
   return copy.deepcopy(answer)
  except Exception as e:
   with self.lock:self.failures+=1;self.states[family]['status']='request failed; native processing continues';self.last={**self.last,'status':'failed','error':str(e)[:180]}
   raise
  finally:self.gate.release()
 def reject(self,reason):
  with self.lock:
   self.cache.pop(self.last.get('cache_key'),None);self.failures+=1;self.last={**self.last,'status':'Native validation rejected proposal','validation_error':str(reason)[:160]}
 def mark(self,status,after):
  if status=='Native test completed':self.student.retain(after)
  with self.lock:self.last={**self.last,'status':status,'after':copy.deepcopy(after),'comparison':'Recorded before/after state; independent native results determine usefulness.'}
 def view(self):
  with self.lock:
   last={k:copy.deepcopy(v) for k,v in self.last.items() if k!='answer'}
   models=copy.deepcopy(self.registry)
   if not models:
    models=[{'name':name,'label':name} for name in self.availability.get('models',[]) if isinstance(name,str)]
   return {'inheritance':{'busy':self.teaching,'latest':copy.deepcopy(self.teaching_last),'library':self.skills.view(),'interval_seconds':300,'transfer':'Verified procedures, not model weights'},'student':self.student.view(),'availability':copy.deepcopy(self.availability),'route':self.route,'selected_model':self.selected_model,'route_revision':self.route_revision,'preferred_model':self.model_for(models),'models':models,'registry_scope':'Cached registry only; status reads do not scan disk or contact the model service','nodes':copy.deepcopy(self.states),'busy':self.gate.locked(),'cache_entries':len(self.cache),'latest':last,'recent':[ {k:v for k,v in r.items() if k!='answer'} for r in self.events[-6:]],'policy':'Resident lightweight native bridge, not continuously loaded models. Auto mode prefers Llama 3.2. Explicit Qwen or exact-model selection disables Llama-first selection for this bridge; off disables helper requests. One helper request at a time through the process-wide foreground-priority inference queue, 2048 context, 64 decision tokens or up to 256 for an experiment contract; 30-second model retention. Native learning remains active without a model call.'}
