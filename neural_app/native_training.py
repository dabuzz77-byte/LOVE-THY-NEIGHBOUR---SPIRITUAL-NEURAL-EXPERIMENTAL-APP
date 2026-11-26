"""Native curricula: programs, command language and isolated work-tool trials."""
import collections,hashlib,json,math,random,tempfile,threading,time
from pathlib import Path
from .native_language import canonical_request
CONCEPTS={'sum':(['a + b','a - b','a * b'],lambda a,b:a+b),'product':(['a * b','a + b','a - b'],lambda a,b:a*b),'remainder':(['a % b','a // b','a ^ b'],lambda a,b:a%b),'bit_xor':(['a ^ b','a & b','a | b'],lambda a,b:a^b),'less_than':(['int(a < b)','int(a > b)','int(a == b)'],lambda a,b:int(a<b)),'hold_flip':(['a ^ b','a | b','a & b'],lambda a,b:a^b),'sum_range':(['sum(range(a + 1))','sum(range(a))','a * a'],lambda a,b:a*(a+1)//2)}
class NativeTrainer:
 def __init__(self,runtime,reasoner,bus,registry,start=True):
  self.runtime=runtime;self.reasoner=reasoner;self.bus=bus;self.registry=list(registry);self.lock=reasoner.lock;self.halt=threading.Event();self.last_seed=bytes(range(16));self.last_operation='';self.last_work=0;self.step_count=0;self.pending_seed_lock=threading.Lock();self.point_counts={};self.point_practice={};self.last_input=0
  with self.lock:
   self.s=reasoner.s.setdefault('training',{'enabled':True,'interval':.75,'kinds':['logic','conversation','work'],'sequence':0,'skills':{},'concepts':{},'recent':[],'focus_points':[],'input_events':0,'model_calls':0,'routing':'all connected; automatic attention','catalog':{'logic':'active native curriculum','conversation':'active native command-grammar curriculum','work':'active isolated workspace curriculum','vision':'adapter not configured','audio':'adapter not configured','general research quality':'task-specific validator required'}});reasoner.s.setdefault('native_grammar',{});
   if self.s.get('trainer_generation',0)<2:self.s['kinds']=list(dict.fromkeys(self.s['kinds']+['coordinator','network']));self.s['trainer_generation']=2
   if self.s.get('media_generation',0)<1:self.s['kinds']=list(dict.fromkeys(self.s['kinds']+['graphics','sound','video']));self.s['media_generation']=1
   if self.s.get('recursive_generation',0)<1:self.s['kinds']=list(dict.fromkeys(self.s['kinds']+['reasoning']));self.s['recursive_generation']=1
   self.s['catalog']['reasoning']='active isolated recursive goal/action/filter/delivery practice; fresh cases'
   from .media_skills import CURRICULA
   self.s['catalog'].update({k:{'status':'active procedural curriculum','lessons':v} for k,v in CURRICULA.items()})
   self.s['catalog'].update({'coordinator':'active native scheduling / verification curriculum','network':'active local HTTP / request-response curriculum'});self.s.setdefault('compiler_checks',True);self.s.setdefault('language_checks',{});self.s.setdefault('retained_lessons',{})
   self.s['catalog'].update({'project work':'workspace inventory, symbols, exact edit previews, file verification and undo','memory':'ranked retrieval across memories, procedures, tasks, files and indexed sources','planning':'explicit dependency chain; previous-result substitution; pause/resume/retry','script repair':'deterministic Python block-colon/indentation and JSON trailing-comma proposals; parser checked','research':'source-grouped indexed excerpts; shared terms are not independent confirmation','benchmarks':'72 fixed holdout component checks; no training updates during evaluation','ethical challenge':'labelled four-way reference cases including false positives and unresolved evidence; not scored as moral accuracy'})
  self.worker=None
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='native-capability-trainers');self.worker.start()
 def submit(self,result,seed):
  with self.pending_seed_lock:self.last_seed=bytes(seed[:16]);self.last_operation=result.get('operation','')
 def observe(self,event):
  if event.get('origin')=='native-trainer':return
  p=event.get('payload');p=p if isinstance(p,dict) else {}
  if event.get('origin')=='flow-backbone' and p.get('source_origin')=='native-trainer':return
  entry=p.get('entry',event.get('target'));entry=entry if entry in self.registry else event.get('origin');entry=entry if entry in self.registry else 'native-trainer'
  with self.pending_seed_lock:
   self.last_input+=1;self.point_counts[entry]=self.point_counts.get(entry,0)+1;self.last_seed=hashlib.sha256(self.last_seed+json.dumps(event,sort_keys=True,default=str).encode()).digest()[:16]
 def configure(self,b):
  with self.lock:
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.s['enabled']=b['enabled']
   if 'compiler_checks' in b:self.s['compiler_checks']=b['compiler_checks'] is True
   if 'interval' in b:
    v=float(b['interval'])
    if not math.isfinite(v):raise ValueError('Interval must be finite')
    self.s['interval']=max(.25,min(30,v))
   if 'kinds' in b:
    if not isinstance(b['kinds'],list) or not b['kinds'] or any(k not in ('logic','conversation','work','coordinator','network','graphics','sound','video','reasoning') for k in b['kinds']):raise ValueError('Choose registered native training curricula')
    self.s['kinds']=list(dict.fromkeys(b['kinds']))
  return self.view()
 def choose(self):
  with self.pending_seed_lock:seed=self.last_seed;counts=dict(self.point_counts)
  with self.lock:
   kinds=self.s['kinds'];total=self.s['sequence'];skills=self.s['skills'];kind=max(kinds,key=lambda k:(1-(skills.get(k,{}).get('validation_passes',0)+1)/(skills.get(k,{}).get('attempts',0)+2))+math.sqrt(math.log(total+2)/(skills.get(k,{}).get('attempts',0)+1))+min(.5,self.s.get('improvement_priorities',{}).get(k,0)))
   ranked=sorted(self.registry,key=lambda p:.5*(1 if counts.get(p) else 0)+1/(1+self.point_practice.get(p,0)),reverse=True);focus=ranked[:8];self.s['focus_points']=focus
   for p in focus:self.point_practice[p]=self.point_practice.get(p,0)+1
  return kind,seed
 def logic_trial(self,seed):
  from .language_formats import recognize,syntax
  from .restricted_test import run_restricted
  rng=random.Random(int.from_bytes(seed,'big')+self.step_count);keys=list(CONCEPTS)
  with self.lock:
   concept=max(keys,key=lambda key:(1-(self.s['concepts'].get(key,{}).get('validation_passes',0)+1)/(self.s['concepts'].get(key,{}).get('attempts',0)+2))+math.sqrt(math.log(self.s['sequence']+2)/(self.s['concepts'].get(key,{}).get('attempts',0)+1)));record=self.s['concepts'].setdefault(concept,{'attempts':0,'arms':{},'retained_template':None});templates,expected=CONCEPTS[concept];rng.shuffle(templates:=list(templates));arms=record['arms']
   for template in templates:arms.setdefault(template,{'attempts':0,'passes':0})
   template=rng.choice(templates) if rng.random()<.2 else max(templates,key=lambda t:(arms[t]['passes']+1)/(arms[t]['attempts']+2)+math.sqrt(math.log(record['attempts']+2)/(arms[t]['attempts']+1)))
  def cases(offset):
   rows=[]
   for i in range(4):
    a=rng.randrange(3+offset,24+offset);b=rng.randrange(2,12)
    if concept=='hold_flip':a=i//2;b=i%2
    if concept=='less_than':a,b=[(3+offset,9+offset),(9+offset,3+offset),(5+offset,5+offset),(7+offset,11+offset)][i]
    source=f'a = {a}\nb = {b}\nanswer = {template}\nprint(answer)\n';parsed=syntax({'language':'python','source':source},self.runtime.data);tested=run_restricted({'language':'python','source':source});actual=tested.get('variables',{}).get('answer');want=str(expected(a,b));rows.append({'input':[a,b],'expected':want,'actual':actual,'passed':parsed.get('passed') is True and tested.get('status')=='complete' and actual==want})
   return rows
  train=cases(0);validation=cases(30);training_ok=all(v['passed'] for v in train);valid=all(v['passed'] for v in validation)
  with self.lock:
   record['attempts']+=1;record['validation_passes']=record.get('validation_passes',0)+int(valid);arm=arms[template];arm['attempts']+=1;arm['passes']+=training_ok
   if arm['passes']>=8 and arm['passes']==arm['attempts'] and valid:record['retained_template']=template
  source=f'a = 7\nb = 3\nanswer = {template}\nprint(answer)\n';recognized=recognize({'language':'python','source':source})
  return {'training_passed':training_ok,'validation_passed':valid,'lesson':concept,'template':template,'source':source,'recognized':recognized['name'],'syntax_checked':True,'execution':'existing restricted Python AST interpreter','training_cases':train,'fresh_validation_cases':validation,'retained':record['retained_template']==template,'scope':'Finite program-template curriculum; fresh validation inputs differ from this trial’s training inputs'}
 def conversation_trial(self,seed):
  if self.step_count%2==0:
   from .native_skills import exercise
   return exercise(seed)
  rng=random.Random(int.from_bytes(seed,'big')+self.step_count);lessons=[('show status','status'),('show my files','list files'),('examine ABCABC','analyze ABCABC'),('list workspace files','list files')];base,expected=rng.choice(lessons);prefix=rng.choice(['please ','could you ','can you ','would you ','kindly ']);question=prefix+base
  with self.lock:aliases=dict(self.reasoner.s['native_grammar'])
  actual=canonical_request(question,aliases);passed=actual==expected
  if not passed:
   with self.lock:self.reasoner.s['native_grammar'][question.lower()]=expected
  fresh='please could you '+base;validation=canonical_request(fresh,aliases)==expected
  return {'training_passed':passed,'validation_passed':validation,'lesson':'intent normalization','input':question,'expected':expected,'actual':actual,'fresh_validation_input':fresh,'scope':'Native supported-command grammar, not a general human-conversation quality score','retained':passed and validation}
 def work_trial(self,seed):
  from .work_tools import WorkTools
  if time.monotonic()-self.last_work<60:
   from .native_language import canonical_request
   commands=['list files','read file training-note.txt','write file training-note.txt\nexample'];passed=all(canonical_request('please '+v)==v for v in commands[:2]);return {'training_passed':passed,'validation_passed':passed,'lesson':'work-plan format check','actual_files_exercised':False,'scope':'Plan normalization; a real isolated file trial is separately paced once a minute','retained':False}
  self.last_work=time.monotonic();base=(self.runtime.data/'native-training-work').resolve();base.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='trial-',dir=base) as directory:
   root=Path(directory).resolve();assert root.is_relative_to(base)
   from types import SimpleNamespace
   tools=WorkTools(SimpleNamespace(data=root));text='native work trial '+seed.hex();tools.write({'path':'note.txt','text':text});first=tools.read({'path':'note.txt'});tools.write({'path':'note.txt','text':text+' verified','expected_sha256':first['sha256']});second=tools.read({'path':'note.txt'});valid=second['text']==text+' verified' and first['sha256']!=second['sha256']
  return {'training_passed':first['text']==text,'validation_passed':valid,'lesson':'isolated write → read → revision → reread','actual_files_exercised':True,'scope':'Temporary training workspace only; user work files unchanged','retained':valid}
 def coordinator_trial(self,seed):
  import heapq
  jobs=[{'id':'background','priority':1,'order':0,'cost':3},{'id':'user','priority':0,'order':1,'cost':2},{'id':'verify','priority':0,'order':2,'cost':1}];heap=[]
  for j in jobs:heapq.heappush(heap,(j['priority'],j['order'],j))
  observed=[];remaining=6
  while heap:
   _,_,job=heapq.heappop(heap)
   if remaining<job['cost']:break
   remaining-=job['cost'];observed.append(job['id'])
  expected=['user','verify','background'];valid=observed==expected and remaining==0
  return {'training_passed':valid,'validation_passed':valid,'lesson':'priority / budget / verification scheduling','expected_order':expected,'actual_order':observed,'retained':valid,'scope':'Native scheduler exercise; system processes and settings unchanged'}
 def network_trial(self,seed):
  import urllib.request,urllib.error
  from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
  if time.monotonic()-getattr(self,'last_network',0)<60:
   from urllib.parse import urlsplit
   valid=urlsplit('https://example.org/path?q=1').scheme=='https' and urlsplit('https://example.org/path?q=1').hostname=='example.org'
   return {'training_passed':valid,'validation_passed':valid,'lesson':'request format / origin / response boundary','live_request':False,'scope':'Protocol plan check; actual local HTTP exchange separately paced once per minute','retained':False}
  self.last_network=time.monotonic();payload={'challenge':seed.hex(),'expected_status':'ok'};raw=json.dumps(payload).encode()
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def do_GET(self):
    if self.path!='/training':self.send_response(404);self.end_headers();return
    self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/training',timeout=3) as response:actual=json.load(response);status=response.status
   valid=status==200 and actual==payload
  finally:server.shutdown();server.server_close()
  return {'training_passed':valid,'validation_passed':valid,'lesson':'actual local HTTP GET → JSON → exact challenge response','live_request':True,'retained':valid,'scope':'Temporary localhost protocol exercise; no third-party account, credentials or remote writes'}
 def language_check(self):
  from .language_formats import recognize,syntax
  names=['json','batch','javascript','powershell','java','csharp'];language=names[(self.s['sequence']//20)%len(names)]
  programs={'json':'{"a":7,"b":3,"operation":"sum","expected":10}','batch':'@echo off\nset /a a=7\nset /a b=3\nset /a answer=a+b\n','javascript':'const a=7,b=3; const answer=a+b;','powershell':'$a=7; $b=3; $answer=$a+$b','java':'public class Check { public static int evaluate(){ int a=7,b=3; return a+b; } }','csharp':'public static class Check { public static int Evaluate(){ int a=7,b=3; return a+b; } }'}
  alias='bat' if language=='batch' else language;source=programs[language]
  try:recognition=recognize({'language':alias,'source':source});result=syntax({'language':alias,'source':source},self.runtime.data);value={'recognized':recognition['name'],'syntax':result,'semantic_execution_verified':False,'scope':'Format / parser / compile curriculum; user programs not executed'}
  except Exception as e:value={'available':False,'error':type(e).__name__+': '+str(e)[:200],'semantic_execution_verified':False}
  with self.lock:self.s['language_checks'][language]=value
 def step(self):
  kind,seed=self.choose();self.step_count+=1
  if self.halt.is_set():return None
  self.reasoner.os_learning.sample()
  if self.s.get('compiler_checks') and self.s['sequence']%20==0:self.language_check()
  if self.halt.is_set():return None
  if self.s['sequence']%100==0:
   from .native_benchmarks import evaluate
   self.s['benchmark']=evaluate()
   from .native_scenario_audit import evaluate_scenarios
   self.s['scenario_benchmark']=evaluate_scenarios(self.runtime.data)
   self.s['improvement_priorities']=self.s['scenario_benchmark']['improvement_priorities']
  try:
   if kind=='reasoning':
    from .recursive_training import trial as recursive_trial
    from .executive_training import trial as executive_trial
    from .mind_training import trial as mind_trial
    if self.step_count%3==0:
     with self.lock:result=mind_trial(seed,self.step_count,self.reasoner.s)
    else:result=executive_trial(seed,self.step_count) if self.step_count%2 else recursive_trial(seed,self.step_count)
   elif kind in ('graphics','sound','video'):
    from .media_skills import trial as media_trial
    result=media_trial(kind,seed,self.step_count)
   elif self.step_count%2==0:
    from .capability_curriculum import trial
    result=trial(kind,seed,self.step_count,self.runtime.data)
   else:result={'logic':self.logic_trial,'conversation':self.conversation_trial,'work':self.work_trial,'coordinator':self.coordinator_trial,'network':self.network_trial}[kind](seed)
  except Exception as e:result={'training_passed':False,'validation_passed':False,'error':type(e).__name__+': '+str(e)[:200]}
  with self.lock:
   self.s['sequence']+=1;score=self.s['skills'].setdefault(kind,{'attempts':0,'training_passes':0,'validation_passes':0,'retained':0});score['attempts']+=1;score['training_passes']+=result['training_passed'];score['validation_passes']+=result['validation_passed'];lessons=self.s['retained_lessons'].setdefault(kind,[])
   if result.get('retained') and result.get('lesson') not in lessons:lessons.append(result['lesson'])
   score['retained']=len(lessons);score['actual_execution_checks']=score.get('actual_execution_checks',0)+int('execution' in result or kind=='coordinator' or result.get('actual_files_exercised',False) or result.get('live_request',False) or result.get('actual_media_checks',False));row={'sequence':self.s['sequence'],'time':time.time(),'kind':kind,**result};self.s['recent']=(self.s['recent']+[row])[-24:];focus=list(self.s['focus_points'])
  summary={'kind':kind,'sequence':row['sequence'],'training_passed':result['training_passed'],'validation_passed':result['validation_passed'],'lesson':result.get('lesson'),'scope':result.get('scope'),'focus_points':focus,'curricula':['command phrasing','generated script formats','multi-step transforms','scheduling','network parsing'],'sphere_io':'omnidirectional registered software bus','ethical_review':{'library':'/api/definition-library','criteria':['actual benefit and harm','false-positive harmful classification','action and inaction','affected people and authority','outcome verification and repair'],'classification':'unresolved until task-specific evidence supports it','bit_rule':'good hold / harmful state propose correction then verify / unresolved hold','universal_certainty':False},'bridge_direction':'all','stochastic':False,'provenance':'observed-training-outcome'}
  self.bus.publish({'target':'all','kind':'stage-output','origin':'native-trainer','payload':summary});return row
 def loop(self):
  while not self.halt.is_set():
   if self.s['enabled'] and not self.reasoner.user_active:
    try:self.step()
    except Exception as e:
     with self.lock:self.s['worker_error']=str(e)[:200]
   busy=self.reasoner.user_active
   queued=sum(t['status'] in ('queued','running') for t in self.reasoner.s['tasks'])
   self.halt.wait(max(self.s['interval'],3. if busy else 2. if queued else .75))
 def summary(self):
  with self.lock:return {'sequence':self.s['sequence'],'enabled':self.s['enabled'],'skills':json.loads(json.dumps(self.s['skills'])),'focus_points':list(self.s['focus_points']),'last':{k:v for k,v in (self.s['recent'][-1] if self.s['recent'] else {}).items() if k in ('kind','lesson','training_passed','validation_passed','time')},'input_events':self.last_input,'all_points_connected':len(self.registry),'benchmark':self.s.get('benchmark'),'curricula':['command phrasing','script generation','multi-step work','scheduler','network protocols','independent component benchmark'],'routing':'all registered points connected; exercise and attention selected from measured skill gaps and source activity'}
 def view(self):
  with self.lock:return json.loads(json.dumps({**self.s,'input_events':self.last_input,'registered_points':self.registry,'model_policy':'native curricula; no Llama training call required'}))
 def close(self):
  self.halt.set()
  worker=getattr(self,'worker',None)
  if worker and worker is not threading.current_thread():worker.join(30)
