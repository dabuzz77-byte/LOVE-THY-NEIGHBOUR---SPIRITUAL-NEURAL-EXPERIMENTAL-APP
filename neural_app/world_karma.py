"""World-karma reflection: explicit ethical framework and traceable app observations."""
import collections,copy,time,threading
STAGES=[
 {'id':'deficiency','title':'Deficiency / provision','question':'Which needs are unmet, and what provision reduces suffering?','digital':'Resource allocation, availability and essential-service continuity.'},
 {'id':'food-chain','title':'Life feeding life','question':'Who bears loss while another gains, and what reduces avoidable suffering?','digital':'Trace dependencies and displaced costs; biological predation is not a verdict on a person.'},
 {'id':'primality','title':'Survival / protective fear','question':'Which pressures generate fear, competition or defensive behaviour?','digital':'Threat detection, false alarms, escalation and resilient alternatives.'},
 {'id':'civilisation','title':'Civilisation / shared systems','question':'Do institutions meet needs fairly or shift harm onto vulnerable beings?','digital':'Infrastructure, access, incentives, privacy and service dependencies.'},
 {'id':'choices','title':'Sin / sinlessness · app framework','question':'Does this choice protect life, reject cruelty and deception, and support repentance and repair?','digital':'Assess actions and consequences, rather than declaring people or religious groups inherently evil.'},
 {'id':'bit-effects','title':'Bit → action → consequence','question':'What actual operation follows this state change, who is affected, and what happens if we wait?','digital':'A bit requires an implemented path to affect a system; trace permissions, propagation, failure and rollback.'},
 {'id':'repair','title':'Redemption / repair','question':'Which correction restores welfare while preserving essential needs?','digital':'Verify outcomes, correct errors and retain lessons without concealing harm.'}]
def bit_correction_audit():
 # Explicit toy contract: bit0 enables provision; bit1 enables protection;
 # bit2 represents a fault; bit3 enables recovery; upper bits are unrelated state.
 def evaluate(v):return {'provision':bool(v&1),'protection':bool(v&2),'fault':bool(v&4),'recovery':bool(v&8)}
 counts=collections.Counter();examples=[]
 for before in range(256):
  a=evaluate(before)
  for bit in range(8):
   after=before^(1<<bit);b=evaluate(after)
   lost=[k for k in ('provision','protection','recovery') if a[k] and not b[k]]
   fixed=a['fault'] and not b['fault'];introduced=not a['fault'] and b['fault']
   improved=any(not a[k] and b[k] for k in ('provision','protection','recovery'))
   beneficial=(fixed or improved) and not lost and not introduced
   harmful=bool(lost or introduced)
   # A "corrective" proposal claims goodness. Classify by the defined contract.
   category='true good' if beneficial else 'false good' if harmful else 'unresolved / no defined effect'
   counts[category]+=1
   if len(examples)<12:examples.append({'before':before,'bit':bit,'after':after,'before_semantics':a,'after_semantics':b,'lost_services':lost,'fault_removed':fixed,'fault_introduced':introduced,'category':category})
 return {'states':256,'changes_tested':2048,'counts':dict(counts),'examples':examples,'contract':'bit0 provision, bit1 protection, bit2 fault, bit3 recovery; bits4–7 unrelated in this model','method':['Decode meaning before change','Enumerate each candidate one-bit change','Compute downstream service and fault effects','Compare unchanged state','Reject regressions; retain beneficial candidates','Require actual system-specific contract before real execution'],'limits':'Exhaustive for this eight-bit model only. Real systems require dependency maps, timing, concurrency, access authority and operation-specific tests; unmodelled outcomes stay open.'}

class WorldKarma:
 def __init__(self):
  self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.history=collections.deque(maxlen=32);self.latest={};self.counts=collections.Counter()
 def reflect(self,c,question=''):
  question=str(question)[:2000]
  with c.lock:
   observations=[{'source':r['source'],'time':r['time'],'provenance':r['provenance'],'facts':copy.deepcopy(r['facts'][:4])} for r in list(c.sources.values()) if r['source']!='world-karma'][-10:]
  scenario={'question':question or 'World welfare: action, inaction and repair','operation':'thought-experiment','authority':'local modelling'}
  assessment=c.consequence_thought.consider(scenario)
  intake=getattr(self,'intake',None);reports=[]
  if intake:
   for term in ('violence','abuse','children','hunger','exploitation'):
    try:reports.extend(r for r in intake.retrieve(term) if not r.get('private'))
    except Exception:pass
  reports=list({r.get('url','')+r.get('title',''):r for r in reports}.values())[:15]
  report_questions=[{'title':r.get('title'),'source':r.get('source'),'url':r.get('url'),'excerpt':r.get('excerpt'),'retrieved':r.get('fetched'),'status':'Reported account; inspect original for allegation, finding, attribution and corrections','inquiries':['Who was harmed and what conduct is documented?','What supports the attribution, and what remains disputed?','Which needs, incentives, coercion or choices contributed?','What timely protection, accountability and repair could reduce harm?','Could a digital intervention expose victims or damage essential services?']} for r in reports]
  # No unmeasured world effect is converted into a numerical moral certainty.
  record={'news_inquiries':report_questions,'bit_correction':bit_correction_audit(),'accountability':'Explain causes without excusing cruelty, exploitation, abuse or deliberate harm. Assess conduct and responsibility individually.','causal_status':'Deficiency → food chain → primality → civilisation is the app’s organising inquiry, not a proven single cause of every human wrong.','question':scenario['question'],'stages':copy.deepcopy(STAGES),'observations':observations,'assessment':assessment,'engine_layers':len(c.element_thinking.layers),'connection':'Receives shared engine observations; broadcasts reflection to every registered thinking layer.','framework':'User-defined karma and Lord’s Prayer ethics: provision, protection, forgiveness, repair and accountable power.','thoughts':[{'stage':s['id'],'question':s['question'],'digital_parallel':s['digital'],'status':'Open inquiry; inspect relevant observations and compare alternatives.'} for s in STAGES], 'world_grid':'Models possible local and remote consequences; this layer does not access remote devices or execute interventions.'}
  with self.lock:
   self.sequence+=1;record.update(sequence=self.sequence,time=time.time());self.latest=record;self.history.append(record)
   for s in STAGES:self.counts[s['id']]+=1
  c.bus.publish({'origin':'world-karma','target':'all','kind':'stage-output','payload':{'reflection_sequence':self.sequence,'question':record['question'],'stage_questions':[s['question'] for s in STAGES],'assessment_category':assessment['assessment']['category'],'source_count':len(observations),'provenance':'prayer-guided-ethical-reflection','stochastic':False,'predefined_text':True}})
  return copy.deepcopy(record)
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+15;self.reflect(c,c.goal)
 def view(self):
  with self.lock:return {'sequence':self.sequence,'stages':copy.deepcopy(STAGES),'latest':copy.deepcopy(self.latest),'stage_cycles':dict(self.counts),'recent':copy.deepcopy(list(self.history)[-4:])}
