"""Automatic public-source polling, lossless local input queue and resident-engine supervision."""
import concurrent.futures,contextlib,re,hashlib,html,html.parser,importlib.util,ipaddress,json,os,pathlib,queue,socket,sqlite3,subprocess,sys,threading,time,urllib.error,urllib.parse,urllib.request,xml.etree.ElementTree as ET
class PlainText(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.hidden=0
 def handle_starttag(self,tag,attrs):
  if tag in ['script','style']:self.hidden+=1
 def handle_endtag(self,tag):
  if tag in ['script','style']:self.hidden=max(0,self.hidden-1)
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
def plain(value):
 p=PlainText();p.feed(str(value));return ' '.join(' '.join(p.parts).split())
def public_url(url):
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Use a public HTTPS URL without embedded credentials')
 if p.port not in [None,443]:raise ValueError('Public sources use HTTPS port 443')
 for result in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM):
  if not ipaddress.ip_address(result[4][0]).is_global:raise ValueError('Public-source URLs cannot target private network addresses')
 return url
class PublicRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return super().redirect_request(req,fp,code,msg,headers,public_url(newurl))
class AutoRuntime:
 def __init__(self,root,catalog,event,obs_request):
  self.root=root;self.catalog=catalog;self.event=event;self.obs_request=obs_request;self.path=root/'data/autonomous.sqlite3';self.settings_file=root/'data/automatic-inputs.json';self.lock=threading.RLock();self.stop=threading.Event();self.process=None;self.worker_restarts=0;self.current=None;self.last_output=None;self.sources=[];self.engine_rows={};self.received=0;self.status='starting';self.stop_workers=False
  self.settings={'enabled':True,'web_enabled':True,'bus_enabled':True,'recheck_seconds':30,'sources':[]}
  topics=['Cryptography','Distributed computing','Artificial intelligence','Resource allocation','Star','Ethics of artificial intelligence']
  for title in topics:self.settings['sources'].append({'name':'Wikipedia · '+title,'kind':'wikipedia','url':'https://en.wikipedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','prop':'extracts|info|revisions','explaintext':1,'exintro':1,'inprop':'url','rvprop':'ids|timestamp','redirects':1,'titles':title}),'enabled':True,'interval':900})
  for name,kind,url,interval in [('NASA news','rss','https://www.nasa.gov/feed/',900),('CISA advisories','rss','https://www.cisa.gov/cybersecurity-advisories/all.xml',900),('NIST research news','rss','https://www.nist.gov/news-events/news/rss.xml',900),('World Bank · global electricity access','json','https://api.worldbank.org/v2/country/WLD/indicator/EG.ELC.ACCS.ZS?format=json&per_page=5',21600)]:self.settings['sources'].append({'name':name,'kind':kind,'url':url,'enabled':True,'interval':interval})
  try:self.settings.update(json.loads(self.settings_file.read_text(encoding='utf8')))
  except (OSError,ValueError):pass
  with self.db() as c:
   c.executescript('CREATE TABLE IF NOT EXISTS inputs(id INTEGER PRIMARY KEY,identity TEXT UNIQUE,source TEXT,kind TEXT,title TEXT,url TEXT,producer TEXT,sha256 TEXT,text TEXT,data TEXT,retrieved REAL,status TEXT DEFAULT "pending",passes INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS executions(id INTEGER PRIMARY KEY,input_id INTEGER,trigger TEXT,created REAL,result TEXT); CREATE TABLE IF NOT EXISTS cursors(name TEXT PRIMARY KEY,value INTEGER); CREATE TABLE IF NOT EXISTS snapshots(sha256 TEXT PRIMARY KEY,url TEXT,created REAL,raw BLOB); CREATE TABLE IF NOT EXISTS source_status(url TEXT PRIMARY KEY,result TEXT);')
   c.execute('UPDATE inputs SET status="pending" WHERE status="processing"')
   for r in c.execute('SELECT result FROM source_status'):self.sources.append(json.loads(r[0]))
   for r in c.execute('SELECT result FROM executions ORDER BY id DESC LIMIT 1'):
    self.last_output=json.loads(r[0]);self.engine_rows={m['id']:m for m in self.last_output.get('engines',[])}
  self.persist()
  for name,target in [('Automatic web intake',self.web_loop),('Live process intake',self.bus_loop),('Resident engine supervisor',self.engine_loop)]:threading.Thread(target=target,daemon=True,name=name).start()
 @contextlib.contextmanager
 def db(self):
  c=sqlite3.connect(self.path,timeout=20);c.row_factory=sqlite3.Row
  try:
   with c:yield c
  finally:c.close()
 def persist(self):
  with self.lock:
   p=self.settings_file.with_suffix('.tmp');p.write_text(json.dumps(self.settings,indent=2),encoding='utf8');p.replace(self.settings_file)
 def configure(self,x):
  with self.lock:
   for k in ['enabled','web_enabled','bus_enabled']:
    if k in x:self.settings[k]=bool(x[k])
   if 'recheck_seconds' in x:self.settings['recheck_seconds']=max(5,min(3600,float(x['recheck_seconds'])))
   if 'sources' in x:
    sources=x['sources']
    if not isinstance(sources,list) or len(sources)>40:raise ValueError('Use up to 40 sources')
    for row in sources:
     public_url(row['url']);row['interval']=max(300,min(86400,float(row.get('interval',900))))
     if row.get('kind') not in ['wikipedia','rss','json','html']:raise ValueError('Unknown source type')
    self.settings['sources']=sources
   self.persist()
  return self.view()
 def ingest(self,source,kind,title,url,text,data=None,producer=None):
  raw=str(text).encode('utf8',errors='backslashreplace').decode('utf8');digest=hashlib.sha256(raw.encode()).hexdigest();data_json=json.dumps(data if data is not None else {'text':raw},ensure_ascii=True,sort_keys=True,allow_nan=False)
  identity=hashlib.sha256((source+'|'+digest+'|'+data_json).encode()).hexdigest()
  if len(raw.encode())>2_000_000:raise ValueError('Input exceeds 2 MB; full source snapshot remains separately archived')
  with self.db() as c:
   cur=c.execute('INSERT OR IGNORE INTO inputs(identity,source,kind,title,url,producer,sha256,text,data,retrieved) VALUES(?,?,?,?,?,?,?,?,?,?)',(identity,source,kind,title,url,producer or source,digest,raw,data_json,time.time()))
   return cur.lastrowid if cur.rowcount else None
 def source_record(self,url,**x):
  item=next((s for s in self.sources if s['url']==url),{'url':url});item.update(x)
  with self.lock:self.sources=[s for s in self.sources if s['url']!=url]+[item]
  with self.db() as c:c.execute('INSERT OR REPLACE INTO source_status VALUES(?,?)',(url,json.dumps(item)))
 def poll_source(self,source):
  url=source['url'];start=time.time()
  try:
   public_url(url);request=urllib.request.Request(url,headers={'User-Agent':'InferenceObservatory/1.1 (personal local research)','Accept':'application/json, application/rss+xml, application/atom+xml, text/html;q=0.8'})
   with urllib.request.build_opener(PublicRedirect()).open(request,timeout=20) as response:
    raw=response.read(8_000_001);content_type=response.headers.get('Content-Type','')
    if len(raw)>8_000_000:raise ValueError('Snapshot exceeds 8 MB read limit')
    charset=response.headers.get_content_charset() or 'utf8'
   digest=hashlib.sha256(raw).hexdigest()
   with self.db() as c:c.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?)',(digest,url,time.time(),raw))
   docs=[];body=raw.decode(charset,errors='replace');kind=source['kind']
   if kind=='wikipedia':
    payload=json.loads(body)
    for page in payload.get('query',{}).get('pages',{}).values():
     if 'missing' in page:continue
     docs.append((page.get('title',source['name']),page.get('fullurl',url),page.get('extract',''),{'title':page.get('title'),'revision':page.get('revisions',[]),'attribution':'Wikipedia contributors; CC BY-SA 4.0','upstream_api':url,'text':page.get('extract','')}))
   elif kind=='rss':
    tree=ET.fromstring(body);items=tree.findall('.//item') or tree.findall('.//{http://www.w3.org/2005/Atom}entry')
    for item in items[:12]:
     def field(name):
      e=next((n for n in item if n.tag.split('}')[-1]==name),None);return ''.join(e.itertext()) if e is not None else ''
     title=plain(field('title'));link=field('link')
     if not link:
      el=next((n for n in item if n.tag.split('}')[-1]=='link'),None);link=el.attrib.get('href','') if el is not None else url
     description=plain(field('description') or field('summary') or field('content'));docs.append((title,link,title+'\n'+description,{'title':title,'url':link,'published':field('pubDate') or field('updated'),'description':description,'feed':url}))
   elif kind=='json':
    payload=json.loads(body);docs=[(source['name'],url,json.dumps(payload,ensure_ascii=False),{'dataset':payload,'upstream_api':url})]
   else:docs=[(source['name'],url,plain(body),{'text':plain(body),'upstream_url':url})]
   inserted=0
   for title,link,text,data in docs:
    if urllib.parse.urlsplit(link).scheme not in ['http','https']:link=url
    if text.strip():inserted+=bool(self.ingest(source['name'],'web',title,link,text,data,urllib.parse.urlsplit(url).hostname))
   self.source_record(url,name=source['name'],status='connected',last_checked=time.time(),last_success=time.time(),next_poll=time.time()+source['interval'],sha256=digest,bytes=len(raw),documents=len(docs),new_inputs=inserted,duration_ms=round((time.time()-start)*1000))
  except Exception as e:self.source_record(url,name=source['name'],status='error',last_checked=time.time(),next_poll=time.time()+min(source['interval'],300),error=type(e).__name__+': '+str(e))
 def web_loop(self):
  while not self.stop.is_set():
   if self.settings['enabled'] and self.settings['web_enabled']:
    due=[s for s in self.settings['sources'] if s.get('enabled',True) and time.time()>=next((x.get('next_poll',0) for x in self.sources if x['url']==s['url']),0)]
    for source in due:
     if self.stop.is_set():break
     self.poll_source(source);self.stop.wait(1)
   self.stop.wait(5)
 def cursor(self,name):
  with self.db() as c:
   r=c.execute('SELECT value FROM cursors WHERE name=?',(name,)).fetchone();return r[0] if r else 0
 def set_cursor(self,name,value):
  with self.db() as c:c.execute('INSERT OR REPLACE INTO cursors VALUES(?,?)',(name,value))
 def accept_bus(self,topic,data):
  if not self.settings['enabled'] or not self.settings['bus_enabled']:return
  if topic=='process-event':
   inner=data.get('topic','') if isinstance(data,dict) else ''
   if inner.startswith(('inference.','autonomous.')) or (isinstance(data,dict) and data.get('name')=='Inference Observatory'):return
  if topic not in ['module','process-event']:return
  if topic=='module' and data.get('status') not in ['complete','error']:return
  self.ingest('Observatory · '+topic,'bus',str(data.get('id',data.get('topic',topic))),'',json.dumps(data,ensure_ascii=False),data,str(data.get('name',data.get('id','Observatory'))))
 def bus_loop(self):
  last_obs=0
  # Consume existing saved events as well as new UDP packets; cursors prevent replay storms.
  while not self.stop.is_set():
   if self.settings['enabled'] and self.settings['bus_enabled']:
    try:
     with sqlite3.connect((self.root/'data/observatory.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=5) as c:
      cursor=self.cursor('observatory')
      if not cursor:
       cursor=max(0,c.execute('SELECT coalesce(max(id),0) FROM events').fetchone()[0]-60)
      rows=c.execute('SELECT id,topic,payload FROM events WHERE id>? AND topic IN ("observatory.module","observatory.process-event") ORDER BY id LIMIT 60',(cursor,)).fetchall()
     for ident,topic,payload in rows:self.accept_bus(topic.split('.',1)[1],json.loads(payload));self.set_cursor('observatory',ident)
    except Exception as e:self.bus_error=str(e)
    try:self.read_flux()
    except Exception as e:self.flux_error=str(e)
    if time.time()-last_obs>60:
     try:
      sources=self.obs_request('/api/sources');self.ingest('Observatory · existing sources','bus','Existing web research & source state','',json.dumps(sources,ensure_ascii=False),sources,'Observatory source hub')
     except Exception as e:self.bus_error=str(e)
     last_obs=time.time()
   self.stop.wait(3)
 def read_flux(self):
  app=pathlib.Path.home()/'Desktop/CHAT GPT APPS/FluxBus-v2';path=app/'FluxBus-data/world_grid_hub.db'
  if not path.exists():raise FileNotFoundError('FluxBus database unavailable')
  if not hasattr(self,'flux_storage'):
   spec=importlib.util.spec_from_file_location('flux_readonly_storage',app/'source/payload_storage.py');self.flux_storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.flux_storage)
  c=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,factory=self.flux_storage.StoredConnection,timeout=5)
  try:
   try:c.execute('SELECT 1 FROM node_events LIMIT 1').fetchone();self.flux_mode='Live read-only database'
   except sqlite3.OperationalError:
    c.close();c=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True,factory=self.flux_storage.StoredConnection,timeout=5);self.flux_mode='Checkpoint-only read; live FluxBus events also arrive through Observatory';self.flux_error=None
   cursor=self.cursor('fluxbus')
   if not cursor:cursor=max(0,c.execute('SELECT coalesce(max(id),0) FROM node_events').fetchone()[0]-60)
   for row in c.execute('SELECT id,node_id,after_json FROM node_events WHERE id>? ORDER BY id LIMIT 60',(cursor,)).fetchall():
    ident,node,raw=row
    if node!='inference-observatory':
     raw=self.flux_storage.unpack_text(c,raw);data=json.loads(raw)
     self.ingest('FluxBus · '+node,'bus',node,'',json.dumps(data,ensure_ascii=False),data,node)
    self.set_cursor('fluxbus',ident)
  finally:c.close()
 def start_worker(self):
  if self.process and self.process.poll() is None:return
  self.process=subprocess.Popen([sys.executable,str(self.root/'resident_engines.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(self.root/'data/resident-errors.log').open('a'),text=True,encoding='utf8',bufsize=1,cwd=self.root,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));self.reader=queue.Queue()
  def read_lines(proc,out):
   for line in proc.stdout:out.put(line)
  threading.Thread(target=read_lines,args=(self.process,self.reader),daemon=True).start()
  ready=json.loads(self.reader.get(timeout=20))
  if not ready.get('ready'):raise RuntimeError('Engine worker did not initialize')
  self.worker_restarts+=1
 def engine_loop(self):
  last_run=0;retry=1
  while not self.stop.is_set():
   if not self.settings['enabled']:self.status='paused';self.stop.wait(1);continue
   try:
    self.start_worker();self.status='listening'
    with self.db() as c:
     row=c.execute('SELECT * FROM inputs WHERE status="pending" ORDER BY CASE kind WHEN "web" THEN 0 ELSE 1 END,id LIMIT 1').fetchone();trigger='new_input'
     if row is None and time.time()-last_run>=self.settings['recheck_seconds']:
      row=c.execute('SELECT * FROM inputs ORDER BY CASE kind WHEN "web" THEN 0 ELSE 1 END,retrieved DESC LIMIT 1').fetchone();trigger='interval_recheck'
     if row is None:self.stop.wait(.5);continue
     item=dict(row);c.execute('UPDATE inputs SET status="processing" WHERE id=?',(item['id'],))
    self.current={'input_id':item['id'],'source':item['source'],'title':item['title'],'trigger':trigger};self.status='processing'
    envelope={**item,'data':json.loads(item['data'])}
    # Fetch actual module output instead of treating a completion notification as the result itself.
    if item['source']=='Observatory · module' and envelope['data'].get('id') and time.time()-getattr(self,'last_module_fetch',0)>30:
     self.last_module_fetch=time.time()
     try:envelope['data']['module_output']=self.obs_request('/api/module?'+urllib.parse.urlencode({'id':envelope['data']['id']}))
     except Exception as e:envelope['data']['result_fetch_error']=str(e)
    self.process.stdin.write(json.dumps(envelope,ensure_ascii=True)+'\n');self.process.stdin.flush();result=json.loads(self.reader.get(timeout=25))
    if result.get('error'):raise RuntimeError(result['error'])
    with self.db() as c:
     c.execute('INSERT INTO executions(input_id,trigger,created,result) VALUES(?,?,?,?)',(item['id'],trigger,time.time(),json.dumps(result,ensure_ascii=True,allow_nan=False)));c.execute('UPDATE inputs SET status="complete",passes=passes+1 WHERE id=?',(item['id'],))
    self.engine_rows={m['id']:m for m in result['engines']};self.last_output=result;self.current=None;last_run=time.time();retry=1
   except Exception as e:
    self.status='recovering: '+str(e)
    if self.process and self.process.poll() is None:self.process.kill();self.process.wait()
    with self.db() as c:c.execute('UPDATE inputs SET status="pending" WHERE status="processing"')
    self.stop.wait(retry);retry=min(retry*2,30)
 def context(self,query=''):
  with self.db() as c:rows=[dict(r) for r in c.execute('SELECT source,title,url,text,kind FROM inputs ORDER BY CASE kind WHEN "web" THEN 0 ELSE 1 END,retrieved DESC LIMIT 90')]
  words={w for w in re.findall(r'[a-z]{4,}',query.lower()) if w not in {'this','that','with','have','prev','please','core','true','scripts'}}
  rows.sort(key=lambda r:sum(w in (r['title']+' '+r['text'][:12000]).lower() for w in words),reverse=True)
  picked=[];domains={}
  for row in rows:
   domain=urllib.parse.urlsplit(row['url']).hostname or row['source']
   if domains.get(domain,0)>=2:continue
   domains[domain]=domains.get(domain,0)+1;picked.append(row)
   if len(picked)>=5:break
  return '\n\n'.join(f"SOURCE: {r['source']}\nTITLE: {r['title']}\nURL: {r['url']}\nEXCERPT: {r['text'][:4000]}" for r in picked)
 def view(self):
  with self.db() as c:
   counts=dict(c.execute('SELECT status,count(*) FROM inputs GROUP BY status'));total=c.execute('SELECT count(*) FROM inputs').fetchone()[0];passes=c.execute('SELECT count(*) FROM executions').fetchone()[0];recent=[dict(r) for r in c.execute('SELECT id,source,kind,title,url,sha256,retrieved,status,passes FROM inputs ORDER BY id DESC LIMIT 30')]
  return {'settings':self.settings,'status':self.status,'worker_pid':self.process.pid if self.process and self.process.poll() is None else None,'worker_starts':self.worker_restarts,'current':self.current,'counts':counts,'inputs':total,'passes':passes,'sources':self.sources,'engines':[self.engine_rows.get(m['id'],{'id':m['id'],'name':m['name'],'status':'starting','received':0,'source_calls':0}) for m in self.catalog['modules']],'recent':recent,'bus_error':getattr(self,'bus_error',None),'flux_error':getattr(self,'flux_error',None),'flux_mode':getattr(self,'flux_mode','Waiting for input'),'context_scope':'Latest five source excerpts feed the historical prompt loop. All retained text stays in the input database. External text never executes as code.'}
 def close(self):
  self.stop.set()
  if self.process and self.process.poll() is None:self.process.terminate()
