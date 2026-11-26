"""Coalesced automatic public-course reading, separate from native reasoning work."""
import copy,threading,time,math,hashlib
class SourceStudy:
 def __init__(self):self.lock=threading.RLock();self.next_at=0;self.cursor=0;self.busy=False;self.closed=False;self.sequence=0;self.latest={};self.history=[];self.discovered={};self.discovery_cursor=0;self.next_discovery=0;self.discovery_status={}
 def read(self,c,kind,row):
  try:
   result=c.capability_validation.read_source(c,row['url'],row['summary']);record={'domain':kind,'title':row['title'],'url':row['url'],'status':'retrieved','fetched':result['fetched'],'cached':result['cached'],'excerpts':result['excerpts'],'next':'Use this material as source evidence and test any derived procedure independently.'}
  except Exception as e:record={'domain':kind,'title':row['title'],'url':row['url'],'status':'unavailable','error':type(e).__name__+': '+str(e)[:200]}
  if record['status']=='retrieved':
   text=' '.join(record.get('excerpts',[])).lower()
   options={'document':('Document structure',['document','writing','report','paragraph','style']),'art':('Geometric transform invariants',['animation','geometry','mesh','rotation','render']),'music':('Audio timing and PCM',['music','rhythm','frequency','sample','synth']),'game':('Game-state reachability',['game','scene','node','player','path'])}
   scored=sorted([(sum(word in text for word in words),domain,test) for domain,(test,words) in options.items()],reverse=True)
   score,domain,test=scored[0]
   record['inference']={'kind':'Source-linked relevance hypothesis','suggested_domain':domain if score else None,'matching_concepts':score,'proposed_native_test':test if score else 'No matching native test; retain as research evidence','support':record.get('excerpts',[])[:2],'next':'Compare the source-derived proposal with an independent task contract. A matching topic is not proof of the source claim.','verified':False}
   record['available_test_results']=c.capability_validation.view()['counts']
  with self.lock:self.sequence+=1;record['cycle']=self.sequence;self.latest=record;self.history=(self.history+[record])[-16:];self.busy=False
  if not self.closed:c.bus.publish({'origin':'source-study','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'retrieved':record['status']=='retrieved','provenance':'public-course-source-retrieval','predefined_text':True,'stochastic':False}})
 def tick(self,c):
  now=time.monotonic()
  if self.closed or self.busy or now<self.next_at:return
  self.discover(c)
  from .free_learning import RESOURCES,resources
  rows=[(kind,row) for kind in RESOURCES for row in resources(kind)]
  with self.lock:extra=[(v['domain'],v) for v in list(self.discovered.values())[-16:]]
  rows+=extra
  kind,row=rows[self.cursor%len(rows)];self.cursor+=1;self.next_at=now+300;self.busy=True
  threading.Thread(target=self.guarded_read,args=(c,kind,row),daemon=True,name='public-course-study').start()
 def view(self):
  with self.lock:return {'sequence':self.sequence,'busy':self.busy,'refresh_seconds':300,'latest':copy.deepcopy(self.latest),'recent':copy.deepcopy(self.history),'discovery':copy.deepcopy(self.discovery_status),'discovered_sources':len(self.discovered),'scope':'Public-source extraction and local indexing, not course completion or model-weight training.'}
 def close(self):self.closed=True

 def discover(self,c):
  now=time.monotonic()
  if now<self.next_discovery:return
  self.next_discovery=now+300
  research=getattr(c.software_theory,'research',None)
  if not research:return
  from .element_thinking import SPECS
  stages=list(SPECS);stage=stages[self.discovery_cursor%len(stages)];self.discovery_cursor+=1
  query=SPECS[stage][0]+' methods evaluation open access'
  try:
   research.request(query);found=research.retrieve(SPECS[stage][0].split('/')[0].strip())
   with self.lock:
    for ref in found[:8]:
     url=ref.get('url','')
     if url.startswith('https://'):
      self.discovered[url]={'domain':stage,'title':ref.get('title','Discovered source'),'url':url,'summary':ref.get('summary','Public research source'),'provenance':ref.get('source'),'discovered':time.time()}
    while len(self.discovered)>128:self.discovered.pop(next(iter(self.discovered)))
    self.discovery_status={'stage':stage,'query':query,'metadata_matches':len(found),'submitted':time.time(),'status':'Submitted public topic search; read available source text in bounded turns.'}
  except Exception as e:
   with self.lock:self.discovery_status={'stage':stage,'status':type(e).__name__+': '+str(e)[:200]}

 def sphere(self,c):
  state=self.view();thought=c.active_thought.view()
  with c.lock:source_count=len(c.sources)
  with self.lock:discovered=copy.deepcopy(list(self.discovered.values())[-24:])
  records=[{'kind':'retrieval',**r} for r in state['recent']]+[{'kind':'discovered-source',**r} for r in discovered]+[{'kind':'stage-inquiry','stage':k,'question':r.get('question'),'source':r.get('source'),'parent_event':r.get('parent_event')} for k,r in thought['stages'].items()]
  stream=getattr(c,'net_learning_stream',None)
  if stream:
   parallel=stream.view();state['parallel_stream']=parallel
   records=[{'kind':'parallel-source-excerpt',**row} for row in parallel.get('recent_packets',[])]+records
  particles=[]
  for i,row in enumerate(records[:96]):
   y=1-2*(i+.5)/max(1,min(96,len(records)));a=i*math.pi*(3-math.sqrt(5));radius=math.sqrt(max(0,1-y*y));ident=hashlib.sha256(str(row).encode()).hexdigest()[:16]
   particles.append({'id':'discovery:'+ident,'point':[radius*math.cos(a),y,radius*math.sin(a)],'phase':1.,'autonomy':0.,'selected':row.get('status')=='retrieved','symbol':'◇','expression_type':row['kind'],'source':row.get('source') or row.get('url','shared-stage-inquiry'),'parent_event':row.get('parent_event'),'path':[],'value_preview':row.get('title',row.get('question','Discovery'))[:120],'record':row})
  return {'sequence':state['sequence'],'particles':particles,'retained_sources':source_count,'received_events':state['sequence'],'represented_values':len(particles),'selected_phases':[1.],'thought_trace':records[:96],'network_intake':state,'rate_control':thought['policy'],'scope':'Shared public discovery, bounded text retrieval, relevance hypotheses and native test context. The sphere displays recorded activity; source statements remain distinct from verified outcomes.'}

 def guarded_read(self,c,kind,row):
  try:self.read(c,kind,row)
  except Exception as e:
   with self.lock:self.latest={'status':'study-error','url':row.get('url'),'error':type(e).__name__+': '+str(e)[:200]}
  finally:
   with self.lock:self.busy=False
