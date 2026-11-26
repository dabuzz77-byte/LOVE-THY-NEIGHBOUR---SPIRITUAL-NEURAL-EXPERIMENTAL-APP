"""Flux's original continuous engines share the common computation workers."""
import ast,inspect,textwrap,time,types
from . import section_threads

def evaluate_once(method):
 tree=ast.parse(textwrap.dedent(inspect.getsource(method)))
 class Once(ast.NodeTransformer):
  def visit_While(self,node):return ast.copy_location(ast.For(target=ast.Name(id='_shared_tick',ctx=ast.Store()),iter=ast.Call(func=ast.Name(id='range',ctx=ast.Load()),args=[ast.Constant(1)],keywords=[]),body=node.body,orelse=node.orelse),node)
 tree=Once().visit(tree)
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='get' and any(k.arg=='timeout' for k in node.keywords):
   node.func.attr='get_nowait';node.keywords=[]
 ast.fix_missing_locations(tree);space={};exec(compile(tree,inspect.getsourcefile(method),'exec'),method.__func__.__globals__,space)
 return types.MethodType(space[method.__name__],method.__self__)

class FluxScheduler:
 def __init__(self,window,runtime):
  self.window=window;self.runtime=runtime;self.pending={};self.due={};self.closed=False;self.jobs={};window.data_active=True
  for name in ('live_audit','mesh_module','unified_core','platform_alignment','karmic_welfare','virtue_text','souls_ingress','reference','neural','web_research'):
   engine=getattr(window,name)
   self.jobs[name]=engine.process_next
  def pipeline():
   job=window.pipeline._claim()
   if job:return window.pipeline.process(job)
  self.jobs['pipeline']=pipeline
  bridge=window.observatory;host=runtime.component_host
  bridge.request=lambda path:host.invoke('observatory',path)
  def publish(topic,data):
   host.adapter('observatory')[2]['controller'].publish('flux.'+topic,data);return True
  bridge.publish=publish;bridge.status='Integrated shared Observatory';self.evaluate=evaluate_once(bridge._evaluate)
  def observatory():
   rt=host.adapter('observatory')[2]['controller']
   for name,module in list(rt.modules.items()):
    if module.get('runs',0):bridge._enqueue({'id':name,'runs':module['runs'],'last_run':module.get('last_run')})
   self.evaluate()
  self.jobs['observatory']=observatory
 def pulse(self):
  if self.closed:return
  now=time.monotonic()
  for name,job in self.jobs.items():
   prior=self.pending.get(name)
   if prior and not prior.done() or now<self.due.get(name,0):continue
   self.due[name]=now+(2 if name in ('web_research','observatory') else .5)
   def run(job=job,name=name):
    section_threads.scope.ident='flux'
    try:return job()
    except Exception as error:self.runtime.errors.append('Flux '+name+': '+str(error))
   self.pending[name]=(section_threads.pool if name in ('web_research','mesh_module') else section_threads.compute).submit(run)
 def close(self):
  self.closed=True
  for future in self.pending.values():future.cancel()
