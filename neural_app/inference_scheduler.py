"""Original inference cycles scheduled once per due interval without sleeping workers."""
import ast,inspect,textwrap,time,types
from . import section_threads

def one_cycle(method):
 source=textwrap.dedent(inspect.getsource(method))
 if method.__name__=='loop' and type(method.__self__).__name__=='Federation':
  source=source.replace('last_catalog = time.time()',"self._shared_last_catalog = getattr(self, '_shared_last_catalog', time.time())",1)
  import re
  source=re.sub(r'(?<![\w.])last_catalog\b','self._shared_last_catalog',source)
 tree=ast.parse(source)
 class Cooperative(ast.NodeTransformer):
  def visit_Expr(self,node):
   value=node.value
   if isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute) and value.func.attr in ('wait','sleep'):return None
   return self.generic_visit(node)
 tree=Cooperative().visit(tree);ast.fix_missing_locations(tree);namespace={}
 exec(compile(tree,inspect.getsourcefile(method),'exec'),method.__func__.__globals__,namespace)
 return types.MethodType(namespace[method.__name__],method.__self__)

class InferenceScheduler:
 def __init__(self,module,runtime,host,engine_tick,publish):
  self.module=module;self.runtime=runtime;self.host=host;self.engine_tick=engine_tick;self.pending={};self.due={};self.closed=False
  auto=module.autonomous
  def shared_bus():
   if not auto.settings['enabled'] or not auto.settings['bus_enabled']:return
   if host:
    rt=host.adapter('observatory')[2]['controller']
    cursor=auto.cursor('shared_receipts')
    # Only original externally observed events feed intake; no recursive receipt training.
    with module.db() as db:rows=db.execute('SELECT id,topic,payload FROM events WHERE id>? AND topic IN ("observatory.module","observatory.process-event") ORDER BY id LIMIT 60',(cursor,)).fetchall()
    for ident,topic,payload in rows:
     import json
     auto.accept_bus(topic.split('.',1)[1],json.loads(payload));auto.set_cursor('shared_receipts',ident)
    if time.time()>=getattr(self,'next_sources',0):
     import json
     sources=module.obs_request('/api/sources');auto.ingest('Observatory · existing sources','bus','Existing web research & source state','',json.dumps(sources,ensure_ascii=False),sources,'Observatory source hub');self.next_sources=time.time()+60
   auto.bus_error=None;auto.flux_error=None;auto.flux_mode='Shared in-process event delivery'
  auto.bus_loop=shared_bus
  module.federation.allprev=lambda payload:{'http_status':200,'response':{'accepted':True,'result':runtime.engine('pipeline',{'text':str(payload)[:4000]})},'meaning':'Integrated pipeline completion'}
  self.jobs={'engine':(engine_tick,lambda:True,lambda:.5),'bus':(shared_bus,lambda:auto.settings['enabled'] and auto.settings['bus_enabled'],lambda:3),'web':(one_cycle(auto.web_loop),lambda:auto.settings['enabled'] and auto.settings['web_enabled'],lambda:5),'prompts':(one_cycle(module.prompt_loop.run),lambda:module.prompt_loop.settings['enabled'],lambda:max(1,module.prompt_loop.settings['interval'])),'federation':(one_cycle(module.federation.loop),lambda:True,lambda:10),'research':(one_cycle(module.native_research.loop),lambda:module.native_research.state['enabled'],lambda:2)}
 def pulse(self):
  if self.closed:return
  now=time.monotonic()
  for name,(job,enabled,interval) in self.jobs.items():
   previous=self.pending.get(name)
   if previous and not previous.done() or now<self.due.get(name,0) or not enabled():continue
   self.due[name]=now+interval()
   def run(job=job,name=name):
    section_threads.scope.ident='inference'
    try:return job()
    except Exception as error:self.runtime.errors.append('Inference '+name+': '+str(error))
   self.pending[name]=(section_threads.pool if name in ('web','research','prompts') else section_threads.compute).submit(run)
 def close(self):
  self.closed=True
  for future in self.pending.values():future.cancel()
