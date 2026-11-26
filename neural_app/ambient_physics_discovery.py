"""Equation rediscovery from a labelled software physics environment."""
import hashlib,json,math,random,os,uuid
from collections import OrderedDict

EXPONENTS=(-3.,-2.,-1.,-.5,.25,.5,1.,2.,3.)

def predict(model,x):
 if not math.isfinite(x) or not 1e-9<=x<=1e9:raise ValueError('Positive finite input within model range required')
 return model['coefficient']*x**model['exponent']

def discover(oracle,domain,validation,initial,tolerance=1e-8,max_probes=4):
 if any(type(x) not in (int,float) or not math.isfinite(x) or not 1e-9<=x<=1e9 for x in [initial]+domain+validation):return {'status':'invalid-input'}
 if initial in domain or initial in validation or set(domain)&set(validation):return {'status':'invalid-split'}
 if not domain or len(validation)<4 or len(set(validation))!=len(validation):return {'status':'insufficient-inputs'}
 y=oracle(initial)
 if not math.isfinite(y) or not 0<y<1e100:return {'status':'unsupported-observation'}
 hypotheses=[{'coefficient':y/initial**p,'exponent':p} for p in EXPONENTS];observations=[{'input':initial,'output':y}];probes=[];remaining=list(domain)
 for _ in range(max(0,min(8,max_probes))):
  if len(hypotheses)<=1 or not remaining:break
  # Log-prediction spread is scale independent; the oracle is not used to choose x.
  x=max(remaining,key=lambda x:max(math.log(predict(m,x)) for m in hypotheses)-min(math.log(predict(m,x)) for m in hypotheses))
  spread=max(math.log(predict(m,x)) for m in hypotheses)-min(math.log(predict(m,x)) for m in hypotheses)
  before=len(hypotheses);actual=oracle(x);remaining.remove(x)
  if not math.isfinite(actual) or not 0<actual<1e100:return {'status':'unsupported-observation'}
  hypotheses=[m for m in hypotheses if abs(predict(m,x)-actual)<=tolerance*max(1.,abs(actual))]
  observations.append({'input':x,'output':actual});probes.append({'input':x,'log_prediction_spread':spread,'hypotheses_before':before,'hypotheses_after':len(hypotheses)})
  if not hypotheses:break
 report={'observations':observations,'active_probes':probes,'remaining_models':len(hypotheses),'validation_used_for_selection':False}
 if len(hypotheses)!=1:return {**report,'status':'no-supported-equation' if not hypotheses else 'ambiguous'}
 model=hypotheses[0];checks=[]
 for x in validation:
  observed=oracle(x);estimate=predict(model,x);error=abs(estimate-observed)/max(1.,abs(observed));checks.append({'input':x,'predicted':estimate,'observed':observed,'relative_error':error,'passed':math.isfinite(error) and error<=tolerance})
 return {**report,'status':'validated-model' if all(c['passed'] for c in checks) else 'counterexample-found','model':model,'heldout_checks':checks,'formula':'y = '+format(model['coefficient'],'.9g')+' Ãƒâ€” x^('+format(model['exponent'],'.6g')+')'}

class PhysicsDiscovery:
 def __init__(self,path=None):
  from .ambient_coupled_discovery import CoupledDiscovery
  self.coupled=CoupledDiscovery()
  from .ambient_possibilities import PossibilityModel
  self.possibilities=PossibilityModel()
  self.path=path;self.models=OrderedDict();self.tasks=0;self.visits={'hydrogen':0,'stellar':0,'earth':0};self.verified=0;self.transfers=0;self.latest=None;self.storage_error=None;self.relearn_queue=[]
  if path and path.exists():
   try:
    if path.stat().st_size>20000:raise ValueError('Model file exceeds budget')
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('version')!=1:raise ValueError('Unknown model format')
    self.coupled.restore(data.get('coupled_models',{}),data.get('coupled_visits',{}))
    self.possibilities.restore(data.get('possibilities',{}))
    for key,value in data.get('visits',{}).items():
     if key in self.visits and type(value)is int and 0<=value<=10000000:self.visits[key]=value
    for key,m in list(data['models'].items())[:3]:
     if key not in ('hydrogen','stellar','earth') or m['exponent'] not in EXPONENTS or type(m['coefficient']) not in (int,float) or not math.isfinite(m['coefficient']) or not 0<m['coefficient']<1e12:raise ValueError('Invalid model')
     self.models[key]={'coefficient':m['coefficient'],'exponent':m['exponent']}
   except (OSError,ValueError,KeyError,TypeError) as exc:self.models.clear();self.coupled.models.clear();self.coupled.visits.clear();self.storage_error=str(exc)[:180]
 def study(self,source,raw):
  if not raw:return {'status':'waiting-for-input'}
  digest=hashlib.sha256(bytes(raw[:256])).hexdigest();rng=random.Random(int(digest[:16],16));stage=self.possibilities.choose(self.coupled.models,raw,self.relearn_queue)
  if stage in self.relearn_queue:self.relearn_queue.remove(stage)
  self.tasks+=1;self.visits[stage]+=1
  if stage=='hydrogen':
   oracle=lambda n:13.598433/n**2;domain=list(range(1,13));held=list(range(14,22));units={'input':'principal quantum number n','output':'binding-energy magnitude eV'}
  elif stage=='stellar':
   oracle=lambda r:1361/r**2;domain=[.5+i*.25 for i in range(19)];held=[.63,1.13,1.83,2.63,3.37,4.13,5.7,6.3];units={'input':'distance AU','output':'solar irradiance W/mÃ‚Â²'}
  else:
   oracle=lambda s:(s*.7/(4*5.670374419e-8))**.25;domain=[100.+i*100 for i in range(25)];held=[125.,375.,725.,1125.,1575.,2125.,2700.,3000.];units={'input':'incident irradiance W/mÃ‚Â²','output':'effective radiative-equilibrium temperature K'}
  initial=rng.choice(domain);probes=[x for x in domain if x!=initial];known=self.models.get(stage);transfer=None
  if known:
   fresh_input=32.+self.visits[stage] if stage=='hydrogen' else 6.5+.137*self.visits[stage] if stage=='stellar' else 3100.+37*self.visits[stage]
   transfer={'input':fresh_input,'predicted':predict(known,fresh_input),'observed':oracle(fresh_input),'new_probe_for_this_model_context':True};transfer['passed']=abs(transfer['predicted']-transfer['observed'])<=1e-8*max(1.,abs(transfer['observed']))
   self.transfers+=bool(transfer['passed'])
   if not transfer['passed']:self.models.pop(stage,None)
  result=discover(oracle,probes,held,initial)
  if result['status']=='validated-model':self.models[stage]=result['model'];self.verified+=1
  coupled_result=self.coupled.study(stage,source,raw)
  self.possibilities.observe(stage,coupled_result)
  from .ambient_chain_reasoning import reason,reason_noisy
  chain_reasoning=reason(self.coupled.models,self.tasks)
  for failed_stage in chain_reasoning.get('relearn_stages',[]):
   self.coupled.models.pop(failed_stage,None)
   if failed_stage not in self.relearn_queue:self.relearn_queue.append(failed_stage)
  self.latest={**result,'noisy_chain_reasoning':reason_noisy(self.coupled.noisy_memory,self.tasks),'chain_reasoning':chain_reasoning,'coupled_discovery':coupled_result,'stage':stage,'source':source,'source_sha256':digest,'units':units,'retained_model_transfer':transfer,'scope':'Rediscovery of an already defined software reference model from numeric observations. Simulated hydrogen binding, inverse-square solar irradiance and Earth equilibrium are not physical sensor data, new scientific discoveries or zero-point measurements.'}
  return self.latest
 def view(self):return {'possibilities':self.possibilities.view(),'coupled_discovery':self.coupled.view(),'experiments':self.tasks,'verified_models':self.verified,'retained_models':dict(self.models),'successful_unseen_transfers':self.transfers,'latest':self.latest,'storage_error':self.storage_error}
 def flush(self):
  if self.path is None:return
  tmp=self.path.with_name(self.path.name+'.'+uuid.uuid4().hex+'.tmp')
  try:
   self.path.parent.mkdir(parents=True,exist_ok=True);tmp.write_text(json.dumps({'possibilities':self.possibilities.checkpoint(),'version':1,'models':self.models,'visits':self.visits,'coupled_models':self.coupled.models,'coupled_visits':self.coupled.visits}),encoding='utf-8');os.replace(tmp,self.path);self.storage_error=None
  except OSError as exc:self.storage_error=str(exc)[:180]
  finally:
   if tmp.exists():tmp.unlink()
