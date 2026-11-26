"""Dense cube stream using the existing AmbientLogic spectrum and shared bus."""
import collections,hashlib,json,os,threading,time,math
from .ambient_logic import AmbientLogic
class OmniCube:
 def __init__(self,runtime,bus,start=True):
  self.runtime=runtime;self.bus=bus;self.lock=threading.RLock();self.halt=threading.Event();self.logic=AmbientLogic();self.logic.depth=.5;self.lines=collections.deque(maxlen=160);self.sequence=0;self.received=0;self.last_input=None;self.digest=hashlib.sha256(b'omni-cube').digest();self.enabled=True;self.rate=10;self.last_send=0;self.last_error=None;self.receipt=None;self.latest={};self.next_context=0;self.context={}
  if start:threading.Thread(target=self.loop,daemon=True,name='omni-cube-spectrum').start()
 def observe(self,event):
  if event.get('origin')=='omni-cube':return
  if event.get('origin')=='flow-backbone' and isinstance(event.get('payload'),dict) and event['payload'].get('source_origin')=='omni-cube':return
  raw=json.dumps(event,sort_keys=True,default=str,separators=(',',':')).encode()
  with self.lock:self.digest=hashlib.sha256(self.digest+raw).digest();self.received+=1;self.last_input={'sequence':event.get('sequence'),'origin':event.get('origin'),'time':event.get('time'),'sha256':hashlib.sha256(raw).hexdigest()}
 def configure(self,b):
  with self.lock:
   if 'depth' in b:self.logic.configure({'depth':b['depth']})
   if 'rate' in b:
    rate=float(b['rate'])
    if not math.isfinite(rate):raise ValueError('Rate must be finite')
    self.rate=max(1,min(20,rate))
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.enabled=b['enabled']
  return self.view()
 def step(self):
  if time.monotonic()>=self.next_context:
   with self.runtime.lock:self.context={'engine_receipts':{k:v.get('receipt') for k,v in self.runtime.latest.items()},'queue':self.runtime.queue.qsize(),'sections':list(self.runtime.utility),'learning_updates':self.runtime.get_model().updates,'field':self.runtime.field.snapshot()}
   self.next_context=time.monotonic()+2
  with self.lock:
   self.sequence+=1;random=os.urandom(64);context=json.dumps(self.context,sort_keys=True,default=str).encode();self.digest=hashlib.sha256(self.digest+context+random).digest()
   # Pure random input plus a separately mixed context projection.
   mixed=bytes(v^self.digest[i%32] for i,v in enumerate(random))
   stream=random if self.logic.depth==0 else mixed;text=''.join(chr(33+b%94) for b in stream)
   result=self.logic.process([{'text':''.join(chr(33+b%94) for b in stream),'stochastic':True,'predefined_text':False,'contains_model_text':False}])
   bit=(result or self.latest.get('analysis') or {}).get('output') or {'bit':0}
   line={'sequence':self.sequence,'time':time.time(),'text':text,'selected_bit':bit['bit'],'phase':(result or {}).get('output',{}).get('phase'),'provenance':'generated software stream'}
   self.lines.append(line);self.latest={'bits':''.join(f'{b:08b}' for b in stream),'analysis':result,'state_sha256':self.digest.hex(),'input_context':list(self.context),'mapping':'Printable byte projection; characters are generated output, not decoded external messages'}
   send=time.monotonic()-self.last_send>=2
   if send:self.last_send=time.monotonic()
  if send:
   event=self.bus.publish({'target':'all','kind':'stage-output','origin':'omni-cube','payload':{'text':text,'stochastic':True,'predefined_text':False,'contains_model_text':False,'omni_cube':{'sequence':self.sequence,'selected_bit':bit['bit'],'depth':self.logic.depth,'state_sha256':self.digest.hex()},'bits':self.latest['bits'],'labels':['unknown']*len(self.latest['bits']),'filter_context':'Unclassified generated bits hold for review in the backbone'}})
   self.receipt=event['event']['sequence']
  return line
 def loop(self):
  while not self.halt.is_set():
   if self.enabled:
    try:self.step()
    except Exception as e:self.last_error=type(e).__name__+': '+str(e)[:180]
   self.halt.wait(1/self.rate)
 def view(self):
  with self.lock:return {'enabled':self.enabled,'rate':self.rate,'depth':self.logic.depth,'sequence':self.sequence,'received':self.received,'last_input':self.last_input,'bus_output':self.receipt,'latest':self.latest,'lines':list(self.lines)[-50:],'error':self.last_error,'scope':'Registered app context and bus inputs; output shared with registered subscribers, not external device access'}
 def close(self):self.halt.set()
