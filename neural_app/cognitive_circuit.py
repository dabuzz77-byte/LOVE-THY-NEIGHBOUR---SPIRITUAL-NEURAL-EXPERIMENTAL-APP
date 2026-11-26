"""Shared typed working state and a learned, action-conditioned local world."""
import collections,copy,hashlib,json,math,random,threading,time
from .native_workbench import CHAIN

class ActionWorld:
 def __init__(self,saved=None):
  saved=saved or {};self.seed=int(saved.get('seed',83017));rng=random.Random(self.seed);self.transitions=[]
  for _ in range(2):
   row=list(range(7));rng.shuffle(row);self.transitions.append(row)
  self.model=dict(saved.get('model',{}));self.state=1;self.target=6;self.sequence=0;self.successes=0;self.predictions=0;self.correct=0;self.last=None
 def plan(self):
  queue=collections.deque([(self.state,[])]);seen={self.state}
  while queue:
   state,path=queue.popleft()
   if state==self.target:return path
   for action in (0,1):
    row=self.model.get(f'{state}/{action}')
    if not row:continue
    dest=int(row['next'])
    if dest not in seen:seen.add(dest);queue.append((dest,path+[action]))
  return []
 def step(self):
  before=self.state;path=self.plan();unknown=[a for a in (0,1) if f'{before}/{a}' not in self.model]
  if unknown:action=unknown[self.sequence%len(unknown)];reason='explore an unobserved state/action pair'
  elif path:action=path[0];reason='follow a learned route toward the goal'
  else:action=self.sequence%2;reason='explore where no learned route reaches the goal'
  key=f'{before}/{action}';prediction=self.model.get(key,{}).get('next');after=self.transitions[action][before]
  if prediction is not None:self.predictions+=1;self.correct+=int(prediction==after)
  self.model[key]={'next':after,'samples':self.model.get(key,{}).get('samples',0)+1};self.state=after;self.sequence+=1;reached=after==self.target;self.successes+=int(reached)
  self.last={'before':before,'action':action,'predicted_next':prediction,'observed_next':after,'prediction_matches':prediction==after if prediction is not None else None,'goal':self.target,'goal_reached':reached,'selection':reason,'planned_actions':path,'learning_reward':int(prediction is None)+int(reached),'scope':'Local seven-state learning environment; no host or network actions'}
  if reached:self.state=(self.sequence%6);self.target=(self.target+3)%7
  return self.last
 def checkpoint(self):return {'seed':self.seed,'model':self.model}
 def view(self):return {'state':self.state,'target':self.target,'steps':self.sequence,'learned_pairs':len(self.model),'possible_pairs':14,'goals_reached':self.successes,'predictions_tested':self.predictions,'prediction_accuracy':self.correct/self.predictions if self.predictions else None,'last':self.last,'branches':self.plan()}

class CognitiveCircuit:
 def __init__(self,bus,reasoner,start=True):
  self.bus=bus;self.r=reasoner;self.lock=threading.RLock();self.halt=threading.Event();self.worker=None;self.wake=threading.Event();self.bus_wakeups=0;self.enabled=True;self.interval=.1;self.selection_buffer={};self.calculation_queue=collections.deque(maxlen=32);self.calculation_results=collections.deque(maxlen=16);self.sources=collections.OrderedDict();self.receipts=collections.deque(maxlen=128);self.sequence=0;self.errors=0;self.duplicates=0;self.goal='';self.last_error=None;self.service_errors={};self.training_worker=None;self.training_health={}
  from .experimental_thought import ExperimentalThought
  from .consequence_thought import ConsequenceThought
  self.experimental_thought=ExperimentalThought();self.consequence_thought=ConsequenceThought()
  from .world_karma import WorldKarma
  self.world_karma=WorldKarma()
  from .correction_projection import CorrectionProjection
  self.correction_projection=CorrectionProjection()
  from .souls_digits import SoulsDigits
  self.souls_digits=SoulsDigits(reasoner.runtime.data)
  from .parallel_thought_streams import ParallelThoughtStreams
  self.parallel_thought_streams=ParallelThoughtStreams()
  from .skill_trainers import SkillTrainers
  self.skill_trainers=SkillTrainers(reasoner.runtime.data)
  from .creative_thought_sphere import CreativeThoughtSphere
  self.creative_thought_sphere=CreativeThoughtSphere()
  from .ternary_layer import TernaryLayer
  self.ternary_layer=TernaryLayer();self.ternary_layer.circuit=self
  from .plane_orientations import PlaneOrientations
  self.plane_orientations=PlaneOrientations()
  from .neural_topology_views import NeuralTopologyViews
  self.neural_topology_views=NeuralTopologyViews()
  from .ethical_projection import EthicalProjection
  self.ethical_projection=EthicalProjection()
  from .interaction_learning import InteractionLearning
  self.interaction_learning=InteractionLearning(reasoner.runtime.data)
  from .mind_improvement import MindImprovement
  self.mind_improvement=MindImprovement(reasoner.runtime.data)
  from .net_learning_stream import NetLearningStream
  self.net_learning_stream=NetLearningStream()
  from .source_study import SourceStudy
  self.source_study=SourceStudy()
  from .principle_research import PrincipleResearch
  self.principle_research=PrincipleResearch()
  from .video_ambience import VideoAmbience
  self.video_ambience=VideoAmbience()
  from .capability_validation import CapabilityValidation
  self.capability_validation=CapabilityValidation(reasoner.runtime.data)
  from .active_thought import ActiveThought
  self.active_thought=ActiveThought()
  from .online_prediction import OnlinePrediction
  self.active_thought.engine.predictor=OnlinePrediction(reasoner.s.get('stage_prediction_memory',{}))
  from .choice_action_study import ChoiceActionStudy
  self.choice_action_study=ChoiceActionStudy()
  from .periodic_study import PeriodicStudy
  self.periodic_study=PeriodicStudy()
  from .world_knowledge import WorldKnowledge
  self.world_knowledge=WorldKnowledge()
  from .thought_cloud import ThoughtCloud
  self.thought_cloud=ThoughtCloud()
  from .cognition_quality import CognitionQuality
  self.cognition_quality=CognitionQuality(reasoner.runtime.data)
  from .self_analysis import SelfAnalysis
  self.self_analysis=SelfAnalysis()
  from .service_metrics import ServiceMetrics
  self.service_metrics=ServiceMetrics()
  self.input_attention={};self.input_consumers={};self.last_priority_input=0
  from .expression_canvas import ExpressionCanvas
  self.expression_canvas=ExpressionCanvas()
  from .potential_selection import PotentialSelection
  self.potential_selection=PotentialSelection()
  from .ethical_refinement import EthicalRefinement
  self.ethical_refinement=EthicalRefinement(reasoner.runtime.data)
  from .finance_industry import FinanceIndustry
  self.finance_industry=FinanceIndustry(reasoner.runtime.data)
  from .tech_industry import TechIndustry
  self.tech_industry=TechIndustry(reasoner.runtime.data)
  from .platform_trainer import PlatformTrainer
  self.platform_trainer=PlatformTrainer()
  from .email_trainer import EmailTrainer
  self.email_trainer=EmailTrainer()
  from .paint_trainer import PaintTrainer
  self.paint_trainer=PaintTrainer(reasoner.runtime.data)
  from .art_trainer import ArtTrainer
  self.art_trainer=ArtTrainer()
  from .game_trainer import GameTrainer
  self.game_trainer=GameTrainer()
  from .music_trainer import MusicTrainer
  self.music_trainer=MusicTrainer()
  from .document_trainer import DocumentTrainer
  self.document_trainer=DocumentTrainer()
  from .software_theory import SoftwareTheory
  self.software_theory=SoftwareTheory(reasoner.runtime.data)
  from .investigations import Investigations
  self.investigations=Investigations(reasoner.runtime.data)
  from .synthesis_sphere import SynthesisSphere
  self.synthesis_sphere=SynthesisSphere(reasoner.s.get('cognitive_circuit',{}).get('synthesis_sphere'))
  from .potential_zero_sphere import PotentialZeroSphere
  self.potential_zero_sphere=PotentialZeroSphere()
  from .neural_activity_space import NeuralActivitySpace
  self.neural_space=NeuralActivitySpace()
  from .system_flux_sphere import SystemFluxSphere
  self.system_flux_sphere=SystemFluxSphere()
  from .experiment_sphere import ExperimentSphere
  from .total_plane_sphere import TotalPlaneSphere
  self.total_plane_sphere=TotalPlaneSphere()
  self.experiment_sphere=ExperimentSphere(reasoner.s.get('cognitive_circuit',{}).get('experiment_sphere'))
  from .ascii_chain import AsciiChain
  self.ascii_chain=AsciiChain(reasoner.runtime.data)
  from .spectrum_logic_sphere import SpectrumLogicSphere
  self.spectrum_logic=SpectrumLogicSphere(reasoner.s.setdefault('spectrum_deliberation',{}),reasoner.controller.save)
  from .intelligence_sphere import IntelligenceSphere
  from .core_modulators import CoreModulators
  self.sphere_modulators=CoreModulators()
  self.expression_sphere=IntelligenceSphere();self.selection_sphere=IntelligenceSphere(self_selecting=True);self.sphere_next=0
  from .generation_selector import GenerationSelector
  from .action_definitions import ActionDefinitions
  self.action_definitions=ActionDefinitions(reasoner.s.get('cognitive_circuit',{}).get('action_definitions'))
  from .teacher_intake import TeacherIntake
  self.teacher_intake=TeacherIntake(reasoner.runtime.data)
  from .deep_decision import DeepDecision
  self.deep_decision=DeepDecision(reasoner.runtime.data)
  from .decision_ledger import DecisionLedger
  from .native_reasoning import NativeReasoning
  self.decision_ledger=DecisionLedger(reasoner.runtime.data);self.action_definitions.ledger=self.decision_ledger
  self.native_reasoning=NativeReasoning(self.action_definitions)
  self.generation_selector=GenerationSelector();self.generation_selector.definitions=self.action_definitions
  from .element_thinking import ElementThinking
  self.element_thinking=ElementThinking(reasoner.s.get('cognitive_circuit',{}).get('element_thinking'))
  self.world=ActionWorld(reasoner.s.get('cognitive_circuit',{}).get('world'));self.last_publish=0
  from .system_shield import SystemShield
  self.system_shield=SystemShield()
  from .thin_inference import ThinInference
  self.thin_inference=ThinInference(reasoner.runtime.data)
  self.thin_inference.skills=self.teacher_intake
  from .model_substrate import ModelSubstrate
  from .whole_mind_study import WholeMindStudy
  self.model_substrate=ModelSubstrate(reasoner.runtime.data);self.whole_mind_study=WholeMindStudy(reasoner.runtime.data)
  def native_result(record):
   work=record.get('work') or {};receipt=work.get('receipt') or {};plan=work.get('plan') or {};code=work.get('code') or {};checks=code.get('checks') or (work.get('coding_result') or {})
   result=self.bus.publish({'target':'all','kind':'stage-output','origin':'native-only-work','payload':{'request_sha256':hashlib.sha256(record['user'].encode()).hexdigest(),'answer_sha256':record.get('answer_sha256'),'status':work.get('status','native-response'),'operation_count':len(receipt.get('steps',[])),'verified_steps':sum(bool(s.get('independent_check')) for s in receipt.get('trace',[])),'inquiry_candidates':(work.get('inquiry') or {}).get('candidate_count'),'inquiry_revision':(work.get('inquiry') or {}).get('revision'),'inquiry_phase':(work.get('inquiry') or {}).get('phase'),'plan_nodes':len(plan.get('trace',[])),'plan_acceptance_verified':plan.get('task_acceptance_verified',False),'code_checks_passed':checks.get('passed'),'code_checks_total':checks.get('total'),'model_calls':0,'stochastic':False,'processing_receipt':True,'provenance':'local native result receipt; message contents remain in conversation storage'}})
   return result['event']['sequence']
  self.whole_mind_study.native_dialogue.on_result=native_result
  from .world_ai import WorldAI
  self.world_ai=WorldAI()
  from .self_controller import SelfController
  self.self_controller=SelfController(self,reasoner.s.get('cognitive_circuit',{}).get('self_controller'))
  from .adaptive_rail import AdaptiveRail
  self.adaptive_rail=AdaptiveRail(self,start=start)
  from .activity_policy import ActivityPolicy
  self.activity_policy=ActivityPolicy(reasoner.runtime.data)
  from .stochastic_structure import StochasticStructure
  self.stochastic_structure=StochasticStructure()
  from .sphere_workspace import SphereWorkspace
  self.sphere_workspace=SphereWorkspace(self);self.choice_action_study.circuit=self
  from .sphere_functions import SphereFunctions
  self.sphere_functions=SphereFunctions(self.r.runtime.data/'sphere-functions.json')
  from .episode_bus import EpisodeBus
  self.episode_bus=EpisodeBus()
  from .self_improvement_engine import SelfImprovementEngine
  self.self_improvement_engine=SelfImprovementEngine(self.r.runtime.data)
  self.self_improvement_engine.circuit=self
  self.whole_mind_study.native_dialogue.work.improvement_engine=self.self_improvement_engine
  if start:self.sphere_workspace.start()
  if start:self.ternary_layer.worker=threading.Thread(target=self.ternary_layer.loop,daemon=True,name='ternary-shadow');self.ternary_layer.worker.start()
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='cognitive-circuit');self.worker.start()
 def capture(self,event):
  self.self_improvement_engine.observe(event)
  self.episode_bus.observe(event)
  self.stochastic_structure.observe(event)
  if event.get('origin')=='cognitive-circuit' or isinstance(event.get('payload'),dict) and event['payload'].get('processing_receipt') is True:self.spectrum_logic.observe_event(event)
  if event.get('origin')=='cognitive-circuit':return
  # Display/scheduler receipts stay on the bus but do not re-trigger their own cognition.
  if isinstance(event.get('payload'),dict) and event['payload'].get('processing_receipt') is True:return
  p=event.get('payload');source=str(event.get('origin','unknown'))[:120];raw=json.dumps(p,sort_keys=True,default=str,ensure_ascii=True);digest=hashlib.sha256(raw.encode()).hexdigest();facts=[];stack=[(p,[])];n=0
  while stack and len(facts)<48 and n<256:
   value,path=stack.pop();n+=1
   if len(path)>6:continue
   if isinstance(value,dict):
    for k,v in list(value.items())[:48]:
     if not any(s in str(k).lower() for s in ('secret','password','token','authorization')):stack.append((v,path+[str(k)]))
   elif isinstance(value,list):stack.extend((v,path+[i]) for i,v in enumerate(value[:16]))
   elif type(value) in (int,float,bool,str) or value is None:
    if type(value) is float and not math.isfinite(value):continue
    facts.append({'path':path,'type':type(value).__name__,'value':value[:512] if isinstance(value,str) else value})
  with self.lock:
   old=self.sources.get(source)
   if old and old['digest']==digest and event.get('kind')!='input':self.duplicates+=1;return
   self.wake.set();self.bus_wakeups+=1;self.experiment_sphere.next_at=0
   self.sequence+=1;self.sources[source]={'id':f'{source}/{event.get("sequence",self.sequence)}','source':source,'parent_event':event.get('sequence'),'time':time.time(),'digest':digest,'facts':facts,'units':p.get('units',{}) if isinstance(p,dict) else {},'status':'captured observation, not automatically a verified fact','provenance':p.get('provenance','bus input') if isinstance(p,dict) else 'bus input','evidence_origin':p.get('evidence_origin','unknown') if isinstance(p,dict) else 'unknown'};self.sources.move_to_end(source)
   if event.get('kind')=='input':
    self.input_attention={'source':source,'parent_event':event.get('sequence',self.sequence),'received':time.time(),'target':event.get('target','all')}
    if time.monotonic()-self.last_priority_input>=.1:
     self.last_priority_input=time.monotonic()
     for name in ('thought_cloud','expression_canvas','potential_selection','ethical_refinement','active_thought','choice_action_study','periodic_study','paint_trainer','email_trainer','platform_trainer'):
      service=getattr(self,name,None)
      if service is not None:service.next_at=0
   while len(self.sources)>128:self.sources.popitem(last=False)
   self.ternary_layer.observe(self.sources[source],event)
   from .symbol_bus import BUS as symbol_bus
   if isinstance(p,dict) and (p.get('stochastic') is True or any(t in source for t in ('ascii','matrix','flux','ambient','cursor'))):symbol_bus.register(source,'every indexed character position; full ASCII alternatives')
   self.neural_space.observe(self.sources[source],event,self.element_thinking.layers)
   self.element_thinking.observe(self.sources[source],event)
   self.generation_selector.observe(self.sources[source],event)
   self.ascii_chain.observe(event,self.sources[source])
   self.spectrum_logic.observe(self.sources[source],event)
   if source.startswith('ascii-chain-complete'):
    self.expression_sphere.observe(self.sources[source],event);self.selection_sphere.observe(self.sources[source],event)
   if event.get('origin')!='section-calculation' and isinstance(p,dict) and isinstance(p.get('calculation'),dict):self.calculation_queue.append(copy.deepcopy(p['calculation']))
 def dispatch(self,event,observers):
  try:self.capture(event)
  except Exception as exc:
   with self.lock:self.errors+=1;self.last_error='capture: '+type(exc).__name__+': '+str(exc)[:180]
  for name,callback in observers:
   started=time.perf_counter();error=None
   try:callback(event)
   except Exception as exc:error=type(exc).__name__+': '+str(exc)[:180]
   with self.lock:
    if error:self.errors+=1;self.last_error=error
    self.receipts.append({'parent_event':event.get('sequence'),'consumer':name,'status':'observer-error' if error else 'observer-returned','cost_ms':(time.perf_counter()-started)*1000,'error':error,'scope':'Callback processing receipt; action outcomes require their own verification'})
 def step(self):
  for _ in range(4):
   with self.lock:request=self.calculation_queue.popleft() if self.calculation_queue else None
   if request is None:break
   try:
    from .section_calculation import run
    result=run(request,self)
   except Exception as exc:result={'error':type(exc).__name__+': '+str(exc)[:200],'request':request}
   with self.lock:self.calculation_results.append(result)
  with self.r.lock:
   goals=self.r.workbench.executive.s['goals'];active=next((g for g in reversed(goals) if g['status']=='running'),None);self.goal=active['goal'] if active else 'Learn action consequences and reusable routes'
  with self.lock:
   result=self.world.step();snapshot=self.world.checkpoint();self.element_thinking.focus(self.goal);layer_snapshot=self.element_thinking.checkpoint();element_thoughts=[{'id':v['id'],'question':v['question'],'attention':v['attention'],'predictions':v['predictions']} for v in sorted(self.element_thinking.layers.values(),key=lambda v:-v['attention'])[:4]]
  with self.r.lock:
   self.r.s['cognitive_circuit']={'synthesis_sphere':self.synthesis_sphere.checkpoint(),'self_controller':self.self_controller.checkpoint(),'experiment_sphere':self.experiment_sphere.checkpoint(),'experiment_lessons':copy.deepcopy(self.experiment_sphere.lessons),'world':snapshot,'element_thinking':layer_snapshot,'action_definitions':self.action_definitions.checkpoint(),'goal':self.goal,'time':time.time()}
   self.r.workbench.executive.put('action-world-outcome',result,'cognitive-circuit')
  with self.r.lock:phase_performance=copy.deepcopy(self.r.s.get('mind_curriculum',{}).get('phase_scores',{}))
  with self.lock:
   self.generation_selector.phase_performance=phase_performance
   chain_packet=self.ascii_chain.step(self.generation_selector,self.goal)
   choices=self.generation_selector.batch(self.element_thinking.layers,self.goal)
   self.selection_buffer.update({c['stage']:c for c in choices})
   if time.monotonic()>=self.sphere_next:
    wave=self.sphere_modulators.sample();self.expression_sphere.step([],self.goal,wave);self.selection_sphere.step(list(self.generation_selector.last.values()),self.goal,wave);self.system_flux_sphere.step([self.expression_sphere.latest,self.selection_sphere.latest,self.selection_sphere.unmodulated],self.generation_selector,self.sources,self.goal);self.sphere_next=time.monotonic()+1
  with self.lock:
   self.experiment_sphere.step([self.expression_sphere.latest,self.selection_sphere.latest,self.selection_sphere.unmodulated,self.system_flux_sphere.view(),self.system_flux_sphere.inverse_view()],self.action_definitions,self.goal,self.sources);self.total_plane_sphere.step(self);self.potential_zero_sphere.step(self);self.neural_space.step(self);self.synthesis_sphere.step(self)
  if chain_packet:
   self.bus.publish({'origin':'ascii-chain-complete/'+chain_packet['root_source'][:70],'target':'all','kind':'stage-output','payload':{**chain_packet,'ascii_chain_trace':True,'provenance':'verified-ascii-chain' if chain_packet['verified'] else 'unverified-ascii-chain','stochastic':False,'bridge_direction':'all'}})
  if time.monotonic()-self.last_publish>=2:
   choices=list(self.selection_buffer.values());self.selection_buffer.clear()
   self.last_publish=time.monotonic();self.bus.publish({'origin':'cognitive-circuit','target':'all','kind':'stage-output','payload':{'goal':self.goal,'experiment_learning':{'trials':self.experiment_sphere.trials,'matched':self.experiment_sphere.passed,'lessons':copy.deepcopy(self.experiment_sphere.lessons)},'learning':result,'element_thoughts':element_thoughts,'generation_choices':[{'stage':c['stage'],'kind':c['kind'],'selection':c['selection']} for c in choices],'selection_trace':True,'text':json.dumps([{'stage':c['stage'],'kind':c['kind'],'value':c['value']} for c in choices],ensure_ascii=True)[:6000],'chain_context':CHAIN,'basis':'User-defined zero-point → cosmological chain → divine-source intention','provenance':'observed-local-learning-environment','stochastic':False,'bridge_direction':'all'}})
   if self.generation_selector.feedback:
    for start in range(0,len(choices)):
     # Keep full phase/Unicode alternatives in selector.last; route the exact chosen value and lineage.
     part=[{k:choice.get(k) for k in ('stage','kind','value','source','path','parent_event','selection','operation','spectrum_depth','state_selection','selected_mask')} for choice in choices[start:start+1]]
     self.bus.publish({'origin':'selected-generation-input','target':'all','kind':'input','payload':{'text':json.dumps([{'stage':c['stage'],'kind':c['kind'],'value':c['value']} for c in part],ensure_ascii=True)[:6000],'selection_trace':True,'provenance':'selected-generated-values','stochastic':False,'choices':part,'bridge_direction':'all'}})
  return result
 def configure(self,b):
  if 'enabled' in b:
   if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
   self.enabled=b['enabled']
  return self.view()
 def view(self):
  from .action_ethics import PRINCIPLES
  with self.lock:return {'learned_action_framework':PRINCIPLES,'self_controller':self.self_controller.view(),'experiment_state':self.experiment_sphere.view(),'investigations':self.investigations.view(),'adaptive_resources':self.adaptive_rail.view(),'ascii_chain':self.ascii_chain.view(),'calculation_results':list(self.calculation_results),'action_definitions':self.action_definitions.view(),'generation_selector':self.generation_selector.view(),'element_thinking':self.element_thinking.view(),'bus_responsiveness':{'priority_input':copy.deepcopy(self.input_attention),'priority_coalescing_seconds':.1,'policy':'Direct input wakes native studies; publisher fetch intervals and action permissions remain independent.','event_wakeups':self.bus_wakeups,'mode':'event-triggered with CPU duty-cycle pacing','all_stage_inputs':'broadcast target all reaches every thinking layer'},'enabled':self.enabled,'goal':self.goal,'captured_events':self.sequence,'source_count':len(self.sources),'duplicate_captures':self.duplicates,'sources':list(self.sources.values())[-12:],'consumer_receipts':list(self.receipts)[-24:],'world':self.world.view(),'errors':self.errors,'last_error':self.last_error,'service_performance':self.service_metrics.view(),'creative_training_worker':copy.deepcopy(self.training_health),'service_errors':copy.deepcopy(self.service_errors),'compute_budget':getattr(self,'compute_budget',{}),'chain_context':CHAIN,'input_bus':'Existing authenticated app bus; every published input passes capture and dispatch','scope':'Shared software observations and local action learning; framework context is separate from measured outcomes'}
 def training_loop(self):
  from .fair_slices import FairSlices
  self.training_scheduler=FairSlices()
  while not self.halt.is_set():
   started=time.perf_counter()
   services=[('world-ai-study',self.world_ai),('deep-decision',self.deep_decision),('decision-ledger',self.decision_ledger),('system-shield',self.system_shield),('model-weight-data',self.model_substrate),('whole-mind-study',self.whole_mind_study),('thin-inference-availability',self.thin_inference),('overall-thought-cloud',self.thought_cloud),('expression-canvas',self.expression_canvas),('potential-selection',self.potential_selection),('ethical-refinement',self.ethical_refinement),('financial-industry',self.finance_industry),('tech-industry',self.tech_industry),('platform-trainer',self.platform_trainer),('email-etiquette-trainer',self.email_trainer),('paint-trainer',self.paint_trainer),('periodic-study',self.periodic_study),('source-study',self.source_study),('principle-research',self.principle_research),('video-ambience',self.video_ambience),('net-learning-stream',self.net_learning_stream),('document-trainer',self.document_trainer),('music-trainer',self.music_trainer),('game-trainer',self.game_trainer),('art-trainer',self.art_trainer),('active-thought',self.active_thought),('native-reasoning-engine',self.r.workbench.reasoning_engine),('capability-validation',self.capability_validation),('emergence-memory',self.ascii_chain.emergence),('spectrum-logic',self.spectrum_logic),('mind-improvement',self.mind_improvement),('self-analysis',self.self_analysis),('cognition-quality',self.cognition_quality)]
   def visit(name,service):
    if self.halt.is_set():return
    if not self.service_metrics.ready('practice/'+name):return
    service_started=time.perf_counter();service_error=None
    try:
     if self.enabled:service.tick(self)
     with self.lock:self.service_errors.pop(name,None)
    except Exception as exc:
     service_error=type(exc).__name__+': '+str(exc)[:180]
     with self.lock:self.errors+=1;self.last_error=name+': '+str(exc)[:180];self.service_errors[name]={'error':str(exc)[:180],'time':time.time()}
    finally:self.service_metrics.record('practice/'+name,(time.perf_counter()-service_started)*1000,service_error)
   settings=self.activity_policy.for_circuit(self)
   self.training_scheduler.run(services,visit,limit=8 if settings['multiplier']>=1 else 3,budget_seconds=.04 if settings['multiplier']>=1 else .015)
   self.training_health={'last_pass_ms':round((time.perf_counter()-started)*1000,3),'mode':'One shared bounded practice/study worker; no additional models'}
   self.training_health['scheduler']=copy.deepcopy(self.training_scheduler.last)
   from .service_metrics import practice_delay
   delay=practice_delay(time.perf_counter()-started,self.r.user_active,self.activity_policy.for_circuit(self)['multiplier'])
   self.training_health['yield_seconds']=round(delay,3)
   self.halt.wait(delay)
 def loop(self):
  if not getattr(self,'improvement_worker',None):
   self.improvement_worker=threading.Thread(target=self.self_improvement_engine.loop,args=(self,),daemon=True,name='self-improvement-development');self.improvement_worker.start()
  if not getattr(self,'sphere_function_worker',None):
   self.sphere_function_worker=threading.Thread(target=self.sphere_functions.loop,args=(self,),daemon=True,name='sphere-function-reasoning');self.sphere_function_worker.start()
  if self.training_worker is None:
   self.training_worker=threading.Thread(target=self.training_loop,daemon=True,name='shared-creative-practice');self.training_worker.start()
  while not self.halt.is_set():
   self.experiment_sphere.activity_multiplier=self.activity_policy.for_circuit(self)['multiplier']
   cpu_start=time.thread_time()
   if self.enabled and not self.r.user_active:
    try:self.step()
    except Exception as exc:self.errors+=1;self.last_error=str(exc)[:200]
   elif self.enabled:
    try:
     from .fair_slices import refresh_root_spheres
     refresh_root_spheres(self)
     with self.lock:self.experiment_sphere.step([self.expression_sphere.latest,self.selection_sphere.latest,self.selection_sphere.unmodulated,self.system_flux_sphere.view(),self.system_flux_sphere.inverse_view()],self.action_definitions,self.goal,self.sources);self.total_plane_sphere.step(self);self.potential_zero_sphere.step(self);self.neural_space.step(self);self.synthesis_sphere.step(self)
    except Exception as exc:self.errors+=1;self.last_error=str(exc)[:200]
   if self.enabled:
    try:
     services=[('investigations',self.investigations.tick),('controller',self.self_controller.tick)]+[(name,lambda service=service:service.tick(self)) for name,service in [('experimental',self.experimental_thought),('consequence',self.consequence_thought),('karma',self.world_karma),('correction',self.correction_projection),('welfare',self.souls_digits),('parallel-streams',self.parallel_thought_streams),('trainers',self.skill_trainers),('creative-sphere',self.creative_thought_sphere),('plane-orientations',self.plane_orientations),('neural-topology',self.neural_topology_views),('ethical-projection',self.ethical_projection),('software-theory',self.software_theory),('world-knowledge',self.world_knowledge)]]
     for name,callback in services:
      if not self.service_metrics.ready('thinking/'+name):continue
      service_started=time.perf_counter();service_error=None
      try:callback();self.service_errors.pop(name,None)
      except Exception as exc:
       service_error=type(exc).__name__+': '+str(exc)[:180]
       self.errors+=1;self.last_error=name+': '+str(exc)[:180];self.service_errors[name]={'error':str(exc)[:180],'time':time.time()}
      finally:self.service_metrics.record('thinking/'+name,(time.perf_counter()-service_started)*1000,service_error)
     from .symbol_bus import BUS as symbol_bus
     symbolic=symbol_bus.tick()
     if symbolic:
      codes=symbolic['groups'][0]['sample_codes'];self.bus.publish({'origin':'symbol-potential','target':'all','kind':'stage-output','payload':{'ascii_codes':[v for v in codes if v<128],'unicode_codes':codes,'text':''.join(map(chr,codes)),'character_encoding':'unicode','symbol_sets':symbolic,'stochastic':True,'predefined_text':False,'contains_model_text':False,'provenance':'generated-symbol-subset'}})
    except Exception as exc:self.errors+=1;self.last_error=str(exc)[:200]
   with self.lock:
    neural_outputs=list(self.experimental_thought.pending)+list(self.neural_space.pending)+list(self.potential_zero_sphere.pending)+list(self.synthesis_sphere.pending);self.experimental_thought.pending.clear();self.synthesis_sphere.pending.clear();self.neural_space.pending.clear();self.potential_zero_sphere.pending.clear()
   neural_outputs.extend(self.stochastic_structure.drain())
   neural_outputs.extend(self.sphere_workspace.drain())
   neural_outputs.extend(self.sphere_functions.drain())
   neural_outputs.extend(self.episode_bus.drain())
   for event in neural_outputs:self.bus.publish(event)
   if self.enabled and not self.whole_mind_study.native_dialogue.shared_reasoning_worker:
    try:self.whole_mind_study.deliberation.advance(2)
    except Exception as exc:self.service_errors['task-deliberation']={'error':str(exc)[:180],'time':time.time()}
   cpu_used=time.thread_time()-cpu_start
   metrics=self.adaptive_rail.view().get('resource_metrics',{})
   pressure=max(metrics.get('cpu_percent',70)/100,metrics.get('memory_percent',70)/100,metrics.get('gpu_memory_percent',0)/100)
   duty=.75 if pressure<.7 else .4 if pressure<.85 else .15 if pressure<.93 else .05
   self.compute_budget={'duty_target':duty,'pressure':pressure,'reason':'Use available headroom; back off under shared-system pressure'}
   self.halt.wait(max(.01,cpu_used/duty-cpu_used))
   self.wake.wait(max(.02,self.interval/self.activity_policy.for_circuit(self)['multiplier']));self.wake.clear()
 def close(self):
  self.net_learning_stream.close();self.deep_decision.flush();self.decision_ledger.flush();self.thin_inference.close();self.model_substrate.close();self.ethical_refinement.flush();self.finance_industry.close();self.tech_industry.close();self.paint_trainer.flush();self.source_study.close();self.principle_research.close();self.video_ambience.close();self.ascii_chain.emergence.close();self.spectrum_logic.close();self.halt.set();self.wake.set();self.ternary_layer.close();self.adaptive_rail.close();self.self_controller.close()
  self.sphere_workspace.close()
  self.sphere_functions.close(self)
  self.self_improvement_engine.wake.set()
  improvement_worker=getattr(self,'improvement_worker',None)
  if improvement_worker and improvement_worker is not threading.current_thread():improvement_worker.join(2)
  if self.worker and self.worker is not threading.current_thread():self.worker.join(5)
  if self.training_worker and self.training_worker is not threading.current_thread():self.training_worker.join(2)
  with self.skill_trainers.lock:self.skill_trainers.save()
  with self.capability_validation.lock:self.capability_validation.save()
