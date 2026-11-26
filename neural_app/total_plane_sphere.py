"""Whole-engine and inverse data mapped into a continuous XYZ domain and working plane."""
import copy,hashlib,json,math,random,time
from .system_flux_sphere import invert_value
from .systemic_outcomes import FAMILIES
from .causal_assessment import compare
from .systemic_library import view as systemic_library_view
PRAYER_ASSESSMENT={
 'guiding_text':'Your will be done; give us today our daily bread; forgive us; lead us not into temptation; deliver us from evil.',
 'principles':[
 {'phrase':'Your will be done','application':'Consider affected beings and evidence rather than treating the engine preference as final authority.'},
 {'phrase':'Daily bread','application':'Prioritise essential needs and preserve services people depend upon.'},
 {'phrase':'Forgive us as we forgive','application':'Prefer repair, correction, restoration and opportunities for redemption.'},
 {'phrase':'Lead us not into temptation','application':'Examine domination, greed, deception and false appearances of benefit.'},
 {'phrase':'Deliver us from evil','application':'Assess harms from both action and inaction; test protective alternatives.'},
 {'phrase':'The power and glory are yours','application':'Retain humility, traceable decisions, permission and accountable review.'}],
 'four_way':['true good','false good','true evil','false evil'],
 'causal_chain':['input provenance','chosen transformation','predicted consequences','affected systems and beings','local test or reviewed action','actual result','repair and learning'],
 'scope':'Spiritual and ethical guidance for concrete action assessment; uncertain consequences remain open questions.'}
class TotalPlaneSphere:
 def __init__(self):
  self.sequence=0;self.latest={};self.rng=random.Random();self.cursor=0;self.next_at=0;self.results=[];self.interval=.1;self.budget=192;self.rate_state={}
  from .knowledge_library import search
  self.causal_library=search("HTTP action effects causal processing traces Windows process",8)
 def step(self,circuit):
  if time.monotonic()<self.next_at:return
  start=time.perf_counter();engine=circuit.experiment_sphere
  resources=circuit.adaptive_rail.view();metrics=resources.get('resource_metrics',{});cpu=metrics.get('cpu_percent');memory=metrics.get('memory_percent')
  pressure=max((cpu if cpu is not None else 70)/100,(memory if memory is not None else 70)/100,metrics.get('gpu_memory_percent',0)/100)
  requested=resources.get('adaptive_interval_seconds',engine.interval)
  self.interval=max(.02,min(2,requested if pressure<.85 else max(.4,requested) if pressure<.95 else 1))
  self.budget=max(24,min(384,int(192*(1.2-pressure))))
  self.rate_state={'selected_interval_seconds':self.interval,'selected_ceiling_hz':1/self.interval,'cpu_percent':cpu,'memory_percent':memory,'gpu_memory_percent':metrics.get('gpu_memory_percent'),'gpu_backend':resources.get('gpu'),'pressure_threshold_percent':85,'high_pressure_percent':95,'point_budget':self.budget,'reason':'high-pressure backoff' if pressure>=.85 else 'available headroom','scope':'Ceiling for eligibility; actual cadence depends on shared worker scheduling and work cost.'}
  frames=[circuit.expression_sphere.latest,circuit.selection_sphere.latest,circuit.selection_sphere.unmodulated,circuit.system_flux_sphere.view(),circuit.system_flux_sphere.inverse_view(),engine.view()]
  candidates=engine.collect(frames,circuit.sources);self.sequence+=1;points=[];results=[]
  for i in range(min(self.budget,len(candidates)*2)):
   original,source,path=candidates[(self.cursor+i//2)%len(candidates)];inverse=bool(i%2);value=invert_value(original,'integer' if type(original)is int else 'variable') if inverse else original
   alternatives=circuit.action_definitions.alternatives(value);choice=alternatives[(self.sequence+i)%len(alternatives)] if alternatives else None
   digest=hashlib.sha256(json.dumps([source,path,value],ensure_ascii=True).encode()).hexdigest();a=int(digest[:8],16)/0xffffffff*math.tau;z=self.rng.uniform(-1,1);radius=self.rng.random()**(1/3);r=math.sqrt(1-z*z)*radius
   plane=i%3==0;point=[r*math.cos(a),0 if plane else z*radius,r*math.sin(a)]
   if inverse:point=[-x for x in point]
   behaviour=['orbit','radial','drift','pulse'][int(digest[8:10],16)%4];vector=[self.rng.uniform(-.12,.12) for _ in range(3)]
   if plane:vector[1]=0
   if behaviour=='radial':vector=[x*.12 for x in point]
   if behaviour=='orbit':vector=[-point[2]*.12,0,point[0]*.12]
   points.append({'id':'total:'+digest[:18]+str(inverse),'point':point,'vector':vector,'birth':time.time(),'lifetime':3,'phase':i%5/4,'selected':plane,'symbol':str(value)[:1] or '·','value_preview':str(value)[:160],'source':source,'path':path,'inverse':inverse,'behaviour':behaviour,'on_plane':plane})
   if choice and plane and len(results)<12:results.append({'source':source,'path':path,'inverse':inverse,'action':choice['action'],'prediction':str(choice['expected'])[:180],'status':'registered contract prediction','reference_experiment_trials':engine.trials,'ethical_status':'local data transformation; downstream consequences require assessment','prayer_application':['retain source truth','preserve original for repair','check actual consequences before wider action']})
  self.cursor=(self.cursor+max(1,len(points)//2))%len(candidates);self.results=results;cost=time.perf_counter()-start;self.interval=max(self.interval,cost*10);self.next_at=time.monotonic()+self.interval;self.rate_state.update(actual_interval_seconds=self.interval,processing_ms=cost*1000);
  self.latest={'rate_control':copy.deepcopy(self.rate_state),'sequence':self.sequence,'updated_at':time.time(),'particles':points,'goal':circuit.goal,'selected_phases':[0,.25,.5,.75,1],'retained_sources':len(circuit.sources),'represented_values':len(candidates),'received_events':circuit.sequence,'counterfactual_assessment':compare({'claimed':'good','evidence':'projected','effects':{},'inaction_effects':{},'correction_effects':{}}),'prayer_assessment':copy.deepcopy(PRAYER_ASSESSMENT),'plane':{'normal':[0,1,0],'equation':'y = 0','domain':'x² + z² ≤ 1','role':'source-linked candidate selection, prediction and experiment results'},'coordinate_map':{'sphere':'x² + y² + z² ≤ 1','resolution':'continuous float coordinates sampled on demand; not an enumeration of infinitely many points','inverse':'(x,y,z) → (-x,-y,-z); source value represented through inverse encoding'},'behaviours':['orbit','radial','drift','pulse'],'behaviour_contracts':circuit.action_definitions.view()['definitions'],'connected_library':systemic_library_view(circuit.goal),'systemic_outcome_knowledge':FAMILIES,'experiments':engine.view().get('experiments',{}),'manifestations':results,'adaptive_resources':circuit.adaptive_rail.view(),'causal_library':self.causal_library,'knowledge':engine.knowledge,'investigation_workspace':circuit.investigations.view() if hasattr(circuit,'investigations') else {},'scope':'All retained engine sources are eligible; bounded rotating samples map the sphere. Supported behaviours and registered actions are selectable. Systemic outcomes are proposals until tested through existing work tools; this is not exhaustive knowledge of every possible world consequence.'}
 def view(self):return copy.deepcopy(self.latest or {'sequence':0,'particles':[]})
