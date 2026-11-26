"""Pure finite Boolean dependency projections; no host bit mutation or generated execution."""
import copy,collections,time,threading
SOURCES=[{'title':'Pearl · A Causal Calculus for Statistical Research','url':'https://proceedings.mlr.press/r0/pearl95a.html','lesson':'Observation and intervention answer different questions; causal structure supplies assumptions.'},{'title':'NIST · Dynamic Analysis Tools','url':'https://www.nist.gov/itl/csd/secure-systems-and-applications/dynamic-analysis-tools','lesson':'Fault injection tests system behaviour under controlled changes.'}]
DEFAULT={'inputs':{'power':1,'fault':1,'backup':1},'nodes':[{'id':'healthy','op':'not','args':['fault']},{'id':'supply','op':'and','args':['power','healthy']},{'id':'available','op':'or','args':['supply','backup']}],'desired':{'healthy':1,'available':1},'protected':{'available':1},'claimed':'good'}
def project(spec):
 if not isinstance(spec,dict):raise ValueError('Model must be an object')
 inputs=spec.get('inputs',{});nodes=spec.get('nodes',[]);desired=spec.get('desired',{});protected=spec.get('protected',{})
 if not 1<=len(inputs)<=10 or len(nodes)>48 or not desired:raise ValueError('Use 1–10 input bits, up to 48 ordered nodes and explicit desired outcomes')
 def bit(v):return type(v)is int and v in (0,1)
 if not all(isinstance(k,str) and 0<len(k)<=80 and bit(v) for k,v in inputs.items()):raise ValueError('Inputs need names and exact integer 0/1 values')
 known=set(inputs);clean=[]
 for row in nodes:
  name=row.get('id');op=row.get('op');args=row.get('args',[])
  if not isinstance(name,str) or not 0<len(name)<=80 or name in known or op not in ('and','or','xor','not','copy') or not isinstance(args,list) or not 1<=len(args)<=8 or not all(isinstance(a,str) and a in known for a in args):raise ValueError('Use unique, topologically ordered named Boolean gates')
  if op in ('not','copy') and len(args)!=1:raise ValueError('Unary gate requires one input')
  clean.append((name,op,args));known.add(name)
 for goals in (desired,protected):
  if not isinstance(goals,dict) or not all(k in known and bit(v) for k,v in goals.items()):raise ValueError('Outcomes must address known bits with exact 0/1 values')
 def evaluate(initial):
  state=dict(initial)
  for name,op,args in clean:
   v=[state[a] for a in args];state[name]=int(all(v)) if op=='and' else int(any(v)) if op=='or' else sum(v)%2 if op=='xor' else 1-v[0] if op=='not' else v[0]
  return state
 before=evaluate(inputs);keys=list(inputs);base={k:before[k]==v for k,v in desired.items()};counts=collections.Counter();candidates=[];rejected=[]
 for mask in range(1<<len(keys)):
  initial={k:v^((mask>>i)&1) for i,(k,v) in enumerate(inputs.items())};after=evaluate(initial)
  violations=[k for k,v in protected.items() if after[k]!=v];gains=[k for k,v in desired.items() if not base[k] and after[k]==v];losses=[k for k,v in desired.items() if base[k] and after[k]!=v]
  good=bool(gains) and not violations and not losses;bad=bool(violations or losses);claimed=spec.get('claimed','good')
  category=('true good' if claimed=='good' else 'false evil') if good else ('false good' if claimed=='good' else 'true evil') if bad else 'unresolved / unchanged'
  counts[category]+=1;row={'mask':mask,'flipped':[k for i,k in enumerate(keys) if mask>>i&1],'after':after,'gains':gains,'losses':losses,'protected_violations':violations,'category':category,'changed_outputs':[k for k in after if after[k]!=before[k]]}
  if good:candidates.append(row)
  elif bad and len(rejected)<8:rejected.append(row)
 candidates.sort(key=lambda r:(len(r['flipped']),-len(r['gains'])))
 return {'baseline':before,'model':copy.deepcopy(spec),'assignments_projected':1<<len(keys),'complete_for_supplied_model':True,'categories':dict(counts),'candidates':candidates[:16],'rejected_examples':rejected,'inaction':{'state':before,'unmet_goals':[k for k,v in desired.items() if before[k]!=v]},'rollback':{'restore_inputs':dict(inputs),'restored_state':evaluate(inputs)},'hypothesis_status':'Predictions conditional on the supplied deterministic model; validate against independent observations before applying to real systems.','unmodelled':['delays','concurrency','measurement error','hidden dependencies','physical effects','adversarial responses'],'execution':'Pure in-memory projection only; no host memory, device, account or network changes.'}
class CorrectionProjection:
 def __init__(self):self.lock=threading.RLock();self.sequence=0;self.latest={};self.next_at=0
 def calculate(self,spec=None):
  r=project(DEFAULT if spec is None else spec)
  with self.lock:self.sequence+=1;r.update(sequence=self.sequence,time=time.time());self.latest=r
  return copy.deepcopy(r)
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+20;r=self.calculate()
  c.bus.publish({'origin':'correction-projection','target':'all','kind':'stage-output','payload':{'sequence':r['sequence'],'projected_states':r['assignments_projected'],'categories':r['categories'],'provenance':'conditional-Boolean-model-projection','stochastic':False,'predefined_text':True}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'latest':copy.deepcopy(self.latest),'default_model':copy.deepcopy(DEFAULT),'sources':SOURCES,'prayer_tests':['Preserve essential provision and protection','Compare delay and intervention','Identify harmful consequences despite good labels','Permit beneficial alternatives despite bad labels','Verify and repair errors']}
