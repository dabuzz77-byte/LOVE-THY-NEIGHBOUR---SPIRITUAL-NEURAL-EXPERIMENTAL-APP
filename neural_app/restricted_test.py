"""Bounded AST interpreter. No eval/exec, imports, attributes or OS facilities."""
import ast,operator,time

class RestrictedTest:
 def __init__(self):self.values={};self.output=[];self.steps=0;self.deadline=time.monotonic()+1
 def tick(self):
  self.steps+=1
  if self.steps>5000 or time.monotonic()>self.deadline:raise ValueError('Execution budget reached.')
 def bounded(self,v):
  if isinstance(v,(str,list,tuple,dict,range)) and len(v)>4096:raise ValueError('Value length limit reached.')
  if isinstance(v,int) and v.bit_length()>4096:raise ValueError('Integer size limit reached.')
  if not isinstance(v,(str,int,float,bool,list,tuple,dict,type(None),range)):raise ValueError('Unsupported value type.')
  return v
 def expression(self,n):
  self.tick()
  if isinstance(n,ast.Constant):return self.bounded(n.value)
  if isinstance(n,ast.Name):
   if n.id not in self.values:raise ValueError('Unknown local variable: '+n.id)
   return self.values[n.id]
  if isinstance(n,(ast.List,ast.Tuple)):return self.bounded([self.expression(e) for e in n.elts])
  if isinstance(n,ast.Dict):return self.bounded({self.expression(k):self.expression(v) for k,v in zip(n.keys,n.values)})
  if isinstance(n,ast.UnaryOp):
   v=self.expression(n.operand);f={ast.USub:operator.neg,ast.UAdd:operator.pos,ast.Not:operator.not_,ast.Invert:operator.invert}.get(type(n.op))
   if not f:raise ValueError('Unsupported unary operator.')
   return self.bounded(f(v))
  if isinstance(n,ast.BinOp):
   a,b=self.expression(n.left),self.expression(n.right);f={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow,ast.BitAnd:operator.and_,ast.BitOr:operator.or_,ast.BitXor:operator.xor}.get(type(n.op))
   if not f:raise ValueError('Unsupported arithmetic operator.')
   if isinstance(n.op,ast.Pow) and (not isinstance(b,int) or abs(b)>128 or (isinstance(a,int) and a.bit_length()*max(1,b)>4096)):raise ValueError('Power size limit reached.')
   if isinstance(n.op,ast.Mult):
    if isinstance(a,(str,list,tuple)) and isinstance(b,int) and len(a)*max(0,b)>4096:raise ValueError('Sequence multiplication limit reached.')
    if isinstance(b,(str,list,tuple)) and isinstance(a,int) and len(b)*max(0,a)>4096:raise ValueError('Sequence multiplication limit reached.')
   if isinstance(n.op,ast.Mod) and isinstance(a,str):raise ValueError('String format execution is outside this subset.')
   return self.bounded(f(a,b))
  if isinstance(n,ast.Compare):
   left=self.expression(n.left)
   for op,node in zip(n.ops,n.comparators):
    right=self.expression(node);f={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge,ast.In:lambda a,b:a in b,ast.NotIn:lambda a,b:a not in b}.get(type(op))
    if not f or not f(left,right):return False
    left=right
   return True
  if isinstance(n,ast.BoolOp):
   for child in n.values:
    value=self.expression(child)
    if isinstance(n.op,ast.And) and not value:return value
    if isinstance(n.op,ast.Or) and value:return value
   return value
  if isinstance(n,ast.IfExp):return self.expression(n.body if self.expression(n.test) else n.orelse)
  if isinstance(n,ast.Subscript):
   value=self.expression(n.value);index=self.expression(n.slice)
   return self.bounded(value[index])
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and not n.keywords:
   name=n.func.id;args=[self.expression(a) for a in n.args]
   if name=='print':
    text=' '.join(str(a) for a in args)
    if sum(map(len,self.output))+len(text)>8192:raise ValueError('Output budget reached.')
    self.output.append(text);return None
   functions={'abs':abs,'len':len,'min':min,'max':max,'sum':sum,'int':int,'float':float,'str':str,'bool':bool,'sorted':sorted,'range':range}
   if name not in functions:raise ValueError('Function not available: '+name)
   if name=='range':
    value=range(*args)
    if len(value)>4096:raise ValueError('Loop range limit reached.')
    return value
   return self.bounded(functions[name](*args))
  raise ValueError('Unsupported expression: '+type(n).__name__)
 def block(self,nodes):
  for n in nodes:
   self.tick()
   if isinstance(n,ast.Expr):self.expression(n.value)
   elif isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) for t in n.targets):
    value=self.expression(n.value)
    for target in n.targets:self.values[target.id]=value
   elif isinstance(n,ast.If):self.block(n.body if self.expression(n.test) else n.orelse)
   elif isinstance(n,ast.For) and isinstance(n.target,ast.Name):
    iterable=self.expression(n.iter)
    for value in iterable:self.tick();self.values[n.target.id]=value;self.block(n.body)
    self.block(n.orelse)
   elif isinstance(n,ast.While):
    while self.expression(n.test):self.tick();self.block(n.body)
    self.block(n.orelse)
   elif isinstance(n,ast.Pass):pass
   else:raise ValueError('Unsupported statement: '+type(n).__name__)
   if len(self.values)>256:raise ValueError('Local variable limit reached.')

def run_restricted(body):
 source=str(body.get('source',''));language=str(body.get('language','python')).lower()
 if len(source)>16000:raise ValueError('Use up to 16,000 characters for restricted execution.')
 if language not in ('python','python3','py'):return {'status':'unsupported','program_executed':False,'scope':'Restricted execution currently supports the documented Python subset. Other formats use parser / compile checks.'}
 runner=RestrictedTest()
 try:runner.block(ast.parse(source).body);return {'status':'complete','method':'Bounded in-memory Python AST subset','output':runner.output,'variables':{k:str(v)[:1000] for k,v in runner.values.items()},'steps':runner.steps,'host_file_network_process_access':False,'program_executed':'restricted subset only'}
 except Exception as e:return {'status':'blocked','method':'Bounded in-memory Python AST subset','diagnostics':str(e),'output':runner.output,'steps':runner.steps,'host_file_network_process_access':False,'program_executed':'restricted subset only; stopped at unsupported operation or limit'}
