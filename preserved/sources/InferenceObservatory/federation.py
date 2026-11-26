"""Federated app catalogue, measurable online neural topic router and research outbox."""
import collections,contextlib,hashlib,json,math,os,pathlib,re,secrets,socket,sqlite3,threading,time,urllib.request,uuid
import numpy as np
TOPICS={
 'security':['crypto','encrypt','security','tls','signature','identity','key derivation'],
 'distributed systems':['mesh','bus','distributed','node','message','routing'],
 'neural learning':['neural','learning','inference','model','training','llama'],
 'resources':['resource','economic','scarcity','allocation','energy','floor'],
 'ethics':['ethic','virtue','covenant','souls','redemption','human benefit'],
 'signals':['signal','frequency','waveform','resonance','spectrum','hydrogen']}
LABELS=list(TOPICS)
def features(text):
 x=np.zeros(128,dtype=np.float64)
 for word in re.findall(r'[a-z][a-z0-9_-]{2,}',text.lower()):
  d=hashlib.blake2b(word.encode(),digest_size=4).digest();x[int.from_bytes(d[:2],'big')%128]+=1 if d[2]&1 else -1
 return x/max(np.linalg.norm(x),1)
def weak_label(text):
 text=text.lower();scores=[sum(text.count(w) for w in terms) for terms in TOPICS.values()]
 return int(np.argmax(scores)) if max(scores,default=0)>0 else None
class NeuralRouter:
 def __init__(self,path):
  self.path=path;self.lock=threading.RLock();self.steps=0;self.cursor=0;self.train=[];self.test=[];self.history=[];rng=np.random.default_rng(17)
  self.w1=rng.normal(0,.15,(128,24));self.b1=np.zeros(24);self.w2=rng.normal(0,.15,(24,len(LABELS)));self.b2=np.zeros(len(LABELS))
  if path.exists():
   with np.load(path,allow_pickle=False) as z:
    for n in ['w1','b1','w2','b2']:setattr(self,n,z[n])
    self.steps=int(z['steps']);self.cursor=int(z['cursor']);self.train=[(x,int(y)) for x,y in zip(z['train_x'],z['train_y'])];self.test=[(x,int(y)) for x,y in zip(z['test_x'],z['test_y'])]
 def forward(self,x):
  h=np.tanh(x@self.w1+self.b1);z=h@self.w2+self.b2;z-=z.max(axis=-1,keepdims=True);p=np.exp(z);p/=p.sum(axis=-1,keepdims=True);return h,p
 def observe(self,text,label=None,identity=None):
  label=weak_label(text) if label is None else label
  if label is None:return False
  identity=identity or hashlib.sha256(text.encode(errors='backslashreplace')).hexdigest();pair=(features(text),label)
  with self.lock:
   target=self.test if int(hashlib.sha256(identity.encode()).hexdigest()[:8],16)%5==0 else self.train
   target.append(pair)
   # Keep per-class memory balanced. Raw documents remain in the durable input store.
   indices=[i for i,(_,y) in enumerate(target) if y==label]
   if len(indices)>300:target.pop(indices[0])
  return True
 def train_batch(self):
  with self.lock:
   if len(self.train)<12 or len({y for _,y in self.train})<2:return None
   classes={y for _,y in self.train};selected=[]
   for y in classes:
    candidates=[i for i,(_,v) in enumerate(self.train) if v==y];selected.extend(candidates[-6:])
   x=np.array([self.train[i][0] for i in selected]);y=np.array([self.train[i][1] for i in selected]);h,p=self.forward(x);loss=float(-np.log(np.maximum(p[np.arange(len(y)),y],1e-12)).mean());d=p.copy();d[np.arange(len(y)),y]-=1;d/=len(y)
   dw2=h.T@d;db2=d.sum(0);dh=(d@self.w2.T)*(1-h*h);dw1=x.T@dh;db1=dh.sum(0)
   for n,g in [('w1',dw1),('b1',db1),('w2',dw2),('b2',db2)]:setattr(self,n,getattr(self,n)-.04*np.clip(g,-2,2))
   self.steps+=1;row={'step':self.steps,'training_cross_entropy':loss,'timestamp':time.time()};self.history=(self.history+[row])[-120:];return row
 def save(self):
  with self.lock:
   tmp=self.path.with_suffix('.tmp')
   with tmp.open('wb') as f:np.savez_compressed(f,w1=self.w1,b1=self.b1,w2=self.w2,b2=self.b2,steps=self.steps,cursor=self.cursor,train_x=np.array([x for x,y in self.train]).reshape(-1,128),train_y=np.array([y for x,y in self.train]),test_x=np.array([x for x,y in self.test]).reshape(-1,128),test_y=np.array([y for x,y in self.test]))
   tmp.replace(self.path)
 def predict(self,text):
  with self.lock:p=self.forward(features(text)[None,:])[1][0]
  return dict(zip(LABELS,map(float,p)))
 def view(self):
  with self.lock:
   score=None;support=collections.Counter(y for _,y in self.test)
   if self.test:
    p=self.forward(np.array([x for x,y in self.test]))[1];score=float(np.mean(np.argmax(p,axis=1)==np.array([y for _,y in self.test])))
   return {'architecture':'128 hashed-text inputs → 24 tanh neurons → 6 topic outputs','parameters':sum(getattr(self,n).size for n in ['w1','b1','w2','b2']),'updates':self.steps,'training_examples':len(self.train),'held_out_examples':len(self.test),'held_out_weak_label_agreement':score,'held_out_support':{LABELS[y]:n for y,n in support.items()},'history':self.history,'weights_sha256':hashlib.sha256(self.w1.tobytes()+self.w2.tobytes()).hexdigest(),'objective':'Topic routing from source-derived/keyword weak labels; agreement is not factual accuracy or general intelligence','labels':LABELS}
class Federation:
 def __init__(self,root,autonomous,publish,flux):
  self.root=root;self.auto=autonomous;self.publish=publish;self.flux=flux;self.apps=pathlib.Path.home()/'Desktop/CHAT GPT APPS';self.catalog=[];self.stop=threading.Event();self.path=root/'data/research.sqlite3';self.router=NeuralRouter(root/'data/neural-router.npz');self.status='starting'
  with self.db() as c:c.executescript('CREATE TABLE IF NOT EXISTS research(id TEXT PRIMARY KEY,identity TEXT UNIQUE,topic TEXT,query TEXT,answer TEXT,citations TEXT,url TEXT,created REAL,input_id INTEGER,delivery TEXT); CREATE TABLE IF NOT EXISTS learned(digest TEXT PRIMARY KEY);')
  self.refresh_catalog();threading.Thread(target=self.loop,daemon=True,name='Federated neural learning').start()
 @contextlib.contextmanager
 def db(self):
  c=sqlite3.connect(self.path,timeout=15);c.row_factory=sqlite3.Row
  try:
   with c:yield c
  finally:c.close()
 def refresh_catalog(self):
  rows=[]
  for folder in sorted(self.apps.iterdir()):
   if not folder.is_dir():continue
   doc='';readmes=list(folder.glob('README*'))[:1]
   if readmes:
    try:doc=readmes[0].read_text(encoding='utf-8-sig',errors='replace')[:120000]
    except OSError:pass
   scores={topic:sum(w in (folder.name+' '+doc).lower() for w in words) for topic,words in TOPICS.items()}
   rows.append({'name':folder.name,'path':str(folder),'subjects':[n for n,v in scores.items() if v>0],'launchers':[f.name for f in folder.iterdir() if f.suffix.lower() in ['.cmd','.bat','.exe','.vbs']][:12],'connection':'adapter_required','evidence':'README and root file inventory; catalogue presence does not establish execution'})
  for row in rows:
   if row['name']=='FluxBus-v2':row['connection']='existing TCP + Observatory bridge'
   elif row['name']=='Postscarcity Observatory v4':row['connection']='authenticated live UDP + HTTP'
   elif row['name']=='AllPrevUnifiedEngine-FluxExpanded':row['connection']='HTTP broadcast endpoint configured'
   elif row['name'] in ['InferenceObservatory']:row['connection']='separate installation discovered; current hub is workspace version'
  self.catalog=rows
 def next_task(self):
  counts={topic:sum(topic in r['subjects'] for r in self.catalog) for topic in LABELS}
  with self.db() as c:done=dict(c.execute('SELECT topic,count(*) FROM research GROUP BY topic'))
  topic=max(LABELS,key=lambda t:counts[t]/(1+done.get(t,0)))
  query=f'Research practical advances in {topic} for interoperable local Python and Java applications, message-bus engines and human-benefit-oriented tools. Give implementable methods, failure modes, measurable evaluations and primary-source citations. Separate verified evidence from speculation. Do not request or use private account information.'
  return {'topic':topic,'query':query,'apps_sharing_subject':counts[topic],'action':'App-owned public source research and local model synthesis; optional Google captures remain supported','cadence':'One research cycle per 5 minutes; no rapid automated query loop'}
 def accept(self,x):
  answer=str(x.get('answer','')).strip();query=str(x.get('query','')).strip();topic=x.get('topic','distributed systems');provider='Native research' if x.get('provider')=='Native research' else 'Google AI Mode'
  if not answer or not query:raise ValueError('A real question and captured Google answer are required')
  if len(answer.encode())>1_000_000:raise ValueError('Answer exceeds 1 MB')
  citations=[str(v) for v in x.get('citations',[]) if str(v).startswith(('https://','http://'))];identity=hashlib.sha256((query+'\n'+answer).encode()).hexdigest()
  with self.db() as c:
   old=c.execute('SELECT id FROM research WHERE identity=?',(identity,)).fetchone()
   if old:return {'id':old['id'],'status':'already_retained'}
   ident=uuid.uuid4().hex
   input_id=self.auto.ingest(provider+' · '+topic,'research',query,x.get('url','https://www.google.com/search?udm=50'),answer,{'provider':provider,'query':query,'answer':answer,'citations':citations,'factual_verification':'unverified model output','research_id':ident,'topic':topic},provider+' research')
   c.execute('INSERT INTO research VALUES(?,?,?,?,?,?,?,?,?,?)',(ident,identity,topic,query,answer,json.dumps(citations),x.get('url',''),time.time(),input_id,'pending'))
  threading.Thread(target=self.deliver,args=(ident,),daemon=True).start();return {'id':ident,'input_id':input_id,'status':'retained_and_queued','engines':36,'verification':'Google output retained as unverified evidence'}
 def deliver(self,ident):
  with self.db() as c:r=dict(c.execute('SELECT * FROM research WHERE id=?',(ident,)).fetchone())
  provider='Native research' if r['answer'].startswith(('LOCAL MODEL REPORT','SOURCE DIGEST')) else 'Google AI Mode'
  parts=[r['answer'][i:i+2400] for i in range(0,len(r['answer']),2400)];results=[]
  previous={p['part']:p for p in json.loads(r['delivery'])} if r['delivery']!='pending' else {}
  for i,text in enumerate(parts):
   payload={'research_id':ident,'provider':provider,'topic':r['topic'],'part':i+1,'total':len(parts),'text':text,'question':r['query'][:1000],'citations':json.loads(r['citations'])[:12],'answer_sha256':hashlib.sha256(r['answer'].encode()).hexdigest(),'factual_verification':'unverified','origin':'Inference Observatory research'};row=dict(previous.get(i+1,{'part':i+1}))
   for name,fn in [('observatory',lambda:self.publish('inference.research.native' if provider=='Native research' else 'inference.research.google_ai_mode',payload)),('fluxbus',lambda:self.flux(payload)),('allprev',lambda:self.allprev(payload))]:
    old=row.get(name,{})
    if (name=='fluxbus' and old.get('ack',{}).get('status')=='ACK') or (name=='allprev' and old.get('response',{}).get('accepted') is True) or (name=='observatory' and old.get('status')=='sent_unconfirmed'):continue
    try:result=fn();row[name]=result
    except Exception as e:row[name]={'status':'unavailable','error':str(e)}
   results.append(row);time.sleep(.2)
  with self.db() as c:c.execute('UPDATE research SET delivery=? WHERE id=?',(json.dumps(results),ident))
 def allprev(self,payload):
  request=urllib.request.Request('http://127.0.0.1:48763/api/events',data=json.dumps({'source':'Inference Observatory research','pid':os.getpid(),'target':'all','topic':'research.native' if payload.get('provider')=='Native research' else 'research.google_ai_mode','data':payload}).encode(),headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(request,timeout=5) as r:return {'http_status':r.status,'response':json.load(r),'meaning':'Bus acceptance, not downstream algorithm completion'}
 def loop(self):
  last_catalog=time.time()
  while not self.stop.is_set():
   try:
    with self.auto.db() as c:rows=c.execute('SELECT id,text,sha256,data FROM inputs WHERE id>? ORDER BY id LIMIT 128',(self.router.cursor,)).fetchall()
    for row in rows:
     digest=row['sha256']
     with self.db() as c:cur=c.execute('INSERT OR IGNORE INTO learned VALUES(?)',(digest,))
     if cur.rowcount:
      payload=json.loads(row['data']);label=LABELS.index(payload['topic']) if payload.get('provider') in ['Google AI Mode','Native research'] and payload.get('topic') in LABELS else None
      self.router.observe(row['text'],label,identity=digest)
     self.router.cursor=row['id']
    for _ in range(4):self.router.train_batch()
    self.router.save();self.status='learning' if self.router.steps else 'awaiting labelled diversity'
    if time.time()-last_catalog>300:self.refresh_catalog();last_catalog=time.time()
   except Exception as e:self.status='error: '+str(e)
   self.stop.wait(10)
 def view(self):
  with self.db() as c:research=[dict(r) for r in c.execute('SELECT id,topic,query,url,created,input_id,delivery FROM research ORDER BY created DESC LIMIT 20')]
  for r in research:
   if r['delivery']!='pending':r['delivery']=json.loads(r['delivery'])
  return {'apps':self.catalog,'subjects':{t:sum(t in r['subjects'] for r in self.catalog) for t in LABELS},'neural':self.router.view(),'status':self.status,'research':research,'next_task':self.next_task(),'web_action_scope':'Public-topic research in Google AI Mode, retain outputs, feed local engines and compatible buses. No posting, purchases or account changes.'}
 def close(self):self.stop.set();self.router.save()
