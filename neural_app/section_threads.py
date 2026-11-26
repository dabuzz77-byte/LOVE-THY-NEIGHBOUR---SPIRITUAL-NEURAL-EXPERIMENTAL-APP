"""Shared task ownership for converted section controllers."""
from threading import Event,Lock,RLock,Semaphore,BoundedSemaphore,Condition,local,current_thread
import threading,time
from .task_pool import TaskPool
pool=TaskPool(2,'neural-section-io');compute=TaskPool(1,'neural-section-compute');scheduled=[];scope=local()
def ensure_pool():
 global pool,compute
 if pool._shutdown:pool=TaskPool(2,'neural-section-io')
 if compute._shutdown:compute=TaskPool(1,'neural-section-compute')

class Thread:
 def __init__(self,group=None,target=None,name=None,args=(),kwargs=None,daemon=None,**kw):self._target=target;self._args=args;self._kwargs=kwargs or {};self.name=name;self.daemon=daemon;self.future=None;self.ident=None;self._registered=False;self.cycle=None
 def start(self):
  target=self._target or getattr(self,'run',None);owner=getattr(target,'__self__',None)
  step=None
  for method in ('step_once','step'):
   if owner is not None and callable(getattr(type(owner),method,None)):
    step=getattr(owner,method);break
  if step:
   def guarded_step():
    running=getattr(owner,'running',True)
    if isinstance(running,bool) and not running:return
    return step()
   if not self._registered:scheduled.append((getattr(scope,'ident',''),owner,guarded_step,(),{}));self._registered=True
   return
  name=getattr(target,'__name__','')
  if name in ('serve_forever','serve','listen','accept','recv_loop','receive_loop'):
   return
  code=getattr(target,'__code__',None)
  cooperative=code is not None and '_shared_tick' in code.co_varnames
  if cooperative:
   if not self._registered:
    from .cooperative_cycle import LoopCycle
    self.cycle=LoopCycle(target,self._args,self._kwargs);scheduled.append((getattr(scope,'ident',''),owner,self.cycle,(),{}));self._registered=True
   return
  if target:
   owner_id=getattr(scope,'ident','')
   def finite_task():
    scope.ident=owner_id
    return target(*self._args,**self._kwargs)
   self.future=pool.submit(finite_task)
 def is_alive(self):return self._registered and (self.cycle is None or not self.cycle.closed) or self.future is not None and not self.future.done()
 def join(self,timeout=None):
  if self.cycle and self.cycle.stopped():self.cycle.close()
  if self.future:
   try:self.future.result(timeout)
   except Exception:pass
 def run(self):
  if self._target:self._target(*self._args,**self._kwargs)
class Timer(Thread):
 def __init__(self,interval,function,args=None,kwargs=None):super().__init__(target=function,args=args or (),kwargs=kwargs);self.interval=interval
 def cancel(self):pass
