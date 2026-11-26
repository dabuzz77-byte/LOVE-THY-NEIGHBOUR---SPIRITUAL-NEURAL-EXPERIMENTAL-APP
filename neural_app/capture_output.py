"""Thread-local captures keep concurrent engine printouts separate."""
from contextlib import *
import contextlib as _contextlib
import sys,threading
_local=threading.local();_lock=threading.RLock()
class _ThreadStream:
 _neural_thread_stream=True
 def __init__(self,stream,name):self.stream=stream;self.name=name
 def target(self):return getattr(_local,self.name,self.stream)
 def write(self,text):
  target=self.target()
  return len(text) if target is None else target.write(text)
 def flush(self):
  target=self.target()
  if target is not None:return target.flush()
 def __getattr__(self,name):return getattr(self.target(),name)
class _Capture:
 def __init__(self,name,target):self.name=name;self.target=target
 def __enter__(self):
  with _lock:
   current=getattr(sys,self.name)
   if not getattr(current,'_neural_thread_stream',False):setattr(sys,self.name,_ThreadStream(current,self.name))
  self.previous=getattr(_local,self.name,None);self.had=hasattr(_local,self.name);setattr(_local,self.name,self.target);return self.target
 def __exit__(self,*args):
  if self.had:setattr(_local,self.name,self.previous)
  else:delattr(_local,self.name)
def redirect_stdout(target):return _Capture('stdout',target)
def redirect_stderr(target):return _Capture('stderr',target)
