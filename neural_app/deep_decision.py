"""Bounded native counterfactual selection for existing typed tasks."""
import copy,hashlib,json,math,threading,time,os
from .decision_framework import assess
INTERNAL={'calculate','sort','unique','analyze','reverse','upper','lower','statistics','test_python','debug_python','build_project'}
class DeepDecision:
 def __init__(self,data=None):
  self.lock=threading.RLock();self.sequence=0;self.records=[];self.outcomes={};self.next_at=0;self.latest={};self.last_signature=None;self.observed_ids=set();self.observed_order=[];self.path=data/'decision-outcomes.json' if data else None;self.dirty=False;self.storage_error=None
  if self.path:
   try:
    saved=json.loads(self.path.read_text(encoding='utf-8'))
    for op,row in list(saved.get('outcomes',{}).items())[:32]:
     if isinstance(row,dict) and all(type(row.get(k)) is int and 0<=row[k]<=10**12 for k in ('verified','failures')) and type(row.get('total_ms')) in (int,float) and math.isfinite(row['total_ms']) and row['total_ms']>=0:self.outcomes[str(op)[:80]]=row
   except (OSError,ValueError,AttributeError):pass
 def decide(self,goal,skills=None):
  started=time.perf_counter();skills=skills or {};steps=goal.get('steps',[]);pending=next(((i,s) for i,s in enumerate(steps) if s.get('status')=='pending'),None)
  candidates=[];selected=None
  if pending:
   i,step=pending;op=step.get('operation');prior=steps[:i];ready=all(s.get('status')=='verified' for s in prior);missing=not ready or ('{{previous}}' in step.get('input','') and i==0)
   attempts=skills.get(op,{}).get('attempts',0);successes=skills.get(op,{}).get('successes',0);probability=(successes+1)/(attempts+2)
   cost=skills.get(op,{}).get('cost_ms',0)/max(1,attempts);calibration=self.outcomes.get(op,{});failures=calibration.get('failures',0);verified=calibration.get('verified',0)
   if verified+failures:probability=(verified+1)/(verified+failures+2);cost=calibration['total_ms']/(verified+failures)
   prediction=(goal.get('world_model',{}).get('predictions') or []);preview=next((x for x in prediction if x.get('step')==i),{})
   for kind in ('execute-next','clarify','wait','inspect-evidence'):
    eligible=(ready and not missing and preview.get('status')!='predicted-failure') if kind=='execute-next' else True
    components={'progress':4.0 if kind=='execute-next' else 1.5 if kind=='clarify' and missing else .6 if kind=='inspect-evidence' else .1,'empirical_reliability':probability if kind=='execute-next' else 0.,'evidence_gain':1.5 if kind=='inspect-evidence' and preview.get('status')=='deferred' else .2 if kind=='execute-next' else 0.,'cost_penalty':min(1,cost/1000) if kind=='execute-next' else .05,'delay_penalty':.5 if kind=='wait' and ready else 0.,'unresolved_dependency_penalty':6 if kind=='execute-next' and missing else 0.}
    score=components['progress']+components['empirical_reliability']+components['evidence_gain']-components['cost_penalty']-components['delay_penalty']-components['unresolved_dependency_penalty']
    candidates.append({'id':kind,'eligible':eligible,'score':round(score,4),'components':components,'step':i,'operation':op,'prediction_scope':'Empirical task completion and bounded branch preview; not a universal outcome probability','expected_effect':{'execute-next':'Run exactly the existing pending supported step and verify its actual result','clarify':'Obtain missing input or dependency correction','wait':'Keep state unchanged; account for deferred progress','inspect-evidence':'Review available source or preview before extending the plan'}[kind]})
   # Missing dependencies dominate score; no unrequested action is manufactured.
   selected='clarify' if missing else max((x for x in candidates if x['eligible']),key=lambda x:x['score'])['id']
   # Deferred source/host observations are gathered by the existing executor, not guessed.
   if selected=='inspect-evidence' and ready and preview.get('status')!='predicted-failure':selected='execute-next'
   review=assess('native/'+str(op));review['operation_context']={'internal_computation':op in INTERNAL,'dependencies_verified':ready,'expected_condition':step.get('completion_condition'),'recovery':'Preserve completed steps; correct the failing step before retry','external_authority':'Existing executor permissions remain authoritative'}
  else:i=None;op=None;selected='complete' if steps and all(s.get('status')=='verified' for s in steps) else 'idle';review=assess('decision/idle');probability=None;verified=0;failures=0
  with self.lock:
   self.sequence+=1;record={'id':self.sequence,'goal_id':goal.get('id'),'selected':selected,'step':i,'operation':op,'candidates':candidates,'decision_review':review,'learning':{'verified':verified,'failures':failures},'elapsed_ms':round((time.perf_counter()-started)*1000,3),'model_calls':0,'status':'proposal before existing executor','scope':'Bounded alternatives for registered task steps; no new system authority'};self.latest=record;self.records=(self.records+[record])[-64:]
  return copy.deepcopy(record)
 def observe(self,decision,ok,cost_ms):
  op=decision.get('operation')
  if not op:return
  with self.lock:
   if type(ok) is not bool or type(cost_ms) not in (int,float) or not math.isfinite(cost_ms):raise ValueError('Use a verified boolean and finite execution duration')
   ident=decision.get('id')
   if type(ident) is not int or ident<=0:raise ValueError('A recorded decision identifier is required')
   if ident in self.observed_ids:return False
   if not any(r['id']==ident and r.get('operation')==op for r in self.records):raise ValueError('Outcome must reference a retained matching decision')
   self.observed_ids.add(ident);self.observed_order.append(ident)
   if len(self.observed_order)>256:self.observed_ids.discard(self.observed_order.pop(0))
   self.dirty=True
   row=self.outcomes.setdefault(op,{'verified':0,'failures':0,'total_ms':0.});row['verified' if ok else 'failures']+=1;row['total_ms']+=max(0,float(cost_ms));decision['actual']={'verified':ok is True,'cost_ms':cost_ms,'repair_required':ok is not True}
   for record in reversed(self.records):
    if record['id']==decision.get('id'):record['actual']=copy.deepcopy(decision['actual']);break
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  self.next_at=time.monotonic()+1
  self.flush()
  executive=c.r.workbench.executive
  with executive.lock:
   goal=next((g for g in reversed(executive.s['goals']) if g.get('status')=='running'),None)
   if not goal:return
   snapshot=copy.deepcopy(goal);skills=copy.deepcopy(executive.s['skills'])
  signature=hashlib.sha256(json.dumps([snapshot.get('id'),[(s.get('status'),s.get('attempts')) for s in snapshot.get('steps',[])]],sort_keys=True).encode()).hexdigest()
  if signature==self.last_signature:return
  self.last_signature=signature;decision=self.decide(snapshot,skills)
  c.bus.publish({'origin':'deep-decision','target':'all','kind':'stage-output','payload':{'decision_id':decision['id'],'selected':decision['selected'],'step':decision['step'],'provenance':'native-counterfactual-task-selection','processing_receipt':True}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'latest':copy.deepcopy(self.latest),'recent':copy.deepcopy(self.records[-12:]),'outcomes':copy.deepcopy(self.outcomes),'persistence':{'enabled':self.path is not None,'pending_save':self.dirty,'error':self.storage_error,'scope':'Aggregate operation outcomes only; no raw user inputs or task text'},'principles':'✝ Provision, protection, dignity, forgiveness and repair; assess act, delay and alternatives.','efficiency':'One bounded changed-state review per second; existing executor calls the same selector immediately before action. No LLM required.','scope':'Typed-task decision engine; broader natural-language goals still require planning or clarification.'}

 def flush(self):
  with self.lock:
   if not self.path or not self.dirty:return
   try:
    temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'version':1,'outcomes':self.outcomes}),encoding='utf-8');os.replace(temp,self.path);self.dirty=False;self.storage_error=None
   except OSError as exc:self.storage_error=type(exc).__name__
