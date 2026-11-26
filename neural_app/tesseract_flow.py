"""Three cube-derived 4D projections and a shared filtered I/O channel."""
import collections,hashlib,json,threading,time
from .ambient_logic import AmbientLogic
class TesseractFlow:
 def __init__(self,runtime,bus,omni,start=True):
  self.runtime=runtime;self.bus=bus;self.omni=omni;self.lock=threading.RLock();self.halt=threading.Event();self.sequence=0;self.received=0;self.last_error=None;self.channels=[{'id':str(i+1),'source':name,'input_digest':bytes(32),'lines':collections.deque(maxlen=40),'logic':AmbientLogic(),'latest':{}} for i,name in enumerate(['App-state cube','Stochastic cube','Omni spectrum cube'])];self.combined={'input_digest':bytes(32),'lines':collections.deque(maxlen=40),'logic':AmbientLogic(),'latest':{}};self.source_at=0;self.source_bits=['','',''];self.last_input=None
  if start:threading.Thread(target=self.loop,daemon=True,name='tesseract-flow').start()
 def observe(self,event):
  if event.get('origin')=='tesseract-flow':return
  p=event.get('payload');p=p if isinstance(p,dict) else {'value':p}
  if event.get('origin')=='flow-backbone' and p.get('source_origin')=='tesseract-flow':return
  target=event.get('target','all')
  if target not in ('all','tesseract','tesseract-1','tesseract-2','tesseract-3','tesseract-combined'):return
  raw=json.dumps(event,sort_keys=True,default=str).encode();requested=p.get('tesseract_channel','all')
  with self.lock:
   self.received+=1;self.last_input={'sequence':event.get('sequence'),'origin':event.get('origin'),'time':event.get('time')}
   for c in self.channels:
    if requested in ('all','combined',c['id']) and target in ('all','tesseract','tesseract-'+c['id'],'tesseract-combined'):c['input_digest']=hashlib.sha256(c['input_digest']+raw).digest()
   self.combined['input_digest']=hashlib.sha256(self.combined['input_digest']+raw).digest()
 def calculate(self,channel,bits,source):
  raw=bits.encode()+channel['input_digest'];digest=hashlib.sha256(raw).digest();text=''.join(chr(33+b%94) for b in digest);channel['logic'].configure({'depth':self.omni.logic.depth});analysis=channel['logic'].process([{'text':text,'stochastic':True,'predefined_text':False,'contains_model_text':False}]);output=''.join(f'{v:08b}' for v in digest)
  latest={'cycle':self.sequence,'time':time.time(),'source':source,'source_bits':len(bits),'source_sha256':hashlib.sha256(bits.encode()).hexdigest(),'bits':output,'text':text,'analysis':analysis,'source_available':bool(bits),'provenance':'derived-cube-byte-projection'};channel['latest']=latest;channel['lines'].append({'cycle':self.sequence,'text':text});return latest
 def step(self):
  if time.monotonic()>=self.source_at:
   cube=self.runtime.logic_cube();v=cube.view();self.source_bits=[v.get('state_bits',''),(v.get('stochastic') or {}).get('output_bits',''),self.omni.view().get('latest',{}).get('bits','')];self.source_at=time.monotonic()+2
  with self.lock:
   self.sequence+=1;outputs=[self.calculate(c,bits,c['source']) for c,bits in zip(self.channels,self.source_bits)];combined=self.calculate(self.combined,''.join(r['bits'] for r in outputs),'Combined three tesseract outputs + shared input');combined['source_available']=all(r['source_available'] for r in outputs);combined['missing_sources']=[r['source'] for r in outputs if not r['source_available']];rows=[(c['id'],c['latest']) for c in self.channels]+[('combined',combined)]
  for ident,row in rows:
   receipt=self.bus.publish({'target':'all','kind':'stage-output','origin':'tesseract-flow','payload':{'tesseract_channel':ident,'cycle':self.sequence,'source_sha256':row['source_sha256'],'source_available':row['source_available'],'bits':row['bits'],'labels':['unknown']*len(row['bits']),'text':row['text'],'provenance':'derived-cube-byte-projection','stochastic':False,'filter':'Unclassified working bits hold for review; backbone applies declared per-bit rule'}})
   with self.lock:
    channel=self.combined if ident=='combined' else self.channels[int(ident)-1];channel['latest']['bus_receipt']=receipt['event']['sequence']
 def loop(self):
  while not self.halt.is_set():
   try:self.step()
   except Exception as e:self.last_error=type(e).__name__+': '+str(e)[:180]
   self.halt.wait(.5)
 def view(self):
  with self.lock:return {'sequence':self.sequence,'received':self.received,'last_input':self.last_input,'error':self.last_error,'channels':[{'id':c['id'],'source':c['source'],'latest':dict(c['latest']),'lines':list(c['lines'])} for c in self.channels],'combined':{'latest':dict(self.combined['latest']),'lines':list(self.combined['lines'])},'scope':'4D mathematical projections of actual available cube byte streams; generated strings, not external messages'}
 def close(self):self.halt.set()
