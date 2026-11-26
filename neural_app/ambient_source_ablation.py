"""Matched-environment comparison of generated-input sampling strategies."""
import hashlib,math,random
from .ambient_noisy_learning import controlled_fit

def compare(raw,serial):
 if not raw:return {'status':'waiting-for-generated-input'}
 raw=bytes(raw[:256]);env=random.Random(911+serial)
 coefficient=env.uniform(.5,3);p=env.uniform(-1.7,1.7);q=env.uniform(-1.7,1.7)
 def observe(x,z):return coefficient*x**p*z**q
 reserved=[(.83,4.3),(1.71,3.7),(3.31,.61),(5.17,2.71)]
 held=[(x,z,observe(x,z)) for x,z in reserved]
 shuffled=list(raw);random.Random(44).shuffle(shuffled)
 arms=[]
 for name,source in [('capture',raw),('unchanged-input',b'fixed-input-baseline'),('shuffled-capture',bytes(shuffled))]:
  seed=int(hashlib.sha256(source).hexdigest()[:16],16);rng=random.Random(seed)
  points=[(rng.uniform(.6,4),rng.uniform(.6,3.5)) for _ in range(16)]
  training=[(x,z,observe(x,z)) for x,z in points];result=controlled_fit(training,held)
  baseline=sum(math.log(y) for x,z,y in training)/len(training)
  baseline_error=sum(abs(baseline-math.log(y)) for x,z,y in held)/len(held)
  arms.append({'arm':name,'training_inputs':points,'status':result['status'],'heldout_log_error':result.get('heldout_mean_log_error'),'constant_baseline_log_error':baseline_error})
 return {'status':'matched-environment-evaluated','environment_id':hashlib.sha256(str((coefficient,p,q)).encode()).hexdigest(),'arms':arms,'same_environment_and_reserved_inputs':True,'capture_role':'Selects training input locations only; environment and test outcomes are independent of capture','conclusion':'Compare measured errors; no advantage for ambient input is presumed','scope':'Synthetic sampling ablation, not physical zero-point sensing'}

def budget_comparison(raw,serial):
 """Same noisy environment and test set, equal observation budgets."""
 if not raw:return {'status':'waiting-for-generated-input'}
 env=random.Random(2111+serial);coefficient=env.uniform(.5,3);p=env.uniform(-1.7,1.7);q=env.uniform(-1.7,1.7)
 def clean(x,z):return coefficient*x**p*z**q
 def observe(x,z):
  seed=int(hashlib.sha256(repr((serial,x,z)).encode()).hexdigest()[:16],16)
  return clean(x,z)*math.exp(random.Random(seed).uniform(-.05,.05))
 held=[(x,z,clean(x,z)) for x,z in ((.83,4.3),(1.71,3.7),(3.31,.61),(5.17,2.71))]
 capture=random.Random(int(hashlib.sha256(bytes(raw[:256])).hexdigest()[:16],16));fixed=random.Random(871)
 points={'capture':[(capture.uniform(.6,4),capture.uniform(.6,3.5)) for _ in range(16)],'fixed-random':[(fixed.uniform(.6,4),fixed.uniform(.6,3.5)) for _ in range(16)],'spread-design':[(x,z) for x,z in ((.6,.6),(4,3.5),(.6,3.5),(4,.6),(1.2,1.2),(3.2,2.8),(1.2,2.8),(3.2,1.2),(2,2),(2.5,2.5),(.8,2),(3.8,2),(2,.8),(2,3.3),(1.5,3),(3,1.5))]}
 rows=[]
 for budget in (6,10,16):
  for name,inputs in points.items():
   training=[(x,z,observe(x,z)) for x,z in inputs[:budget]];r=controlled_fit(training,held)
   rows.append({'arm':name,'observation_budget':budget,'observations_used':len(training),'status':r['status'],'heldout_log_error':r.get('heldout_mean_log_error'),'test_observations':len(held)})
 return {'status':'budget-comparison-complete','rows':rows,'environment_id':hashlib.sha256(repr((coefficient,p,q)).encode()).hexdigest(),'noise':'Deterministic coordinate-indexed synthetic multiplicative noise, same for every arm at identical coordinates','test_used_for_sampling':False,'scope':'Bounded synthetic design comparison; no ambient-source advantage assumed'}
