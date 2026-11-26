"""Parallel, addressable recursive processing with bounded self-selected work."""
import collections,hashlib,json,math,queue,random,threading,time,uuid
from .logic_cube import transform

def leaves(value,path=(),limit=64):
 out=[];stack=[(value,path)];visited=0
 while stack and len(out)<limit and visited<512:
  value,path=stack.pop();visited+=1
  if len(path)>12:continue
  if isinstance(value,dict):stack.extend((v,path+(str(k),)) for k,v in reversed(list(value.items())[:128]) if not any(s in str(k).lower() for s in ('password','secret','token','authorization')))
  elif isinstance(value,list):stack.extend((v,path+(i,)) for i,v in reversed(list(enumerate(value))[:256]))
  elif value is None or type(value) in (str,int,float,bool):
   if isinstance(value,float) and not math.isfinite(value):continue
   out.append({'path':list(path),'value':value[:2048] if isinstance(value,str) else value})
 return out

def resolve(value,path):
 if not isinstance(path,list) or len(path)>12:raise ValueError('Use a captured payload path up to 12 levels')
 for key in path:
  if isinstance(value,dict) and isinstance(key,str):
   if any(s in key.lower() for s in ('password','secret','token','authorization')):raise ValueError('Sensitive credential fields are not processing inputs')
   value=value[key]
  elif isinstance(value,list) and type(key) is int:value=value[key]
  else:raise ValueError('Path does not match the captured payload')
 if not (value is None or type(value) in (str,int,float,bool)):raise ValueError('Select a scalar field or array item')
 return value

class RecursiveCore:
 def __init__(self,bus,backbone,reasoner,start=True,name='recursive-core'):
  self.name=name;self.lane_offset=0 if name=='recursive-core' else int(name.rsplit('-',1)[-1])-1;self.policy_key='recursive_policy' if self.lane_offset==0 else 'recursive_policy_'+str(self.lane_offset+1);self.bus=bus;self.backbone=backbone;self.reasoner=reasoner;self.lock=threading.RLock();self.step_lock=threading.Lock();self.halt=threading.Event();self.worker=None;self.enabled=True;self.rate=4.;self.depth_limit=5;self.fanout=1;self.feedback='mixed';self.goal='';self.sequence=0;self.received=0;self.coalesced=0;self.dropped=0;self.errors=0;self.last_error=None;self.observations={};self.pending=collections.deque(maxlen=128);self.history=collections.deque(maxlen=96);self.coverage=collections.Counter();self.element_coverage=collections.Counter();self.stats={};self.acks={};self.awaiting={};self.delivered=0;self.point=[0,0,0];self.last_cost=0;self.last_mode=None;self.memory={};self.predictions={};self.prediction_scores={'tested':0,'correct':0};self.last_checkpoint=0;self.goal_result=None;self.pipeline_jobs={};self.pipeline_seen=set();self.last_pipeline=0
  from .core_modulators import CoreModulators
  self.modulators=CoreModulators();self.modulators.ticks=self.lane_offset*137;self.modulation={}
  self.saved_policy=dict(reasoner.s.get(self.policy_key,{}));self.stats=dict(self.saved_policy.get('route_stats',{}));self.goal=str(self.saved_policy.get('goal',''))[:1000];self.memory=dict(self.saved_policy.get('memory',{}));self.prediction_scores=dict(self.saved_policy.get('prediction_scores',self.prediction_scores))
  from .mind_workspace import MindWorkspace
  self.mind=MindWorkspace(self.saved_policy.get('mind'))
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name=self.name);self.worker.start()
 def observe(self,event):
  origin=str(event.get('origin','unknown'))[:100];p=event.get('payload');p=p if isinstance(p,dict) else {'value':p}
  if origin==self.name or p.get('recursive_trace'):return
  if origin=='flow-backbone':
   if p.get('source_origin')==self.name:
    with self.lock:self.acks[p.get('source_sequence')]={'targets':p.get('targets',[]),'filtered':p.get('filtered'),'sequence':p.get('sequence')}
   return
  sample=leaves(p)
  if not sample:return
  # The bus already bounds payload size; keep its snapshot, never host memory.
  with self.lock:
   self.mind.observe(origin,p)
   self.received+=1
   if origin in self.observations:self.coalesced+=1
   elif len(self.observations)>=128:
    self.observations.pop(min(self.observations,key=lambda key:self.observations[key]['time']));self.dropped+=1
   digest=hashlib.sha256(json.dumps(sample,sort_keys=True,ensure_ascii=True,default=str).encode()).hexdigest();old=self.observations.get(origin,{})
   snapshot=json.loads(json.dumps(p,ensure_ascii=False,default=str))
   self.observations[origin]={'source':origin,'payload':snapshot,'leaves':sample,'sequence':event.get('sequence'),'target':event.get('target'),'changed':digest!=old.get('digest'),'digest':digest,'count':old.get('count',0)+1,'time':time.time()}
   while len(self.acks)>128:self.acks.pop(next(iter(self.acks)))
   for key,prediction in list(self.predictions.items()):
    if prediction['source']!=origin:continue
    try:
     captured=resolve(snapshot,prediction['path']);raw=(captured if isinstance(captured,str) else json.dumps(captured,ensure_ascii=False)).encode() or bytes([0]);position=prediction['bit_index'];actual=(raw[(position//8)%len(raw)]>>(7-position%8))&1
     self.prediction_scores['tested']+=1;self.prediction_scores['correct']+=int(actual==prediction['predicted']);prediction.update(actual=actual,correct=actual==prediction['predicted'],status='tested on later source capture');self.memory[key]=prediction
    except (ValueError,KeyError,IndexError,TypeError):pass
    self.predictions.pop(key,None)

 def configure(self,b):
  with self.lock:
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.enabled=b['enabled']
   for key,lo,hi in [('rate',.25,20),('depth_limit',1,12),('fanout',1,3)]:
    if key in b:
     value=float(b[key])
     if not math.isfinite(value):raise ValueError('Processing controls must be finite')
     setattr(self,key,max(lo,min(hi,value)) if key=='rate' else int(max(lo,min(hi,value))))
   if 'feedback' in b:
    if b['feedback'] not in ('walk','result','mixed'):raise ValueError('Choose walk, result or mixed feedback')
    self.feedback=b['feedback']
   if 'goal' in b:
    new_goal=str(b['goal'])[:1000]
    if new_goal!=self.goal:
     self.goal_result=None;self.pending.clear()
    self.goal=new_goal
   if 'modulators' in b:self.modulators.configure(b['modulators'])
  return self.view()
 def seed(self,b):
  with self.lock:
   source=str(b.get('source','manual'))
   if source in self.observations:
    captured=self.observations[source];path=b.get('path',captured['leaves'][0]['path']);value=resolve(captured['payload'],path);origin_sequence=captured['sequence']
   elif 'value' in b:value=b['value'];path=b.get('path',[]);origin_sequence=None
   else:raise ValueError('Choose a captured source or supply a scalar value')
   if not (value is None or type(value) in (str,int,float,bool)):raise ValueError('Select a scalar value')
   if isinstance(value,float) and not math.isfinite(value):raise ValueError('Use a finite scalar value')
   if not isinstance(path,list) or len(path)>12:raise ValueError('Use a payload path array up to 12 levels')
   if len(str(value).encode())>4096:raise ValueError('Use an entry value below 4 KiB')
   entry=str(b.get('entry',self.backbone.stages[0]))
   if entry not in self.backbone.stages:raise ValueError('Choose a registered backbone entry')
   mode=b.get('mode','variable')
   if mode not in ('variable','ascii','bit'):raise ValueError('Choose variable, ascii or bit')
   job={'root':uuid.uuid4().hex,'depth':0,'source':source,'source_sequence':origin_sequence,'path':path,'value':value,'entry':entry,'mode':mode,'char_index':int(b.get('char_index',0)),'bit_index':int(b.get('bit_index',0)),'label':b.get('label','unknown'),'visited':[],'parent':None,'created':time.time()}
   if job['label'] not in ('good','evil','unknown'):raise ValueError('Choose good, evil or unknown')
   if len(self.pending)>=self.pending.maxlen:raise ValueError('Recursive work queue is full')
   if b.get('priority',True):self.pending.appendleft(job)
   else:self.pending.append(job)
   return {'accepted':True,'root':job['root'],'entry':entry,'path':path,'mode':mode}
 def auto_seed(self,goal):
  with self.lock:
   rows=list(self.observations.values());rows=rows[self.lane_offset%max(1,len(rows)):]+rows[:self.lane_offset%max(1,len(rows))]
   if not rows:return False
   terms=set(goal.lower().split());explore=self.sequence%4==0
   if explore:source=min(rows,key=lambda r:self.coverage['source:'+r['source']])
   else:source=max(rows,key=lambda r:self.mind.priority(r['source'],r['payload'],goal)+.7*int(r['changed'])+.2*int(any(word in r['source'].lower() for word in ('cosmic','hydrogen','solar','earth','silicon','atomic','ambient')))+len(terms&set(r['source'].lower().replace('-',' ').split()))+1/(1+self.coverage['source:'+r['source']]))
   leaf=max(source['leaves'],key=lambda v:self.mind.priority(source['source'],v['value'],goal)+1/(1+self.element_coverage[source['source']+json.dumps(v['path'])]));mode=('variable','ascii','bit')[(self.sequence+self.lane_offset)%3]
   stages=self.backbone.stages;entry=stages[(self.sequence//3+self.lane_offset*59)%len(stages)]
   if source['target'] in stages and not explore:entry=source['target']
   self.coverage['source:'+source['source']]+=1;source['changed']=False;self.element_coverage[source['source']+json.dumps(leaf['path'])]+=1
   label='unknown'
   if mode=='bit' and isinstance(leaf['value'],str) and leaf['value'] and set(leaf['value'])<=set('01'):
    container=source['payload']
    try:
     for key in leaf['path'][:-1]:container=container[key]
     labels=container.get('labels') if isinstance(container,dict) else None
     if isinstance(labels,list) and len(labels)==len(leaf['value']) and labels[self.sequence%len(labels)] in ('good','evil','unknown'):label=labels[self.sequence%len(labels)]
    except (KeyError,IndexError,TypeError):pass
   return self.seed({'source':source['source'],'path':leaf['path'],'entry':entry,'mode':mode,'char_index':self.sequence,'bit_index':self.sequence,'label':label,'priority':True})
 def select_route(self,job,goal):
  stages=self.backbone.stages;index=stages.index(job['entry']);terms=set(goal.lower().split());candidates=[]
  if index: candidates.append(('upstream',stages[index-1]))
  if index+1<len(stages):candidates.append(('downstream',stages[index+1]))
  candidates.append(('incur-anywhere',stages[(self.sequence*17)%len(stages)]))
  if self.sequence%4==0:candidates.append(('coverage',min(stages,key=lambda s:self.coverage['stage:'+s])))
  def score(pair):
   direction,target=pair;key=job['entry']+'>'+target+'/'+job['mode'];stat=self.stats.get(key,{'attempts':0,'reward':0})
   mean=stat['reward']/max(1,stat['attempts']);explore=math.sqrt(2*math.log(self.sequence+2)/(stat['attempts']+1));relevance=.4*len(terms&set(target.lower().replace('-',' ').split()));coverage=.3/(1+self.coverage['stage:'+target]);repeat=-2 if target in job['visited'][-3:] else 0
   return mean+explore+relevance+coverage+repeat
  bias=self.modulation.get('applied',0);pair=max(candidates,key=lambda pair:score(pair)+bias*(1 if pair[0] in ('downstream','incur-anywhere') else -1));return pair,score(pair)
 def select_mode(self,goal,value,branch=0):
  words=goal.lower();modes=['variable','ascii','bit'];scores={}
  for mode in modes:
   used=sum(v['attempts'] for k,v in self.stats.items() if k.endswith('/'+mode));relevant=any(word in words for word in {'variable':['value','entropy','count','measure'],'ascii':['text','character','string','ascii'],'bit':['bit','binary','flip','balance']}[mode]);scores[mode]=.5*int(relevant)+1/(1+used)
  return sorted(modes,key=lambda mode:-scores[mode])[branch%3]
 def apply_acks(self):
  with self.lock:
   for sequence in list(self.awaiting):
    if sequence not in self.acks:continue
    ticket=self.awaiting.pop(sequence);ack=self.acks.pop(sequence);valid=ticket['target'] in ack['targets'] and (ack.get('filtered') or {}).get('output_bits')==ticket['bit'];ticket['row']['delivery']='mailbox verified' if valid else 'mailbox mismatch';ticket['row']['backbone_receipt']=ack['sequence'];ticket['row']['delivery_verified']=valid
    stat=self.stats.get(ticket['key'])
    if stat is None:continue
    stat['deliveries']=stat.get('deliveries',0)+int(valid);stat['reward']+=.2*int(valid);self.delivered+=int(valid)
   for sequence,ticket in list(self.awaiting.items()):
    if time.time()-ticket['time']>10:ticket['row']['delivery']='receipt timeout';self.awaiting.pop(sequence)
 def step(self):
  if not self.step_lock.acquire(blocking=False):return {'busy':True,'scope':'A recursive pass is already running'}
  try:return self.process_step()
  finally:self.step_lock.release()
 def process_step(self):
  self.apply_acks();self.poll_pipeline()
  with self.reasoner.lock:goal=self.goal or str(self.reasoner.s.get('current_goal',{}).get('input_summary',''))
  if not self.goal and hasattr(self.reasoner,'workbench'):
   with self.reasoner.lock:
    active=next((g for g in reversed(self.reasoner.workbench.executive.s['goals']) if g['status']=='running'),None)
    if active:goal=active['goal']
  with self.lock:
   if not self.pending or (self.sequence>0 and self.sequence%8==0 and len(self.pending)<96):self.auto_seed(goal)
   if not self.pending:return None
   job=self.pending.popleft();self.sequence+=1
  self.modulation=self.modulators.sample(job['depth'])
  started=time.perf_counter();value=job['value'];text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False);raw=text.encode('utf-8')[:2048];raw=raw or bytes([0]);char_index=job['char_index']%max(1,len(text));char=text[char_index] if text else '';byte_index=job['bit_index']//8%len(raw);offset=job['bit_index']%8;encoding='UTF-8 representation of captured scalar; not host memory'
  literal=isinstance(value,str) and bool(value) and set(value)<=set('01') and (job['mode']=='bit')
  before=int(value[job['bit_index']%len(value)]) if literal else (raw[byte_index]>>(7-offset))&1
  filtered=transform(str(before),[job['label']]);after=int(filtered['output_bits']);verified=filtered['roundtrip'] and (after==before if job['label']!='evil' else after!=before)
  if job['mode']=='variable':
   counts=collections.Counter(raw);metrics={'type':type(value).__name__,'bytes':len(raw),'distinct_bytes':len(counts),'entropy_bits_per_byte':-sum((v/len(raw))*math.log2(v/len(raw)) for v in counts.values())};operation='measure captured scalar'
  elif job['mode']=='ascii':metrics={'character_index':char_index,'character':char,'codepoint':ord(char) if char else None,'utf8_bytes':list(char.encode()),'ascii':bool(char) and ord(char)<128};operation='inspect character encoding'
  else:metrics={'byte_index':byte_index,'bit_offset_MSB':offset,'input_bit':before,'output_bit':after,'literal_bit_index':job['bit_index']%len(value) if literal else None,'classification':job['label'],'correction_proposed':job['label']=='evil'};operation='hold / propose bit correction'
  with self.lock:self.mind.decision(goal,job['source'],value)
  (direction,target),route_score=self.select_route(job,goal);elapsed=time.perf_counter()-started;digest=hashlib.sha256(raw).hexdigest();key=job['entry']+'>'+target+'/'+job['mode'];novel=digest not in [r['input_sha256'] for r in list(self.history)[-16:]];reward=.15*int(verified)+.05*int(novel)+.05*int(elapsed<.02)
  angle=self.sequence*.37;radius=(job['depth']+1)/(self.depth_limit+1);point=[radius*math.cos(angle),radius*math.sin(angle),(-1 if after==0 else 1)*radius*.5]
  row={'id':uuid.uuid4().hex,'root':job['root'],'parent':job['parent'],'depth':job['depth'],'source':job['source'],'source_sequence':job['source_sequence'],'path':job['path'],'entry':job['entry'],'target':target,'direction':direction,'mode':job['mode'],'operation':operation,'metrics':metrics,'input_sha256':digest,'input_preview':text[:120],'encoding':'literal supplied bit sequence' if literal else encoding,'input_bit':before,'output_bit':after,'filter':filtered,'verified':verified,'reward':reward,'reward_components':{'calculation_check':.15*int(verified),'novel_input':.05*int(novel),'under_20ms':.05*int(elapsed<.02),'mailbox_delivery_pending':.2},'route_score':route_score,'selection_reason':'UCB outcome history + goal relevance + coverage; recent route repetition penalized','modulation':dict(self.modulation),'cost_ms':elapsed*1000,'time':time.time(),'point':point,'delivery':'awaiting backbone receipt','depth_limit':self.depth_limit,'goal':goal[:300]}
  with self.lock:
   if len(self.stats)>=512 and key not in self.stats:self.stats.pop(next(iter(self.stats)))
   stat=self.stats.setdefault(key,{'attempts':0,'reward':0.,'deliveries':0});stat['attempts']+=1;stat['reward']+=reward;self.coverage['stage:'+target]+=1;self.point=point;self.last_cost=elapsed*1000;self.last_mode=job['mode'];self.history.append(row)
  memory_key=job['source']+json.dumps(job['path'])
  with self.lock:
   self.memory[memory_key]={'source':job['source'],'path':job['path'],'mode':job['mode'],'input_sha256':digest,'metrics':metrics,'verified':verified,'time':time.time(),'provenance':'calculated from captured input'}
   if job['mode']=='bit' and not literal and not job['source'].startswith('recursive-core'):self.predictions[memory_key]={'source':job['source'],'path':job['path'],'bit_index':job['bit_index'],'predicted':before,'status':'pending later capture','method':'persistence baseline; not an external-message claim'}
   while len(self.memory)>128:self.memory.pop(next(iter(self.memory)))
   while len(self.predictions)>128:self.predictions.pop(next(iter(self.predictions)))
  from .native_skills import respond
  if goal.startswith('run pipeline:') and hasattr(self.reasoner.runtime,'submit') and time.monotonic()-self.last_pipeline>5 and len(self.pipeline_jobs)<2:
   template=goal[len('run pipeline:'):].strip();supplied=template.replace('{{value}}',text).replace('{{bit}}',str(after));supplied=supplied.encode()[:512].decode('utf-8',errors='ignore');signature=hashlib.sha256(supplied.encode()).hexdigest()
   if signature not in self.pipeline_seen:
    job_result=self.reasoner.runtime.submit('pipeline',{'text':supplied,'sections':['signals','translation','inference']});self.pipeline_jobs[job_result['id']]={'text':supplied,'source':job['source'],'started':time.time(),'goal':goal};self.goal_result={'job':job_result['id'],'status':'queued','verified':False};self.pipeline_seen.add(signature);self.last_pipeline=time.monotonic()
    if len(self.pipeline_seen)>128:self.pipeline_seen.clear();self.pipeline_seen.add(signature)
  if goal:

   substituted=goal.replace('{{bit}}',str(after)).replace('{{bytes}}',str(len(raw))).replace('{{value}}',text[:256])
   try:
    result=respond(substituted)
    if result is not None:
     with self.lock:new_outcome=self.mind.record(goal,job['source'],result['skill'],True,result['result'])
     with self.lock:
      self.stats[key]['reward']+=.55*int(new_outcome)
      row['reward_components']['native_goal_result']=.55*int(new_outcome)
     self.goal_result={'goal':goal,'resolved_request':substituted[:400],'skill':result['skill'],'result':result['result'],'source':job['source'],'input_sha256':digest,'provenance':'native goal calculation','time':time.time()}
   except (ValueError,SyntaxError,ZeroDivisionError,TypeError):self.goal_result={'goal':goal,'status':'needs a supported native expression','time':time.time()}
  packet={'target':'all','origin':self.name,'kind':'stage-output','payload':{'bridge_targets':[target],'bridge_direction':'all','bits':str(after),'labels':['unknown'],'text':json.dumps({'operation':operation,'metrics':metrics},ensure_ascii=True)[:1200],'point':point,'provenance':'observed-native-calculation','stochastic':False,'recursive_trace':{'root':job['root'],'node':row['id'],'depth':job['depth'],'path':job['path'],'source_sequence':job['source_sequence']},'filter_receipt':filtered,'classification_after_correction':'unresolved until outcome validation','definition_library':'/api/definition-library','scope':'Selected stage mailbox routing; subscriber execution is separately measured'}}
  receipt=self.bus.publish(packet);sequence=receipt['event']['sequence']
  with self.lock:
   self.awaiting[sequence]={'target':target,'bit':str(after),'key':key,'row':row,'time':time.time()}
   # Explicit internal recursion, not unrestricted re-ingestion of our own bus output.
   if job['depth']+1<self.depth_limit:
    for branch in range(self.fanout):
     if len(self.pending)>=128:self.dropped+=1;break
     child={**job,'parent':row['id'],'depth':job['depth']+1,'entry':target,'mode':self.select_mode(goal,job['value'],branch),'char_index':job['char_index']+1+branch,'bit_index':job['bit_index']+1+branch,'label':'unknown','visited':(job['visited']+[job['entry']])[-12:]}
     if self.feedback=='result' or (self.feedback=='mixed' and child['depth']%2==0):
      child.update(source=self.name,source_sequence=sequence,path=['derived_result',row['id']],value=json.dumps({'metrics':metrics,'output_bit':after,'verified_calculation':verified},ensure_ascii=True))
     self.pending.append(child)
  self.apply_acks()
  if time.monotonic()-self.last_checkpoint>10:self.checkpoint()
  return row
 def poll_pipeline(self):
  for ident,ticket in list(self.pipeline_jobs.items()):
   result=self.reasoner.runtime.result(ident)
   if result.get('status') in ('queued','running'):
    if time.time()-ticket['started']<60:continue
    self.goal_result={'job':ident,'status':'timeout waiting for pipeline','verified':False};self.pipeline_jobs.pop(ident);continue
   value=result.get('result') or {};verified=False;reason=result.get('error')
   if result.get('status')=='complete':
    try:
     from .translation import decode
     stages=value.get('stages',{});ready=all(key in stages and not str(stages[key].get('status','')).lower().startswith(('error','failed','partial','awaiting','unsupported')) for key in ('signals','translation','inference'));verified=decode(value['input_transport'])==ticket['text'].encode() and ready and bool(result.get('receipt'))
    except (KeyError,ValueError,TypeError):reason='Pipeline result did not match expected transport/stages'
   pipeline_result={'job':ident,'status':result.get('status'),'verified':verified,'receipt':result.get('receipt'),'source':ticket['source'],'reason':reason,'scope':'Actual registered pipeline result; does not certify every semantic inference'};self.memory['pipeline:'+ident]=dict(pipeline_result)
   with self.lock:self.mind.record(ticket.get('goal',''),ticket['source'],'pipeline',verified,pipeline_result)
   if ticket.get('goal')==self.goal:self.goal_result=pipeline_result
   self.pipeline_jobs.pop(ident)
 def checkpoint(self):
  with self.lock:policy={'mind':self.mind.checkpoint(),'goal':self.goal,'route_stats':{k:dict(v) for k,v in self.stats.items()},'prediction_scores':dict(self.prediction_scores),'memory':dict(list(self.memory.items())[-64:]),'time':time.time()}
  with self.reasoner.lock:self.reasoner.s[self.policy_key]=policy
  self.last_checkpoint=time.monotonic()
 def view(self):
  from .native_workbench import CHAIN
  with self.lock:return {'mind':self.mind.view(),'name':self.name,'cosmological_chain':CHAIN,'modulators':self.modulation,'pipeline_jobs':list(self.pipeline_jobs),'goal_syntax':'calculate {{bit}} + 1 / run pipeline: {{value}}','working_memory':list(self.memory.values())[-12:],'pending_predictions':len(self.predictions),'prediction_scores':self.prediction_scores,'goal_result':self.goal_result,'enabled':self.enabled,'rate':self.rate,'depth_limit':self.depth_limit,'fanout':self.fanout,'feedback':self.feedback,'goal':self.goal,'sequence':self.sequence,'received':self.received,'coalesced':self.coalesced,'dropped':self.dropped,'pending':len(self.pending),'errors':self.errors,'last_error':self.last_error,'point':self.point,'last_mode':self.last_mode,'last_cost_ms':self.last_cost,'verified_mailboxes':self.delivered,'stages':self.backbone.stages,'sources':[{'source':r['source'],'sequence':r['sequence'],'fields':[{'path':v['path'],'type':type(v['value']).__name__,'preview':str(v['value'])[:100]} for v in r['leaves'][:24]],'count':r['count']} for r in list(self.observations.values())],'coverage':dict(self.coverage),'route_stats':[{'route':k,**v,'mean_reward':v['reward']/max(1,v['attempts'])} for k,v in sorted(self.stats.items(),key=lambda row:-row[1]['attempts'])[:24]],'history':list(self.history)[-40:],'scope':'Captured app variables, character encodings and bits; finite parallel recursion; no arbitrary host-memory access or generated command execution'}
 def loop(self):
  while not self.halt.is_set():
   if self.enabled:
    try:self.step()
    except Exception as e:self.errors+=1;self.last_error=type(e).__name__+': '+str(e)[:240]
   self.halt.wait(max(.05,1/self.rate))
 def close(self):
  self.halt.set()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(5)
  self.checkpoint()
