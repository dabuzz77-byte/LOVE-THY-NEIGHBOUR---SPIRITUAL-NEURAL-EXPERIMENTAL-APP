"""Keep original Core calculation timing independent of its drawing callbacks."""
import ast,inspect,textwrap,types

def core(controller):
 method=controller.frame;tree=ast.parse(textwrap.dedent(inspect.getsource(method)))
 class Compute(ast.NodeTransformer):
  def visit_Expr(self,node):
   call=node.value
   if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr in ('draw_field','draw_chart'):return None
   return self.generic_visit(node)
  def visit_Assign(self,node):
   if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='after':return None
   return self.generic_visit(node)
 tree=Compute().visit(tree);ast.fix_missing_locations(tree);namespace={};exec(compile(tree,inspect.getsourcefile(method),'exec'),method.__func__.__globals__,namespace)
 controller.shared_step=types.MethodType(namespace['frame'],controller)
 def frame(self):
  if self.closed:return
  import time
  self.draw_field(time.monotonic());self.draw_chart();self.after_id=self.root.after(33,self.frame)
 controller.frame=types.MethodType(frame,controller)
 for key,(due,fn,args) in list(controller.root.scheduled.items()):
  if getattr(fn,'__self__',None) is controller and getattr(fn,'__name__','')=='frame':controller.root.scheduled[key]=(due,controller.frame,args)
