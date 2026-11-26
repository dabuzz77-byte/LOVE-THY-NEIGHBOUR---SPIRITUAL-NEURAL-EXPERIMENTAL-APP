"""Refreshable public scholarly metadata with topic selection, provenance and bounded storage."""
import collections,contextlib,hashlib,html,json,re,sqlite3,threading,time,urllib.parse,urllib.request
from pathlib import Path
from .learning_intake import public_url,NoRedirect
TOPICS=[('Tesla / resonance','Nikola Tesla resonance wireless power',3),('Electrical engineering','resonant inductive power transmission',2),('Unconventional physics','experimental tests anomalous electromagnetic effects',2),('Mathematics','numerical analysis exact arithmetic',1),('Physics','quantum mechanics measurement',1),('Cosmology','cosmology observational constraints',1),('Chemistry','chemical reaction kinetics',1),('Biology','ecology biodiversity',1),('Earth science','climate atmosphere observations',1),('Computing','causal inference computer systems',1),('Engineering','control systems reliability',1),('Health science','systematic review evidence quality',1),('Social systems','infrastructure resilience human welfare',1)]
PATENTS=[('US645576A','Tesla: System of transmission of electrical energy','https://patents.google.com/patent/US645576A/en','Historical patent describing proposed electrical-energy transmission. Patent claims require separate engineering and replication assessment.'),('US649621A','Tesla: Apparatus for transmission of electrical energy','https://patents.google.com/patent/US649621A/en','Historical patent describing transmitting and receiving apparatus. Retained as primary historical material, not proof of every claimed outcome.')]
class ScienceLibrary:
 def __init__(self,data,bus=None,intake=None,circuit=None,start=True):
  self.data=Path(data);self.data.mkdir(parents=True,exist_ok=True);self.path=self.data/'science-library.sqlite3';self.settings_path=self.data/'science-library-settings.json';self.bus=bus;self.intake=intake;self.circuit=circuit;self.halt=threading.Event();self.wake=threading.Event();self.lock=threading.RLock();self.pending=collections.deque(maxlen=16);self.status=[];self.visits=collections.Counter();self.cache={};self.worker=None;self.busy=False;self.sequence=0
  try:self.settings=json.loads(self.settings_path.read_text(encoding='utf-8'))
  except (OSError,ValueError):self.settings={'enabled':True,'interval_seconds':900}
  with self.connect() as db:
   db.execute('create virtual table if not exists science using fts5(ident UNINDEXED,title,body,source,record UNINDEXED)')
  for ident,title,url,body in PATENTS:self.store({'id':ident,'title':title,'url':url,'summary':body,'source':'Tesla primary patent','classification':'historical primary document','published':'1900','retrieved':None,'indexed':time.time(),'access':'Primary-source link; full text not downloaded'})
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='science-library-intake');self.worker.start()
 @contextlib.contextmanager
 def connect(self):
  db=sqlite3.connect(self.path,timeout=5)
  try:
   with db:yield db
  finally:db.close()
 def store(self,row):
  row={**row,'title':html.unescape(re.sub('<[^>]+>',' ',str(row['title'])))[:500]};ident=row.get('id') or hashlib.sha256((row['url']+'\n'+row['title']).encode()).hexdigest();row['id']=ident
  with self.connect() as db:
   db.execute('delete from science where ident=?',(ident,));db.execute('insert into science values(?,?,?,?,?)',(ident,row['title'],row.get('summary',''),row['source'],json.dumps(row,ensure_ascii=True)))
   db.execute('delete from science where rowid not in (select rowid from science order by rowid desc limit 5000)')
  return row
 def request(self,query):
  query=str(query).strip()[:200]
  if not query or re.search(r'(?i)(?:[\w.+-]+@[\w.-]+\.[a-z]{2,}|password|api[_ -]?key|bearer |secret|token=)',query):raise ValueError('Use a public scientific topic, without account details or secrets')
  with self.lock:self.pending.append(query)
  self.wake.set();return {'scheduled':True,'public_query':query}
 def choose_topic(self):
  goal=str(getattr(self.circuit,'goal','')).lower();name,query,weight=max(TOPICS,key=lambda t:t[2]/(1+self.visits[t[0]])+.25*sum(w in goal for w in t[1].lower().split() if len(w)>4));self.visits[name]+=1;return query
 def fetch_json(self,url):
  if urllib.parse.urlsplit(url).hostname not in ('api.crossref.org','www.ebi.ac.uk'):raise ValueError('Unregistered provider')
  public_url(url);req=urllib.request.Request(url,headers={'User-Agent':'NeuralAppScienceLibrary/1.0','Accept':'application/json'})
  with urllib.request.build_opener(NoRedirect()).open(req,timeout=8) as response:raw=response.read(1_000_001)
  if len(raw)>1_000_000:raise ValueError('Metadata response exceeds limit')
  return json.loads(raw)
 def cycle(self,query=None):
  with self.lock:
   if self.busy:return {'status':'busy'}
   self.busy=True
  try:
   query=query or self.choose_topic()
   if time.time()-self.cache.get(query,0)<21600:
    with self.lock:self.status=[{'query':query,'status':'cached','policy':'six-hour query cache'}]
    return {'status':'cached'}
   recent=query.startswith('[recent] ');search_query=query[9:] if recent else query
   params={'query':search_query,'rows':5,'select':'DOI,title,published,type,URL,license'}
   if recent:params.update(sort='published',order='desc',filter='until-pub-date:'+time.strftime('%Y-%m-%d',time.gmtime()))
   providers=[('Crossref','https://api.crossref.org/works?'+urllib.parse.urlencode(params)),('Europe PMC','https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':search_query+(' sort_date:y' if recent else ''),'format':'json','resultType':'lite','pageSize':5}))];states=[];received=[]
   for provider,url in providers:
    if self.halt.is_set():break
    try:
     payload=self.fetch_json(url);items=payload.get('message',{}).get('items',[]) if provider=='Crossref' else payload.get('resultList',{}).get('result',[]);count=0
     for item in items[:5]:
      if self.halt.is_set():break
      title=(item.get('title') or ['Untitled'])[0] if provider=='Crossref' else item.get('title','Untitled');doi=str(item.get('DOI') or item.get('doi') or '');link='https://doi.org/'+urllib.parse.quote(doi,safe='/') if re.fullmatch(r'10\.\d{4,9}/\S+',doi) else url
      if not doi and provider=='Europe PMC' and item.get('id'):link='https://europepmc.org/article/'+urllib.parse.quote(str(item.get('source','MED')),safe='')+'/'+urllib.parse.quote(str(item['id']),safe='')
      year=str(item.get('published',{}).get('date-parts',[['unknown']])[0][0]) if provider=='Crossref' else str(item.get('pubYear','unknown'))
      row=self.store({'title':title,'url':link,'summary':'Publication metadata for topic: '+query+'; year: '+year+'; type: '+str(item.get('type',item.get('pubType','publication'))),'source':provider,'classification':'research publication metadata; claims not independently validated','published':year,'retrieved':time.time(),'query':query,'access':'Source link; no full-text or paywall bypass'});received.append(row);count+=1
      if self.intake and hasattr(self.intake,'store'):self.intake.store('Science / '+provider,row['url'],row['title'],row['summary'])
     states.append({'source':provider,'url':url,'query':query,'status':'received' if count else 'empty','records':count,'retrieved':time.time()})
    except Exception as e:states.append({'source':provider,'query':query,'status':'unavailable','error':type(e).__name__+': '+str(e)[:180]})
   with self.lock:self.status=states;self.sequence+=1
   if received:self.cache[query]=time.time()
   if self.bus and received:self.bus.publish({'origin':'science-library-intake','target':'all','kind':'stage-output','payload':{'sources':received[:6],'provenance':'retrieved-scientific-metadata','predefined_text':True,'stochastic':False}})
   return {'status':states,'received':len(received)}
  finally:
   with self.lock:self.busy=False
 def retrieve(self,query):
  words=re.findall(r'[^\W_]+',str(query),re.UNICODE)[:12]
  if not words:return []
  match=' OR '.join('"'+w+'"' for w in words)
  with self.connect() as db:rows=db.execute('select record from science where science match ? order by bm25(science,0,6,1,1,0) limit 8',(match,)).fetchall()
  return [{'type':'science-source',**json.loads(raw),'excerpt':json.loads(raw).get('summary','')} for raw, in rows]
 def configure(self,b):
  with self.lock:
   if 'enabled' in b:
    if type(b['enabled'])is not bool:raise ValueError('Enabled must be boolean')
    self.settings['enabled']=b['enabled']
   if 'interval_seconds' in b:self.settings['interval_seconds']=max(300,min(86400,int(b['interval_seconds'])))
   self.settings_path.write_text(json.dumps(self.settings),encoding='utf-8')
  self.wake.set();return self.view()
 def view(self):
  with self.connect() as db:count=db.execute('select count(*) from science').fetchone()[0];recent=[json.loads(r[0]) for r in db.execute('select record from science order by rowid desc limit 12')]
  with self.lock:return {'sequence':self.sequence,'settings':copy_settings(self.settings),'busy':self.busy,'sources':list(self.status),'topics':[{'name':n,'query':q,'weight':w} for n,q,w in TOPICS],'records':count,'recent':recent,'scope':'Refreshable metadata and source links, not all scientific knowledge. Automatic queries are public topic labels; app conversations and private account data are not exported.'}
 def loop(self):
  while not self.halt.is_set():
   if self.settings.get('enabled'):
    with self.lock:query=self.pending.popleft() if self.pending else None
    self.cycle(query)
   self.wake.wait(self.settings.get('interval_seconds',900));self.wake.clear()
 def close(self):
  self.halt.set();self.wake.set()
  if self.worker:self.worker.join(2)

def copy_settings(value):return dict(value)
