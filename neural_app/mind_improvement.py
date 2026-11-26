"""Reversible attention-policy tuning, gated by finite independent workloads."""
import copy,json,threading,time,math,hashlib
POLICIES=('changed-first','balanced-age')
def simulate(policy,pattern):
 if policy not in POLICIES:raise ValueError('Unknown attention policy')
 n=12;last=[-1]*n;changes=[0]*n;reviewed=[0]*n;max_wait=0
 for tick in range(96):
  dirty={i for i in range(n) if (i<3 if pattern==0 else i%4==tick%4 if pattern==1 else tick%13==i if pattern==2 else i<6 or tick%11==i)}
  for i in dirty:changes[i]+=1
  def rank(i):
   age=tick-last[i];pending=changes[i]!=reviewed[i]
   return (pending,age,-i) if policy=='changed-first' else (age+3*int(pending),age,-i)
  for i in sorted(range(n),key=rank,reverse=True)[:2]:last[i]=tick;reviewed[i]=changes[i]
  max_wait=max(max_wait,max(tick-x for x in last))
 return {'pattern':pattern,'maximum_wait_slots':max_wait,'covered_stages':sum(x>=0 for x in last),'state_preserved':all(x>=0 for x in changes)}
def trial():
 rows=[]
 for pattern in range(4):
  a=simulate('changed-first',pattern);b=simulate('balanced-age',pattern);rows.append({'split':'training' if pattern<2 else 'held-out','baseline':a,'candidate':b})
 # Explicit contract: bound starvation across all finite fixtures, improve at least one,
 # preserve complete stage coverage. No claim of universal workload optimality.
 passed=all(r['candidate']['maximum_wait_slots']<=12 and r['candidate']['covered_stages']==12 for r in rows) and any(r['candidate']['maximum_wait_slots']<r['baseline']['maximum_wait_slots'] for r in rows)
 return {'candidate':'balanced-age','baseline':'changed-first','passed':passed,'workloads':rows,'protected_contracts':['No source modification','No host or network action','Original observations retained','Resource backoff and per-slot budget unchanged'],'criterion':'Avoid stage starvation and retain complete coverage in four finite workload models, including two held out.'}
class MindImprovement:
 def __init__(self,data):
  self.path=data/'mind-improvement.json';self.lock=threading.RLock();self.next_at=0;self.sequence=0;self.latest={};self.history=[];self.frame={}
  try:
   saved=json.loads(self.path.read_text(encoding='utf-8'));self.sequence=saved.get('sequence',0);self.latest=saved.get('latest',{})
  except (OSError,ValueError):pass
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+300;result=trial();source=c.source_study.view().get('latest',{});result['source_context']={'url':source.get('url'),'title':source.get('title'),'status':source.get('status'),'relation':'Source context can motivate inquiry; local tests determine this narrow tuning decision.'}
  gate={'scope':'One registered reversible attention policy only','true_good':'Reduce starvation and distribute useful processing fairly','false_good':'Mistaking a faster animation or plausible source for improved task performance','false_evil':'Blocking a reversible local policy test without identified harm','true_evil':'Unreviewed code execution, privacy invasion or damage to services','hard_checks_passed':result['passed']}
  with c.active_thought.lock:
   previous=getattr(c.active_thought,'priority_mode','changed-first')
   if result['passed']:c.active_thought.priority_mode='balanced-age'
  with c.lock:layers=c.element_thinking.view()['layers'];source_count=len(c.sources)
  proposals=[{'stage':r['id'],'question':r['question'],'observed_changes':r['changes'],'source':r.get('source'),'parent_event':r.get('parent_event'),'proposal':'Compare bounded scheduling policies; inspect independent task contracts before extending capability.','status':'Needs operation-specific experiment beyond the tested attention policy','protected':['Original source lineage','Resource backoff','Privacy and access boundaries']} for r in layers]
  result['self_write_engine']=c.self_improvement_engine.view() if hasattr(c,'self_improvement_engine') else {}
  result['stage_proposals']=proposals;result['experiment_coverage']={'policies':2,'workloads':4,'slots_per_workload':96,'held_out_workloads':2,'possible_changes_applied':1,'scope':'Finite scheduler models, not exhaustive real-world outcomes'}
  result.update(previous_policy=previous,applied_policy='balanced-age' if result['passed'] else previous,rollback_policy=previous,virtue_gate=gate,status='applied reversible tuning' if result['passed'] else 'rejected')
  with self.lock:
   self.sequence+=1;self.latest=result;self.history=(self.history+[result])[-8:];tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps({'sequence':self.sequence,'latest':result}),encoding='utf-8');tmp.replace(self.path)
  particles=[]
  records=[{'kind':'policy-test',**v} for v in result['workloads']]+[{'kind':'stage-proposal',**v} for v in proposals]
  for i,row in enumerate(records):
   a=i*math.pi*(3-math.sqrt(5));y=1-2*(i+.5)/max(1,len(records));rr=math.sqrt(max(0,1-y*y));ident=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()[:16]
   particles.append({'id':'mind-improvement:'+ident,'point':[rr*math.cos(a),y,rr*math.sin(a)],'phase':1.,'autonomy':0.,'selected':row['kind']=='policy-test','symbol':'◇','expression_type':row['kind'],'source':row.get('source') or 'mind-improvement-test','parent_event':row.get('parent_event'),'path':[],'value_preview':row.get('stage',row.get('split','policy test')),'record':row})
  with self.lock:self.frame={'sequence':self.sequence,'particles':particles,'received_events':self.sequence,'retained_sources':source_count,'represented_values':len(records),'selected_phases':[1.],'thought_trace':records,'experiments':{'total':8},'app_law':gate,'scope':'Safe self-engineering study: tested attention tuning only; other proposals remain inert. Source context is not authority to rewrite code or grant access.'}
  c.bus.publish({'origin':'mind-improvement','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'passed':result['passed'],'provenance':'tested-reversible-attention-tuning','processing_receipt':True,'predefined_text':True,'stochastic':False}})
 def rollback(self,c):
  with self.lock:policy=self.latest.get('rollback_policy','changed-first')
  if policy not in POLICIES:raise ValueError('Invalid rollback policy')
  with c.active_thought.lock:c.active_thought.priority_mode=policy
  # Pause automatic reapplication until the next scheduled evaluation.
  self.next_at=time.monotonic()+300
  return {'policy':policy,'status':'rolled back','reevaluation_in_seconds':300}
 def sphere(self):
  with self.lock:return copy.deepcopy(self.frame or {'sequence':0,'particles':[]})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'latest':copy.deepcopy(self.latest),'scope':'Narrow tested attention tuning, not autonomous rewriting of the app or proof that every future change is harmless.'}
