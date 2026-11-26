"""Run the original catalogue in the shared process, with shared receipts."""
import importlib,json,os,time,types,uuid,collections,threading
from pathlib import Path
from .runtime import ROOT,clean

def integrate(rt,runtime):
 package=type(rt).__module__.rsplit('.',1)[0];worker=importlib.import_module(package+'.worker');telemetry=rt.telemetry
 allowed={(rt.root/m['file']).resolve() for m in rt.modules.values()}
 def execute(name,request,origin='module schedule'):
  path=Path(request['path']).resolve()
  if path not in allowed:raise ValueError('Choose a built-in catalogue module')
  request,primary=rt.primary.prepare(name,request,origin);key=uuid.uuid4().hex[:16];stamp=time.monotonic();before=telemetry.snapshot()
  row={'id':key,'module':name,'origin':origin,'started':time.time(),'status':'running','pid':os.getpid(),'duration_ms':0,'cpu_seconds':0,'peak_rss_bytes':0,'samples':1,'before':before,'primary_cascade':primary,'input_dictionaries':list(request.get('inputs',{})),'source_count':len(request.get('sources',[])),'definition_count':len(request.get('definitions',{})),'shared_process':True}
  with telemetry.lock:telemetry.active[key]=row
  try:
   result={'ok':True,**worker.run(path,request.get('inputs'),request.get('sources'),request.get('definitions'),request.get('runtime'),request.get('predictive'),primary)};code=0
  except Exception as error:result={'ok':False,'error':type(error).__name__+': '+str(error)};code=1
  result['status']=outcome(result) if result.get('ok') else 'ERROR'
  result['telemetry_id']=key;row['duration_ms']=(time.monotonic()-stamp)*1000;result['shared_receipt']=runtime.component_result('observatory',{'module':name,'inputs':request.get('inputs',{})},result,row['duration_ms'])
  return types.SimpleNamespace(returncode=code,stdout=json.dumps(result),stderr=result.get('error',''),telemetry_id=key)
 telemetry.execute=execute
 # One coalesced catalogue queue replaces a pool owned by each old app.
 from . import section_threads
 rt.pool.shutdown(wait=False,cancel_futures=True)
 class SharedExecutor:
  def __init__(self):self.futures=set();self.lock=threading.RLock();self.closed=False
  def submit(self,fn,*args,**kwargs):
   with self.lock:
    if self.closed:raise RuntimeError('Section is stopping')
    future=section_threads.compute.submit(fn,*args,**kwargs);self.futures.add(future)
   def finished(value):
    with self.lock:self.futures.discard(value)
   future.add_done_callback(finished);return future
  def shutdown(self,wait=False,cancel_futures=False):
   with self.lock:self.closed=True;futures=list(self.futures)
   if cancel_futures:
    for future in futures:future.cancel()
 rt.pool=SharedExecutor();rt.shared_pending=collections.OrderedDict();rt.shared_catalogue_future=None
 # Reviewed local calculations have a bounded automatic path even while the
 # complete, input-driven catalogue is paused. Original manual controls remain.
 from .observatory_wiring import reviewed_modules,automatic_inputs,outcome
 rt.shared_auto_modules=reviewed_modules(rt)
 rt.shared_auto_last=-1e9
 rt.shared_auto_cursor=0
 original_run=rt.run_module
 def run_module(name):
  auto=name in rt.shared_auto_modules and not rt.overrides.get(name)
  supplied=automatic_inputs(rt,name) if auto else None
  if supplied:rt.overrides[name]=supplied
  try:
   original_run(name)
   result=rt.results.get(name,{})
   if supplied:result['input_provenance']={'kind':'shared app measurements','fields':list(supplied['inputs']['payload']),'automatic':True}
   if result.get('ok'):
    with rt.lock:rt.modules[name]['status']=outcome(result)
  finally:
   if supplied and rt.overrides.get(name) is supplied:rt.overrides.pop(name,None)
 rt.run_module=run_module
 def schedule(name):
  with rt.lock:
   if name not in rt.modules:raise ValueError('Unknown module')
   if name in rt.inflight:return False
   rt.inflight.add(name);rt.last_scheduled[name]=time.monotonic();rt.modules[name]['status']='queued';rt.shared_pending[name]=None
  return True
 rt.schedule=schedule
 def pump(now=None):
  now=time.monotonic() if now is None else now
  if rt.stop.is_set():return
  pace=runtime.settings.get('pace','medium');interval={'low':4,'medium':2,'high':1}[pace]
  if not rt.config.get('running') and rt.shared_auto_modules and now-rt.shared_auto_last>=interval:
   name=rt.shared_auto_modules[rt.shared_auto_cursor%len(rt.shared_auto_modules)]
   rt.shared_auto_cursor+=1;rt.shared_auto_last=now;schedule(name)
  if rt.config.get('running'):
   period=rt.config.get('cycle_seconds',5)
   for name in rt.modules:
    if rt.economy.owns(name):continue
    interval=rt.config.get('module_loops',{}).get(name,period)
    if now-rt.last_scheduled.get(name,-1e9)>=interval:schedule(name)
  if rt.shared_catalogue_future and not rt.shared_catalogue_future.done():return
  with rt.lock:
   if not rt.shared_pending:return
   name,_=rt.shared_pending.popitem(last=False)
  rt.shared_catalogue_future=rt.pool.submit(rt.run_module,name)
 rt.shared_pump=pump
 original_snapshot=rt.snapshot
 def execution_status():
  with rt.lock:
   return {'reviewed':len(rt.shared_auto_modules),'total':len(rt.modules),'visited':sum(m['runs']>0 for m in rt.modules.values()),'complete':sum(m['status']=='complete' for m in rt.modules.values()),'awaiting_input':sum(m['status']=='awaiting input' for m in rt.modules.values()),'errors':sum(m['status']=='error' for m in rt.modules.values()),'pending':len(rt.shared_pending),'slot_seconds':{'low':4,'medium':2,'high':1}[runtime.settings.get('pace','medium')]}
 rt.shared_execution=execution_status
 def snapshot():
  state=original_snapshot();state['shared_execution']=execution_status();state['worker_limit']=1
  return state
 rt.snapshot=snapshot
 original_telemetry_view=telemetry.view
 def telemetry_view():
  state=original_telemetry_view();state['workers']=1;state['scope']='Shared-process catalogue calculations, recorded outputs and measured host telemetry.'
  return state
 telemetry.view=telemetry_view
 original_settings=rt.update_settings
 def settings(body):
  body=dict(body);body.pop('port',None)
  return original_settings(body)
 rt.update_settings=settings
 return rt
