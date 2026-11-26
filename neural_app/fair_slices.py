"""Cooperative round-robin slices; a slow callback cannot be preempted."""
import time

def refresh_root_spheres(c):
 """Keep captured-data projections fresh during conversation, at most once/sec."""
 with c.lock:
  if time.monotonic()<c.sphere_next:return False
  wave=c.sphere_modulators.sample()
  c.expression_sphere.step([],c.goal,wave)
  c.selection_sphere.step(list(c.generation_selector.last.values()),c.goal,wave)
  c.system_flux_sphere.step([c.expression_sphere.latest,c.selection_sphere.latest,c.selection_sphere.unmodulated],c.generation_selector,c.sources,c.goal)
  c.sphere_next=time.monotonic()+1
  return True

class FairSlices:
 def __init__(self):self.cursor=0;self.calls={};self.last={}
 def run(self,items,visit,limit=8,budget_seconds=.04):
  started=time.perf_counter();visited=[]
  for _ in range(min(len(items),max(1,limit))):
   if visited and time.perf_counter()-started>=budget_seconds:break
   index=self.cursor%len(items);self.cursor=(index+1)%len(items);name,item=items[index]
   try:visit(name,item)
   finally:
    visited.append(name);self.calls[name]=self.calls.get(name,0)+1
  self.last={'visited':visited,'elapsed_ms':(time.perf_counter()-started)*1000,'cursor':self.cursor,'slice_limit':limit,'budget_ms':budget_seconds*1000,'policy':'Fair cooperative slices; one slow callback may exceed the slice budget, then later roles retain their turn.'}
  return self.last
