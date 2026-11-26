"""Function-specific, bounded work for every Whole Engine sphere.

Consumes existing observations and retrieved references; never executes source text.
Forecasts concern the next observation of the same numeric channel, not arbitrary events.
"""
import copy
import hashlib
import json
import math
import statistics
import threading
import time
import functools
from urllib.parse import urlsplit

PROFILES = {
 'original': ('capture', 'source provenance information preservation'),
 'selected': ('selection', 'decision selection validation'),
 'unmodulated': ('comparison', 'controlled experiment modulation baseline'),
 'combined': ('integration', 'data integration provenance'),
 'inverse-combined': ('comparison', 'inversion reversible transformation'),
 'experiment': ('experiment', 'hypothesis testing falsification'),
 'total-plane': ('integration', 'coordinate transformation information preservation'),
 'plane-rotated-positive': ('geometry', 'orthogonal rotation norm preservation'),
 'plane-rotated-inverse': ('geometry', 'orthogonal rotation norm preservation'),
 'plane-three-combined': ('integration', 'coordinate copies independent evidence'),
 'potential-zero': ('comparison', 'zero baseline information loss'),
 'neural-space': ('topology', 'graph connectivity source routing'),
 'neural-inverse': ('topology', 'graph inversion connectivity'),
 'neural-combined': ('topology', 'graph combination duplicate evidence'),
 'neural-overse': ('topology', 'graph outer node connectivity'),
 'neural-all-three': ('topology', 'graph integration connectivity'),
 'synthesis': ('synthesis', 'evidence synthesis uncertainty conflicting evidence'),
 'choice-study': ('selection', 'decision alternatives validation'),
 'action-study': ('action', 'execution verification expected outcome'),
 'consequence-study': ('forecast', 'forecast error baseline time series'),
 'choice-action-consequence': ('integration', 'decision action outcome feedback'),
 'whole-mind-study': ('coordination', 'task planning feedback verification'),
 'self-analysis': ('diagnosis', 'failure measurement regression diagnosis'),
 'mind-improvement': ('improvement', 'regression testing controlled improvement'),
 'source-study': ('research', 'source provenance research evidence'),
 'atomic-theory': ('theory', 'atomic physics hypothesis units measurement'),
 'etiquette-study': ('training', 'communication etiquette evaluation'),
 'platform-study': ('training', 'operating system command verification'),
 'ethical-hacking-research': ('research', 'vulnerability disclosure incident response'),
 'souls-digits-research': ('research', 'social protection welfare policy evaluation'),
 'power-influence-research': ('research', 'ownership lobbying documentary evidence'),
 'cosmic-emergence-research': ('theory', 'cosmology nucleosynthesis evidence'),
 'spectrum-logic': ('experiment', 'randomness structure logic truth table'),
 'thought-cloud': ('synthesis', 'working memory evidence synthesis'),
}

def snapshot(c, lane):
 if lane=='whole-mind-study' and hasattr(c.whole_mind_study,'frame'):
  service=c.whole_mind_study
  with service.lock:
   frame=service.frame
   return {'sequence':frame.get('sequence',0),'particles':[{k:copy.deepcopy(p[k]) for k in ('id','point','source','path','source_digest','selected') if k in p} for p in frame.get('particles',[])[:512]],'thought_trace':compact(frame.get('thought_trace',[])),'role_task':compact(frame.get('role_task',{})),'network_intake':compact(frame.get('network_intake',{})),'snapshot_scope':'Bounded function-specific input; full visual frame remains available separately.'}
 direct = {'whole-mind-study':'whole_mind_study','original':'expression_sphere',
  'selected':'selection_sphere','combined':'system_flux_sphere','experiment':'experiment_sphere',
  'total-plane':'total_plane_sphere','potential-zero':'potential_zero_sphere',
  'neural-space':'neural_space','synthesis':'synthesis_sphere','thought-cloud':'thought_cloud'}
 if lane in direct:return getattr(c,direct[lane]).view()
 if lane=='unmodulated':return copy.deepcopy(c.selection_sphere.unmodulated)
 if lane=='inverse-combined':return c.system_flux_sphere.inverse_view()
 if lane.startswith('plane-'):return c.plane_orientations.view(lane)
 if lane.startswith('neural-'):return c.neural_topology_views.view(lane)
 if lane in ('choice-study','action-study','consequence-study','choice-action-consequence'):return c.choice_action_study.view(lane)
 if lane.endswith('-research'):return c.principle_research.sphere(lane)
 service={'self-analysis':'self_analysis','mind-improvement':'mind_improvement','source-study':'source_study',
  'atomic-theory':'periodic_study','etiquette-study':'email_trainer','platform-study':'platform_trainer','spectrum-logic':'spectrum_logic'}[lane]
 return getattr(c,service).sphere() if lane in ('self-analysis','mind-improvement','spectrum-logic') else getattr(c,service).sphere(c)

def evidence(frame):
 rows=[]
 intake=frame.get('network_intake',{})
 for key in ('recent','sources'):
  if isinstance(intake.get(key),list):rows.extend(intake[key][:64])
 if isinstance(intake.get('latest'),dict):rows.append(intake['latest'])
 rows.extend(r for r in frame.get('thought_trace',[])[:64] if isinstance(r,dict))
 unique={}
 for row in rows:
  url=row.get('url') or row.get('source')
  if not isinstance(url,str) or urlsplit(url).scheme not in ('http','https'):continue
  excerpts=row.get('excerpts') or row.get('excerpt') or row.get('summary') or ''
  text=json.dumps(excerpts,ensure_ascii=False)[:4000] if not isinstance(excerpts,str) else excerpts[:4000]
  retrieved=row.get('status')=='retrieved' and bool(text.strip())
  digest=hashlib.sha256(text.encode()).hexdigest() if text else None
  if url in unique and unique[url]['status']=='retrieved-text' and not retrieved:continue
  unique[url]={'url':url,'title':str(row.get('title',''))[:180],'publisher':urlsplit(url).hostname,
   'status':'retrieved-text' if retrieved else 'reference-only','content_sha256':digest,
   'excerpt':text[:700],'retrieved_at':row.get('time',row.get('fetched'))}
 return list(unique.values())[:32]

def geometry(frame):
 points=[p for p in frame.get('particles',[])[:512] if isinstance(p,dict)]
 coords=[p.get('point') for p in points]
 valid=[p for p in coords if isinstance(p,list) and len(p)==3 and all(type(v) in (int,float) and math.isfinite(v) for v in p)]
 identities=[(p.get('source'),json.dumps(p.get('path',[]),sort_keys=True),p.get('source_digest')) for p in points]
 return {'sampled_nodes':len(points),'finite_xyz':len(valid),'invalid_xyz':len(points)-len(valid),
  'distinct_source_paths':len(set(identities)), 'selected_nodes':sum(bool(p.get('selected')) for p in points),
  'mean_radius':statistics.fmean(math.sqrt(sum(v*v for v in p)) for p in valid) if valid else None,
  'scope':'Bounded displayed-node sample; coordinate copies do not count as independent sources.'}

def compact(value,depth=0):
 if depth>7:return '[nested detail omitted; original sphere retains full record]'
 if isinstance(value,str):return value[:1200]
 if isinstance(value,list):return [compact(v,depth+1) for v in value[:12]]
 if isinstance(value,dict):return {str(k):compact(v,depth+1) for k,v in list(value.items())[:24]}
 return value

@functools.lru_cache(maxsize=64)
def topic_references(topic):
 from .knowledge_library import search
 return search(topic,3)

def evidence_kind(source,row):
 declared=row.get('evidence_origin')
 if declared in ('measured','modelled','generated','derived','user-supplied'):return declared
 if any(t in source for t in ('ascii','matrix','ternary','expression','recursive','potential','weight-data','flux','backbone')):return 'generated'
 return 'unknown'

def stable(value):
 if isinstance(value,dict):return {k:stable(v) for k,v in value.items() if k not in ('time','updated_at','issued_at','observed_at','mean_radius')}
 if isinstance(value,list):return [stable(v) for v in value]
 return value

def topology(frame):
 nodes={p.get('id') for p in frame.get('particles',[])[:2048] if isinstance(p,dict) and p.get('id')}
 edges=frame.get('connections',[])[:4096];adj={n:set() for n in nodes};dangling=0
 for edge in edges:
  a,b=edge.get('source'),edge.get('target')
  if a not in nodes or b not in nodes:dangling+=1;continue
  adj[a].add(b);adj[b].add(a)
 unseen=set(nodes);sizes=[]
 while unseen:
  todo=[unseen.pop()];size=0
  while todo:
   n=todo.pop();size+=1;fresh=adj[n]&unseen;unseen.difference_update(fresh);todo.extend(fresh)
  sizes.append(size)
 return {'sampled_nodes':len(nodes),'sampled_edges':len(edges),'dangling_edges':dangling,
  'connected_components':len(sizes),'largest_component':max(sizes,default=0),'isolated_nodes':sum(not a for a in adj.values()),
  'scope':'Connectivity on bounded displayed graph sample. Dangling endpoints may lie outside the sample; graph reachability is not external device access.'}

def record_checks(frame):
 outcomes=[]
 def walk(v,path=(),depth=0):
  if len(outcomes)>=64 or depth>6:return
  if isinstance(v,dict):
   for k,val in list(v.items())[:24]:
    if k in ('passed','matched','all_passed','verified') and type(val) is bool:outcomes.append({'path':list(path)+( [k]),'passed':val})
    elif isinstance(val,(dict,list)):walk(val,path+(str(k),),depth+1)
  elif isinstance(v,list):
   for i,row in enumerate(v[:16]):walk(row,path+(str(i),),depth+1)
 walk(frame.get('thought_trace',[]),('thought_trace',));walk(frame.get('role_task',{}),('role_task',))
 return {'recorded_checks':outcomes,'passed':sum(r['passed'] for r in outcomes),'failed':sum(not r['passed'] for r in outcomes),
  'scope':'Recorded check flags, not independent re-execution. Synthetic test results retain their original scope.'}

class SphereFunctions:
 def __init__(self,path=None):
  self.lock=threading.RLock();self.path=path;self.cursor=0;self.next_at=0;self.records={};self.channels={};self.sequence=0;self.pending=[];self.last_save=0
  from .fair_slices import FairSlices
  from .sphere_ambient_reasoning import AmbientSphereReasoning
  self.ambient_reasoning=AmbientSphereReasoning(expected_roles=len(PROFILES),skill_path=path.with_name('ambient-rule-skills.json') if path else None)
  self.scheduler=FairSlices();self.lane_retry_at={};self.next_observe=0;self.source_cursor=0;self.lane_costs={}
  if path and path.exists():
   try:
    data=json.loads(path.read_text(encoding='utf-8'));self.channels=data.get('channels',{});self.records=data.get('records',{});self.sequence=data.get('sequence',0)
   except (OSError,ValueError,TypeError):pass

 def observe_numbers(self,sources):
  """Prequential evaluation: score the old forecast before learning the new value."""
  for source,row in list(sources.items())[:128]:
   if source.startswith('sphere-function'):continue
   facts=row.get('facts',[]);offset=(self.cursor*16)%max(1,len(facts));facts=facts[offset:]+facts[:offset]
   for fact in facts[:16]:
    value=fact.get('value')
    if type(value) not in (int,float) or abs(value)>1e100 or not math.isfinite(value):continue
    path=fact.get('path',[]);key=hashlib.sha256(json.dumps([source,path],sort_keys=True).encode()).hexdigest()[:24]
    event=json.dumps([row.get('parent_event'),row.get('digest')],sort_keys=True)
    ch=self.channels.get(key)
    if ch and ch['event']==event:continue
    kind=evidence_kind(source,row)
    if not ch:
     if kind in ('generated','derived') and sum(c.get('evidence_origin') in ('generated','derived') for c in self.channels.values())>=128:continue
     if len(self.channels)>=256:
      eligible=[(k,c) for k,c in self.channels.items() if time.time()-c.get('last_seen',0)>300 or kind=='measured' and c.get('evidence_origin')!='measured']
      if not eligible:continue
      victim=min(eligible,key=lambda pair:pair[1].get('last_seen',0))[0];self.channels.pop(victim)
     ch={'source':source,'path':path,'values':[],'scores':{'persistence':{'n':0,'absolute_error':0.},'trend':{'n':0,'absolute_error':0.}},'forecast':None}
    if ch['forecast']:
     old=ch['forecast'];errors={m:abs(value-pred) for m,pred in old['candidates'].items()}
     for m,error in errors.items():ch['scores'][m]['n']+=1;ch['scores'][m]['absolute_error']+=error
     ch['last_check']={'forecast_at':old['issued_at'],'observed_at':time.time(),'actual':value,'errors':errors,'selected_before_observation':old['selected']}
    values=(ch['values']+[value])[-32:];candidates={'persistence':value}
    if len(values)>1:candidates['trend']=value+statistics.median([b-a for a,b in zip(values[-9:],values[-8:])]) if len(values)>8 else value+statistics.median([values[i]-values[i-1] for i in range(1,len(values))])
    selected=min(candidates,key=lambda m:(ch['scores'][m]['absolute_error']/ch['scores'][m]['n'] if ch['scores'][m]['n']>=3 else float('inf'),m!='persistence'))
    ch.update(values=values,event=event,last_seen=time.time(),evidence_origin=kind,units=row.get('units',{}),forecast={'issued_at':time.time(),'candidates':candidates,'selected':selected,'prediction':candidates[selected],'target':'next distinct captured event on this source/path; no fixed wall-clock horizon'})
    self.channels[key]=ch

 def process(self,lane,frame,workspace):
  role,topic=PROFILES[lane];geo=geometry(frame);refs=evidence(frame)
  library=topic_references(topic)
  research={'question':topic,'sources':refs,'reference_matches':library,'retrieved_texts':sum(r['status']=='retrieved-text' for r in refs),
   'distinct_publishers':len({r['publisher'] for r in refs if r['status']=='retrieved-text'}),
   'duplicate_text_groups':len([h for h in {r['content_sha256'] for r in refs if r['content_sha256']} if sum(r['content_sha256']==h for r in refs)>1]),
   'conclusion':'Retrieved text is evidence to examine; publisher count alone does not establish correctness. Reference-only entries are not completed research.'}
  checks=[];result={};next_step='Collect additional relevant observations.'
  if role in ('capture','selection','comparison','integration','geometry'):
   checks=[{'name':'finite displayed coordinates','passed':geo['invalid_xyz']==0 if geo['sampled_nodes'] else None,'tested':geo['sampled_nodes']}]
   result={'representation_audit':geo,'task_role':frame.get('role_task'),'checks':checks}
   next_step='Inspect failed representation checks.' if geo['invalid_xyz'] else 'Retain source identities when combining or transforming observations.'
  elif role=='topology':
   result={'node_audit':geo,'connectivity':topology(frame),'connection_fields':[k for k in frame if any(t in k for t in ('edge','connect','topolog'))],
    'limitation':'Displayed connections describe routing; semantic learning requires task evidence.'}
   next_step='Compare routing coverage with successful downstream task receipts.'
  elif role in ('experiment','action','training'):
   traces=[r for r in frame.get('thought_trace',[]) if isinstance(r,dict)][-12:]
   result={'actual_records':traces,'task_role':frame.get('role_task'),'check_summary':record_checks(frame),'tested_records':sum(any(k in r for k in ('passed','matched','checks','result')) for r in traces)}
   next_step='Run an unseen task and record acceptance checks; generated examples alone are not a passed test.'
  elif role=='forecast':
   result={'channels':copy.deepcopy(list(self.channels.values())[:12]),'scope':'Next-observation numeric forecasts from actual captured channels; persistence baseline, trend alternative and error scores. Not causal certainty.'}
   next_step='Wait for new independent channel observations, then score forecasts before updating them.'
  elif role in ('diagnosis','improvement','coordination'):
   result={'workspace_status':workspace.get('status'),'workspace_error':workspace.get('error'),
    'next_action':workspace.get('next_action'),'last_work':workspace.get('last_work'),'mission':workspace.get('sphere_mission')}
   next_step='Investigate recorded failures before proposing changes.' if workspace.get('error') or workspace.get('status')=='failed' else 'Compare a proposed change against unchanged baseline and regression tasks.'
  else:
   result={'evidence_groups':{'retrieved':[r['url'] for r in refs if r['status']=='retrieved-text'],'not_retrieved':[r['url'] for r in refs if r['status']!='retrieved-text']},
    'hypothesis':{'statement':'Relevant source material may support a testable model for '+topic,'status':'proposal','test':'Specify measurable output, units, independent observation and a failure condition.'}}
   next_step='Compare actual source passages, retain disagreements and test the proposed model.'
  ambient_work=self.ambient_reasoning.process(lane,role)
  result['ambient_reasoning']=ambient_work
  episode=workspace.get('reasoning_episode')
  signature=hashlib.sha256(json.dumps(stable([result,refs,{'id':episode['id'],'sequence':episode['sequence']} if episode else None]),sort_keys=True,default=str).encode()).hexdigest()
  prior=self.records.get(lane,{})
  record={'lane':lane,'function':role,'question':topic,'status':'processed' if ambient_work.get('status')=='completed' or frame.get('sequence',0) or frame.get('particles') else 'waiting-for-source',
   'updated_at':time.time(),'source_sequence':frame.get('sequence',0),'revision':prior.get('revision',0)+(signature!=prior.get('input_signature')),
   'input_signature':signature,'ambient_reasoning':ambient_work,'result':compact(result),'research':compact(research),'next_step':next_step,'model_calls':0}
  if episode:
   record['reasoning_episode']={'id':episode['id'],'name':episode['name'],'status':episode['status'],'phase':episode['phase'],
    'owned_steps':[r for r in episode.get('trace',[]) if r['role']==lane],
    'shared_findings':compact(episode.get('artifacts',{})),'scope':'Role-owned recorded steps plus shared evidence; views of the same episode are not independent experiments.'}
  self.records[lane]=record;self.sequence+=1
  if signature!=prior.get('input_signature'):
   self.pending.append({'origin':'sphere-function/'+lane,'target':'all','kind':'stage-output','payload':{'processing_receipt':True,'function':role,'revision':record['revision'],'status':record['status'],'model_calls':0,'record_signature':signature,'result':compact(result),'next_step':next_step}})
  return record

 def tick(self,c):
  if time.monotonic()<self.next_at:return
  settings=c.activity_policy.for_circuit(c) if getattr(c,'activity_policy',None) else {'multiplier':1,'duty_target':.25}
  self.next_at=time.monotonic()+max(.08,.2/max(.25,settings['multiplier']))
  # Never hold the circuit lock while acquiring the native workspace lock.
  if hasattr(c.sphere_workspace,'latest'):
   with c.sphere_workspace.lock:workspace=copy.deepcopy({key:c.sphere_workspace.latest.get(key) for key in ('status','error','next_action','last_work','sphere_mission','reasoning_episode')})
  else:workspace=c.sphere_workspace.view()
  if time.monotonic()>=self.next_observe:
   with c.lock:
    entries=list(c.sources.items());sources=dict(entries[self.source_cursor:self.source_cursor+32]);self.source_cursor=(self.source_cursor+32)%max(1,len(entries));sources=copy.deepcopy(sources)
   with self.lock:self.observe_numbers(sources)
   self.next_observe=time.monotonic()+.5
  chain=getattr(c,'ascii_chain',None)
  if chain is not None:
   with c.lock:generated=[{k:copy.deepcopy(row.get(k)) for k in ('source','raw','digest','parent_event','generated','conditions')} for row in list(chain.sources.values()) if row.get('generated')][:32]
   learned=chain.emergence.view(detail=True).get('heldout_pattern_checks',{})
   with self.lock:self.ambient_reasoning.ingest(generated,learned)
  def visit(lane,_):
   self.cursor+=1
   if time.monotonic()<self.lane_retry_at.get(lane,0):return
   began=time.perf_counter();error=None
   try:
    if lane in ('choice-study','action-study','consequence-study','choice-action-consequence') and getattr(c,'choice_action_study',None):c.choice_action_study.tick(c)
    with self.lock:ambient_result=self.ambient_reasoning.process(lane,PROFILES[lane][0])
    frame=snapshot(c,lane)
    with self.lock:self.process(lane,frame,workspace)
   except Exception as exc:
    error=type(exc).__name__+': '+str(exc)[:180]
    with self.lock:self.records[lane]={'lane':lane,'function':PROFILES[lane][0],'status':'error','ambient_reasoning':self.ambient_reasoning.process(lane,PROFILES[lane][0]),'error':type(exc).__name__+': '+str(exc)[:180],'updated_at':time.time()}
   elapsed=time.perf_counter()-began;self.lane_costs[lane]={'elapsed_ms':elapsed*1000,'error':error}
   self.lane_retry_at[lane]=time.monotonic()+(2 if error else min(5.,elapsed*4) if elapsed>.05 else 0)
  self.scheduler.run(list(PROFILES.items()),visit,limit=12 if settings['multiplier']>=1 else 3,budget_seconds=.025 if settings['multiplier']>=1 else .01)
  with self.lock:
   self.pending=self.pending[-128:]
   if self.path and time.monotonic()-self.last_save>30:
    from .deliberation import Deliberation
    self.ambient_reasoning.physics_discovery.flush();self.ambient_reasoning.rule_lab.flush();Deliberation.write_json(self.path,{'records':self.records,'channels':self.channels,'sequence':self.sequence});self.last_save=time.monotonic()

 def loop(self,c):
  while not c.halt.is_set():
   started=time.monotonic()
   try:
    if c.enabled:self.tick(c)
   except Exception as exc:
    with self.lock:self.records['_worker']={'status':'error','error':str(exc)[:180]}
   # Separate bounded worker: slow source views cannot hold up the main thinking loop.
   settings=c.activity_policy.for_circuit(c) if getattr(c,'activity_policy',None) else {'multiplier':1,'duty_target':.25}
   duty=settings.get('duty_target',.25);cost=time.monotonic()-started
   c.halt.wait(max(.08,.2/max(.25,settings['multiplier']),cost*(1-duty)/duty))

 def view(self,lane=None):
  with self.lock:
   if lane:
    record=copy.deepcopy(self.records.get(lane,{'lane':lane,'status':'waiting','function':PROFILES.get(lane,('unknown',))[0]}))
    record['scheduler_health']={'last_processed_age_seconds':max(0,time.time()-record['updated_at']) if record.get('updated_at') else None,'visits':self.scheduler.calls.get(lane,0),'last_cost':copy.deepcopy(self.lane_costs.get(lane)), 'retry_in_seconds':max(0,self.lane_retry_at.get(lane,0)-time.monotonic())}
    return record
   return {'sequence':self.sequence,'registered':len(PROFILES),'processed':len(self.records),'records':copy.deepcopy(self.records),'ambient_reasoning':self.ambient_reasoning.view(),'numeric_channels':len(self.channels),'scheduler':copy.deepcopy(self.scheduler.last),'lane_costs':copy.deepcopy(self.lane_costs)}

 def decorate(self,lane,frame):
  work=self.view(lane);ambient=work.get('ambient_reasoning') or {};finding=ambient.get('finding') or {};seed=ambient.get('source_sha256','0'*64)
  nodes=[]
  for i,name in enumerate(('source','hypothesis','choice','experiment','forecast','feedback')):
   angle=2*math.pi*i/6
   nodes.append({'id':'ambient-'+name,'point':[math.cos(angle)*.9,math.sin(angle)*.9,.15],'symbol':str(i+1),'phase':1,'selected':ambient.get('status')=='completed','source':ambient.get('source'),'source_digest':seed,'thought_stage':name,'case_id':ambient.get('case_id'),'birth':ambient.get('updated_at'),'scope':'Generated-source reasoning trace node; not a new physical observation.'})
  return {**frame,'functional_work':work,'ambient_reasoning_nodes':nodes if ambient.get('status')=='completed' else []}

 def drain(self):
  with self.lock:rows=self.pending;self.pending=[];return rows

 def close(self,c):
  worker=getattr(c,'sphere_function_worker',None)
  if worker and worker is not threading.current_thread():worker.join(3)
  if self.path:
   from .deliberation import Deliberation
   with self.lock:self.ambient_reasoning.physics_discovery.flush();self.ambient_reasoning.rule_lab.flush();Deliberation.write_json(self.path,{'records':self.records,'channels':self.channels,'sequence':self.sequence})
