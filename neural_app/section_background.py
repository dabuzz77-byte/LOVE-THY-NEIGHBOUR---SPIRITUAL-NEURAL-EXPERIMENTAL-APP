"""One cooperative computation lane for loaded sections; drawing stays in the UI."""
import threading,time
from . import section_threads
from .python_components import LOCK

class SectionBackground:
 def __init__(self,host):self.host=host;self.future=None;self.last=0;self.closed=False;self.cycles={}
 def pulse(self):
  now=time.monotonic();interval={'low':2,'medium':.5,'high':.1}[self.host.runtime.settings['pace']]
  if self.closed or now-self.last<interval or self.future and not self.future.done():return
  self.last=now;self.future=section_threads.compute.submit(self.step)
 def step(self):
  if self.closed:return
  host=self.host
  with LOCK:
   for ident,item in list(host.python.loaded.items()):
    if self.closed:return
    if ident in host.paused:continue
    c=item['controller']
    try:
     if ident=='neural-lab':
      with c.lock:
       if c.running:c.train_steps(min(32,c.speed));c.record_metrics()
     elif ident=='godmind':
      neural=c.session.neural
      with neural.lock:
       if neural.running:neural.train_steps(min(32,neural.speed));neural.record_metrics()
      if c.session.optimizer.running:c.session.optimizer.step_once()
     elif ident=='unified-neural' and c.running and not c.dialog_open:c.train(min(32,c.speed.get()))
     elif ident=='core':
      before=c.engine.cycle;c.shared_step()
      if c.engine.cycle!=before:host.runtime.component_result('core',{'source':'scheduled original engine'},c.engine.snapshot())
     elif ident=='hydrogen':
      from .hydrogen_components import tick
      tick(c,host.runtime)
     elif ident=='atelier':
      c.bus.loop()
      if c.engine.running:c.engine.step()
      if vars(c).get('shared_feedback',False):
       import math
       field=c.engine.snapshot();signal=math.sin(field['ticks']*.035)*.6+(sum(field['bits'])/96-.5)*.8
       with c.engine.lock:c.engine.script_signal=.8*c.engine.script_signal+.2*math.tanh(signal);c.engine.script_at=time.monotonic();c.engine.script_samples+=1
     elif ident=='inference' and item.get('embedded_ready'):item['module']._shared_tick()
     elif ident=='observatory' and item.get('embedded_ready'):
      c.shared_pump();host.tick(ident,item)
    except Exception as error:host.python.errors[ident]=type(error).__name__+': '+str(error)
  for ident,owner,fn,args,kwargs in list(section_threads.scheduled):
   if ident not in host.python.loaded or ident in host.paused or ident in ('godmind','neural-lab','atelier','inference','flux'):continue
   if ident=='observatory' and owner is host.python.loaded[ident]['controller']:continue
   if callable(getattr(fn,'ready',None)) and not fn.ready():continue
   key=(ident,id(owner),id(fn));previous=self.cycles.get(key)
   if previous and not previous.done():continue
   def run_cycle(fn=fn,args=args,kwargs=kwargs,ident=ident):
    section_threads.scope.ident=ident
    try:return fn(*args,**kwargs)
    except Exception as error:host.python.errors[ident]=type(error).__name__+': '+str(error)
   self.cycles[key]=section_threads.pool.submit(run_cycle)
  if host.qt and not self.closed and 'flux' not in host.paused:host.qt.pulse()
  if host.java and not self.closed:
   try:host.java.tick_all()
   except Exception as error:host.runtime.errors.append('Java section tick: '+str(error))
  if not self.closed and hasattr(host.runtime,'_source_atlas'):
   try:host.runtime._source_atlas.background_step(host)
   except Exception as error:host.python.errors['source-atlas']=type(error).__name__+': '+str(error)
  if not self.closed:
   try:host.original_lane.step()
   except Exception as error:host.python.errors['original-lane']=type(error).__name__+': '+str(error)
 def close(self):
  self.closed=True
  for future in self.cycles.values():future.cancel()
  for ident,owner,fn,args,kwargs in list(section_threads.scheduled):
   if callable(getattr(fn,'close',None)):fn.close()
  if self.future:
   self.future.cancel()
   try:self.future.result(5)
   except Exception:pass
