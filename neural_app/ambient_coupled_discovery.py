"""Controlled two-input power-law identification in reference simulations."""
import hashlib,math,random
from .ambient_physics_discovery import EXPONENTS
POWERS=(0.,)+EXPONENTS

def predict(model,point):return model['coefficient']*point[0]**model['powers'][0]*point[1]**model['powers'][1]

def rank_experiments(models,probes,costs=None):
 """Uniform hypothesis-prior information gain; no observation calls."""
 ranked=[]
 for point in probes:
  cost=(costs or {}).get(tuple(point),1.)
  if type(cost) not in (int,float) or not math.isfinite(cost) or cost<=0:raise ValueError('Positive finite experiment cost required')
  groups={}
  for model in models:
   key=round(math.log(predict(model,point)),7);groups[key]=groups.get(key,0)+1
  n=len(models)
  gain=-sum((count/n)*math.log2(count/n) for count in groups.values()) if n else 0.
  ranked.append({'inputs':tuple(point),'cost':cost,'expected_information_bits':gain,'information_per_cost':gain/cost})
 return sorted(ranked,key=lambda r:r['information_per_cost'],reverse=True)

def discover(oracle,initial,probes,validation,tolerance=1e-8,max_probes=4,experiment_budget=4.,probe_costs=None):
 if type(experiment_budget) not in (int,float) or not math.isfinite(experiment_budget) or experiment_budget<0:return {'status':'invalid-budget'}
 spent=0.;selection=[]
 points=[initial]+probes+validation
 if any(not isinstance(p,(list,tuple)) or len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or not 1e-6<=v<=1e6 for v in p) for p in points):return {'status':'invalid-input'}
 initial=tuple(initial);probes=[tuple(p) for p in probes];validation=[tuple(p) for p in validation]
 if len(validation)<4 or len(set(validation))!=len(validation) or set(validation)&set([initial]+probes):return {'status':'invalid-split'}
 if any(sum(a!=b for a,b in zip(p,initial))!=1 for p in probes):return {'status':'uncontrolled-probe'}
 value=oracle(initial)
 if not math.isfinite(value) or not 0<value<1e100:return {'status':'unsupported-observation'}
 models=[{'coefficient':value/(initial[0]**p*initial[1]**q),'powers':[p,q]} for p in POWERS for q in POWERS];observations=[{'inputs':initial,'output':value}];trace=[]
 for _ in range(max(0,min(8,max_probes))):
  if len(models)<=1 or not probes:break
  def spread(point):
   values=[math.log(predict(m,point)) for m in models];return max(values)-min(values)
  ranked=rank_experiments(models,probes,probe_costs)
  affordable=[r for r in ranked if r['cost']<=experiment_budget-spent+1e-12 and r['expected_information_bits']>1e-10]
  if not affordable:break
  choice=affordable[0];selection.append({'selected':choice,'alternatives':ranked[:8],'prior':'uniform over current finite hypotheses'})
  point=choice['inputs'];spent+=choice['cost'];disagreement=spread(point);probes.remove(point);before=len(models);observed=oracle(point)
  if not math.isfinite(observed) or not 0<observed<1e100:return {'status':'unsupported-observation'}
  models=[m for m in models if abs(predict(m,point)-observed)<=tolerance*max(1.,abs(observed))]
  trace.append({'inputs':point,'comparison_anchor':initial,'changed_variable':next(i for i in range(2) if point[i]!=initial[i]),'hypotheses_before':before,'hypotheses_after':len(models),'log_prediction_spread':disagreement});observations.append({'inputs':point,'output':observed})
  if not models:break
 result={'experiment_selection':selection,'probe_budget':experiment_budget,'probe_cost_spent':spent,'budget_scope':'controlled probes only; initial and held-out observations separately required','observations':observations,'controlled_probes':trace,'remaining_models':len(models),'validation_used_for_selection':False}
 if len(models)!=1:return {**result,'status':'no-supported-model' if not models else 'ambiguous'}
 model=models[0];checks=[]
 for point in validation:
  observed=oracle(point);estimate=predict(model,point);error=abs(estimate-observed)/max(1.,abs(observed));checks.append({'inputs':point,'predicted':estimate,'observed':observed,'relative_error':error,'passed':math.isfinite(error) and error<=tolerance})
 return {**result,'status':'validated-model' if all(c['passed'] for c in checks) else 'counterexample-found','model':model,'heldout_checks':checks,'formula':'y = '+format(model['coefficient'],'.8g')+' Ã— x^('+str(model['powers'][0])+') Ã— z^('+str(model['powers'][1])+')'}

class CoupledDiscovery:
 def __init__(self):
  from .ambient_noisy_learning import NoisyMemory
  self.noisy_memory=NoisyMemory()
  self.challenge_history=[];self.last_challenge=None
  self.models={};self.visits={};self.tasks=0;self.verified=0;self.transfers=0;self.latest=None
 def restore(self,models,visits):
  for key,model in list(models.items())[:3]:
   if key not in ('hydrogen','stellar','earth') or len(model.get('powers',[]))!=2 or any(p not in POWERS for p in model['powers']) or type(model.get('coefficient')) not in (int,float) or not math.isfinite(model['coefficient']) or not 0<model['coefficient']<1e12:raise ValueError('Invalid coupled model')
   self.models[key]={'coefficient':model['coefficient'],'powers':model['powers'][:]}
  for key,value in visits.items():
   if key in ('hydrogen','stellar','earth') and type(value)is int and 0<=value<=10000000:self.visits[key]=value
 def study(self,stage,source,raw):
  if stage not in ('hydrogen','stellar','earth'):return {'status':'invalid-stage'}
  if not raw:return {'status':'waiting-for-source'}
  rng=random.Random(int(hashlib.sha256(bytes(raw[:256])).hexdigest()[:16],16));self.tasks+=1;visit=self.visits.get(stage,0)+1;self.visits[stage]=visit
  if stage=='hydrogen':
   oracle=lambda p:13.598433*p[0]**2/p[1]**2;xs=[1.,2.,3.,4.];zs=[1.,2.,3.,4.,5.];held=[(2.,7.),(3.,8.),(4.,9.),(1.,11.)];units={'x':'nuclear charge Z, one-electron reference','z':'principal level n','y':'binding magnitude eV'};fresh=(2.,20.+visit)
  elif stage=='stellar':
   oracle=lambda p:1361*p[0]/p[1]**2;xs=[.5,1.,1.5,2.,3.];zs=[.5,1.,2.,3.,4.];held=[(.7,1.3),(1.2,2.7),(2.2,4.3),(3.7,5.1)];units={'x':'luminosity / solar luminosity','z':'distance AU','y':'irradiance W/mÂ²'};fresh=(1.1,6.+visit*.137)
  else:
   oracle=lambda p:(p[0]*p[1]/(4*5.670374419e-8))**.25;xs=[300.,700.,1100.,1500.,2200.];zs=[.2,.4,.6,.8];held=[(525.,.31),(975.,.53),(1750.,.71),(2600.,.87)];units={'x':'incident irradiance W/mÂ²','z':'absorbed fraction 1âˆ’albedo','y':'effective equilibrium temperature K'};fresh=(3100.+visit*31,.73)
  initial=(rng.choice(xs),rng.choice(zs));probes=[(x,initial[1]) for x in xs if x!=initial[0]]+[(initial[0],z) for z in zs if z!=initial[1]];transfer=None
  if stage in self.models:
   estimate=predict(self.models[stage],fresh);actual=oracle(fresh);transfer={'inputs':fresh,'predicted':estimate,'observed':actual,'passed':abs(estimate-actual)<=1e-8*max(1.,abs(actual)),'new_input_combination':True};self.transfers+=bool(transfer['passed'])
   if not transfer['passed']:self.models.pop(stage,None)
  result=discover(oracle,initial,probes,held)
  if result['status']=='validated-model':self.models[stage]=result['model'];self.verified+=1
  from .ambient_noisy_learning import fit
  # Separate labelled robustness trial; generated bytes seed synthetic perturbations.
  rng.seed(int(hashlib.sha256(bytes(raw[:256])).hexdigest()[:16],16)+visit)
  train_points=[(x,z) for x in xs for z in zs]
  noisy_training=[(x,z,oracle((x,z))*math.exp(rng.uniform(-.02,.02))) for x,z in train_points]
  noisy_validation=[(x*(1+visit*.001),z,oracle((x*(1+visit*.001),z))*math.exp(rng.uniform(-.02,.02))) for x,z in held]
  noisy_result=fit(noisy_training,noisy_validation)
  noisy_memory=self.noisy_memory.observe(stage,noisy_training,noisy_validation)
  noisy_result['origin']='Synthetic multiplicative-noise robustness trial; not sensor measurements'
  from .ambient_transfer_challenge import challenge
  transfer_challenge=challenge(raw,self.tasks) if self.tasks%4==0 else None
  if transfer_challenge:
   self.last_challenge=transfer_challenge
   investigation=transfer_challenge.get('active_family_investigation',{})
   self.challenge_history.append({'learning_summary':transfer_challenge.get('learning_summary',{}),'task_digest':transfer_challenge['task_digest'],'family_status':transfer_challenge.get('family_selection',{}).get('status'),'transfer_status':transfer_challenge['status'],'experiment_count':investigation.get('experiment_count',0),'helpful_experiments':sum(bool(t['improved']) for t in investigation.get('trace',[])),'unresolved':investigation.get('status')=='unresolved-model-family'})
   self.challenge_history=self.challenge_history[-16:]
  self.latest={**result,'unfamiliar_transfer_challenge':transfer_challenge,'noisy_learning':noisy_result,'noisy_memory':noisy_memory,'stage':stage,'source':source,'units':units,'retained_model_transfer':transfer,'scope':'Controlled interventions and held-out combinations in idealised software reference models. These identify simulator input effects, not real-world causal effects or physical zero-point intelligence.'}
  return self.latest
 def view(self):return {'challenge_history':list(self.challenge_history),'last_challenge':self.last_challenge,'noisy_memory':self.noisy_memory.view(),'experiments':self.tasks,'verified_studies':self.verified,'retained_models':self.models,'new_combination_transfers':self.transfers,'latest':self.latest}
