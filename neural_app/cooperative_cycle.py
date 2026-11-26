"""Resume converted loops without losing their local state or sleeping a worker."""
import ast,inspect,textwrap,threading,time,types

def wait_request(event,seconds):return ('wait',event,float('inf') if seconds is None and isinstance(event,threading.Event) else max(0,float(seconds or .1)))

class LoopCycle:
 def __init__(self,target,args=(),kwargs=None):
  self.owner=getattr(target,'__self__',None);self.closed=False;self.generator=None;self.deadline=0;self.event=None;self.value=None;self.lock=threading.Lock();self.target=target;self.args=args;self.kwargs=kwargs or {}
  tree=ast.parse(textwrap.dedent(inspect.getsource(target)))
  class Transform(ast.NodeTransformer):
   def __init__(self):self.outer=False
   def visit_For(self,node):
    old=self.outer;converted=isinstance(node.target,ast.Name) and node.target.id=='_shared_tick';self.outer=converted
    node=self.generic_visit(node);self.outer=old
    if converted:return ast.copy_location(ast.While(test=ast.Constant(True),body=node.body+[ast.Expr(ast.Yield(ast.Constant(0)))],orelse=node.orelse),node)
    return node
   def visit_While(self,node):
    old=self.outer;self.outer=False;result=self.generic_visit(node);self.outer=old;return result
   def visit_Continue(self,node):
    return [ast.copy_location(ast.Expr(ast.Yield(ast.Constant(0))),node),node] if self.outer else node
   def visit_Call(self,node):
    node=self.generic_visit(node)
    if isinstance(node.func,ast.Attribute) and node.func.attr in ('wait','sleep'):
     delay=node.args[0] if node.args else next((k.value for k in node.keywords if k.arg=='timeout'),ast.Constant(None))
     event=node.func.value if node.func.attr=='wait' else ast.Constant(None)
     return ast.copy_location(ast.Yield(ast.Call(func=ast.Name(id='_neural_wait_request',ctx=ast.Load()),args=[event,delay],keywords=[])),node)
    if isinstance(node.func,ast.Attribute) and node.func.attr=='get' and any(k.arg=='timeout' for k in node.keywords):node.func.attr='get_nowait';node.args=[];node.keywords=[]
    return node
  tree=Transform().visit(tree);ast.fix_missing_locations(tree)
  namespace=dict(target.__func__.__globals__ if inspect.ismethod(target) else target.__globals__);namespace['_neural_wait_request']=wait_request
  code=target.__func__ if inspect.ismethod(target) else target
  if code.__closure__:namespace.update(zip(code.__code__.co_freevars,(cell.cell_contents for cell in code.__closure__)))
  local={};exec(compile(tree,inspect.getsourcefile(target),'exec'),namespace,local);fn=local[target.__name__]
  self.fn=types.MethodType(fn,self.owner) if self.owner is not None else fn
 def stopped(self):
  if self.owner is None:return False
  return any(isinstance(value,threading.Event) and value.is_set() for name,value in vars(self.owner).items() if name in ('stop','stop_event','halt','closed_event'))
 def ready(self):return not self.closed and (self.stopped() or time.monotonic()>=self.deadline or isinstance(self.event,threading.Event) and self.event.is_set())
 def __call__(self):
  if not self.ready() or not self.lock.acquire(False):return
  try:
   if self.stopped():self._close();return
   if self.generator is None:self.generator=self.fn(*self.args,**self.kwargs);result=next(self.generator)
   else:result=self.generator.send(self.event.is_set() if isinstance(self.event,threading.Event) else self.value)
   self.event=None;self.value=None;self.deadline=0
   if isinstance(result,tuple) and len(result)==3 and result[0]=='wait':self.event=result[1];self.deadline=time.monotonic()+result[2]
   elif isinstance(result,(int,float)):self.deadline=time.monotonic()+max(0,result)
  except StopIteration:self.closed=True
  finally:self.lock.release()
 def _close(self):
  self.closed=True
  if self.generator is not None:self.generator.close()
 def close(self):
  self.closed=True
  if self.lock.acquire(False):
   try:self._close()
   finally:self.lock.release()
