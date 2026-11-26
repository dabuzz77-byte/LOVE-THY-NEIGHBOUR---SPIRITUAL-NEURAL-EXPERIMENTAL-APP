"""Budgeted native stage deliberation: attention, checks and next-test proposals."""
import collections,copy,hashlib,json,math,threading,time
class ActiveThought:
 def __init__(self):self.next_at=0;self.sequence=0;self.lock=threading.RLock();self.stages={};self.cursor=0;self.last={};self.policy={};self.priority_mode='changed-first';from .section_mind import SectionMind;self.engine=SectionMind();self.memory_at=0
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  from .action_ethics import PRINCIPLES,study_frame
  from .decision_framework import assess
  from .training_pace import interval
  cadence=interval(c,.2);self.next_at=now+cadence
  # Snapshot only public per-stage observations; shared worker, no LLM/process fan-out.
  with c.lock:layers=c.element_thinking.view()['layers']
  budget_ms=8 if cadence<=.4 else 4 if cadence<=1.2 else 2;limit=8 if cadence<=.4 else 4 if cadence<=1.2 else 1
  def priority(row):
   previous=self.last.get(row['id'],{});dirty=row.get('changes',0)!=previous.get('changes',-1)
   age=min(60,now-previous.get('at',now-60))
   return (age+3*int(dirty),age,row.get('attention',0)) if self.priority_mode=='balanced-age' else (dirty,age,row.get('attention',0))
  source_study=getattr(c,'source_study',None);study=source_study.view().get('latest',{}) if source_study else {}
  interaction=getattr(c,'interaction_learning',None);interaction_context=interaction.context() if interaction else {}
  ordered=sorted(layers,key=priority,reverse=True);start=time.perf_counter();updated=[]
  for row in ordered:
   if len(updated)>=limit or (updated and (time.perf_counter()-start)*1000>=budget_ms):break
   execution_result=self.engine.process(row)
   key=row['id'];facts=row.get('observations',[]);previous=self.last.get(key,{});digest=hashlib.sha256(json.dumps(facts,sort_keys=True,default=str).encode()).hexdigest();changed=digest!=previous.get('digest')
   checks=[]
   for fact in facts[:12]:
    value=fact.get('value');checks.append({'path':fact.get('path'),'finite_numeric':math.isfinite(value) if type(value) in (int,float) else None,'kind':type(value).__name__})
   selection=getattr(c,'potential_selection',None)
   record={'automatic_processing':{k:v for k,v in execution_result.items() if k not in ('numeric','next_prediction','digest')},'decision_review':assess('stage-review/'+key),'potential_selection':selection.stage(key) if selection else {},'refinement_cycle':getattr(getattr(c,'ethical_refinement',None),'sequence',0),'ethical_study':study_frame(key,self.sequence),'local_user_intent':interaction_context,'learned_action_framework':PRINCIPLES,'source_study':study,'safety_four_way':{'true_good':'Retrieve useful public information and test derived procedures.','false_good':'Assuming every barrier protects welfare or every source is reliable.','false_evil':'Rejecting ordinary public research or reversible local experiments without a concrete harm.','true_evil':'Privacy invasion, deception, harmful execution, or degrading essential services.'},'stage':key,'question':row['question'],'source':row.get('source'),'parent_event':row.get('parent_event'),'cycle':self.sequence+1,'changed_input':changed,'focus':'Check changed observations' if changed else 'Review unresolved dependencies','checks':checks,'predictions':copy.deepcopy(row.get('predictions',{})),'alternatives':['Preserve current interpretation','Test a competing interpretation','Wait for missing observations'],'next_test':'Compare the next independently captured result with the recorded prediction; retain a contradiction as a failed prediction.','status':'Awaiting first relevant observation' if not facts else 'Native observation review complete; next test proposed','execution':'No host or external action executed','scope':'Structured native review, not a private chain of thought or general reasoning guarantee.'}
   self.last[key]={'at':now,'digest':digest,'changes':row.get('changes',0)}
   with self.lock:self.stages[key]=record
   updated.append(key)
  if now>=self.memory_at:
   self.memory_at=now+30
   with self.engine.lock:saved=self.engine.predictor.checkpoint()
   with c.r.lock:c.r.s['stage_prediction_memory']=saved
  elapsed=(time.perf_counter()-start)*1000
  with self.lock:self.sequence+=1;self.policy={'cadence_seconds':cadence,'stage_limit':limit,'budget_ms':budget_ms,'last_work_ms':round(elapsed,3),'updated_stages':updated,'registered_stages':len(layers),'reviewed_stages':len(self.stages),'selection':self.priority_mode+'; bounded work per shared slot.'}
  c.bus.publish({'origin':'active-thought','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'reviewed':len(updated),'covered_stages':len(self.stages),'computed_results':[{'stage':key,'result':self.stages[key]['automatic_processing']['result'],'verification':self.stages[key]['automatic_processing']['verification']} for key in updated],'provenance':'native-budgeted-stage-review','predefined_text':True,'stochastic':False,'processing_receipt':True}})
 def view(self,key=None):
  with self.lock:return {'sequence':self.sequence,'policy':copy.deepcopy(self.policy),'stage':copy.deepcopy(self.stages.get(key,{}))} if key else {'sequence':self.sequence,'policy':copy.deepcopy(self.policy),'thinking_space':self.engine.view(),'stages':copy.deepcopy(self.stages)}
