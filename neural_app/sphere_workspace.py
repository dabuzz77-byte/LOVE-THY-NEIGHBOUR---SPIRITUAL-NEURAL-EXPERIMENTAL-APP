"""One outcome-driven workspace shared by sphere projections, separate from rendering."""
import copy,hashlib,json,threading,time

class SphereWorkspace:
 def __init__(self,c):
  self.c=c;self.dialogue=c.whole_mind_study.native_dialogue;self.lock=threading.RLock();self.worker=None;self.sequence=0;self.latest={};self.events=[];self.pending=[];self.signature=None;self.last_save=0;self.dirty=False;self.error=None;self.last_cycle=0;self.max_cycle_ms=0
 def start(self):
  with self.lock:
   if self.worker and self.worker.is_alive():return
   self.dialogue.shared_reasoning_worker=True
   self.worker=threading.Thread(target=self.loop,daemon=True,name='sphere-reasoning-workspace');self.worker.start()
 def step(self):
  d=self.dialogue;started=time.perf_counter();action='idle';changed=False
  policy=getattr(self.c,'activity_policy',None);activity=policy.for_circuit(self.c) if policy else {'mode':'balanced','multiplier':1,'workspace_interval_seconds':.25,'practice_interval_seconds':30,'native_search_slice_ms':4,'duty_target':.25}
  with d.lock:
   bus_changed=self.c.episode_bus.apply(d.work.state) if hasattr(self.c,'episode_bus') else False
   w=d.work;goal=w.state.get('active_goal');inquiries=w.state.get('inquiries',{});tasks=d.engine.view(compact=True)['tasks']
   if goal and goal['status']=='running':changed=w.think_step();action='advance requested goal'
   elif w.state.get('reasoning_episode',{}).get('status')=='running':
    from .reasoning_episode import advance
    changed=advance(w.state['reasoning_episode']);action='advance shared research and prediction episode'
   elif w.state.get('sphere_mission',{}).get('status')=='running':
    from .sphere_mission import advance
    changed=advance(w.state['sphere_mission'],w);action='execute named sphere role'
   elif any(i['phase']=='enumerating' for i in inquiries.values()):changed=w.think_step();action='compare inquiry hypotheses'
   elif any(t['status']=='running' for t in tasks):d.engine.advance(activity['native_search_slice_ms']);action='test task candidates'
   elif not getattr(self.c.r,'user_active',False):changed=w.autonomous_step(activity['practice_interval_seconds']);action='checked native practice' if changed else 'wait for new evidence or task'
   goal=w.state.get('active_goal');tasks=d.engine.view(compact=True)['tasks'];focus=inquiries.get(w.state.get('focus_inquiry'));task=next((t for t in tasks if t['id']==d.selected),tasks[-1] if tasks else None)
   plans=list(w.state.get('example_plans',{}).values());practice=w.state.get('study_results',[])
   goal_view=None if not goal else {'name':goal['name'],'status':goal['status'],'completed':goal['cursor'],'total':len(goal['stages']),'committed':goal['committed'],'next_step':goal['stages'][goal['cursor']]['instruction'] if goal['status']=='running' else None,'checks':[{'stage':r['stage'],'passed':r['passed'],'acceptance_checked':r['acceptance_checked']} for r in goal['trace']],'receipt_id':goal.get('receipt_id'),'error':goal.get('error')}
   inquiry=None if not focus else {'name':focus['name'],'status':focus['phase'],'observations':len(focus['observations']),'tested':focus['cursor'],'candidates':len(focus['survivors']),'next_question':focus['question'],'revision':focus['revision']}
   task_view=None if not task else {k:copy.deepcopy(task.get(k)) for k in ('id','question','status','phase','tested','solution','conclusion')}
   learning={'completed_practice_studies':sum(w.state.get('study_metrics',{}).values()),'saved_workflows':len(w.state.get('workflow_library',{})),'example_plans':[{'name':p['name'],'status':p['status'],'tested':p['tested'],'validation_passed':sum(r['passed'] for r in p.get('validation',[])),'validation_total':len(p.get('validation',[]))} for p in plans[-4:]],'practice_results':[{'task':r['task'],'passed':r['passed'],'source':r['source']} for r in practice[-4:]]}
   from .artifact_memory import index
   artifacts=index(w.state,d.memory);experiments=[{k:copy.deepcopy(r[k]) for k in ('question','workflow','kind','passed','total','baseline_passed','revoked','procedure_version')} for r in w.state.get('relevant_experiments',[])[-3:]]
   from .sphere_mission import summary as mission_summary
   mission=mission_summary(w.state.get('sphere_mission'))
   from .reasoning_episode import summary as episode_summary
   episode=episode_summary(w.state.get('reasoning_episode'))
   requested_focus=w.state.get('focus_kind');receipt=(w.state.get('receipts') or [None])[-1]
   from .general_reasoning import summary as reasoning_summary
   general=reasoning_summary(w.state.get('general_reasoning_result'))
   from .open_reasoning import summary as open_summary
   opened=open_summary(w.state.get('open_reasoning'))
   workflow_check_passed=w.state.get('last_workflow_check',{}).get('passed')
   code_review=copy.deepcopy(w.state.get('last_code_review'))
   last_work=None if receipt is None else {k:copy.deepcopy(receipt.get(k)) for k in ('id','output_sha256','verified','model_calls')}
   changed=changed or bus_changed
   if changed:self.dirty=True
   # Retain a completed result even when no subsequent computation occurs.
   if self.dirty and d.path and time.monotonic()-self.last_save>=2:
    from .deliberation import Deliberation
    Deliberation.write_json(d.path,{'messages':d.messages,'memory':d.memory,'selected':d.selected,'work':w.state});self.last_save=time.monotonic();self.dirty=False
  if opened and requested_focus=='open-reasoning':focus_type='open-reasoning';status=opened['status'];next_action=opened['next_question']
  elif general and requested_focus=='general-reasoning':focus_type='general-reasoning';status=general.get('status','complete');next_action=general.get('next_step','Review the retained reasoning assumptions and checks.')
  elif episode and requested_focus=='reasoning-episode':focus_type='reasoning-episode';status=episode['status'];next_action=episode['phase']
  elif goal_view and goal_view['status']=='running':focus_type='goal';status='running';next_action=goal_view['next_step']
  elif mission and mission['status']=='running':focus_type='sphere-mission';status='running';next_action=mission['phase']
  elif inquiry and inquiry['status'] in ('enumerating','awaiting-observation','ambiguous'):focus_type='inquiry';status=inquiry['status'];next_action=inquiry['next_question']
  elif task_view and task_view['status']=='running':focus_type='task';status='running';next_action=task_view['phase']
  elif requested_focus=='sphere-mission' and mission:focus_type='sphere-mission';status=mission['status'];next_action='inspect actual role checks and retained result'
  elif requested_focus=='relevant-experiment' and experiments:focus_type='experiment';status='failed' if experiments[-1]['revoked'] else 'checked';next_action='repair the revoked procedure' if status=='failed' else 'compare additional independent cases before generalising'
  elif requested_focus=='workflow-check':focus_type='workflow-evidence';status='checked' if workflow_check_passed else 'revoked';next_action='inspect the counterexample and dependency status'
  elif requested_focus=='example-plan' and plans:focus_type='learned-procedure';status=plans[-1]['status'];next_action='use the validated procedure on a fresh input' if status=='validated-candidate' else 'supply more training evidence or a different operation family'
  elif requested_focus=='inquiry' and inquiry:focus_type='inquiry';status=inquiry['status'];next_action=inquiry['next_question']
  elif requested_focus=='code' and code_review:focus_type='code';status='checked' if code_review.get('checks',{}).get('all_passed') else 'review-required';next_action='inspect code checks and their covered inputs'
  elif requested_focus=='native':focus_type='native-operation';status='complete';next_action='inspect the operation-specific verification or give the next request'
  elif requested_focus=='goal' and goal_view:focus_type='goal';status=goal_view['status'];next_action='review checked result' if goal_view['committed'] else 'correct the failed stage or supply another task'
  elif requested_focus=='workflow' and last_work:focus_type='workflow';status='complete';next_action='inspect the result, export checked Python, or save this procedure'
  elif requested_focus=='workflow-lesson':focus_type='learning-session';status='needs-input';next_action='supply training and separate validation examples'
  elif requested_focus=='task' and task_view:focus_type='task';status=task_view['status'];next_action=task_view['conclusion']
  else:focus_type='practice';status='waiting';next_action='supply a task or observed examples'
  state={'focus_type':focus_type,'status':status,'next_action':next_action,'goal':goal_view,'inquiry':inquiry,'task':task_view,'learning':learning,'last_work':last_work,'code_review':code_review,'artifacts':artifacts,'relevant_experiments':experiments,'sphere_mission':mission}
  state['reasoning_episode']=episode
  state['general_reasoning']=general
  state['open_reasoning']=opened
  functions=getattr(self.c,'sphere_functions',None)
  if functions:
   with functions.lock:state['ambient_reasoning']=functions.ambient_reasoning.view()
  if hasattr(self.c,'episode_bus'):state['episode_bus']=self.c.episode_bus.view()
  compiler=getattr(self.c,'stochastic_structure',None)
  if compiler:state['stochastic_logic']=compiler.view(summary=True)
  signature=hashlib.sha256(json.dumps(state,sort_keys=True,ensure_ascii=True).encode()).hexdigest()
  with self.lock:
   if signature!=self.signature:
    self.signature=signature;self.sequence+=1;event={'sequence':self.sequence,'time':time.time(),'focus_type':focus_type,'status':status,'state_sha256':signature};self.events=(self.events+[event])[-48:]
    self.pending=(self.pending+[{'origin':'sphere-workspace','target':'all','kind':'stage-output','payload':{**event,'processing_receipt':True,'model_calls':0,'provenance':'shared native workspace state receipt; no source claim promoted to fact'}}])[-32:]
   cycle_ms=(time.perf_counter()-started)*1000;self.max_cycle_ms=max(self.max_cycle_ms,cycle_ms);self.last_cycle=time.time();self.error=None
   self.latest={**state,'sequence':self.sequence,'last_action':action,'cycle_ms':round((time.perf_counter()-started)*1000,3),'activity':activity,'model_calls':0,'evidence_policy':'Observed examples, separate validation, operation checks and committed receipts are different evidence types. Source text and generated symbols are not automatically facts.','roles':{'original/combined/inverse':'alternative projections of captured data, not independent confirmations','experiment/synthesis':'bounded hypothesis tests; synthetic practice stays labelled','whole-mind-study':'shared goal, evidence, chosen test, checked result and retained procedure','self-analysis':'service errors, regressions, stalled tasks and processing costs'},'scope':'Bounded native reasoning shared by sphere views; rendering speed and node count do not establish intelligence.'}
  return copy.deepcopy(self.latest)
 def loop(self):
  while not self.c.halt.is_set():
   started=time.perf_counter()
   try:
    if self.c.enabled:self.step()
   except Exception as exc:
    with self.lock:self.error=type(exc).__name__+': '+str(exc)[:250]
   policy=getattr(self.c,'activity_policy',None);settings=policy.for_circuit(self.c) if policy else {'workspace_interval_seconds':.25,'duty_target':.25}
   cost=time.perf_counter()-started;duty=settings['duty_target']
   self.c.halt.wait(max(settings['workspace_interval_seconds'],cost*(1-duty)/duty))
 def view(self):
  with self.lock:return {**copy.deepcopy(self.latest),'recent':copy.deepcopy(self.events),'error':self.error,'worker_active':bool(self.worker and self.worker.is_alive()),'health':{'last_cycle_age_seconds':round(max(0,time.time()-self.last_cycle),3) if self.last_cycle else None,'max_cycle_ms':round(self.max_cycle_ms,3),'stale':bool(self.last_cycle and time.time()-self.last_cycle>3)}}
 def drain(self):
  with self.lock:events=self.pending;self.pending=[];return events
 def close(self):
  if self.worker and self.worker is not threading.current_thread():self.worker.join(2)
  d=self.dialogue
  if self.dirty and d.path:
   from .deliberation import Deliberation
   with d.lock:
    Deliberation.write_json(d.path,{'messages':d.messages,'memory':d.memory,'selected':d.selected,'work':d.work.state});self.dirty=False
