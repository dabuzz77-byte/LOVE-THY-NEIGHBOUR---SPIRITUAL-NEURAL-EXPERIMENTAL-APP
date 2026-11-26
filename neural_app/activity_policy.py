"""Resource-aware processing ceilings, separate from external I/O and rendering."""
import json,math,os,threading
from pathlib import Path

class ActivityPolicy:
 def __init__(self,data=None):
  self.lock=threading.RLock();self.mode='high';self.path=Path(data)/'engine-activity.json' if data else None
  if self.path:
   try:
    saved=json.loads(self.path.read_text(encoding='utf-8'))
    if saved.get('mode') in ('balanced','high','maximum'):self.mode=saved['mode']
   except (OSError,ValueError,AttributeError):pass
 def configure(self,body):
  mode=body.get('mode')
  if mode not in ('balanced','high','maximum'):raise ValueError('Choose balanced, high or maximum')
  with self.lock:
   if self.path:
    temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps({'mode':mode}),encoding='utf-8');os.replace(temp,self.path)
   self.mode=mode
  return self.settings()
 def settings(self,metrics=None,user_active=False):
  metrics=metrics or {}
  def reading(key,default):
   value=metrics.get(key,default)
   return max(0,min(100,float(value))) if type(value) in (int,float) and math.isfinite(value) else default
  cpu=reading('cpu_percent',70);memory=reading('memory_percent',70);gpu=reading('gpu_memory_percent',0)
  with self.lock:mode=self.mode
  factor={'balanced':1.,'high':8.,'maximum':12.}[mode];reason='available headroom'
  if memory>=96 or cpu>=98 or gpu>=98:factor=.25;reason='severe resource pressure'
  elif memory>=90 or cpu>=92 or gpu>=94:factor=.5;reason='resource pressure'
  elif memory>=84 or cpu>=84:factor=min(factor,2.);reason='limited headroom'
  if user_active:factor=min(factor,2.);reason+='; conversation priority'
  duty=.12 if user_active else .6 if factor>1 else .25 if factor>=1 else .08
  return {'mode':mode,'multiplier':factor,'reason':reason,'workspace_interval_seconds':max(.02,.25/factor),'practice_interval_seconds':max(2.,30/factor),'whole_mind_interval_seconds':max(.2,2/factor),'native_search_slice_ms':min(12,max(1,4*factor)),'duty_target':duty,'cpu_percent':cpu,'memory_percent':memory,'gpu_memory_percent':gpu,'scope':'Adaptive eligibility ceilings for native work; actual throughput depends on work cost. External fetch rates and model-call policies are unchanged.'}
 def for_circuit(self,c):
  return self.settings(dict(getattr(c.adaptive_rail,'metrics',{}) or {}),getattr(c.r,'user_active',False))
