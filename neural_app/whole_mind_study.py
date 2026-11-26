"""Whole-app observation, hypothesis, safe trial and model-efficiency review."""
import collections,copy,hashlib,json,statistics,threading,time
from .intelligence_sphere import IntelligenceSphere

class WholeMindStudy:
 def __init__(self,data=None):
  from .deliberation import Deliberation
  from .native_dialogue import NativeDialogue
  self.deliberation=Deliberation(data);self.native_dialogue=NativeDialogue(self.deliberation,data);self.last_goal=None;self.bootstrap=False;self.last_thought_sequence=0;self.last_native_thought_save=0;self.native_thought_dirty=False
  self.lock=threading.RLock();self.next_at=0;self.sequence=0;self.cursor=0;self.geometry=IntelligenceSphere(self_selecting=True);self.frame={};self.review={};self.history=collections.deque(maxlen=24);self.seen=set();self.costs=collections.defaultdict(lambda:collections.deque(maxlen=24));self.predictions={};self.error_scores=collections.Counter()
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  policy=getattr(c,'activity_policy',None);interval=policy.for_circuit(c)['whole_mind_interval_seconds'] if policy else 2
  self.next_at=time.monotonic()+interval
  with c.lock:sources=[copy.deepcopy(r) for r in c.sources.values() if r['source']!='whole-mind-study']
  if sources:
   ordered=sources[self.cursor%len(sources):]+sources[:self.cursor%len(sources)];self.cursor+=32
   for row in ordered[:32]:self.geometry.observe(row,{'payload':{}})
  self.deliberation.observe(sources)
  if not self.bootstrap:
   self.bootstrap=True
   if not self.deliberation.tasks:self.deliberation.submit({'question':'Sort and deduplicate lines','source':'bundled demonstration contract'})
  with c.r.lock:active=next((g for g in reversed(c.r.workbench.executive.s['goals']) if g['status']=='running'),None)
  if active and active['id']!=self.last_goal:
   self.last_goal=active['id'];self.deliberation.submit({'question':active['goal'],'source':'executive goal '+active['id']})
  if not self.native_dialogue.shared_reasoning_worker and not getattr(c.r,'user_active',False):self.deliberation.advance()
  self.deliberation.start_helper(c.thin_inference,getattr(c.r,'user_active',False))
  with self.native_dialogue.lock:
   thought_changed=False
   if not self.native_dialogue.shared_reasoning_worker:
    thought_changed=self.native_dialogue.work.think_step()
    if not getattr(c.r,'user_active',False):thought_changed=self.native_dialogue.work.autonomous_step() or thought_changed
   self.native_thought_dirty=self.native_thought_dirty or thought_changed
   if self.native_thought_dirty and self.native_dialogue.path and time.monotonic()-self.last_native_thought_save>=5:
    self.last_native_thought_save=time.monotonic();self.native_thought_dirty=False
    from .deliberation import Deliberation
    Deliberation.write_json(self.native_dialogue.path,{'messages':self.native_dialogue.messages,'memory':self.native_dialogue.memory,'selected':self.native_dialogue.selected,'work':self.native_dialogue.work.state})
   native_thought=self.native_dialogue.work.thought_status()
  thought=self.deliberation.view(compact=True)
  node=c.thin_inference.view();last=node['latest'];model=last.get('model');latency=last.get('elapsed_ms');prediction_check=None
  identity=last.get('cache_key')
  if model and identity and type(latency) in (float,int) and identity not in self.seen:
   self.seen.add(identity)
   if len(self.seen)>256:self.seen={identity}
   prior=self.predictions.get(model)
   if prior is not None:self.error_scores['tested']+=1;self.error_scores['absolute_ms']+=abs(prior-latency);prediction_check={'predicted_ms':prior,'observed_ms':latency,'absolute_error_ms':abs(prior-latency)}
   self.costs[model].append(latency);self.predictions[model]=statistics.median(self.costs[model])
  skills=c.teacher_intake.view()['skills'];experiment={'status':'waiting for a retained native skill','model_calls':0}
  if skills:
   skill=skills[self.sequence%len(skills)];number=skill['task'].endswith('number');value=-(self.sequence+3)/7 if number else '  Trial '+str(self.sequence)+' β\nALPHA\nALPHA  '
   started=time.perf_counter()
   try:
    result=c.teacher_intake.run(skill['id'],value);experiment={'status':'verified','skill':skill['task'],'result':result,'elapsed_ms':round((time.perf_counter()-started)*1000,4),'model_calls':0}
   except Exception as exc:experiment={'status':'failed','skill':skill['task'],'error':str(exc)[:200],'model_calls':0}
  with c.r.lock:
   goals=[{'id':g['id'],'status':g['status'],'steps':len(g['steps']),'verified':sum(s['status']=='verified' for s in g['steps'])} for g in c.r.workbench.executive.s['goals'][-3:]]
  substrate=c.model_substrate.view();bridge_failures=getattr(getattr(c.r,'selective_bridge',None),'s',{}).get('consecutive_failures',0);direction='qwen-fallback-proposal' if max(c.thin_inference.failures,bridge_failures)>=2 else 'native-reuse-then-small-llama'
  review={'observed_sources':len(sources),'source_cursor':self.cursor,'current_goals':goals,'hypothesis':'A previously verified native procedure can handle a fresh matching task without an LLM call.','experiment':experiment,'model_integration':{'direction':direction,'basis':'Actual retained skills and helper validation/failure records; raw weight samples are observations, not a capability score','retained_skills':len(skills),'last_helper':last,'latency_forecasts_ms':dict(self.predictions),'latest_forecast_check':prediction_check,'forecast_mae_ms':self.error_scores['absolute_ms']/self.error_scores['tested'] if self.error_scores['tested'] else None,'forecast_cases':self.error_scores['tested'],'model_data_sequence':substrate['sequence'],'sampled_tensor':substrate['latest'].get('tensor'),'weights_modified':False},'four_way_review':{'true_good':'Verified useful work with the smallest sufficient resource cost','false_good':'Treating more data, larger prompts or animation as demonstrated understanding','false_evil':'Rejecting a useful local procedure merely because it originated with a model','true_evil':'Causing harm or representing an untested proposal as a verified action'},'source_coverage':'Rotating bounded snapshots of registered captured sources, not every bit of memory','output':'Omnidirectional shared app-bus observation; no instruction from this sphere directly executes host commands'}
  review['deliberation']=thought;review['native_inquiry']=native_thought
  workspace=getattr(c,'sphere_workspace',None)
  if workspace:review['reasoning_workspace']=workspace.view()
  choice={'value':direction,'kind':'model-integration-policy','source':'whole-mind-study','phase_candidates':[{'phase':1.0}],'parallel_selection_groups':{'selected':[0]}}
  frame=self.geometry.step([choice],c.goal)
  task=next((t for t in thought['tasks'] if t['status']=='running'),thought['tasks'][-1] if thought['tasks'] else None)
  if task:
   import math
   for index,check in enumerate(task['constraints']):
    angle=index*2.399963;radius=.55+.15*(check['state']+1)
    frame['particles'].append({'id':'deliberation/'+task['id']+'/'+check['id'],'point':[radius*math.cos(angle),.55*math.sin(angle*.7),radius*math.sin(angle)],'phase':(check['state']+1)/2,'selected':True,'symbol':str(check['state']),'source':'task-deliberation','value_preview':check['id']+' '+check['basis'],'expression_type':'checked-task-constraint','constraint':check,'task_id':task['id'],'task_status':task['status'],'parent_event':thought['sequence']})
  if task:frame['represented_values']+=len(task['constraints']);frame['represented_forms']=list(dict.fromkeys([*frame.get('represented_forms',[]),'checked-task-constraint']))
  if native_thought['inquiries'] or native_thought.get('autonomous_study'):
   import math
   inquiry=native_thought['inquiries'][-1] if native_thought['inquiries'] else native_thought['autonomous_study']
   for index,program in enumerate(inquiry['survivors'][:16]):
    angle=index*2.399963;phase=1.0 if inquiry['candidate_count']==1 else .5
    frame['particles'].append({'id':'inquiry/'+inquiry['name']+'/'+str(index),'point':[.8*math.cos(angle),.8*math.sin(angle),.25*math.sin(index)],'phase':phase,'selected':True,'symbol':'?','source':'native-inquiry','value_preview':' → '.join(program) or 'identity','expression_type':'consistent-hypothesis','hypothesis':program,'inquiry_phase':inquiry['phase'],'selected_question':inquiry['question'],'parent_event':inquiry['sequence']})
   frame['represented_forms']=list(dict.fromkeys([*frame.get('represented_forms',[]),'consistent-hypothesis']))
  frame['deliberation']=thought
  with self.lock:
   self.sequence+=1;frame['sequence']=self.sequence;frame['thought_review']=review;self.frame=frame;self.review=review;self.history.append({'sequence':self.sequence,'experiment':experiment['status'],'direction':direction,'time':time.time()})
  c.bus.publish({'origin':'whole-mind-study','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'direction':direction,'experiment':experiment,'model_data_sequence':substrate['sequence'],'source_count':len(sources),'native_agenda':{k:v for k,v in native_thought.get('agenda',{}).items() if k not in ('question','focus')},'provenance':'whole-app safe thought and experiment review','processing_receipt':True,'stochastic':False,'host_action_executed':False,'deliberation':{'sequence':thought['sequence'],'tasks':[{'id':t['id'],'question':t['question'][:200],'status':t['status'],'tested':t['tested'],'best_score':t['best_score'],'solution':t['solution']} for t in thought['tasks'][-4:]]}}})
 def view(self):
  with self.lock:return {**copy.deepcopy(self.frame),'thought_review':copy.deepcopy(self.review),'recent':list(self.history)}
