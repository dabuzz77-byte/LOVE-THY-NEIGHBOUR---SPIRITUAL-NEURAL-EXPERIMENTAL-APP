"""Expandable software taxonomy plus source-linked theories and temporal prediction tests."""
import collections,copy,hashlib,json,math,threading,time
from .experimental_thought import CATALOG,run
REFERENCES=[
 {'title':'LLVM documentation','url':'https://llvm.org/docs/','summary':'Compiler infrastructure, intermediate representations, optimisation and code-generation documentation.'},
 {'title':'SQLite architecture','url':'https://sqlite.org/arch.html','summary':'SQLite compiles SQL into bytecode and executes it in a virtual machine.'},
 {'title':'MDN Web APIs','url':'https://developer.mozilla.org/en-US/docs/Web/API','summary':'Reference entry point for browser-platform interfaces.'},
 {'title':'Linux kernel documentation','url':'https://www.kernel.org/doc/html/latest/','summary':'Kernel APIs, drivers, locking, testing and tracing documentation.'},
 {'title':'Vulkan','url':'https://www.vulkan.org/','summary':'Graphics and compute API resources, tools and platform guidance.'},
 {'title':'TLA+','url':'https://lamport.azurewebsites.net/tla/tla.html','summary':'Mathematical modelling of programs and systems, particularly concurrent and distributed systems.'},
 {'title':'ROS 2 middleware interface','url':'https://design.ros2.org/articles/ros_middleware_interface.html','summary':'Robotics middleware design reference; access availability is reported by retrieval, not assumed.'},
 {'title':'NIST experimental-design selection','url':'https://www.itl.nist.gov/div898/handbook/pri/section3/pri33.htm','summary':'Experimental design is selected according to objectives and the factors being investigated.'},
 {'title':'Thought experiments','url':'https://plato.stanford.edu/entries/thought-experiment/','summary':'Conceptual experiments explore consequences of stated scenarios; their evidential role differs from physical observation.'}]
CATEGORIES=['Operating systems','Kernels and drivers','Firmware','Embedded and real-time systems','Compilers and interpreters','Programming tools','Databases','Storage and filesystems','Networking and protocols','Distributed systems','Cloud and virtualisation','Containers','Web platforms','Desktop applications','Mobile applications','Browser extensions','Security and privacy','Formal verification','Testing and observability','Scientific computing','Simulation and digital twins','AI and machine learning','Robotics and control','Graphics and game engines','Audio and music','Video and media','CAD and engineering design','GIS and environmental systems','Finance and accounting','Healthcare and accessibility','Education and collaboration','Resource and welfare systems']
METHODS=[('controlled comparison','Compare alternatives while holding defined inputs fixed.'),('factorial design','Vary combinations of factors to investigate interactions.'),('sensitivity analysis','Change assumptions or parameters and record outcome changes.'),('temporal prediction','Predict a later observation and score it when that observation arrives.'),('thought experiment','Derive implications within explicitly stated assumptions.'),('simulation','Execute a specified model; validate separately against the world.'),('formal model checking','Search finite states for property violations under the model.'),('software testing','Compare actual outputs with independent contracts.'),('fault injection','Introduce defined faults in an isolated model to test resilience.'),('falsification and counterexample','Seek a result that would contradict the proposed explanation.'),('replication','Repeat an independently specified procedure and compare results.'),('creative exploration','Explore candidate forms without treating aesthetic novelty as factual proof.')]
class SoftwareTheory:
 def __init__(self,data):
  self.path=data/'software-theory-models.json';self.lock=threading.RLock();self.models=collections.OrderedDict();self.sequence=0;self.next_at=0;self.latest={};self.trials=collections.deque(maxlen=24);self.research=None;self.intake=None;self.next_research=0;self.research_cursor=0
  try:self.models.update(json.loads(self.path.read_text(encoding='utf-8')).get('models',{}))
  except (OSError,ValueError):pass
 def experiment(self,model,parameters=None):
  if model not in CATALOG:raise ValueError('Choose a registered local experiment model')
  result=run(model,parameters)
  with self.lock:self.trials.append(result)
  return result
 def update(self,c,question=''):
  if not isinstance(question,str) or len(question)>2000:raise ValueError('Use a question up to 2000 characters')
  with c.lock:layers=c.element_thinking.view()['layers'];source_count=len(c.sources);variable_count=sum(len(r['facts']) for r in c.sources.values());goal=question or c.goal
  theories=[];forecasts=[];seen=set()
  with self.lock:
   for layer in layers:
    refs=[]
    for fact in layer['observations']:
     value=fact['value']
     if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>1e15:continue
     key=json.dumps([layer['source'],fact['path']]);signature=hashlib.sha256(json.dumps([layer['source'],layer['parent_event'],value]).encode()).hexdigest();m=self.models.get(key,{'last':None,'delta':0,'tested':0,'persistence_error':0.,'trend_error':0.,'signature':''})
     if key not in seen and m['signature']!=signature:
      if m['last'] is not None:
       m['tested']+=1;m['persistence_error']+=abs(value-m['last']);m['trend_error']+=abs(value-(m['last']+m['delta']));m['delta']=value-m['last']
      m.update(last=value,signature=signature);self.models[key]=m;self.models.move_to_end(key)
     seen.add(key);method='trend' if m['tested']>=3 and m['trend_error']<m['persistence_error'] else 'persistence';pred=value+(m['delta'] if method=='trend' else 0)
     refs.append({'source':layer['source'],'path':fact['path'],'stage':layer['id'],'method':method,'next_capture_prediction':pred,'tested':m['tested'],'persistence_MAE':m['persistence_error']/m['tested'] if m['tested'] else None,'trend_MAE':m['trend_error']/m['tested'] if m['tested'] else None,'horizon':'next changed capture of this source/path','scope':'Temporal numeric forecast; not a causal conclusion.'})
     if len(refs)>=3:break
    forecasts.extend(refs)
    theories.append({'stage':layer['id'],'question':layer['question'],'kind':'testable stage hypothesis','basis':{'source':layer['source'],'parent_event':layer['parent_event'],'received':layer['received']},'proposal':'Compare persistence and trend predictions for observed numeric paths; inspect changing dependencies before proposing a causal model.','counter_hypothesis':'App scheduling, shared inputs or noise may explain the pattern.','prediction_candidates':refs,'status':'awaiting relevant observations' if not layer['received'] else 'hypothesis; compare with later evidence','design_alternative':{'proposal':'A typed, provenance-preserving event adapter with coalescing and verified feedback for '+layer['title'],'status':'Speculative software design, not an implemented or validated improvement','test':'Compare latency, fidelity, resource use and affected-being consequences against the existing path.'}})
   while len(self.models)>1024:self.models.popitem(last=False)
   self.sequence+=1
   if self.sequence%10==0:
    tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps({'models':dict(self.models)},ensure_ascii=True),encoding='utf-8');tmp.replace(self.path)
  # One registered local calculation per cycle; no generated commands are executed.
  model=list(CATALOG)[self.sequence%len(CATALOG)];trial=self.experiment(model)
  def scene(rows,kind):
   points=[]
   for i,r in enumerate(rows[:192]):
    ident=kind+':'+str(i);h=int(hashlib.sha256(ident.encode()).hexdigest()[:12],16);a=(h%100000)/100000*math.tau;z=1-2*((h>>16)%100000)/100000;radius=math.sqrt(max(0,1-z*z));points.append({'id':ident,'position':[radius*math.cos(a),z,radius*math.sin(a)],'w':((h%200)-100)/100,'shape':'ring' if kind=='prediction' else 'triangle' if kind=='experiment' else 'point','motion':'pulse' if kind=='prediction' else 'orbit','rate':.2+(h%50)/50,'amplitude':.025,'label':str(r.get('stage',r.get('model',kind)))[:24],'source':r.get('stage',r.get('source',kind)),'path':r.get('path',[]),'colour':h%4,'record':r})
   return {'sequence':self.sequence,'points':points,'coverage':{'rendered':len(points),'available_captured_variables':variable_count,'thinking_stages':len(layers),'sources':source_count},'tests':[{'model':trial['model'],'passed':trial['passed']}],'scene_checks':{'finite_coordinates':True},'scope':kind+' view; hypotheses, forecasts and experimental observations remain distinct.'}
  from .creative_thought_sphere import SHAPES,MOTIONS
  from .native_scripts import FORMATS
  capabilities={'registered_actions':c.action_definitions.view().get('definitions',{}),'local_models':list(CATALOG),'graphics_shapes':SHAPES,'graphics_motions':MOTIONS,'script_formats':list(FORMATS),'ternary_states':[-1,0,1],'context':'Captured sphere/generation sources and every registered per-stage observation; not unregistered process state.'}
  record={'sequence':self.sequence,'goal':goal,'categories':[{'id':i,'name':name,'status':'Software taxonomy / discovery topic','design_question':'What useful, reliable and welfare-supporting system could be built in this family?'} for i,name in enumerate(CATEGORIES)],'references':REFERENCES,'experiment_methods':[{'name':a,'meaning':b} for a,b in METHODS],'theories':theories,'predictions':forecasts,'recent_experiments':list(self.trials),'capabilities':capabilities,'coverage':{'stages':len(layers),'sources':source_count,'captured_variables':variable_count,'forecast_models':len(self.models)},'scope':'Expandable software/design library and native hypothesis workbench; not all software knowledge or universal predictive ability. Capability definitions inform planning, not permission to execute.'}
  record['theory_frame']=scene(theories,'theory');record['prediction_frame']=scene(forecasts,'prediction');record['experiment_frame']=scene(list(self.trials),'experiment')
  with self.lock:self.latest=record
  c.bus.publish({'origin':'software-theory','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'theories':len(theories),'predictions':len(forecasts),'tested_forecast_models':sum(m['tested'] for m in self.models.values()),'local_trial_passed':trial['passed'],'provenance':'native-theory-prediction-experiment-workbench','stochastic':False,'predefined_text':True}})
  return self.view()
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+5
  if self.research and time.monotonic()>=self.next_research:
   topic=CATEGORIES[self.research_cursor%len(CATEGORIES)];self.research_cursor+=1;self.research.request(topic+' software architecture testing reliability');self.next_research=time.monotonic()+900
  self.update(c)
 def view(self,frame=None):
  with self.lock:return copy.deepcopy(self.latest.get(frame+'_frame',{}) if frame else self.latest)
