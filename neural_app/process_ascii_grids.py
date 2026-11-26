from .symbol_bus import BUS as SYMBOL_BUS
"""Process ASCII capture, dense grid and slower any-vector projection."""
import collections,hashlib,json,math,random,threading,time
class ProcessAsciiGrid:
 def __init__(self,bus,start=True):
  self.bus=bus;self.lock=threading.RLock();self.halt=threading.Event();self.sources={};self.counts={};self.digest=bytes(32);self.received=0;self.captured=0;self.sequence=0;self.cursor=0;self.columns=192;self.rows=96;self.rate=20;self.logic_share=.15;self.enabled=True;self.codes=[];self.receipt=None;self.last_output=0;self.error=None
  if start:threading.Thread(target=self.loop,daemon=True,name='process-ascii-flux-grid').start()
 def observe(self,event):
  if event.get('origin')=='process-ascii-grid':return
  p=event.get('payload');p=p if isinstance(p,dict) else {};origin=str(event.get('origin','unknown'))[:100]
  if origin=='flow-backbone' and p.get('source_origin')=='process-ascii-grid':return
  raw=json.dumps(event,sort_keys=True,default=str).encode();generated=(p.get('stochastic') is True and p.get('predefined_text') is False and p.get('contains_model_text') is False) or p.get('provenance') in ('derived-cube-byte-projection','derived-process-ascii-grid','derived-vector-ascii-grid')
  codes=[]
  if generated:
   if isinstance(p.get('ascii_codes'),list):codes=[v for v in p['ascii_codes'][:4096] if type(v) is int and 0<=v<128]
   elif isinstance(p.get('text'),str):codes=[ord(c) for c in p['text'][:4096] if ord(c)<128]
  for source in p.get('sources',[])[:32] if isinstance(p.get('sources'),list) else []:
   if isinstance(source,dict) and source.get('stochastic') is True and source.get('predefined_text') is False and source.get('contains_model_text') is False:codes.extend(ord(c) for c in str(source.get('text',''))[:512] if ord(c)<128)
  with self.lock:
   self.received+=1;self.digest=hashlib.sha256(self.digest+raw).digest()
   if codes:
    existing=self.sources.setdefault(origin,collections.deque(maxlen=2048));existing.extend(codes);self.counts[origin]=self.counts.get(origin,0)+len(codes);self.captured+=len(codes)
    while len(self.sources)>64:old=next(iter(self.sources));self.sources.pop(old);self.counts.pop(old,None)
 def configure(self,b):
  with self.lock:
   for key,lo,hi in [('columns',64,256),('rows',32,192),('rate',2,40),('logic_share',0,1)]:
    if key in b:
     v=float(b[key])
     if not math.isfinite(v):raise ValueError('Grid controls must be finite')
     setattr(self,key,max(lo,min(hi,v)) if key=='logic_share' else int(max(lo,min(hi,v))))
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.enabled=b['enabled']
  return self.view()
 def step(self):
  with self.lock:
   pool=[code for values in self.sources.values() for code in values];context=list(self.digest.hex().encode('ascii'));n=self.columns*self.rows;share=self.logic_share;start=self.cursor
   self.codes=[];cursor=start;mask=round(share*100)
   for i in range(n):
    if i%100<mask or not pool:self.codes.append(context[(i+self.sequence)%len(context)])
    else:self.codes.append(pool[cursor%len(pool)]);cursor+=1
   self.cursor=cursor%max(1,len(pool));self.sequence+=1
   SYMBOL_BUS.register('process-ascii-grid',n)
   for position in range(max(0,len(self.codes)-16),len(self.codes)):SYMBOL_BUS.select('process-ascii-grid',position,self.codes[position],mode='hold')
   output=self.codes[-128:];publish=time.monotonic()-self.last_output>=.5
   if publish:self.last_output=time.monotonic()
  if publish and output:
   bits=''.join(f'{c:08b}' for c in output);r=self.bus.publish({'target':'all','kind':'stage-output','origin':'process-ascii-grid','payload':{'ascii_codes':output,'text':''.join(map(chr,output)),'bits':bits,'labels':['unknown']*len(bits),'stochastic':False,'provenance':'derived-process-ascii-grid','sequence':self.sequence,'logic_share':share,'source_count':len(self.sources),'scope':'Captured generated ASCII plus hexadecimal projection of app-event digest; original raw bus flow preserved'}});self.receipt=r['event']['sequence']
 def snapshot_codes(self):
  with self.lock:return list(self.codes)
 def loop(self):
  while not self.halt.is_set():
   if self.enabled:
    try:self.step()
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:180]
   self.halt.wait(1/self.rate)
 def view(self):
  with self.lock:return {'sequence':self.sequence,'received':self.received,'captured':self.captured,'columns':self.columns,'rows':self.rows,'rate':self.rate,'logic_share':self.logic_share,'enabled':self.enabled,'codes':list(self.codes),'sources':[{'source':k,'retained':len(v),'captured':self.counts[k]} for k,v in self.sources.items()],'context_sha256':self.digest.hex(),'receipt':self.receipt,'error':self.error,'scope':'App-activity digest rail + exact retained generated ASCII rail; bounded rolling source buffers, not a copy of all program memory'}
 def close(self):self.halt.set()

class VectorAsciiGrid:
 def __init__(self,bus,fast,start=True):
  self.bus=bus;self.fast=fast;self.lock=threading.RLock();self.halt=threading.Event();self.rng=random.SystemRandom();self.enabled=True;self.count=9;self.speed=.018;self.interval=1;self.jitter=.4;self.sequence=0;self.received=0;self.receipt=None;self.streams=[];self.digest=bytes(32);self.outbound=[];self.last_publish=0;self.last_spawn=0;self.error=None
  if start:threading.Thread(target=self.loop,daemon=True,name='vector-ascii-potential-grid').start()
 def observe(self,event):
  if event.get('origin')=='vector-ascii-grid':return
  p=event.get('payload')
  if event.get('origin')=='flow-backbone' and isinstance(p,dict) and p.get('source_origin')=='vector-ascii-grid':return
  with self.lock:self.received+=1;self.digest=hashlib.sha256(self.digest+json.dumps(event,sort_keys=True,default=str).encode()).digest()
 def configure(self,b):
  with self.lock:
   for key,lo,hi in [('count',1,24),('speed',.001,.08),('interval',.2,8),('jitter',0,.8)]:
    if key in b:
     v=float(b[key])
     if not math.isfinite(v):raise ValueError('Vector controls must be finite')
     setattr(self,key,int(max(lo,min(hi,v))) if key=='count' else max(lo,min(hi,v)))
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.enabled=b['enabled']
  return self.view()
 def spawn(self,index):
  a=self.rng.uniform(0,math.tau);return {'id':index,'x':self.rng.uniform(-1,1),'y':self.rng.uniform(-1,1),'vx':math.cos(a)*self.speed,'vy':math.sin(a)*self.speed,'next_at':0,'trail':[],'age':0,'lifetime':self.rng.uniform(12,50)}
 def step(self,dt=.1):
  pool=self.fast.snapshot_codes();now=time.monotonic()
  with self.lock:
   while len(self.streams)<self.count:self.streams.append(self.spawn(len(self.streams)))
   self.streams=self.streams[:self.count];self.sequence+=1
   for i,s in enumerate(self.streams):
    s['age']+=dt
    if abs(s['x'])>1.05 or abs(s['y'])>1.05 or s['age']>s['lifetime']:s=self.spawn(i);self.streams[i]=s
    length=math.hypot(s['vx'],s['vy']) or 1;s['vx']=s['vx']/length*self.speed;s['vy']=s['vy']/length*self.speed;s['x']+=s['vx']*dt;s['y']+=s['vy']*dt
    if pool and now>=s['next_at']:
     index=(self.sequence*17+i*131+self.digest[i%32])%len(pool);code=pool[index];s['trail'].append({'x':s['x'],'y':s['y'],'code':code});s['trail']=s['trail'][-64:];self.outbound.append(code);s['next_at']=now+self.interval*self.rng.uniform(1-self.jitter,1+self.jitter)
   publish=now-self.last_publish>=2
   if publish:batch=self.outbound;self.outbound=[];self.last_publish=now
  if publish and batch:
   codes=batch[-128:];bits=''.join(f'{c:08b}' for c in codes);r=self.bus.publish({'target':'all','kind':'stage-output','origin':'vector-ascii-grid','payload':{'text':''.join(map(chr,codes)),'ascii_codes':codes,'bits':bits,'labels':['unknown']*len(bits),'stochastic':False,'provenance':'derived-vector-ascii-grid','sequence':self.sequence,'scope':'Slower any-origin, any-angle sampling from the fast grid; paced upstream/downstream bus feedback'}});self.receipt=r['event']['sequence']
 def loop(self):
  while not self.halt.is_set():
   if self.enabled:
    try:self.step(.1)
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:180]
   self.halt.wait(.1)
 def view(self):
  with self.lock:return json.loads(json.dumps({'sequence':self.sequence,'received':self.received,'count':self.count,'speed':self.speed,'interval':self.interval,'jitter':self.jitter,'enabled':self.enabled,'streams':self.streams,'receipt':self.receipt,'error':self.error,'context_sha256':self.digest.hex()}))
 def close(self):self.halt.set()
