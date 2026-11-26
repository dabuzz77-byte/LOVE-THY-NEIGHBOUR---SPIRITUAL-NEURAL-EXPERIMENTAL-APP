"""Source-linked synthesis cloud with isolated experiment traces."""
import collections,copy,hashlib,json,math,random,time
from .investigation_models import choose,experiment
from .causal_assessment import compare
ELEMENTS=['Hydrogen','Helium','Lithium','Beryllium','Boron','Carbon','Nitrogen','Oxygen','Fluorine','Neon','Sodium','Magnesium','Aluminium','Silicon']
MODELS=['data-preservation','sort-properties','retry-effects','resource-scheduling','exact-arithmetic']
class SynthesisSphere:
 def __init__(self,saved=None):
  self.sequence=0;self.next_at=0;self.next_test=0;self.rng=random.Random();self.history=collections.deque(maxlen=32);self.coverage=copy.deepcopy((saved or {}).get('coverage',{}));self.latest={};self.pending=[];self.cursor=0
 def checkpoint(self):return {'coverage':copy.deepcopy(self.coverage)}
 def step(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  started=time.perf_counter();resources=c.adaptive_rail.view();metrics=resources.get('resource_metrics',{});pressure=max(metrics.get('cpu_percent',70),metrics.get('memory_percent',70),metrics.get('gpu_memory_percent',0))/100
  cadence=max(.05,c.total_plane_sphere.interval,resources.get('adaptive_interval_seconds',.2));budget=max(24,min(384,resources.get('batch_per_stage',168)));test_interval=.5 if pressure<.7 else 3 if pressure<.9 else 8
  policy=getattr(c,'activity_policy',None);activity=policy.for_circuit(c)['multiplier'] if policy else 1.
  test_interval=max(.08,test_interval/activity)
  self.next_at=now+cadence;self.sequence+=1
  frames=[c.expression_sphere.latest,c.selection_sphere.latest,c.selection_sphere.unmodulated,c.system_flux_sphere.view(),c.system_flux_sphere.inverse_view(),c.experiment_sphere.view(),c.total_plane_sphere.view(),c.potential_zero_sphere.view(),c.neural_space.view()]
  values=c.experiment_sphere.collect(frames,c.sources);particles=[];selected_model=None
  if now>=self.next_test:
   relevant=choose(c.goal);selected_model=min(MODELS,key=lambda k:self.coverage.get(k,0)-(1 if k==relevant else 0));value,source,path=values[self.cursor%len(values)];digest=hashlib.sha256(json.dumps([value,source,path],ensure_ascii=True).encode()).hexdigest();result=experiment(selected_model,int(digest[:8],16)^self.sequence);self.coverage[selected_model]=self.coverage.get(selected_model,0)+1
   trace={'id':'synthesis-test:'+str(self.sequence),'source':source,'path':path,'input_hash':digest,'model':selected_model,'result':result,'assessment':compare({'claimed':'good','evidence':'projected','effects':{}}),'scope':'Observed isolated model run; source selects seed, not proof that the source claim or world outcome is true.'};self.history.append(trace);self.next_test=now+test_interval
   self.pending.append({'origin':'synthesis-sphere','target':'all','kind':'stage-output','payload':{'selection_trace':True,'model':selected_model,'trace_id':trace['id'],'observations':result['observations'],'provenance':'isolated-native-experiment','scope':result['scope']}})
  latest=self.history[-1] if self.history else None
  for i in range(min(budget,len(values))):
   value,source,path=values[(self.cursor+i)%len(values)];identity=hashlib.sha256(json.dumps([source,path,value],ensure_ascii=True).encode()).hexdigest();zindex=(self.sequence+i)%14;blend=zindex/13
   # Illustrative radial morph: diffuse exponential-like cloud to multi-shell geometry.
   diffuse=min(1.4,-math.log(max(1e-9,self.rng.random()))*.3);shell=(.25,.6,1.05)[min(2,zindex//5)]+self.rng.gauss(0,.055);r=(1-blend)*diffuse+blend*shell;theta=self.rng.uniform(0,math.tau);vertical=self.rng.uniform(-1,1);horizontal=math.sqrt(max(0,1-vertical*vertical));point=[r*horizontal*math.cos(theta),r*vertical,r*horizontal*math.sin(theta)]
   behaviour=('radial','orbit','drift','pulse')[int(identity[8:10],16)%4];vector=[self.rng.uniform(-.15,.15) for _ in range(3)]
   if behaviour=='orbit':vector=[-point[2]*.15,0,point[0]*.15]
   elif behaviour=='radial':vector=[x*.12 for x in point]
   particles.append({'id':'synthesis:'+identity[:20],'point':point,'vector':vector,'birth':time.time(),'lifetime':self.rng.uniform(.8,3.2),'phase':blend,'selected':bool(latest and source==latest['source']),'symbol':str(value)[:1] or '·','value_preview':str(value)[:160],'source':source,'path':path,'element':ELEMENTS[zindex],'atomic_number':zindex+1,'behaviour':behaviour,'experiment_trace':latest['id'] if latest and source==latest['source'] else None})
  cost=time.perf_counter()-started;self.next_at=max(self.next_at,time.monotonic()+cost*10);self.cursor+=max(1,len(particles));self.latest={'sequence':self.sequence,'updated_at':time.time(),'particles':particles,'goal':c.goal,'received_events':c.sequence,'retained_sources':len(c.sources),'represented_values':len(values),'selected_phases':[0,.25,.5,.75,1],'rate_control':{'selected_interval_seconds':cadence,'experiment_interval_seconds':test_interval,'point_budget':budget,'processing_ms':cost*1000,'measured_pressure':pressure,'gpu_backend':resources.get('gpu'),'meaning':'Resource-aware eligibility; actual cadence also depends on shared worker scheduling.'},'input_spheres':9,'element_spectrum':{'elements':ELEMENTS,'meaning':'Illustrative hydrogen-to-silicon radial morph controlling representation; not solved electron orbitals or measured atomic probability densities.'},'thought_trace':list(self.history),'experiment_coverage':copy.deepcopy(self.coverage),'registered_behaviours':c.action_definitions.view()['definitions'],'systemic_models':c.total_plane_sphere.latest.get('connected_library',{}),'prayer_assessment':c.total_plane_sphere.latest.get('prayer_assessment',{}),'self_selection':{'method':'least-tested supported model with goal relevance; source-derived seeds; independent cloud sampling','controller':c.self_controller.view()},'scope':'All retained engine values and nine sphere representations eligible. Finite rotating samples and bounded experiment families, with unresolved external consequences. Four-way assessment is revisable guidance, not presumed perfected.'}
 def view(self):return copy.deepcopy(self.latest or {'sequence':0,'particles':[]})
