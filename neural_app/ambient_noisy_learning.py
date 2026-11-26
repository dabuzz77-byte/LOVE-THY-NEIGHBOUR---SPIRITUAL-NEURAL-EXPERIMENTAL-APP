"""Bounded log-linear fitting with reserved, disjoint numerical observations."""
import math,hashlib,json,random

def _fit(training,validation,max_log_error=.08):
 if not 6<=len(training)<=128 or not 4<=len(validation)<=128:return {'status':'insufficient-observations'}
 rows=training+validation
 if any(len(r)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or not 1e-12<v<1e12 for v in r) for r in rows):return {'status':'invalid-observation'}
 if len({(r[0],r[1]) for r in validation})!=len(validation):return {'status':'duplicate-validation-inputs'}
 if set((r[0],r[1]) for r in training)&set((r[0],r[1]) for r in validation):return {'status':'overlapping-validation'}
 features=[[1.,math.log(x),math.log(z)] for x,z,y in training];targets=[math.log(r[2]) for r in training]
 matrix=[[sum(f[i]*f[j] for f in features) for j in range(3)]+[sum(f[i]*y for f,y in zip(features,targets))] for i in range(3)]
 for i in range(3):
  pivot=max(range(i,3),key=lambda j:abs(matrix[j][i]));matrix[i],matrix[pivot]=matrix[pivot],matrix[i]
  if abs(matrix[i][i])<1e-10:return {'status':'unidentifiable-inputs'}
  scale=matrix[i][i];matrix[i]=[v/scale for v in matrix[i]]
  for j in range(3):
   if j!=i:
    scale=matrix[j][i];matrix[j]=[a-scale*b for a,b in zip(matrix[j],matrix[i])]
 weights=[matrix[i][3] for i in range(3)]
 baseline=sum(targets)/len(targets);checks=[]
 for x,z,y in validation:
  estimate=weights[0]+weights[1]*math.log(x)+weights[2]*math.log(z)
  error=abs(estimate-math.log(y));checks.append({'inputs':[x,z],'observed':y,'predicted':math.exp(estimate),'absolute_log_error':error})
 error=sum(c['absolute_log_error'] for c in checks)/len(checks);base=sum(abs(baseline-math.log(y)) for x,z,y in validation)/len(validation)
 residuals=[abs(sum(a*b for a,b in zip(f,weights))-y) for f,y in zip(features,targets)]
 return {'status':'heldout-supported' if error<=max_log_error and error<base else 'not-supported','model':{'coefficient':math.exp(weights[0]),'powers':weights[1:]},'heldout_mean_log_error':error,'constant_baseline_log_error':base,'training_max_log_residual':max(residuals),'checks':checks,'validation_used_for_fit':False,'scope':'Log-linear power-product fit; residuals are descriptive, not calibrated confidence intervals.'}

def fit(training,validation,max_log_error=.08):
 try:
  if type(max_log_error) not in (int,float) or not math.isfinite(max_log_error) or max_log_error<=0:return {'status':'invalid-error-threshold'}
  return _fit(training,validation,max_log_error)
 except (OverflowError,ZeroDivisionError,ValueError,TypeError):return {'status':'numerically-unsupported'}

def controlled_fit(training,validation):
 result=fit(training,validation)
 if 'model' not in result:return result
 controls=[]
 for seed in range(4):
  outputs=[r[2] for r in training];random.Random(701+seed).shuffle(outputs)
  shuffled=[(r[0],r[1],y) for r,y in zip(training,outputs)]
  control=fit(shuffled,validation)
  if 'heldout_mean_log_error' in control:controls.append(control['heldout_mean_log_error'])
 best=min(controls) if controls else None
 result['shuffled_control_errors']=controls
 result['beats_all_shuffled_controls']=best is not None and result['heldout_mean_log_error']+1e-6<best
 if not result['beats_all_shuffled_controls']:result['status']='not-supported'
 result['control_scope']='Four deterministic output permutations; diagnostic comparison, not a significance test'
 return result

class NoisyMemory:
 """A model earns eligibility only on a later capture before replacement."""
 def __init__(self):self.models={};self.latest={};self.eligible=set();self.captures={}
 def observe(self,key,training,validation):
  result=controlled_fit(training,validation)
  if 'model' not in result:
   self.eligible.discard(key)
   self.latest[key]={'fit':result,'eligible':False,'fresh_capture_check':None,'reason':'Invalid or insufficient evidence; retained model suspended'}
   return self.latest[key]
  fingerprint=hashlib.sha256(json.dumps([training,validation],sort_keys=True).encode()).hexdigest()
  if self.captures.get(key)==fingerprint:return {**self.latest[key],'repeated_capture':True}
  self.captures[key]=fingerprint
  previous=self.models.get(key);transfer=None
  if previous:
   seen={tuple(p) for p in previous['seen_inputs']}
   fresh=[r for r in validation if tuple(r[:2]) not in seen]
   errors=[]
   for x,z,y in fresh:
    estimate=math.log(previous['coefficient'])+previous['powers'][0]*math.log(x)+previous['powers'][1]*math.log(z)
    errors.append(abs(estimate-math.log(y)))
   error=sum(errors)/len(errors) if errors else None
   baseline=sum(abs(math.log(previous['baseline'])-math.log(y)) for x,z,y in fresh)/len(fresh) if fresh else None
   passed=len(fresh)>=4 and error<=.08 and error<baseline
   transfer={'mean_log_error':error,'baseline_log_error':baseline,'passed':passed,'evaluated_before_refit':True,'new_input_combinations':len(fresh)}
   if passed:
    self.eligible.add(key)
    previous['seen_inputs']=(previous['seen_inputs']+[list(r[:2]) for r in fresh])[-512:]
   else:self.eligible.discard(key);self.models.pop(key,None)
  # A newly fitted replacement must itself survive a future capture.
  if result.get('status')=='heldout-supported' and key not in self.models:
   self.models[key]={**result['model'],'baseline':math.exp(sum(math.log(y) for x,z,y in training)/len(training)),'seen_inputs':[list(r[:2]) for r in training+validation]}
   self.eligible.discard(key)
  self.latest[key]={'fresh_capture_check':transfer,'fit':result,'eligible':key in self.eligible,'scope':'Synthetic robustness models kept separate from exact-model plans'}
  return self.latest[key]
 def view(self):return {'eligible_stages':sorted(self.eligible),'retained_stages':sorted(self.models),'latest':dict(self.latest)}
