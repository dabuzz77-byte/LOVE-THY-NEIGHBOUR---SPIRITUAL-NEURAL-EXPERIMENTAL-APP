"""Parallel, resource-aware processing rail over every registered thinking stage."""
import collections,copy,importlib.util,math,threading,time,sys,os
from pathlib import Path
os.environ.setdefault("CUPY_CACHE_DIR",str(Path(__file__).resolve().parents[1]/"data"/"gpu-cache"))
GPU_VENDOR=Path(__file__).resolve().parents[1]/"vendor-gpu"
_dll_handles=[]
if (GPU_VENDOR/'nvidia/cuda_runtime/include/cuda_runtime.h').is_file():
 os.environ.setdefault('CUDA_PATH',str(GPU_VENDOR/'nvidia/cuda_runtime'))
 os.environ['PATH']=os.pathsep.join(str(p) for p in (GPU_VENDOR/'nvidia').glob('*/bin'))+os.pathsep+os.environ.get('PATH','')
 if hasattr(os,'add_dll_directory'):
  for folder in (GPU_VENDOR/'nvidia').glob('*/bin'):_dll_handles.append(os.add_dll_directory(str(folder)))
if GPU_VENDOR.is_dir() and str(GPU_VENDOR) not in sys.path:sys.path.append(str(GPU_VENDOR))
class AdaptiveRail:
 def __init__(self,circuit,start=True):
  self.c=circuit;self.halt=threading.Event();self.lock=threading.RLock();self.worker=None;self.sequence=0;self.interval=.2;self.batch=64;self.seen={};self.history=collections.deque(maxlen=24);self.stages={};self.metrics={};self.gpu=None;self.gpu_status='CPU fallback; optional CuPy CUDA backend not available';self.next_probe=0;self.cpu=None;self.cost_profiles={};self.numeric_cache={};self.reused_samples=0
  try:
   import psutil
   self.cpu=psutil;psutil.cpu_percent(None)
  except ImportError:pass
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='adaptive-intelligence-rail');self.worker.start()
 def probe(self):
  if self.cpu:
   m=self.cpu.virtual_memory();self.metrics={'cpu_percent':self.cpu.cpu_percent(None),'memory_percent':m.percent,'available_memory_bytes':m.available,'logical_cpus':self.cpu.cpu_count()}
  else:self.metrics={'status':'resource counters unavailable; conservative rate'}
  if self.sequence==0 and importlib.util.find_spec('cupy'):
   try:
    import cupy
    if cupy.cuda.runtime.getDeviceCount()>0:self.gpu=cupy;self.gpu_status='CuPy CUDA numeric batches enabled'
   except Exception as e:self.gpu_status='CPU fallback: '+type(e).__name__
  if self.gpu:
   try:
    free,total=self.gpu.cuda.runtime.memGetInfo();self.metrics.update(gpu_memory_total_bytes=total,gpu_memory_available_bytes=free,gpu_memory_percent=100*(total-free)/total)
   except Exception as e:self.metrics['gpu_measurement_error']=type(e).__name__
 def cycle(self):
  start=time.perf_counter()
  if time.monotonic()>=self.next_probe:self.probe();self.next_probe=time.monotonic()+2
  with self.c.lock:
   snapshots=[(key,copy.deepcopy(layer.get('observations',[])),layer.get('parent_event')) for key,layer in self.c.element_thinking.layers.items()]
   goal=self.c.goal;total=self.c.experiment_sphere.trials;novel=self.c.experiment_sphere.novel
  pressure=max(self.metrics.get('cpu_percent',70)/100,self.metrics.get('memory_percent',70)/100,self.metrics.get('gpu_memory_percent',0)/100)
  novelty=novel/max(total,1);target=.85 if novelty>.2 else .65
  multiplier=max(.25,min(2,(target/max(.15,pressure))))
  self.batch=max(16,min(4096,int(self.batch*multiplier)));self.interval=max(.02,min(2,.08 if pressure<.8 and novelty>.05 else .4 if pressure<.9 else 1))
  prepared=[];flat=[];starts=[];gpu_results={};cached_results={}
  for key,facts,parent in snapshots:
   sample=[float(f['value']) for f in facts if type(f.get('value')) in (int,float) and math.isfinite(f['value']) and abs(f['value'])<1e100][:self.batch]
   previous=self.numeric_cache.get(key)
   if sample and previous and previous['samples']==tuple(sample):cached_results[key]=previous['result'];self.reused_samples+=1
   elif sample:starts.append((key,len(flat)));flat.extend(sample)
   prepared.append((key,facts,parent,sample))
  bucket=len(flat).bit_length();profile=self.cost_profiles.get(bucket)
  if self.gpu and len(flat)>=128 and (not profile or profile['gpu_seconds']<=profile['cpu_seconds']):
   try:
    gpu_started=time.perf_counter();arr=self.gpu.asarray(flat,dtype=self.gpu.float64);offsets=self.gpu.asarray([i for _,i in starts],dtype=self.gpu.int64);sums=self.gpu.add.reduceat(arr*arr,offsets).get().tolist();gpu_results=dict(zip([k for k,_ in starts],sums));gpu_cost=time.perf_counter()-gpu_started
    cpu_started=time.perf_counter();reference={key:math.fsum(x*x for x in sample) for key,_,_,sample in prepared if sample and key not in cached_results};cpu_cost=time.perf_counter()-cpu_started
    if not all(math.isclose(gpu_results[k],v,rel_tol=1e-12,abs_tol=1e-12) for k,v in reference.items()):raise ValueError('GPU and CPU numeric cross-check disagreed')
    self.cost_profiles[bucket]={'gpu_seconds':gpu_cost,'cpu_seconds':cpu_cost,'actual_values':len(flat),'preferred':'GPU' if gpu_cost<=cpu_cost else 'CPU'}
   except Exception as e:self.gpu_status='GPU batch failed; CPU fallback: '+type(e).__name__
  outcomes=[]
  for key,facts,parent,sample in prepared:
   backend='checked numeric cache' if key in cached_results else 'GPU / CuPy CUDA' if key in gpu_results else 'CPU';sumsq=cached_results.get(key,gpu_results.get(key))
   if sample and sumsq is None:sumsq=math.fsum(x*x for x in sample)
   if sample:self.numeric_cache[key]={'samples':tuple(sample),'result':sumsq}
   state={'stage':key,'parent_event':parent,'captured_values':len(facts),'numeric_samples':len(sample),'sum_of_squares':sumsq,'backend':backend,'cycles':self.stages.get(key,{}).get('cycles',0)+1,'selected_interval_seconds':self.interval,'goal':goal,'status':'processed captured input' if facts else 'listening for input'}
   outcomes.append(state)
  with self.lock:
   self.stages={r['stage']:r for r in outcomes};self.sequence+=1;self.history.append({'sequence':self.sequence,'cost_ms':(time.perf_counter()-start)*1000,'stages':len(outcomes),'batch':self.batch,'interval':self.interval,'gpu_batches':int(bool(gpu_results)),'actual_numeric_values':len(flat)})
  # Feed actual numeric results back as source-labelled observations, with no host action.
  if self.sequence%10==0:
   self.c.bus.publish({'origin':'adaptive-intelligence-rail','target':'all','kind':'stage-output','payload':{'adaptive_rail':True,'sequence':self.sequence,'results':outcomes,'provenance':'observed-numeric-processing','thinking_layers':['all']}})
 def view(self):
  with self.lock:return {'sequence':self.sequence,'baseline':'Original engine cadence retained','adaptive_interval_seconds':self.interval,'reused_numeric_stage_results':self.reused_samples,'backend_cost_profiles':copy.deepcopy(self.cost_profiles),'batch_per_stage':self.batch,'resource_metrics':copy.deepcopy(self.metrics),'gpu':self.gpu_status,'stages':copy.deepcopy(self.stages),'recent':list(self.history),'scope':'Every registered thinking stage has an adaptive numeric rail. GPU requires compatible CuPy/CUDA; Python control and string work remain on CPU. Bounded batches use available headroom rather than exhausting memory. This does not change independent engines internal clocks.'}
 def loop(self):
  while not self.halt.is_set():
   try:self.cycle()
   except Exception as e:
    with self.lock:self.history.append({'error':type(e).__name__+': '+str(e)[:160]})
   self.halt.wait(self.interval)
 def close(self):
  self.halt.set()
  if self.worker:self.worker.join(3)
