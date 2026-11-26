"""Two same-clock background lanes reusing existing stage implementations."""
import collections,hashlib,json,os,threading,time
from .ambient_logic import AmbientLogic
from .logic_cube import transform
from .omni_cube import OmniCube
from .tesseract_flow import TesseractFlow
from .potential_sphere import PotentialSphere
from .bit_command import BitCommand
class LocalBus:
 def __init__(self):self.sequence=0
 def publish(self,event):self.sequence+=1;return {'event':{'sequence':self.sequence}}
class ParallelNativeLanes:
 def __init__(self,runtime,bus,reasoner,field,start=True):
  self.runtime=runtime;self.bus=bus;self.reasoner=reasoner;self.field=field;self.halt=threading.Event();self.lock=threading.RLock();self.sequence=0;self.rate=2.;self.enabled=True;self.latest=[];self.error=None;self.lanes=[]
  for name in ('A','B'):
   local=LocalBus();omni=OmniCube(runtime,local,start=False);tesseract=TesseractFlow(runtime,local,omni,start=False);sphere=PotentialSphere(local,start=False);sphere.mode='single';native=BitCommand(local);sphere.bit_command=native
   native.context_provider=lambda:{'goal':self.reasoner.s.get('current_goal',{}).get('input_summary','')}
   self.lanes.append({'name':name,'omni':omni,'tesseract':tesseract,'sphere':sphere,'native':native,'local':local})
  if start:threading.Thread(target=self.loop,daemon=True,name='parallel-native-lanes').start()
 def step(self):
  with self.field.lock:available=[dict(s) for s in self.field.sources.values() if not s['id'].startswith('parallel-native-lanes/')]
  with self.lock:self.sequence+=1;cycle=self.sequence;stamp=time.time();outputs=[];summaries=[]
  for i,lane in enumerate(self.lanes):
   partition=available[i::2];chosen=partition[(cycle-1)%len(partition)] if partition else None
   raw=chosen['text'].encode()[:256] if chosen else os.urandom(64);origin=chosen['id'] if chosen else 'independent OS random source';bits=''.join(f'{v:08b}' for v in raw)
   filtered=transform(bits,['unknown']*len(bits));flux=filtered['output_bits'];text=''.join(chr(33+v%94) for v in raw)
   incoming={'target':'all','origin':'lane-'+lane['name']+'-input','payload':{'text':text,'stochastic':True,'predefined_text':False,'contains_model_text':False}}
   lane['omni'].observe(incoming);omni=lane['omni'].step();lane['native'].observe(incoming);t=lane['tesseract'];t.sequence=cycle
   channels=[t.calculate(c,b,c['source']) for c,b in zip(t.channels,[flux,bits,lane['omni'].latest['bits']])];combined=t.calculate(t.combined,''.join(v['bits'] for v in channels),'lane-combined')
   lane['sphere'].observe(incoming);potential=lane['sphere'].step();native=lane['native'].view()
   stages=[('flux-cube',flux[:256]),('omni-cube',omni['text']),*[(f'tesseract-{j+1}',v['text']) for j,v in enumerate(channels)],('tesseract-combined',combined['text']),('potential-sphere',str(potential['bit'])),('native-intelligence',json.dumps((native.get('recent') or [{}])[-1],sort_keys=True)[:512])]
   for stage,value in stages:
    is_native=stage=='native-intelligence'
    outputs.append({'name':'parallel-'+lane['name']+'/'+stage,'text':value,'stochastic':not is_native,'predefined_text':False,'contains_model_text':False,'provenance':'observed-native-calculation' if is_native else 'derived-parallel-stage','point':potential['point'],'lane':lane['name'],'clock_cycle':cycle,'rate_hz':self.rate})
   summaries.append({'lane':lane['name'],'cycle':cycle,'time':stamp,'source':origin,'input_sha256':hashlib.sha256(raw).hexdigest(),'stages':[s for s,_ in stages],'native_operations':lane['native'].sequence,'scope':'existing OmniCube, TesseractFlow, PotentialSphere and BitCommand instances; exact flux hold/flip transform; no duplicate UI or model service'})
  payload={'sources':outputs,'lanes':summaries,'clock_cycle':cycle,'rate_hz':self.rate,'bridge_direction':'all','provenance':'parallel-software-processing','stochastic':False,'scope':'Different source partitions; independent random fallback when empty; no literal infinite computation'}
  self.bus.publish({'target':'all','origin':'parallel-native-lanes','kind':'stage-output','payload':payload})
  with self.lock:self.latest=summaries
  return payload
 def view(self):
  with self.lock:return {'enabled':self.enabled,'rate_hz':self.rate,'cycle':self.sequence,'lanes':self.latest,'error':self.error,'destination':'Expression field → centre/plane selection → backbone'}
 def loop(self):
  while not self.halt.is_set():
   if self.enabled:
    try:self.step()
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:240]
   self.halt.wait(1/self.rate)
 def close(self):self.halt.set()
