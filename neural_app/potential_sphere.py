"""Uniform random 3D volume point + single bit, paced by AmbientLogic."""
import collections,hashlib,json,math,os,random,threading,time
from .ambient_logic import AmbientLogic
class PotentialSphere:
 def __init__(self,bus,start=True):
  self.bus=bus;self.lock=threading.RLock();self.halt=threading.Event();self.logic=AmbientLogic();self.logic.configure({'depth':0});self.rng=random.SystemRandom();self.base=.05;self.jitter=.1;self.enabled=True;self.sequence=0;self.received=0;self.last_input=None;self.latest=None;self.history=collections.deque(maxlen=128);self.batch=[];self.last_publish=0;self.output_receipt=None;self.error=None;self.mode="adaptive";self.target_bps=1_000_000;self.cpu_budget=.02;self.bit_total=0;self.ones_total=0;self.started=time.monotonic();self.worker_cpu=0;self.batch_latest=None;self.bit_command=None;self.trainer=None
  from .cpu_capacity import CpuCapacity
  self.cpu=CpuCapacity()
  from .atomic_clouds import AtomicClouds
  self.atomic=AtomicClouds();self.atom_history={'hydrogen':collections.deque(maxlen=128),'silicon':collections.deque(maxlen=128)}
  if start:threading.Thread(target=self.loop,daemon=True,name='potential-sphere').start()
 def observe(self,event):
  if event.get('origin')=='potential-sphere':return
  p=event.get('payload')
  if event.get('origin')=='flow-backbone' and isinstance(p,dict) and p.get('source_origin')=='potential-sphere':return
  with self.lock:self.received+=1;self.last_input={'sequence':event.get('sequence'),'origin':event.get('origin'),'sha256':hashlib.sha256(json.dumps(p,sort_keys=True,default=str).encode()).hexdigest(),'time':event.get('time')}
 def configure(self,b):
  with self.lock:
   for key,low,high in [('base',.01,1),('jitter',0,.4)]:
    if key in b:
     value=float(b[key])
     if not math.isfinite(value):raise ValueError('Sphere controls must be finite')
     setattr(self,key,max(low,min(high,value)))
   if 'mode' in b:
    if b['mode'] not in ('single','adaptive','capacity'):raise ValueError('Choose single, adaptive or capacity mode')
    self.mode=b['mode']
   for key,lo,hi in [('target_bps',1000,8_000_000),('cpu_budget',.005,.1)]:
    if key in b:
     value=float(b[key])
     if not math.isfinite(value):raise ValueError('Capacity controls must be finite')
     setattr(self,key,max(lo,min(hi,value)))
   if 'enabled' in b:
    if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
    self.enabled=b['enabled']
  return self.view()
 def step(self):
  thread_start=time.thread_time();wall_start=time.monotonic();raw=os.urandom(32);text=''.join(chr(33+b%94) for b in raw);result=self.logic.process([{'text':text,'stochastic':True,'predefined_text':False,'contains_model_text':False}]);bit=result['output']['bit'];z=self.rng.uniform(-1,1);theta=self.rng.uniform(0,math.tau);radius=self.rng.random()**(1/3);ring=math.sqrt(max(0,1-z*z));point=[radius*ring*math.cos(theta),radius*ring*math.sin(theta),radius*z]
  batch=None
  if self.mode=='adaptive':
   count=max(1,min(65536,int(self.target_bps*self.base/8)));pool=os.urandom(count);ones=int.from_bytes(pool,'little').bit_count();batch={'bits':count*8,'ones':ones,'sha256':hashlib.sha256(pool).hexdigest(),'use':'All bits contribute to bit-count and digest; a seed window selects typed calculations; one representative point remains visible'}
   if self.bit_command:self.bit_command.execute(bytes.fromhex(batch['sha256'])[:16],batch)
  elif self.bit_command:self.bit_command.execute(raw[:16],None)
  atomic=self.atomic.sample(self.rng);cpu_sample=self.cpu.sample();cpu_used=time.thread_time()-thread_start;wall_used=time.monotonic()-wall_start
  with self.lock:
   self.worker_cpu+=cpu_used
   if batch:self.bit_total+=batch['bits'];self.ones_total+=batch['ones'];self.batch_latest=batch
   self.sequence+=1;interval=self.base*(1+self.jitter*(1 if bit else -1));stochastic_interval=interval;interval=max(interval,cpu_used/max(.005,self.cpu_budget)-wall_used);self.latest={'sequence':self.sequence,'time':time.time(),'point':point,'bit':bit,'next_interval_seconds':interval,'spectrum_phase':result['output']['phase'],'atomic_states':atomic,'stochastic_interval_seconds':stochastic_interval,'input_receipt':(self.last_input or {}).get('sequence')};self.history.append({k:v for k,v in self.latest.items() if k!='atomic_states'});self.batch.append({**{k:v for k,v in self.latest.items() if k!='atomic_states'},'atomic_positions_nm':{name:atomic[name]['position_nm'] for name in ('hydrogen','silicon')},'silicon_orbital':atomic['silicon']['orbital']})
   for name in self.atom_history:self.atom_history[name].append(atomic[name]['position_nm'])
   publish=time.monotonic()-self.last_publish>=.2
   if publish:batch=self.batch;self.batch=[];self.last_publish=time.monotonic()
  if publish:
   bits=''.join(str(v['bit']) for v in batch);receipt=self.bus.publish({'target':'all','kind':'bit-input','origin':'potential-sphere','payload':{'samples':batch,'bits':bits,'labels':['unknown']*len(bits),'provenance':'software-stochastic-sphere','stochastic':True,'predefined_text':False,'contains_model_text':False,'text':bits,'sampling':'Uniform sphere volume: r=U^(1/3), cos(theta)=uniform[-1,1], azimuth=uniform[0,2pi]','interval_source':'AmbientLogic stochastic output bit; symmetric mild jitter','atomic_model_latest':atomic,'batch_summary':self.batch_latest,'actual_batch_bits_generated':self.bit_total,'raw_values_preserved':True}});self.output_receipt=receipt['event']['sequence']
  return self.latest
 def loop(self):
  while not self.halt.is_set():
   interval=self.base
   if self.enabled:
    try:interval=self.step()['next_interval_seconds']
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:180]
   self.halt.wait(interval)
 def view(self):
  with self.lock:return {'trainers':self.trainer.summary() if self.trainer else None,'atomic_clouds':{k:list(v) for k,v in self.atom_history.items()},'mode':self.mode,'target_bps':self.target_bps,'cpu_budget':self.cpu_budget,'actual_batch_bits_generated':self.bit_total,'actual_average_batch_bps':self.bit_total/max(.001,time.monotonic()-self.started),'worker_cpu_core_fraction':self.worker_cpu/max(.001,time.monotonic()-self.started),'batch_latest':self.batch_latest,'cpu_capacity':self.cpu.snapshot,'bit_command':self.bit_command.view() if self.bit_command else None,'enabled':self.enabled,'sequence':self.sequence,'received':self.received,'base':self.base,'jitter':self.jitter,'latest':self.latest,'history':list(self.history)[-32:],'output_receipt':self.output_receipt,'last_input':self.last_input,'error':self.error,'scope':'Software probability model; one selected point and bit at a time; all samples batched into registered app bus'}
 def close(self):self.halt.set()
