"""Shared pacing policy using cached resource measurements, without extra probes."""
def interval(c,base=.75):
 rail=getattr(c,'adaptive_rail',None)
 metrics=getattr(rail,'metrics',{}) if rail else {}
 if not metrics:return max(base,2.)
 pressure=max(metrics.get('cpu_percent',70),metrics.get('memory_percent',70),metrics.get('gpu_memory_percent',0))
 multiplier=1 if pressure<70 else 2 if pressure<85 else 6 if pressure<93 else 20
 if getattr(getattr(c,'r',None),'user_active',False):multiplier=max(3,multiplier)
 return base*multiplier
