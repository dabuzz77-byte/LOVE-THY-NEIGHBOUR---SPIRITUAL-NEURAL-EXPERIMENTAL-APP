"""Bounded measured service timings; no execution or model calls."""
import copy, math, threading, time
class ServiceMetrics:
 def __init__(self):self.lock=threading.RLock();self.rows={}
 def record(self,name,elapsed_ms,error=None):
  if not isinstance(name,str) or type(elapsed_ms) not in (int,float) or not math.isfinite(elapsed_ms) or elapsed_ms<0:raise ValueError('Finite nonnegative service timing required')
  with self.lock:
   r=self.rows.setdefault(name,{'calls':0,'errors':0,'total_ms':0.,'max_ms':0.,'ewma_ms':0.,'last_ms':0.,'last_at':0.,'last_error':None,'consecutive_errors':0,'retry_at':0.})
   r['calls']+=1;r['errors']+=int(error is not None);r['total_ms']+=elapsed_ms;r['max_ms']=max(r['max_ms'],elapsed_ms);r['ewma_ms']=elapsed_ms if r['calls']==1 else .2*elapsed_ms+.8*r['ewma_ms'];r['last_ms']=elapsed_ms;r['last_at']=time.time();r['last_error']=str(error)[:180] if error is not None else None
   r['consecutive_errors']=r['consecutive_errors']+1 if error is not None else 0
   r['retry_at']=time.monotonic()+min(30.,2.**min(5,r['consecutive_errors']-1)) if error is not None else 0.
 def ready(self,name):
  with self.lock:return time.monotonic()>=self.rows.get(name,{}).get('retry_at',0.)
 def view(self):
  with self.lock:
   rows=[dict(name=k,**copy.deepcopy(v),mean_ms=v['total_ms']/v['calls']) for k,v in self.rows.items()]
  return {'services':sorted(rows,key=lambda x:-x['ewma_ms']),'scope':'Measured callback wall time, including idle checks; counts are scheduler calls, not learning successes.'}

def practice_delay(elapsed_seconds,user_active=False,multiplier=1.):
 """Bound shared training duty; yield more while the user is conversing."""
 multiplier=max(.25,min(12.,float(multiplier)))
 duty=.10 if user_active else .6 if multiplier>1 else .35 if multiplier>=1 else .1
 return max(.03,.2/multiplier,min(3.,max(0.,elapsed_seconds)*(1-duty)/duty))
