"""Local, bounded symbolic learning with prequential evaluation and reviewable extensions."""
import contextlib,queue,collections,hashlib,json,math,random,sqlite3,threading,time,uuid
from pathlib import Path
class LearningCore:
 def __init__(self,data):
  self.path=Path(data)/'language-learning.sqlite3';self.lock=threading.RLock();self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.connect() as db:
   db.execute('create table if not exists events(id integer primary key, time real, source text, kind text, provenance text, digest text, chars integer, details text)')
   db.execute('create table if not exists state(id integer primary key, value text)')
   db.execute('create table if not exists proposals(id text primary key, value text)')
   row=db.execute('select value from state where id=1').fetchone()
  self.s=json.loads(row[0]) if row else {'symbols':{},'contexts':{},'tokens':{},'seen':0,'scored':0,'hits':0,'baseline_hits':0,'shuffled_hits':0,'order':1,'sources':{},'last_text':'','snapshots':[]}
  self.activation={'phase':'memory-restored' if row else 'initialized','time':time.time(),'saved_memory_verified':bool(row),'external_access_granted':False};self.s.setdefault('engine_models',{});self.s.setdefault('engine_metrics',{})
  self.halt=threading.Event();self.queue=queue.Queue(maxsize=128);self.dropped=0;self.worker_error=None
  self.worker=threading.Thread(target=self.work,daemon=True,name='symbolic-learning-events');self.worker.start()
 def work(self):
  last_predict=0;last_seen=0
  while not self.halt.is_set():
   try:event=self.queue.get(timeout=.5)
   except queue.Empty:event=None
   if event:
    try:
     if '_engine' in event:self.engine_update(**event['_engine'])
     else:self.ingest(event['_capture'] if '_capture' in event else {'source':'bus:'+event.get('origin','local'),'kind':event.get('kind','event'),'provenance':'observed','label':event.get('target','all'),'outcome':'bus accepted event '+str(event.get('sequence'))})
    except Exception as e:self.worker_error=str(e)
    finally:self.queue.task_done()
   if time.monotonic()-last_predict>5 and self.s['seen']!=last_seen:
    last_predict=time.monotonic();last_seen=self.s['seen']
    try:
     self.last_prediction=self.predict({'prefix':self.s['last_text'][-2:],'length':32})
     callback=getattr(self,'on_prediction',None)
     if callback:callback(self.last_prediction)
    except Exception as e:self.worker_error=str(e)
 def observe_runtime(self,section,receipt,digest,elapsed,result):
  features={};visited=0
  def walk(value,path='',depth=0):
   nonlocal visited
   visited+=1
   if visited>256 or depth>6:return
   if isinstance(value,(int,float)) and not isinstance(value,bool):
    if math.isfinite(value) and abs(value)<=1e15:features[path[:180]]=float(value)
   elif isinstance(value,dict):
    for key,child in list(value.items())[:32]:
     if not any(word in str(key).lower() for word in ('secret','token','password','email','account','credential','authorization')):walk(child,path+'/'+str(key)[:60],depth+1)
   elif isinstance(value,(tuple,list)):
    for i,child in enumerate(value[:16]):walk(child,path+'/'+str(i),depth+1)
  walk(result)
  try:self.queue.put_nowait({'_engine':{'section':str(section)[:100],'receipt':receipt,'digest':digest,'elapsed':elapsed,'features':features}})
  except queue.Full:self.dropped+=1
 def engine_update(self,section,receipt,digest,elapsed,features):
  with self.lock,self.connect() as db:
   if section not in self.s['engine_models'] and len(self.s['engine_models'])>=256:return
   model=self.s['engine_models'].setdefault(section,{})
   for path,value in list(features.items())[:64]:
    if path not in model and len(model)>=64:continue
    item=model.setdefault(path,{'count':0,'mean':0.,'ewma':value,'absolute_error_sum':0.,'predictions':0})
    if item['count']:item['absolute_error_sum']+=abs(value-item['ewma']);item['predictions']+=1
    item['count']+=1;item['mean']+=(value-item['mean'])/item['count'];item['ewma']=item['ewma']*.8+value*.2;item['latest']=value
   self.s['engine_metrics'][section]={'receipt':receipt,'sha256':digest,'latency_ms':elapsed,'features':len(features),'time':time.time()};self.save(db)
  self.ingest({'source':'engine:'+section,'kind':'engine-result','provenance':'observed','label':str(receipt),'outcome':json.dumps({'sha256':digest,'latency_ms':elapsed,'numeric_features':len(features)})})
 @contextlib.contextmanager
 def connect(self):
  db=sqlite3.connect(self.path,timeout=10)
  try:
   with db:yield db
  finally:db.close()
 def save(self,db):db.execute('insert or replace into state values(1,?)',(json.dumps(self.s),))
 @staticmethod
 def guess(counts):return min(counts,key=lambda c:(-counts[c],c)) if counts else None
 def ingest(self,body):
  self.activation['phase']='learning-active'
  source=str(body.get('source','local'))[:120];kind=str(body.get('kind','observation'))[:60];provenance=str(body.get('provenance','observed'))
  if provenance not in ('stochastic','influenced-stochastic','user-labelled','model-explanation','observed'):raise ValueError('Unknown provenance')
  text=str(body.get('text',''))[:4096];train=provenance in ('stochastic','influenced-stochastic');digest=hashlib.sha256(text.encode()).hexdigest();details={'label':str(body.get('label',''))[:160],'outcome':str(body.get('outcome',''))[:400],'trained':train,'scope':'local software observations'}
  with self.lock,self.connect() as db:
   duplicate=db.execute('select 1 from events where source=? and digest=? and provenance=? limit 1',(source,digest,provenance)).fetchone()
   if duplicate and train:return {'duplicate':True,'trained':False}
   if train and text:
    if source not in self.s['sources'] and len(self.s['sources'])>=128:source='other-generated-streams'
    symbols=self.s['symbols'];contexts=self.s['contexts'];shuffled=list(text);random.Random(int(digest[:16],16)).shuffle(shuffled)
    for i,c in enumerate(text):
     context=text[max(0,i-self.s['order']):i];counts=contexts.get(context,{}) if context else {};prediction=self.guess(counts) or self.guess(symbols);baseline=self.guess(symbols);shuffle_context=''.join(shuffled[max(0,i-self.s['order']):i]);shuffle_prediction=self.guess(contexts.get(shuffle_context,{})) or baseline
     if prediction is not None:self.s['scored']+=1;self.s['hits']+=int(prediction==c);self.s['baseline_hits']+=int(baseline==c);self.s['shuffled_hits']+=int(shuffle_prediction==shuffled[i])
     symbols[c]=symbols.get(c,0)+1
     for order in (1,2):
      if i>=order:
       key=text[i-order:i]
       if key in contexts or len(contexts)<20000:
        nexts=contexts.setdefault(key,{})
        if c in nexts or len(nexts)<256:nexts[c]=nexts.get(c,0)+1
     for n in (2,3,4):
      token=text[i:i+n]
      if len(token)==n and (token in self.s['tokens'] or len(self.s['tokens'])<20000):self.s['tokens'][token]=self.s['tokens'].get(token,0)+1
    self.s['seen']+=len(text);self.s['sources'][source]=self.s['sources'].get(source,0)+len(text);self.s['last_text']=text;self.s['snapshots'].append({'time':time.time(),'seen':self.s['seen'],'scored':self.s['scored'],'hits':self.s['hits'],'baseline':self.s['baseline_hits']});self.s['snapshots']=self.s['snapshots'][-120:]
   db.execute('insert into events(time,source,kind,provenance,digest,chars,details) values(?,?,?,?,?,?,?)',(time.time(),source,kind,provenance,digest,len(text),json.dumps(details)));db.execute('delete from events where id not in (select id from events order by id desc limit 5000)');self.save(db)
  return {'trained':train,'characters':len(text),'digest':digest,'details':details}
 def observe_bus(self,event):
  payload=event.get('payload')
  if isinstance(payload,dict) and payload.get('stochastic') is True and payload.get('predefined_text') is False and payload.get('contains_model_text') is False and isinstance(payload.get('text'),str):
   try:self.queue.put_nowait({'_capture':{'source':'generated-bus:'+str(event.get('origin','local'))[:100],'kind':'generated-capture','provenance':'influenced-stochastic','text':payload['text'][:4096]}})
   except queue.Full:self.dropped+=1
   return
  try:self.queue.put_nowait(dict(event))
  except queue.Full:self.dropped+=1
 def view(self,query=''):
  with self.lock,self.connect() as db:
   events=[{'id':r[0],'time':r[1],'source':r[2],'kind':r[3],'provenance':r[4],'sha256':r[5],'characters':r[6],**json.loads(r[7])} for r in db.execute('select * from events order by id desc limit 100')]
   proposals=[json.loads(r[0]) for r in db.execute('select value from proposals')];n=max(1,self.s['scored']);total=max(1,sum(self.s['symbols'].values()));tokens=sorted(self.s['tokens'].items(),key=lambda r:(-r[1],r[0]));q=str(query)[:120]
   return {'activation':self.activation,'engine_models':self.s['engine_models'],'engine_metrics':self.s['engine_metrics'],'last_prediction':getattr(self,'last_prediction',None),'pending_events':self.queue.qsize(),'dropped_events':self.dropped,'worker_error':self.worker_error,'characters_seen':self.s['seen'],'scored_predictions':self.s['scored'],'accuracy':self.s['hits']/n,'frequency_baseline':self.s['baseline_hits']/n,'shuffled_control':self.s['shuffled_hits']/n,'entropy':-sum(v/total*math.log2(v/total) for v in self.s['symbols'].values()),'order':self.s['order'],'tokens':[{'text':k,'count':v} for k,v in tokens if v>=2 and (not q or q in k)][:100],'contexts':len(self.s['contexts']),'sources':self.s['sources'],'events':events,'proposals':proposals,'history':self.s['snapshots'],'limits':{'events':5000,'contexts':20000,'tokens':20000,'capture_characters':4096},'evaluation':'Next-character predictions scored before updating counts; shuffled control uses a deterministic permutation, not an independent experiment. Grounding is supplied labels/outcomes, not inferred meaning.'}
 def predict(self,body):
  prefix=str(body.get('prefix',''))[-256:];length=max(1,min(256,int(body.get('length',64))));output='';trace=[]
  with self.lock:
   for _ in range(length):
    context=(prefix+output)[-self.s['order']:];counts=self.s['contexts'].get(context,{}) or self.s['symbols'];c=self.guess(counts)
    if c is None:break
    output+=c;trace.append({'context':context,'next':c,'support':counts[c],'total':sum(counts.values())})
  return {'continuation':output,'trace':trace,'action':'local character prediction only','model_generated':True}
 def propose(self,body):
  # Candidate expansion is a finite predictor configuration, never arbitrary executable code.
  text=self.s['last_text'];split=int(len(text)*.7);train,test=text[:split],text[split:];scores={}
  for order in (1,2):
   contexts={};symbols=collections.Counter(train)
   for i in range(order,len(train)):contexts.setdefault(train[i-order:i],collections.Counter())[train[i]]+=1
   hits=0
   for i,c in enumerate(test):
    previous=(train+test[:i])[-order:];prediction=self.guess(contexts.get(previous,{})) or self.guess(symbols);hits+=int(prediction==c)
   scores[str(order)]=hits/max(1,len(test))
  item={'id':uuid.uuid4().hex,'name':'Second-order symbolic predictor','operation':'predictor_order','value':2,'status':'awaiting_review','heldout_characters':len(test),'scores':scores,'eligible':len(test)>=128 and scores['2']>scores['1'],'scope':'finite local prediction configuration; no new filesystem, network or process permissions','note':'Single retained capture evaluation; improvement here is not general intelligence.'}
  with self.lock,self.connect() as db:db.execute('insert into proposals values(?,?)',(item['id'],json.dumps(item)));db.execute('delete from proposals where id not in (select id from proposals order by rowid desc limit 32)')
  return item
 def approve(self,body):
  with self.lock,self.connect() as db:
   row=db.execute('select value from proposals where id=?',(str(body.get('id','')),)).fetchone()
   if not row:raise ValueError('Unknown proposal')
   item=json.loads(row[0])
   if not item['eligible']:raise ValueError('Candidate has not demonstrated improvement on its retained test capture.')
   self.s['order']=2;item['status']='enabled_after_user_review';db.execute('update proposals set value=? where id=?',(json.dumps(item),item['id']));self.save(db)
  return item
 def restore(self):
  with self.lock,self.connect() as db:self.s['order']=1;self.save(db)
  return {'order':1,'restored':True}

 def close(self):
  self.halt.set();self.worker.join(2)

 def activate(self,body):
  with self.lock:self.activation={'phase':'ready-for-input','time':time.time(),'saved_memory_verified':self.path.is_file(),'external_access_granted':False,'reason':str(body.get('reason','manual activation'))[:120]}
  return self.activation
