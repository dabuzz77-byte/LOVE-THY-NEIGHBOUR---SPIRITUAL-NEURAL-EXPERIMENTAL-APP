"""Measured whole-engine self-review. Recommendations never execute themselves."""
import copy,hashlib,math,threading,time
class SelfAnalysis:
 def __init__(self):self.lock=threading.RLock();self.next_at=0.;self.sequence=0;self.latest={};self.frame={};self.previous={};self.history=[]
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  self.next_at=now+5
  with c.lock:
   layers=[{k:copy.deepcopy(v.get(k)) for k in ('id','title','received','changes','updated','parent_event','source','predictions')} for v in c.element_thinking.layers.values()]
   services=copy.deepcopy(c.service_errors);source_count=len(c.sources);captured=c.sequence
   source_reviews=[{'source':r.get('source'), 'parent_event':r.get('parent_event'),'age_seconds':round(max(0,time.time()-r.get('time',time.time())),2),'captured_fields':len(r.get('facts',[])),'status':'retained observation; not automatically verified'} for r in c.sources.values()]
  performance=c.service_metrics.view()['services'];decisions=c.deep_decision.view();ledger=c.decision_ledger.view();inference=c.thin_inference.view()
  executive=c.r.workbench.executive
  with executive.lock:goals=[{'id':g.get('id'),'status':g.get('status'),'pending':sum(s.get('status')=='pending' for s in g.get('steps',[])),'failed':sum(s.get('status')=='failed' for s in g.get('steps',[]))} for g in executive.s.get('goals',[])[-8:]]
  stamp=time.time();rows=[];findings=[]
  for layer in layers:
   ident=layer['id'];changed=layer.get('changes') or 0;old=self.previous.get(ident);delta=None if old is None else max(0,changed-old);self.previous[ident]=changed
   age=max(0,stamp-layer['updated']) if layer.get('updated') else None
   status='waiting for observations' if not layer.get('received') else 'changed since review' if delta else 'observations retained; no new change'
   predictions=layer.get('predictions') or {};tested=sum(max(0,p.get('tested',0)) for p in predictions.values())
   rows.append({'id':ident,'title':layer['title'],'received':layer.get('received',0),'changes':changed,'changes_since_review':delta,'observation_age_seconds':round(age,2) if age is not None else None,'status':status,'source':layer.get('source'),'parent_event':layer.get('parent_event'),'prediction_fields':len(predictions),'prediction_comparisons':tested,'review':'Numeric predictions require subsequent matching-source observations; activity alone is not task success.'})
  for name,error in sorted(services.items()):
   findings.append({'kind':'service-error','priority':'high','stage':name,'finding':'Service reported an error','evidence':{'time':error.get('time'),'error':str(error.get('error',''))[:180]},'proposal':'Inspect the failing service and dependency; verify recovery before restoring its normal rate.','execution':False})
  for row in performance:
   if row['name'].endswith('/self-analysis'):continue
   if row['calls']>=3 and row['ewma_ms']>50:
    findings.append({'kind':'processing-cost','priority':'medium','stage':row['name'],'finding':'Measured recent callback average exceeds 50 ms','evidence':{'calls':row['calls'],'recent_ms':round(row['ewma_ms'],3),'max_ms':round(row['max_ms'],3)},'proposal':'Profile this callback; compare coalescing or smaller batches against the same task results.','execution':False})
  for goal in goals:
   if goal['status']=='needs-input':findings.append({'kind':'blocked-goal','priority':'high','stage':'executive','finding':'A retained task needs input or correction','evidence':goal,'proposal':'Review the missing dependency or failed step; retain completed results.','execution':False})
  quality=getattr(c,'cognition_quality',None);quality=quality.view().get('latest',{}) if quality else {}
  if quality and not quality.get('all_passed'):
   findings.append({'kind':'capability-regression','priority':'high','stage':'cognition-quality','finding':'A native capability contract did not pass','evidence':{'passed':quality.get('passed'),'total':quality.get('total'),'failed':[r['name'] for r in quality.get('checks',[]) if not r['passed']]},'proposal':'Inspect and repair the failed contract before treating the capability as reliable.','execution':False})
  counts={'stages':len(rows),'stages_with_observations':sum(bool(x['received']) for x in rows),'stages_changed_since_review':sum(bool(x['changes_since_review']) for x in rows),'sources':source_count,'captured_events':captured,'service_errors':len(services),'findings':len(findings),'verified_action_records':sum(x.get('verified') is True for x in ledger.get('records',[])),'failed_action_records':sum(x.get('verified') is False for x in ledger.get('records',[]))}
  review={'sequence':self.sequence+1,'reviewed_at':stamp,'counts':counts,'stages':rows,'source_reviews':source_reviews,'findings':findings[:64],'goals':goals,'capability_evidence':{'sequence':quality.get('sequence'),'passed':quality.get('passed'),'total':quality.get('total'),'scope':quality.get('scope')},'decision_evidence':{'sequence':decisions.get('sequence'),'outcomes':decisions.get('outcomes',{})},'model_evidence':{'busy':inference.get('busy'),'cached_proposals':inference.get('cache_entries'),'status':inference.get('availability',{}).get('status')},'learning_rule':'Prefer independently verified task outcomes and held-out transfer; do not equate more output with improvement.','scope':'Review of registered stage observations, recent task records and measured service timings; not proof of every engine’s correctness. No raw input values or task text copied.','execution':False,'model_calls':0}
  records=[{'kind':'stage-review','source':r.get('source') or r['id'],'parent_event':r.get('parent_event'),'value_preview':r['title']+' · '+r['status'],'record':r} for r in rows]+[{'kind':'finding','source':f['stage'],'value_preview':f['finding'],'record':f} for f in findings[:64]]
  particles=[]
  for i,row in enumerate(records):
   y=1-2*(i+.5)/max(1,len(records));a=i*math.pi*(3-math.sqrt(5));radius=math.sqrt(max(0,1-y*y));h=hashlib.sha256((row['kind']+str(row['source'])+str(i)).encode()).hexdigest()[:16]
   particles.append({'id':'self-analysis:'+h,'point':[radius*math.cos(a),y,radius*math.sin(a)],'phase':1.,'autonomy':0.,'selected':row['kind']=='finding' or bool(row['record'].get('changes_since_review')),'symbol':'◇' if row['kind']=='stage-review' else '!','expression_type':row['kind'],'path':[] ,**row})
  frame={'sequence':review['sequence'],'particles':particles,'received_events':captured,'retained_sources':source_count,'represented_values':len(particles),'selected_phases':[1.],'thought_trace':findings[:64],'self_review':review,'scope':review['scope']}
  with self.lock:self.sequence+=1;self.latest=review;self.frame=frame;self.history=(self.history+[{'sequence':self.sequence,'time':stamp,'counts':counts}])[-24:]
  c.bus.publish({'origin':'self-analysis','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,**counts,'processing_receipt':True,'provenance':'measured-whole-engine-self-review','stochastic':False,'predefined_text':False}})
 def view(self):
  with self.lock:return {'latest':copy.deepcopy(self.latest),'recent':copy.deepcopy(self.history),'refresh_seconds':5,'model_calls':0}
 def sphere(self):
  with self.lock:return copy.deepcopy(self.frame or {'sequence':0,'particles':[],'scope':'Waiting for first measured self-review'})
