"""Bounded daemon workers: pending I/O never holds the desktop process open."""
import queue,threading
from concurrent.futures import Future

class TaskPool:
 def __init__(self,max_workers,name,capacity=64):
  self.max_workers=max_workers;self.name=name;self.jobs=queue.Queue(capacity);self._shutdown=False;self._threads=[];self.lock=threading.Lock()
 def submit(self,fn,*args,**kwargs):
  future=Future()
  with self.lock:
   if self._shutdown:raise RuntimeError('Background workers are stopping')
   try:self.jobs.put_nowait((future,fn,args,kwargs))
   except queue.Full:raise RuntimeError('Background queue is full; try again') from None
   if len(self._threads)<self.max_workers:
    thread=threading.Thread(target=self._worker,name=self.name+'-'+str(len(self._threads)),daemon=True);self._threads.append(thread);thread.start()
  return future
 def _worker(self):
  while True:
   job=self.jobs.get()
   try:
    if job is None:return
    future,fn,args,kwargs=job
    if not future.set_running_or_notify_cancel():continue
    try:future.set_result(fn(*args,**kwargs))
    except BaseException as error:future.set_exception(error)
   finally:self.jobs.task_done()
 def shutdown(self,wait=True,cancel_futures=False):
  with self.lock:
   if self._shutdown:return
   self._shutdown=True
   if cancel_futures:
    while True:
     try:job=self.jobs.get_nowait()
     except queue.Empty:break
     if job is not None:job[0].cancel()
     self.jobs.task_done()
   for thread in self._threads:self.jobs.put(None)
  if wait:
   for thread in self._threads:thread.join()
