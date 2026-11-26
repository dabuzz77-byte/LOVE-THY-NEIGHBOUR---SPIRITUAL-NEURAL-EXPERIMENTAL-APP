"""Inert choice/action projections from bounded shared engine observations."""
from .action_ethics import study_frame
import copy,hashlib,math,time,threading,json
class ChoiceActionStudy:
 def __init__(self):
  self.next_at=0;self.sequence=0;self.frames={};self.lock=threading.RLock();self.source_cursor=0;self.fact_cursors={};self.source_versions={};self.processed=0;self.idle_passes=0;self.mission_frames={};self.numeric_history={};self.latest_cost_ms=0
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  started=time.perf_counter();self.next_at=time.monotonic()+.4
  d=getattr(getattr(c,'whole_mind_study',None),'native_dialogue',None)
  if d:
   with d.lock:mission=copy.deepcopy(d.work.state.get('sphere_mission'))
   if mission:
    from .sphere_mission import frames
    actual=frames(mission);stamp=(mission['name'],mission['created'],mission['sequence'],mission['status'])
    with self.lock:self.mission_frames=actual
    if stamp!=getattr(self,'last_mission_stamp',None):
     self.last_mission_stamp=stamp;c.bus.publish({'origin':'choice-action-study','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'task_status':mission['status'],'role_phase':mission['phase'],'role_records':len(mission['trace']),'committed':mission['committed'],'provenance':'actual bounded sphere-task role results'}})
   else:
    with self.lock:self.mission_frames={}
  with c.lock:
   sources=list(c.sources.values());goal=c.goal;rows=[];count=len(sources)
   names={s['source'] for s in sources};self.source_versions={k:v for k,v in self.source_versions.items() if k in names};self.fact_cursors={k:v for k,v in self.fact_cursors.items() if k in names}
   for offset in range(min(count,64)):
    source=sources[(self.source_cursor+offset)%count]
    if source['source']=='choice-action-study' or not source.get('facts'):continue
    progress=self.source_versions.get(source['source'])
    if progress is None or progress['digest']!=source.get('digest'):
     progress={'digest':source.get('digest'),'paths':set()};self.source_versions[source['source']]=progress
    facts=source['facts'];cursor=self.fact_cursors.get(source['source'],0)
    for step in range(len(facts)):
     index=(cursor+step)%len(facts);fact=facts[index];identity=json.dumps(fact.get('path',[]),sort_keys=True)
     if identity in progress['paths']:continue
     rows.append({'source':source['source'],'event':source.get('parent_event'),'fact':copy.deepcopy(fact),'digest':source.get('digest')});self.fact_cursors[source['source']]=(index+1)%len(facts)
     progress['paths'].add(identity)
     break
    if len(rows)>=32:break
   self.source_cursor=(self.source_cursor+max(1,min(count,32)))%max(1,count)
  if not rows:
   self.idle_passes+=1;self.next_at=time.monotonic()+1
   with self.lock:
    for frame in self.frames.values():frame.setdefault('rate_control',{}).update(last_batch_values=0,idle_passes=self.idle_passes,is_idle=True)
   return
  self.sequence+=1
  decisions=[];actions=[];consequences=[];combined=[]
  for row in rows:
   alternatives=[{'choice':'preserve','effect':'Keep original value and lineage unchanged.','known_cost':'One retained reference','unknown':'Downstream relevance to current goal'},{'choice':'summarise','effect':'Create a bounded derivative while retaining original lineage.','known_cost':'May omit detail','unknown':'Whether omitted detail is important'},{'choice':'defer','effect':'Wait for additional context without discarding the original.','known_cost':'Delay','unknown':'Cost of delay in any real situation'}]
   decision={**row,'ethical_study':study_frame(row['source'],self.sequence),'alternatives':alternatives,'selected':'preserve','reason':'Preserve provenance while the study lacks an independently specified outcome target.','four_way':{'true_good':'Useful information supporting provision and dignity','false_good':'A plausible prediction concealing omitted costs','false_evil':'Rejecting a useful option merely because it challenges a metric','true_evil':'Known harmful consequences or deceptive provenance'},'world_projection':'Public knowledge may inform a hypothesis; no external system state or actor intent is assumed.'}
   decisions.append(decision)
   actions.append({**row,'proposed_action':'Create a labelled local study derivative','preconditions':['Source event retained','Value has valid lineage'],'steps':['Read captured value','Copy into experimental record','Check original unchanged','Return numerical study summary to shared bus'],'expected_result':'A traceable projection, not an executed real-world action','checks':{'original_preserved':True,'external_execution':False,'host_execution':False},'rollback':'Discard the derivative; original remains unchanged.','unknowns':['Real-world effects require an operation-specific model and observations'],'choice_basis':decision['selected']})
  for decision,action in zip(decisions,actions):
   value=decision['fact'].get('value');encoded=json.dumps(value,ensure_ascii=True,sort_keys=True);roundtrip=json.loads(encoded)
   exact=roundtrip==value
   profile={'value_type':type(value).__name__,'encoded_characters':len(encoded),'preview':str(value)[:120],'lossless_roundtrip':exact}
   if isinstance(value,str):profile.update(characters=len(value),words=len(value.split()),unique_characters=len(set(value)))
   if type(value) in (int,float) and abs(value)<=1e100 and math.isfinite(value):
    key=(decision['source'],json.dumps(decision['fact'].get('path',[])));previous=self.numeric_history.get(key)
    if previous is not None:
     profile['numeric_transition']={'previous':previous['value'],'actual':value,'change':value-previous['value'],'previous_event':previous['event'],'current_event':decision['event']}
     if 'prediction' in previous:profile['prediction_check']={'predicted':previous['prediction'],'actual':value,'absolute_error':abs(value-previous['prediction']),'scope':'One-step linear extrapolation across captured events, not a world forecast'}
     predicted=value+(value-previous['value'])
    else:predicted=None
    self.numeric_history[key]={'value':value,'event':decision['event'],**({'prediction':predicted} if predicted is not None and math.isfinite(predicted) else {})}
    while len(self.numeric_history)>512:self.numeric_history.pop(next(iter(self.numeric_history)))
   action['executed_local_derivative']=profile;action['checks']['derivative_computed']=True
   branches=[{'choice':'preserve','direct_effect':'Original retained; copied value compared after JSON round trip','observed_test':{'roundtrip_equal':exact,'encoded_characters':len(encoded)},'downstream':'Consumers retain the original reference and lineage.'},{'choice':'summarise','direct_effect':'Preview limited to 120 characters','observed_test':{'original_characters':len(str(value)),'preview_characters':min(120,len(str(value))),'detail_omitted':len(str(value))>120},'downstream':'A preview may omit important detail; preserve the original for inspection.'},{'choice':'defer','direct_effect':'No processing of this value in the hypothetical next slot','observed_test':{'simulated_slots_delayed':1},'downstream':'Processing is delayed; real-world cost of delay is not known from a captured value alone.'}]
   record={**{k:decision[k] for k in ('source','event','fact','digest')},'branches':branches,'affected_beings':{'people':'Identify actual service users and workers before applying the model.','animals_and_ecology':'Identify dependencies and exposure; absence of data does not imply absence of effects.'},'time_horizons':['Immediate data transformation','Downstream consumer dependencies','Long-term consequences requiring separate evidence'],'reversibility':'Study derivatives can be discarded; original data is retained.','four_way':decision['four_way'],'unknowns':['Probability and severity of real-world harm or benefit','Unobserved dependencies','Distribution of effects and costs of inaction'],'checks':{'external_execution':False,'original_preserved':True,'roundtrip_equal':exact},'summary':'Consequence branches tested locally; wider consequences remain explicitly modelled questions.'}
   consequences.append(record)
   combined.append({**{k:decision[k] for k in ('source','event','fact','digest')},'choice':decision,'action':action,'consequence':record,'summary':'Choice → action plan → tested local consequences → review','review':{'selected':decision['selected'],'reason':decision['reason'],'needs_more_information':True},'feedback':'Numerical study counts return to all registered stages, not raw source content.'})
  self.processed+=len(rows)
  for record,action in zip(consequences,actions):record['local_observation']=copy.deepcopy(action['executed_local_derivative'])
  def frame(kind,records):
   particles=[]
   for i,row in enumerate(records):
    h=hashlib.sha256((kind+row['source']).encode()).hexdigest();a=int(h[:8],16)/0xffffffff*math.tau+self.sequence*.08;y=1-2*(i+.5)/max(1,len(records));radius=math.sqrt(max(0,1-y*y))
    particles.append({'id':kind+':'+h[:16],'point':[radius*math.cos(a),y,radius*math.sin(a)],'phase':1.,'autonomy':0.,'selected':True,'expression_type':{'choice-study':'choice','action-study':'action-plan','consequence-study':'consequence','choice-action-consequence':'integrated-study'}[kind],'symbol':'◇' if kind=='choice-study' else '→','value_preview':row.get('selected',row.get('proposed_action',row.get('summary',''))),'source':row['source'],'path':row['fact'].get('path',[]),'parent_event':row['event'],'source_digest':row['digest'],'record':row})
   return {'sequence':self.sequence,'particles':particles,'retained_sources':len(sources),'represented_values':len(records),'received_events':sum(1 for _ in rows),'selected_phases':[1.],'goal':goal,'thought_trace':records,'represented_forms':['captured variables','choices','plans','tests'],'scope':'Safe experimental study only. Finite alternatives and captured sources; no external actions, device access or automatic verdicts about people. Existing source renderers provide visual forms; arbitrary manifestation is not implemented.'}
  with self.lock:
   self.frames={'choice-study':frame('choice-study',decisions),'action-study':frame('action-study',actions),'consequence-study':frame('consequence-study',consequences),'choice-action-consequence':frame('choice-action-consequence',combined)}
   self.latest_cost_ms=(time.perf_counter()-started)*1000;interval=max(.4,min(2.,self.latest_cost_ms/1000*20));self.next_at=time.monotonic()+interval
   for value in self.frames.values():value['rate_control']={'interval_seconds':interval,'batch_limit':32,'processed_values':self.processed,'last_batch_values':len(rows),'last_compute_ms':self.latest_cost_ms,'idle_passes':self.idle_passes,'is_idle':False,'mode':'change-driven bounded round-robin, adaptive yielding; unchanged values are not new studies'}
  c.bus.publish({'origin':'choice-action-study','target':'all','kind':'stage-output','payload':{'processing_receipt':True,'sequence':self.sequence,'sources':len(rows),'choices_studied':len(decisions)*3,'local_derivatives_computed':len(actions),'consequence_branches':len(consequences)*3,'prediction_checks':sum('prediction_check' in a['executed_local_derivative'] for a in actions),'integrated_studies':len(combined),'external_actions':0,'provenance':'measured-local-study-receipt','stochastic':False,'predefined_text':True}})
 def view(self,lane=None):
  with self.lock:
   result=copy.deepcopy({lane:self.frames.get(lane,{'sequence':0,'particles':[],'thought_trace':[]})} if lane else self.frames)
   for kind,mission in self.mission_frames.items():
    if lane and kind!=lane:continue
    base=result.setdefault(kind,{'sequence':self.sequence,'particles':[],'thought_trace':[]})
    base['particles']+=copy.deepcopy(mission['particles']);base['thought_trace']+=copy.deepcopy(mission['thought_trace']);base['role_task']=copy.deepcopy(mission.get('role_task'));base['mission_sequence']=mission['sequence'];base['represented_values']=len(base['particles'])
   return result.get(lane,{'sequence':0,'particles':[]}) if lane else result
