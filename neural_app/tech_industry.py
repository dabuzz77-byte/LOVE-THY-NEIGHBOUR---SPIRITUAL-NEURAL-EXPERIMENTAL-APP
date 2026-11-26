"""Public technology ecosystem model and bounded publisher-feed updates."""
import copy,hashlib,json,threading,time,xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from .action_ethics import study_frame
LAYERS=[('Hardware',['Semiconductors','Device manufacturers','Storage and memory','Repair and reuse']),('Operating systems',['Desktop and server OS','Mobile OS','Console platforms','Open-source distributions']),('Access networks',['Fixed broadband','Mobile networks','Satellite access','Community networks']),('Internet infrastructure',['Transit networks','Internet exchanges','DNS and naming','Data centres']),('Cloud and platforms',['Compute and storage','Containers and orchestration','Content delivery','Smaller hosting providers']),('Applications',['Communication and email','Search and knowledge','Games and creative tools','Public and community services']),('Access and support',['Identity and permissions','Payments and subscriptions','Accessibility and localisation','Support and digital skills']),('End users',['Individuals and households','Schools and libraries','Small organisations','Underserved communities'])]
SOURCES=[{'title':'Internet Society: Internet ecosystem','url':'https://www.internetsociety.org/internet/','note':'The Internet is composed of independently operated networks, services and communities.'},{'title':'CNCF landscape','url':'https://landscapeapp.cncf.io/cncf/','note':'Public cloud-native project and product catalogue; not an exhaustive industry inventory.'},{'title':'PeeringDB: public interconnection directory','url':'https://www.peeringdb.com/about','note':'User-maintained public infrastructure directory; does not enumerate private end-user devices.'}]
FEEDS=[('Internet Society','https://www.internetsociety.org/feed/'),('CNCF','https://www.cncf.io/feed/')]
def parse_feed(text,publisher,truncated=False):
 if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():raise ValueError('Feed declarations are excluded')
 parser=ET.XMLPullParser(events=('end',));parser.feed(text)
 items=[element for event,element in parser.read_events() if element.tag in ('item','{http://www.w3.org/2005/Atom}entry')]
 if not truncated:parser.close()
 records=[]
 for item in items[:20]:
  title=item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title') or 'Untitled'
  url=item.findtext('link') or ''
  if not url:
   link=item.find('{http://www.w3.org/2005/Atom}link');url=link.get('href','') if link is not None else ''
  parsed=urlsplit(url)
  if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:continue
  date=item.findtext('pubDate') or item.findtext('{http://www.w3.org/2005/Atom}updated')
  records.append({'id':hashlib.sha256(url.encode()).hexdigest(),'title':title[:300],'url':url,'published':date,'publisher':publisher,'classification':'Publisher announcement; not independently verified','retrieved':time.time()})
 return records
class TechIndustry:
 def __init__(self,data,domain="technology",layers=None,sources=None,feeds=None):
  self.domain=domain;self.layers=layers or LAYERS;self.sources=sources or SOURCES;self.feeds=feeds or FEEDS
  self.path=data/(domain+'-industry-updates.json');self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.cursor=0;self.busy=False;self.closed=False;self.updates=[];self.status={}
  try:self.updates=json.loads(self.path.read_text(encoding='utf-8'))[-100:]
  except (OSError,ValueError):pass
 def tick(self,c):
  now=time.monotonic()
  if self.closed or self.busy or now<self.next_at:return
  self.next_at=now+900;publisher,url=self.feeds[self.cursor%len(self.feeds)];self.cursor+=1;self.busy=True
  threading.Thread(target=self.fetch,args=(c,publisher,url),daemon=True,name='public-industry-feed').start()
 def fetch(self,c,publisher,url):
  from .reviewed_web import read_page
  try:
   page=read_page(url)
   rows=parse_feed(page['text'],publisher,page['text_truncated'])
   with self.lock:
    known={r['id']:r for r in self.updates};new=sum(r['id'] not in known for r in rows)
    for row in rows:known[row['id']]=row
    self.updates=list(known.values())[-100:];self.path.write_text(json.dumps(self.updates),encoding='utf-8');self.sequence+=1;self.status[publisher]={'status':'received','checked':time.time(),'items':len(rows),'new_items':new,'url':url,'bounded_prefix':page['text_truncated']}
   study=getattr(c,'source_study',None)
   if study and not self.closed:
    with study.lock:
     for row in rows[:4]:study.discovered[row['url']]={'domain':'techindustry' if self.domain=='technology' else 'financeindustry','title':row['title'],'url':row['url'],'summary':'Study this publisher announcement and its effects on infrastructure and access.','provenance':publisher,'discovered':time.time()}
     while len(study.discovered)>128:study.discovered.pop(next(iter(study.discovered)))
   if not self.closed:c.bus.publish({'origin':self.domain+'-industry','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'received_items':len(rows),'new_items':new,'provenance':'public-publisher-feed','predefined_text':True,'stochastic':False}})
  except Exception as e:
   with self.lock:self.status[publisher]={'status':'unavailable','checked':time.time(),'url':url,'error':type(e).__name__+': '+str(e)[:180]}
  finally:self.busy=False
 def view(self):
  nodes=[];edges=[]
  for layer,(title,roles) in enumerate(self.layers):
   for index,role in enumerate(roles):nodes.append({'id':str(layer)+':'+str(index),'layer':layer,'role':role,'type':'end-user-group' if layer==7 else 'service-or-infrastructure-role','scale':'Large, regional, small and community participants may occupy this role','source':self.sources[0]['url']})
   if layer:
    for index in range(4):edges.append({'from':str(layer-1)+':'+str(index),'to':str(layer)+':'+str(index),'kind':'Illustrative dependency, not a measured provider route'})
  with self.lock:return {'sequence':self.sequence,'layers':[title for title,roles in self.layers],'nodes':nodes,'edges':edges,'updates':copy.deepcopy(self.updates),'status':copy.deepcopy(self.status),'busy':self.busy,'poll_seconds':900,'source_cycle_seconds':1800,'sources':self.sources,'ethical_study':study_frame(self.domain+'industry',self.sequence),'scope':'Role-level ecosystem model, not an exhaustive company inventory or a live map of private devices. Feed arrivals enter the source-study queue; they do not silently rewrite asserted topology.'}
 def close(self):self.closed=True
