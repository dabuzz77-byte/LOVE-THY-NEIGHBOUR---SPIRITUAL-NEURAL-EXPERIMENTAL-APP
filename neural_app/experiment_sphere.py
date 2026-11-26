"""Source-linked cloud exploration, held-out rule discovery and feedback."""
import collections,copy,hashlib,json,math,random,time
from .action_definitions import DEFINITIONS
class ExperimentSphere:
 def __init__(self,saved=None):
  self.sequence=0;self.trials=0;self.passed=0;self.cursor=0;self.next_at=0;self.interval=.1;self.latest={};self.history=collections.deque(maxlen=40);self.knowledge=[];self.query=None;self.lessons={};self.rng=random.Random();self.skills=copy.deepcopy((saved or {}).get('skills',{}));self.forecasts={};self.errors=collections.deque(maxlen=200);self.discovery=collections.deque(maxlen=32);self.seen=collections.OrderedDict();self.novel=0;self.transfers=0;self.rejected=0;self.forecast_scores={'persistence':{'tested':0,'absolute_error':0.},'trend':{'tested':0,'absolute_error':0.}}
 def use_skill(self,name,value):
  skill=self.skills.get(name)
  if not skill or skill['validated_tasks']<3:raise ValueError('Rule needs three validated discovery tasks')
  if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e100:raise ValueError('Provide a finite bounded number')
  operations={'double':lambda x:x*2,'increment':lambda x:x+1,'square':lambda x:x*x,'absolute':abs,'negate':lambda x:-x,'identity':lambda x:x}
  return {'rule':name,'input':value,'output':operations[name](value),'evidence':copy.deepcopy(skill)}
 def checkpoint(self):return {'skills':copy.deepcopy(self.skills)}
 def collect(self,frames,sources):
  candidates=[];seen=set()
  def add(value,source,path):
   if type(value) not in (str,int,float,bool) and value is not None:return
   if isinstance(value,float) and not math.isfinite(value):return
   if isinstance(value,str):value=value[:512]
   key=(source,str(path),json.dumps(value,ensure_ascii=True))
   if key in seen:return
   seen.add(key);candidates.append((value,source,path))
  for source,row in sources.items():
   for fact in row.get('facts',[]):add(fact['value'],source,fact.get('path',[]))
  for i,frame in enumerate(frames):
   for row in frame.get('state_catalog',[]):
    value=row.get('value','')
    if row.get('kind') in ('integer','int'):
     try:value=int(value)
     except (ValueError,TypeError):pass
    add(value,row.get('source','sphere'),['catalog',i])
   for p in frame.get('particles',[]):add(p.get('value_preview',p.get('symbol','')),p.get('source','sphere-'+str(i)),['particle',p.get('id','')])
  return candidates or [('0','initial exploration',[])]
 def discover(self,seed):
  # Controlled synthetic tasks with separate observation and held-out test sets.
  families=[('double',lambda x:x*2),('increment',lambda x:x+1),('square',lambda x:x*x),('absolute',abs),('negate',lambda x:-x),('identity',lambda x:x)]
  name,oracle=families[self.sequence%len(families)];base=int(seed[:8],16)%10000
  xs=[-(base+3),base+7,-(base+13),base+29];train=[(x,oracle(x)) for x in xs[:2]];test=[(x,oracle(x)) for x in xs[2:]]
  surviving=[(n,f) for n,f in families if all(f(x)==y for x,y in train)]
  valid=[n for n,f in surviving if all(f(x)==y for x,y in test)];self.rejected+=len(families)-len(valid);self.transfers+=len(test)
  if len(valid)==1:
   skill=self.skills.setdefault(name,{'rule':name,'validated_tasks':0,'held_out_cases':0});skill['validated_tasks']+=1;skill['held_out_cases']+=len(test)
  self.discovery.append({'question':'Which rule explains these input/output pairs?','task':name,'training':train,'held_out':test,'hypotheses':len(families),'survived_training':[n for n,f in surviving],'validated':valid,'scope':'controlled synthetic rule discovery; not an arbitrary world prediction'})
 def step(self,frames,contracts,goal,sources):
  if time.monotonic()<self.next_at:return
  start=time.perf_counter()
  if self.query!=goal:
   from .knowledge_library import search
   self.knowledge=search(goal,6);self.query=goal
  candidates=self.collect(frames,sources);batch=0;particles=[];new=0
  actions=[k for k in DEFINITIONS if k.startswith('generation/')]+['native/sort','native/unique']
  experiment_start=time.perf_counter();activity=max(.25,min(12.,getattr(self,'activity_multiplier',1.)))
  # Fair traversal with stochastic attention and bounded independent experiment work.
  while batch<min(384,int(96*activity)) and (batch==0 or time.perf_counter()-experiment_start<min(.02,.008*activity)):
   index=self.cursor;self.cursor+=1
   value,source,path=candidates[(index//len(actions))%len(candidates) if self.rng.random()<.7 else self.rng.randrange(len(candidates))];action=actions[index%len(actions)]
   if action in ('native/sort','native/unique') and not isinstance(value,str):continue
   prediction=contracts.predict(action,value)
   if not prediction['predictable']:continue
   key=hashlib.sha256(json.dumps([source,path,value,action],ensure_ascii=True).encode()).hexdigest();fresh=key not in self.seen
   if fresh:self.novel+=1;new+=1
   self.seen[key]=True
   while len(self.seen)>8192:self.seen.popitem(last=False)
   if action=='generation/preserve':actual=copy.deepcopy(value)
   elif action=='generation/encode-json':actual=json.dumps(value,ensure_ascii=True)
   elif action=='generation/increment':actual=value+1
   elif action=='generation/decrement':actual=value-1
   elif action=='generation/reverse':actual=value[::-1]
   elif action=='generation/rotate':actual=''.join(list(value)[1:]+list(value)[:1])
   elif action=='native/sort':actual=sorted(value.splitlines())
   else:actual=list(dict.fromkeys(value.splitlines()))
   matched=type(actual)==type(prediction['expected']) and actual==prediction['expected'];self.trials+=1;self.passed+=int(matched);batch+=1
   lesson=self.lessons.setdefault(action,{'tested':0,'matched':0,'novel_cases':0});lesson['tested']+=1;lesson['matched']+=int(matched);lesson['novel_cases']+=int(fresh)
   self.history.append({'trial':self.trials,'action':action,'source':source,'path':path,'input':str(value)[:160],'predicted':str(prediction['expected'])[:160],'observed':str(actual)[:160],'matched':matched,'novel_in_retained_window':fresh})
   # Isotropic volume samples with a source-derived centre, velocity and life span.
   digest=hashlib.sha256(json.dumps([source,path,value],ensure_ascii=True).encode()).digest();centre=[(digest[k]/255-.5)*.7 for k in range(3)];z=self.rng.uniform(-1,1);a=self.rng.uniform(0,math.tau);r=self.rng.random()**(1/3);q=math.sqrt(1-z*z);point=[centre[0]+r*q*math.cos(a),centre[1]+r*z,centre[2]+r*q*math.sin(a)]
   particles.append({'id':'cloud:'+key[:20],'point':point,'vector':[self.rng.uniform(-.18,.18) for _ in range(3)],'birth':time.time(),'lifetime':self.rng.uniform(.7,3),'phase':self.rng.random(),'selected':fresh or not matched,'symbol':str(actual)[:1] or '·','value_preview':str(actual)[:160],'source':source,'path':path,'expression_type':type(actual).__name__})
  seed=hashlib.sha256(json.dumps(candidates[self.cursor%len(candidates)],ensure_ascii=True).encode()).hexdigest();self.discover(seed)
  # Real chronological forecasts: score the previous prediction only on changed observations.
  for value,source,path in candidates:
   if type(value) not in (int,float) or abs(value)>1e100:continue
   key=source+':'+str(path);old=self.forecasts.get(key)
   if old and value!=old['last']:
    scale=max(1.,abs(value),abs(old['last']));errors={n:abs(value-p)/scale for n,p in old['predicted'].items()}
    for name,error in errors.items():self.forecast_scores[name]['tested']+=1;self.forecast_scores[name]['absolute_error']+=error
    local_scores=old.get('scores',{'persistence':{'tested':0,'absolute_error':0.},'trend':{'tested':0,'absolute_error':0.}})
    for name,error in errors.items():local_scores[name]['tested']+=1;local_scores[name]['absolute_error']+=error
    self.errors.append({'source':source,'path':path,'actual':value,'errors':errors,'best':min(errors,key=errors.get)})
   if old and value==old['last']:continue
   delta=value-old['last'] if old else 0
   self.forecasts[key]={'last':value,'predicted':{'persistence':value,'trend':value+delta},'scores':local_scores if old else {'persistence':{'tested':0,'absolute_error':0.},'trend':{'tested':0,'absolute_error':0.}}}
   if len(self.forecasts)>1024:self.forecasts.pop(next(iter(self.forecasts)))
  cost=time.perf_counter()-start;novelty=new/max(batch,1);self.interval=max(.025,min(8,max(cost*20,.08 if novelty>.25 else .4)/activity));self.next_at=time.monotonic()+self.interval;self.sequence+=1
  self.latest={'sequence':self.sequence,'particles':particles or copy.deepcopy(self.latest.get('particles',[])),'updated_at':time.time(),'goal':goal,'input_layers':['original','selected','unmodulated','combined','inverse-combined'],'received_events':sum(f.get('received_events',0) for f in frames),'retained_sources':len(sources),'represented_values':len(candidates),'selected_phases':[0,.25,.5,.75,1],'experiments':{'total':self.trials,'matched':self.passed,'batch':batch,'self_selected_interval_seconds':self.interval,'batch_cost_ms':cost*1000,'lessons':copy.deepcopy(self.lessons),'recent':list(self.history)[-8:],'novel_cases_in_window':self.novel,'held_out_cases':self.transfers,'rejected_hypotheses':self.rejected,'reusable_rules':copy.deepcopy(self.skills),'discoveries':list(self.discovery)[-3:],'source_forecast_models':{k:{'scores':copy.deepcopy(v.get('scores',{})),'preferred':min(v.get('scores',{'persistence':{}}),key=lambda n:v['scores'][n]['absolute_error']/max(1,v['scores'][n]['tested']))} for k,v in list(self.forecasts.items())[-12:]},'forecast_models':copy.deepcopy(self.forecast_scores),'forecast_error_units':'absolute error divided by max(1, |actual|, |previous|); source-specific observations retained','preferred_forecast':min(self.forecast_scores,key=lambda n:self.forecast_scores[n]['absolute_error']/max(1,self.forecast_scores[n]['tested'])),'prediction_errors':list(self.errors)[-12:],'next_question':'Which competing rule survives a fresh input and improves a real task?','cloud':{'sampling':'isotropic volume; source-derived centres; stochastic vectors and lifetimes','candidate_values':len(candidates),'coverage':'All retained scalar facts and sphere catalogs/particle values; rotating bounded batches, not complete process memory'}},'knowledge':self.knowledge,'scope':'Isolated contract tests, controlled rule discovery and chronological numeric forecasts. Captured claims retain provenance. Host actions require existing reviewed execution; no generated code runs in this loop.'}
 def view(self):return copy.deepcopy(self.latest or {'sequence':0,'particles':[]})
