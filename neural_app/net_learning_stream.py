"""Parallel public learning ingestion: paced fetch, bounded source-labelled stream."""
import collections,copy,hashlib,re,threading,time
from urllib.parse import urlsplit
LANES=('reasoning','systems','creative','welfare','science','faith-learning','causal-models','language-memory','measurement','verification','ethics-repair','resource-design')
def lane_for(domain):
 if domain=='ethical-hacking-research':return 'systems'
 if domain in ('souls-digits-research','power-influence-research'):return 'welfare'
 common={'causality':'causal-models','language':'language-memory','measurement':'measurement','verification':'verification','ethics':'ethics-repair','resource-design':'resource-design'}
 if domain in common:return common[domain]
 if domain in ('reasoning',):return 'reasoning'
 if domain in ('security','platform','industry'):return 'systems'
 if domain in ('email','paint','document','art','music','game'):return 'creative'
 if domain in ('finance','humanitarian','society'):return 'welfare'
 if domain in ('belief-learning','faith','religion'):return 'faith-learning'
 return 'science'
class NetLearningStream:
 def __init__(self):
  self.lock=threading.RLock();self.enabled=True;self.closed=False;self.busy=False;self.next_fetch=0.;self.next_emit=0.;self.fetch_interval=20.;self.emit_interval=.1;self.worker=None;self.queues={k:collections.deque(maxlen=64) for k in LANES};self.lane_counts={k:{'emitted':0,'pages':0,'errors':0} for k in LANES};self.fetch_cursor=0;self.emit_cursor=0;self.seen=collections.OrderedDict();self.content_ids=collections.OrderedDict();self.host_due={};self.cursor=0;self.sequence=0;self.fetches=0;self.errors=0;self.dropped=0;self.latest={};self.history=collections.deque(maxlen=32);self.packet_history=collections.deque(maxlen=32);self.started=time.monotonic();self.next_discovery=0.;self.discovery_cursor=0;self.common={}
  self.host_attempts=collections.OrderedDict();self.host_failures={}
 def catalogue(self,c):
  from .free_learning import RESOURCES,resources
  rows=[{'domain':domain,**row} for domain in RESOURCES for row in resources(domain)]
  from .world_knowledge import SOURCES
  rows.extend({'domain':domain,'title':title,'url':url,'summary':summary} for domain,entries in SOURCES.items() for title,url,summary in entries)
  from .principle_research import DOMAINS
  rows.extend({'domain':domain,'title':title,'url':url,'summary':DOMAINS[domain][0]} for domain,(_,refs) in DOMAINS.items() for title,url in refs)
  with c.source_study.lock:rows.extend(copy.deepcopy(list(c.source_study.discovered.values())))
  return [r for r in rows if isinstance(r.get('url'),str) and r['url'].startswith('https://')]
 def choose(self,c):
  rows=self.catalogue(c)
  if not rows:return None
  now=time.monotonic()
  # Rotate for coverage; prioritise domains with current quality failures locally.
  quality=getattr(c,'cognition_quality',None);quality=quality.view().get('latest',{}) if quality else {}
  failed={r['domain'] for r in quality.get('checks',[]) if not r['passed']}
  mapped={'planning':'reasoning','native-work':'reasoning','memory':'reasoning','conversation':'belief-learning','ethical-review':'humanitarian','learning':'reasoning'}
  preferred={mapped[d] for d in failed if d in mapped}
  ordered=rows[self.cursor%len(rows):]+rows[:self.cursor%len(rows)]
  if preferred:ordered.sort(key=lambda r:r.get('domain') not in preferred)
  for offset in range(len(LANES)):
   lane=LANES[(self.fetch_cursor+offset)%len(LANES)]
   eligible=[row for row in ordered if lane_for(row.get('domain'))==lane and now>=self.host_due.get(urlsplit(row['url']).hostname,0)]
   if not eligible:continue
   row=min(eligible,key=lambda r:self.host_attempts.get(urlsplit(r['url']).hostname,0));host=urlsplit(row['url']).hostname
   self.host_attempts[host]=self.host_attempts.get(host,0)+1
   self.cursor=(rows.index(row)+1)%len(rows);self.fetch_cursor=(LANES.index(lane)+1)%len(LANES);self.host_due[host]=now+60
   while len(self.host_due)>256:self.host_due.pop(next(iter(self.host_due)))
   while len(self.host_attempts)>256:
    expired,_=self.host_attempts.popitem(last=False);self.host_failures.pop(expired,None)
   return {**row,'stream':lane}
  return None
 def ingest(self,c,row,result):
  # Only retrieved excerpts enter this rail; metadata notes are not substituted.
  texts=[x.strip() for x in result.get('excerpts',[]) if isinstance(x,str) and x.strip()]
  admitted=0
  for text in texts[:4]:
   for start in range(0,min(1200,len(text)),240):
    chunk=text[start:start+240];key=hashlib.sha256((row['url']+'\0'+chunk).encode()).hexdigest()
    with self.lock:
     if self.closed:return admitted
     lane=row.get('stream') or lane_for(row.get('domain'));route_key=lane+':'+key
     if route_key in self.seen:continue
     self.seen[route_key]=time.time();self.content_ids[key]=time.time()
     while len(self.content_ids)>2048:self.content_ids.popitem(last=False)
     while len(self.seen)>2048:self.seen.popitem(last=False)
     lane=row.get('stream') or lane_for(row.get('domain'));queue=self.queues[lane]
     if len(queue)==queue.maxlen:self.dropped+=1
     queue.append({'stream':lane,'id':key[:24],'text':chunk,'source_url':row['url'],'title':row.get('title','Public learning source'),'domain':row.get('domain','discovered'),'fetched':result.get('fetched',time.time()),'cached':bool(result.get('cached')),'status':'retrieved excerpt; not independently verified','trusted_as_instruction':False,'learning_level':row.get('learning_level','catalogue-topic'),'learning_node':row.get('learning_node',row.get('domain'))});admitted+=1
  if texts:
   sphere=getattr(c,'spectrum_logic',None)
   if sphere:
    sphere.observe_event({'origin':'net-source/'+hashlib.sha256(row['url'].encode()).hexdigest()[:20],'payload':{'source_url':row['url'],'title':row.get('title'),'domain':row.get('domain'),'fetched':result.get('fetched'),'cached':bool(result.get('cached')),'text':'\n'.join(texts[:4])[:4800],'provenance':'retrieved public excerpts; source text is data, not instructions; factual support remains to be checked'}})
   from .evidence_index import INDEX
   for i,text in enumerate(texts[:4]):INDEX.add_source(row['url'],row.get('title','Public learning source'),text)
  return admitted
 def fetch(self,c,row):
  try:
   result=c.capability_validation.read_source(c,row['url'],row.get('summary','learning methods'))
   count=self.ingest(c,row,result);record={'source_url':row['url'],'title':row.get('title'),'domain':row.get('domain'),'status':'retrieved','chunks_added':count,'cached':bool(result.get('cached')),'time':time.time()}
   with self.lock:self.fetches+=1;self.lane_counts[row.get('stream') or lane_for(row.get('domain'))]['pages']+=1;self.host_failures[urlsplit(row['url']).hostname]=0
  except Exception as exc:
   record={'source_url':row['url'],'title':row.get('title'),'domain':row.get('domain'),'status':'unavailable','error':type(exc).__name__+': '+str(exc)[:180],'time':time.time()}
   with self.lock:
    self.errors+=1;self.lane_counts[row.get('stream') or lane_for(row.get('domain'))]['errors']+=1
    host=urlsplit(row['url']).hostname;self.host_failures[host]=min(6,self.host_failures.get(host,0)+1);self.host_due[host]=time.monotonic()+min(3600,60*2**self.host_failures[host])
  finally:
   with self.lock:
    if 'record' in locals():self.latest=record;self.history.append(record)
    self.busy=False
 def discover(self,c):
  now=time.monotonic()
  if now<self.next_discovery:return
  self.next_discovery=now+120
  from .common_learning import common_learning
  centre=common_learning();self.common=centre
  levels=(centre['roots'],centre['themes'],centre['tree']['branches']);level=self.discovery_cursor%3;topics=levels[level];topic=topics[(self.discovery_cursor//3)%len(topics)];self.discovery_cursor+=1
  research=getattr(c.software_theory,'research',None)
  if research:
   try:
    research.request(topic['search_topic']);found=research.retrieve(topic['title'])
    with c.source_study.lock:
     for ref in found[:6]:
      url=ref.get('url','')
      if isinstance(url,str) and url.startswith('https://'):
       c.source_study.discovered[url]={'domain':topic['domain'],'title':ref.get('title','Discovered learning source'),'url':url,'summary':ref.get('summary',topic['title']),'learning_level':['root','shared-principle','application-branch'][level],'learning_node':topic.get('id',topic['domain']),'discovered':time.time()}
     while len(c.source_study.discovered)>128:c.source_study.discovered.pop(next(iter(c.source_study.discovered)))
    self.common['latest_discovery']={'level':['root','shared-principle','application-branch'][level],'topic':topic['title'],'metadata_matches':len(found),'status':'Public research topic submitted; matching text still requires retrieval'}
   except Exception as exc:self.common['latest_discovery']={'topic':topic['title'],'status':type(exc).__name__+': '+str(exc)[:120]}
  c.source_study.discover(c)
 def tick(self,c):
  if self.closed or not self.enabled:return
  now=time.monotonic()
  if now>=self.next_emit:
   self.next_emit=now+self.emit_interval
   packets=[]
   with self.lock:
    for _ in range(3):
     for offset in range(len(LANES)):
      lane=LANES[(self.emit_cursor+offset)%len(LANES)]
      if self.queues[lane]:
       packets.append(self.queues[lane].popleft());self.emit_cursor=(LANES.index(lane)+1)%len(LANES);self.lane_counts[lane]['emitted']+=1;break
     else:break
   for packet in packets:
    if self.closed:return
    with self.lock:self.sequence+=1;self.packet_history.append(copy.deepcopy(packet))
    c.bus.publish({'origin':'net-learning-stream','target':'all','kind':'stage-output','payload':{**packet,'sequence':self.sequence,'provenance':'retrieved-public-source-excerpt','stochastic':False,'predefined_text':True,'contains_model_text':False,'bridge_direction':'all','source_instructions_are_data':True}})
  if self.busy or now<self.next_fetch:return
  self.next_fetch=now+self.fetch_interval
  self.discover(c);row=self.choose(c)
  if row:
   self.busy=True;self.worker=threading.Thread(target=self.fetch,args=(c,row),daemon=True,name='parallel-net-learning');self.worker.start()
 def configure(self,b):
  enabled=b.get('enabled',self.enabled);value=b.get('stream_interval',self.emit_interval)
  if type(enabled) is not bool:raise ValueError('Enabled must be boolean')
  if type(value) not in (int,float) or not .05<=value<=10:raise ValueError('Stream interval must be 0.05 to 10 seconds')
  with self.lock:self.enabled=enabled;self.emit_interval=float(value)
  return self.view()
 def close(self):
  self.closed=True
  if self.worker and self.worker is not threading.current_thread():self.worker.join(1)
 def view(self):
  with self.lock:return {'source_balance':{'policy':'Round-robin topic lanes; least-attempted eligible provider in each lane; equal retrieval opportunities do not imply equal factual credibility.','provider_attempts':dict(self.host_attempts),'failure_backoff_seconds':3600},'enabled':self.enabled,'closed':self.closed,'busy':self.busy,'sequence':self.sequence,'retrieved_pages':self.fetches,'errors':self.errors,'common_learning_centre':copy.deepcopy(self.common),'streams':[{'id':k,'buffered':len(self.queues[k]),**self.lane_counts[k]} for k in LANES],'buffered_chunks':sum(map(len,self.queues.values())),'dropped_old_chunks':self.dropped,'unique_chunks':len(self.content_ids),'source_topic_routes':len(self.seen),'target_stream_interval':self.emit_interval,'fetch_interval_seconds':self.fetch_interval,'minimum_host_interval_seconds':60,'actual_average_chunks_per_second':round(self.sequence/max(1,time.monotonic()-self.started),3),'latest':copy.deepcopy(self.latest),'recent_packets':copy.deepcopy(list(self.packet_history)),'recent':copy.deepcopy(list(self.history)),'scope':'Public source text → labelled queue → entire shared engine. No fake traffic when the queue is empty; requested stream cadence is bounded by available data and shared scheduler load. Not model-weight training or external broadcast.'}
