"""Scheduled public-feed retrieval and private local-index retrieval. No account scraping."""
import contextlib,hashlib,html,ipaddress,json,re,socket,threading,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET,sqlite3
DEFAULTS=[('NASA news','https://www.nasa.gov/news-release/feed/'),('NASA technology','https://www.nasa.gov/technology/feed/'),('NASA science','https://science.nasa.gov/feed/'),('Earth events','https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson'),('AI research','https://rss.arxiv.org/rss/cs.AI'),('Learning research','https://rss.arxiv.org/rss/cs.LG'),('Physics research','https://rss.arxiv.org/rss/physics'),('Python engineering','https://blog.python.org/rss.xml')]
EXTENDED_SOURCES=[('Mathematics research','https://rss.arxiv.org/rss/math'),('Astrophysics research','https://rss.arxiv.org/rss/astro-ph'),('Mathematical physics research','https://rss.arxiv.org/rss/math-ph'),('General physics / hypotheses','https://rss.arxiv.org/rss/physics.gen-ph'),('Classical physics / electromagnetism','https://rss.arxiv.org/rss/physics.class-ph')]
EXTENDED_SOURCES += [('Humanitarian news / UN','https://news.un.org/feed/subscribe/en/news/all/rss.xml'),('World news / BBC','https://feeds.bbci.co.uk/news/world/rss.xml')]
DEFAULTS += EXTENDED_SOURCES

def public_url(url):
 p=urllib.parse.urlsplit(str(url))
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):raise ValueError('Use a public HTTPS feed without credentials.')
 for row in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM):
  if not ipaddress.ip_address(row[4][0]).is_global:raise ValueError('Public feeds cannot address private or local networks.')
 return url
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k):return None
class KnowledgeIntake:
 def __init__(self,core,data):
  self.core=core;self.data=data;self.stop=threading.Event();self.wake=threading.Event();self.status=[];self.busy=False;self.config_path=data/'learning-sources.json';self.lock=threading.RLock()
  try:self.config=json.loads(self.config_path.read_text())
  except (OSError,ValueError):self.config={'enabled':True,'interval_seconds':1800,'sources':[{'name':n,'url':u,'enabled':True} for n,u in DEFAULTS]}
  existing={v['url'] for v in self.config.get('sources',[])}
  for name,url in EXTENDED_SOURCES:
   if url not in existing and len(self.config['sources'])<32:self.config['sources'].append({'name':name,'url':url,'enabled':True})
  with core.connect() as db:db.execute('create table if not exists knowledge(id text primary key,source text,url text,title text,text text,stamp real,private integer)')
  self.worker=threading.Thread(target=self.loop,daemon=True,name='learning-public-intake');self.worker.start()
 def configure(self,body):
  sources=body.get('sources',self.config['sources'])
  if not isinstance(sources,list) or len(sources)>32:raise ValueError('Use up to 32 public feed sources.')
  clean=[]
  for item in sources:clean.append({'name':str(item.get('name','public feed'))[:100],'url':public_url(str(item.get('url',''))),'enabled':bool(item.get('enabled',True))})
  with self.lock:self.config={'enabled':bool(body.get('enabled',True)),'interval_seconds':max(300,min(86400,int(body.get('interval_seconds',1800)))),'sources':clean};self.config_path.write_text(json.dumps(self.config,indent=2),encoding='utf-8')
  self.wake.set();return self.view()
 def store(self,source,url,title,text,private=False):
  text=html.unescape(re.sub('<[^>]+>',' ',str(text)));text=re.sub(r'\s+',' ',text).strip()[:1200];ident=hashlib.sha256((source+url+text).encode()).hexdigest()
  with self.core.lock,self.core.connect() as db:
   db.execute('insert or ignore into knowledge values(?,?,?,?,?,?,?)',(ident,source,url,str(title)[:300],text,time.time(),int(private)));db.execute('delete from knowledge where id not in (select id from knowledge order by stamp desc limit 3000)')
 def retrieve(self,query=''):
  with self.core.lock,self.core.connect() as db:
   rows=db.execute('select source,url,title,text,stamp,private from knowledge where title like ? or text like ? order by stamp desc limit 30',('%'+str(query)[:120]+'%','%'+str(query)[:120]+'%')).fetchall()
  return [dict(zip(('source','url','title','excerpt','fetched','private'),r)) for r in rows]
 def balanced(self):
  with self.core.lock,self.core.connect() as db:
   names=[r[0] for r in db.execute('select distinct source from knowledge where private=0')];out=[]
   for name in names:
    for r in db.execute('select source,url,title,text,stamp from knowledge where source=? and private=0 order by stamp desc limit 2',(name,)):
     out.append(dict(zip(('source','url','title','excerpt','fetched'),r)))
   return out
 def rails(self):
  groups={'engineering':('python','technology'),'ai-learning':('ai research','learning research'),'cosmos':('physics','nasa science','nasa news'),'earth':('earth',)}
  result=[]
  for name,terms in groups.items():
   sources=[x for x in self.config['sources'] if any(t in x['name'].lower() for t in terms)]
   result.append({'id':name,'sources':sources,'status':[x for x in self.status if any(x['name']==v['name'] for v in sources)],'stages':['retrieve','source-labelled excerpt','local index','native retrieval','task-specific validation'],'automatic':self.config['enabled'],'interval_seconds':self.config['interval_seconds'],'weight_update':False})
  return result
 def view(self,query=''):

  with self.core.connect() as db:counts=db.execute('select private,count(*) from knowledge group by private').fetchall()
  return {'rails':self.rails(),'config':self.config,'busy':self.busy,'sources':self.status,'counts':dict(counts),'documents':self.retrieve(query),'balanced_public':self.balanced(),'scope':'Public feed excerpts and existing private local Google records. No account connection, no private history transmission, no remote instructions executed.'}
 def local_google(self):
  path=self.data/'google-index/index.sqlite3'
  if not path.exists():return 0
  with contextlib.closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:rows=db.execute("select source,url,title,content from sessions where source in ('ai_mode','gemini','google_activity','search') order by created desc limit 100").fetchall()
  for source,url,title,text in rows:self.store('private-google:'+source,url,title,text,True)
  return len(rows)
 def fetch(self,source):
  url=public_url(source['url']);opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
  with opener.open(urllib.request.Request(url,headers={'User-Agent':'NeuralApp-PublicLearning/1.0','Accept':'application/rss+xml,application/atom+xml,application/json,application/xml'}),timeout=12) as response:
   raw=response.read(1000001)
   if len(raw)>1000000:raise ValueError('Feed exceeds 1 MB budget.')
  count=0
  if url.endswith('.geojson'):
   for item in json.loads(raw).get('features',[])[:40]:
    p=item.get('properties',{});self.store(source['name'],p.get('url',url),p.get('title','Earth event'),json.dumps({'magnitude':p.get('mag'),'time':p.get('time'),'place':p.get('place')}));count+=1
  else:
   if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('XML entity declarations are not accepted.')
   root=ET.fromstring(raw)
   for item in [x for x in root.iter() if x.tag.split('}')[-1] in ('item','entry')][:40]:
    fields={x.tag.split('}')[-1]:x for x in item};get=lambda key:''.join(fields[key].itertext()) if key in fields else '';link=get('link') or (fields['link'].get('href','') if 'link' in fields else '') or url
    if urllib.parse.urlsplit(link).scheme!='https':link=url
    self.store(source['name'],link,get('title'),get('description') or get('summary') or get('content'));count+=1
  return count
 def cycle(self):
  if self.busy:return
  self.busy=True;states=[]
  try:
   for source in list(self.config['sources']):
    if self.stop.is_set():break
    if not source['enabled']:continue
    try:count=self.fetch(source);states.append({'name':source['name'],'url':source['url'],'fetched':time.time(),'items':count,'status':'received'})
    except Exception as e:states.append({'name':source['name'],'url':source['url'],'status':'unavailable','error':str(e)[:240]})
   try:states.append({'name':'Private Google index','items':self.local_google(),'status':'local-index-only'})
   except Exception as e:states.append({'name':'Private Google index','error':str(e)[:240]})
   self.status=states
   callback=getattr(self,'on_cycle',None)
   if callback:callback(states)
  finally:self.busy=False
 def loop(self):
  while not self.stop.is_set():
   if self.config['enabled']:self.cycle()
   self.wake.wait(self.config['interval_seconds']);self.wake.clear()
 def refresh(self):self.wake.set();return {'scheduled':True,'busy':self.busy}
 def close(self):self.stop.set();self.wake.set();self.worker.join(2)
