"""Test pure local Python functions with the existing bounded AST interpreter."""
import ast,copy,json,math,hashlib,time
from .restricted_test import RestrictedTest
from .workflow_contracts import equivalent

class Returned(Exception):
 def __init__(self,value):self.value=value
class LoopBreak(Exception):pass
class LoopContinue(Exception):pass
PROGRAM_ERRORS={'ValueError','TypeError','IndexError','KeyError','ZeroDivisionError','RuntimeError','AssertionError'}
class ProgramRaised(Exception):
 def __init__(self,name,message):self.name=name;self.message=message

def data_budget(value):
 pending=[(value,0,frozenset())];nodes=characters=0
 while pending:
  item,depth,ancestors=pending.pop();nodes+=1
  if nodes>8192 or depth>16:raise ValueError('Nested data budget reached')
  if isinstance(item,(list,tuple,dict)):
   if id(item) in ancestors:raise ValueError('Cyclic data is outside the JSON function domain')
   if len(item)>4096:raise ValueError('Container value limit reached')
   children=list(item.items()) if isinstance(item,dict) else item;next_ancestors=ancestors|{id(item)};characters+=2
   for child in children:pending.append((child,depth+1,next_ancestors))
  elif isinstance(item,range):
   if len(item)>4096:raise ValueError('Range value limit reached')
   characters+=100
  elif type(item) in (str,int,float,bool,type(None)):
   if type(item) is int and item.bit_length()>4096:raise ValueError('Integer value limit reached')
   if type(item) is float and not math.isfinite(item):raise ValueError('Nonfinite value')
   characters+=len(str(item))+2
  else:raise ValueError('Unsupported function data type')
  if characters>12000:raise ValueError('Expanded data size limit reached')

def safe_annotation(node):
 if node is None:return True
 if isinstance(node,ast.Name):return node.id in {'int','float','str','bool','list','dict','tuple'}
 if isinstance(node,ast.Constant):return node.value is None or isinstance(node.value,str)
 if isinstance(node,(ast.Tuple,ast.List)):return all(safe_annotation(v) for v in node.elts)
 if isinstance(node,ast.Subscript):return isinstance(node.value,ast.Name) and node.value.id in {'list','dict','tuple'} and safe_annotation(node.slice)
 if isinstance(node,ast.BinOp) and isinstance(node.op,ast.BitOr):return safe_annotation(node.left) and safe_annotation(node.right)
 return False

def literal_default(node):return isinstance(node,ast.Constant) or (isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)) and isinstance(node.operand,ast.Constant) and type(node.operand.value) in (int,float))

def isolated_source(source,name):
 tree=ast.parse(source);functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)};selected=set();pending=[name]
 while pending:
  current=pending.pop()
  if current in selected:continue
  if current not in functions:raise ValueError('Selected function was not found at module scope')
  selected.add(current)
  if len(selected)>16:raise ValueError('Too many local helper functions')
  pending.extend(node.func.id for node in ast.walk(functions[current]) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in functions and node.func.id not in selected)
 builtins={'abs','len','min','max','sum','int','float','str','bool','sorted','range','isinstance','list','tuple','dict','enumerate','zip','reversed','all','any','round','print'}|PROGRAM_ERRORS
 shadowed=set();star=False
 for node in tree.body:
  if isinstance(node,(ast.Import,ast.ImportFrom)):
   shadowed.update(a.asname or a.name.split('.')[0] for a in node.names);star|=any(a.name=='*' for a in node.names)
  elif isinstance(node,(ast.Assign,ast.AnnAssign)):
   targets=node.targets if isinstance(node,ast.Assign) else [node.target]
   shadowed.update(n.id for target in targets for n in ast.walk(target) if isinstance(n,ast.Name))
  elif isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in PROGRAM_ERRORS:shadowed.add(node.name)
 calls={n.func.id for current in selected for n in ast.walk(functions[current]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
 error_names={n.id for current in selected for n in ast.walk(functions[current]) if isinstance(n,ast.Name) and n.id in PROGRAM_ERRORS}
 if star or calls&shadowed&builtins or selected&shadowed or error_names&shadowed:raise ValueError('Module imports or globals shadow selected functions or function-test builtins; use explicit local-helper project tests or provide a closed pure function')
 return ast.unparse(ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in selected],type_ignores=[]))+'\n'

class FunctionTest(RestrictedTest):
 def __init__(self,source):
  super().__init__();self.functions={};self.depth=0
  tree=ast.parse(source)
  if len(list(ast.walk(tree)))>2000:raise ValueError('Function source has too many syntax nodes')
  compile(tree,'<bounded-function-test>','exec') # Syntax validation only; never execute.
  for node in tree.body:
   if isinstance(node,ast.FunctionDef) and not node.decorator_list and all(literal_default(v) for v in node.args.defaults) and not node.args.kw_defaults and not node.args.kwonlyargs and not node.args.vararg and not node.args.kwarg and not getattr(node,'type_params',[]) and safe_annotation(node.returns) and all(safe_annotation(a.annotation) for a in node.args.posonlyargs+node.args.args):
    self.functions[node.name]=node
   elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):continue
   else:raise ValueError('Provide plain function definitions only; no module initialization, imports or decorators')
 def bounded(self,value):
  if type(value) is float and not math.isfinite(value):raise ValueError('Nonfinite function result')
  return super().bounded(value)
 def invoke(self,name,args):
  self.tick();node=self.functions.get(name)
  if node is None:raise ValueError('Unknown supplied function: '+name)
  names=[a.arg for a in node.args.posonlyargs+node.args.args]
  if not len(names)-len(node.args.defaults)<=len(args)<=len(names) or self.depth>=12:raise ValueError('Argument count or call-depth limit reached')
  if len(args)<len(names):args=list(args)+[self.expression(v) for v in node.args.defaults[len(args)-(len(names)-len(node.args.defaults)):]]
  data_budget(args);previous=self.values;arguments=copy.deepcopy(args) if self.depth==0 else args;self.values=dict(zip(names,arguments));self.depth+=1
  try:
   try:self.block(node.body)
   except Returned as returned:return self.bounded(returned.value)
   return None
  finally:self.values=previous;self.depth-=1
 def expression(self,node):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in self.values:raise ValueError('Dynamic or shadowed local calls are outside this pure-function subset')
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='sorted' and node.keywords:
   if len(node.args)!=1 or len(node.keywords)!=1 or node.keywords[0].arg!='reverse':raise ValueError('Only sorted reverse keyword is supported')
   self.tick();value=self.expression(node.args[0]);reverse=self.expression(node.keywords[0].value)
   if type(reverse) is not bool:raise ValueError('Sorted reverse must be boolean')
   data_budget(value);return self.bounded(sorted(value,reverse=reverse))
  if isinstance(node,ast.Tuple):self.tick();return self.bounded(tuple(self.expression(v) for v in node.elts))
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='isinstance' and len(node.args)==2 and not node.keywords and isinstance(node.args[1],ast.Name):
   types={'list':list,'dict':dict,'str':str,'int':int,'float':float,'bool':bool};kind=types.get(node.args[1].id)
   if kind is None:raise ValueError('Unsupported type check')
   self.tick();return isinstance(self.expression(node.args[0]),kind)
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in self.functions and not node.keywords:return self.invoke(node.func.id,[self.expression(a) for a in node.args])
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
   self.tick();name=node.func.id;args=[self.expression(a) for a in node.args];data_budget(args)
   if name=='print':
    text=' '.join(str(a) for a in args)
    if sum(map(len,self.output))+len(text)>8192:raise ValueError('Output budget reached')
    self.output.append(text);return None
   functions={'abs':abs,'len':len,'min':min,'max':max,'sum':sum,'int':int,'float':float,'str':str,'bool':bool,'sorted':sorted,'range':range,'list':list,'tuple':tuple,'dict':dict,'enumerate':lambda *a:list(enumerate(*a)),'zip':lambda *a:list(zip(*a)),'reversed':lambda a:list(reversed(a)),'all':all,'any':any,'round':round}
   if name not in functions:raise ValueError('Function not available: '+name)
   result=functions[name](*args)
   if isinstance(result,range) and len(result)>4096:raise ValueError('Range value limit reached')
   return self.bounded(result)
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and not node.keywords:
   self.tick();value=self.expression(node.func.value);args=[self.expression(a) for a in node.args];name=node.func.attr
   if type(value) is str and name in ('strip','lower','upper','split','splitlines','replace','join','startswith','endswith','count','find','isalnum','isalpha','isdigit','isspace','casefold'):
    if name=='join' and (len(args)!=1 or not isinstance(args[0],list) or not all(type(x) is str for x in args[0]) or sum(map(len,args[0]))+len(value)*max(0,len(args[0])-1)>4096):raise ValueError('Join value limit reached')
    if name=='replace' and len(args)>=2 and all(type(x) is str for x in args[:2]) and len(value)+value.count(args[0])*len(args[1])>4096:raise ValueError('Replacement value limit reached')
    return self.bounded(getattr(value,name)(*args))
   if type(value) is list and name=='append' and len(args)==1:
    if len(value)>=4096:raise ValueError('List value limit reached')
    value.append(self.bounded(args[0]));return None
   if type(value) is dict and name=='get' and 1<=len(args)<=2:return self.bounded(value.get(*args))
   if type(value) is dict and name in ('items','keys','values') and not args:return self.bounded(list(getattr(value,name)()))
   if type(value) is list and name=='extend' and len(args)==1 and type(args[0]) in (list,tuple,range):
    if len(value)+len(args[0])>4096:raise ValueError('List value limit reached')
    data_budget(args);value.extend(args[0]);return None
   if type(value) is list and name=='pop' and len(args)<=1:return self.bounded(value.pop(*args))
   raise ValueError('Unsupported method: '+name)
  if isinstance(node,ast.ListComp) and len(node.generators)==1:
   self.tick();generator=node.generators[0]
   if generator.is_async:raise ValueError('Async comprehensions are unsupported')
   items=self.expression(generator.iter);previous=self.values.copy();out=[]
   try:
    for item in items:
     self.tick();self.bind(generator.target,item)
     if all(self.expression(condition) for condition in generator.ifs):out.append(self.expression(node.elt));self.bounded(out)
    return out
   finally:
    self.values=previous
  if isinstance(node,ast.Subscript) and isinstance(node.slice,ast.Slice):
   self.tick();s=node.slice;index=slice(*(self.expression(v) if v is not None else None for v in (s.lower,s.upper,s.step)));return self.bounded(self.expression(node.value)[index])
  return super().expression(node)
 def bind(self,target,value):
  self.tick()
  if isinstance(target,ast.Name):
   if target.id not in self.values and len(self.values)>=256:raise ValueError('Local variable limit reached')
   self.values[target.id]=self.bounded(value);return
  if isinstance(target,(ast.Tuple,ast.List)) and isinstance(value,(list,tuple)) and len(target.elts)==len(value):
   for child,item in zip(target.elts,value):self.bind(child,item)
   return
  raise ValueError('Use local names or matching tuple/list unpacking')
 def block(self,nodes):
  for node in nodes:
   if isinstance(node,ast.Raise):
    self.tick();exc=node.exc;args=[]
    if isinstance(exc,ast.Call) and isinstance(exc.func,ast.Name) and not exc.keywords:
     name=exc.func.id;args=exc.args
    elif isinstance(exc,ast.Name):name=exc.id
    else:raise ValueError('Only explicit named standard exceptions are supported')
    if node.cause is not None or name not in PROGRAM_ERRORS or name in self.values or name in self.functions or len(args)>1:raise ValueError('Unsupported or shadowed program exception')
    message=str(self.expression(args[0])) if args else ''
    raise ProgramRaised(name,message[:4000])
   if isinstance(node,ast.Assert):
    self.tick()
    if not self.expression(node.test):raise ProgramRaised('AssertionError',str(self.expression(node.msg))[:4000] if node.msg else '')
    continue
   if isinstance(node,ast.Return):self.tick();raise Returned(self.expression(node.value) if node.value is not None else None)
   if isinstance(node,ast.Break):self.tick();raise LoopBreak()
   elif isinstance(node,ast.Continue):self.tick();raise LoopContinue()
   elif isinstance(node,(ast.For,ast.While)):
    self.tick();broken=False
    iterable=iter(self.expression(node.iter)) if isinstance(node,ast.For) else None
    while True:
     self.tick()
     if iterable is not None:
      try:item=next(iterable)
      except StopIteration:break
      self.bind(node.target,item)
     elif not self.expression(node.test):break
     try:self.block(node.body)
     except LoopContinue:continue
     except LoopBreak:broken=True;break
    if not broken:self.block(node.orelse)
   elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],(ast.Tuple,ast.List)):
    self.bind(node.targets[0],self.expression(node.value))
   elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Subscript) and not isinstance(node.targets[0].slice,ast.Slice):
    self.tick();target=node.targets[0];container=self.expression(target.value);index=self.expression(target.slice);value=self.expression(node.value)
    if type(container) not in (dict,list):raise ValueError('Only local list/dictionary element assignment is supported')
    if type(container) is dict and index not in container and len(container)>=4096:raise ValueError('Dictionary value limit reached')
    container[index]=self.bounded(value)
   elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name):
    self.tick();expression=ast.BinOp(left=ast.Name(id=node.target.id,ctx=ast.Load()),op=node.op,right=node.value);self.values[node.target.id]=self.expression(expression)
   else:super().block([node])

def test_function(body):
 source=body.get('source');name=body.get('function');cases=body.get('cases')
 if not isinstance(source,str) or len(source)>16000 or not isinstance(name,str):raise ValueError('Provide source up to 16,000 characters and a function name')
 if not isinstance(cases,list) or not 1<=len(cases)<=24:raise ValueError('Provide 1 to 24 argument/expected cases')
 # Validate structure before evaluating any supplied expression.
 try:
  tested_source=isolated_source(source,name) if body.get('isolate_module') else source
  FunctionTest(tested_source)
 except (SyntaxError,ValueError) as exc:return {'status':'invalid-syntax' if isinstance(exc,SyntaxError) else 'unsupported-source','passed':0,'total':len(cases),'all_passed':False,'cases':[],'diagnostics':str(exc)[:500],'program_executed':False,'host_access':False,'source_sha256':hashlib.sha256(source.encode()).hexdigest()}
 rows=[];deadline=time.monotonic()+2
 for i,case in enumerate(cases):
  if not isinstance(case,dict) or not isinstance(case.get('args'),list) or ('expected' in case)==('raises' in case) or len(json.dumps(case,allow_nan=False))>8192:raise ValueError('Each case needs bounded JSON args and exactly one expected value or raises name')
  if 'raises' in case and (case['raises'] not in PROGRAM_ERRORS or not isinstance(case.get('message_contains',''),str) or len(case.get('message_contains',''))>500):raise ValueError('Use a supported standard exception and optional short message_contains')
  runner=FunctionTest(tested_source);runner.deadline=min(runner.deadline,deadline)
  try:
   actual=runner.invoke(name,case['args']);data_budget(actual);passed='expected' in case and equivalent(actual,case['expected']);rows.append({'case':i+1,'passed':passed,'actual':actual,'expected':case.get('expected'),'expected_exception':case.get('raises'),'steps':runner.steps})
  except ProgramRaised as exc:rows.append({'case':i+1,'passed':case.get('raises')==exc.name and case.get('message_contains','') in exc.message,'exception':exc.name,'message':exc.message,'expected_exception':case.get('raises'),'steps':runner.steps})
  except (ValueError,TypeError,IndexError,KeyError,ZeroDivisionError,OverflowError,RecursionError,RuntimeError,LoopBreak,LoopContinue) as exc:rows.append({'case':i+1,'passed':False,'error':type(exc).__name__+': '+str(exc)[:250],'steps':runner.steps})
 return {'passed':sum(r['passed'] for r in rows),'total':len(rows),'all_passed':all(r['passed'] for r in rows),'cases':rows,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'tested_function_sha256':hashlib.sha256(tested_source.encode()).hexdigest(),'isolated_module':bool(body.get('isolate_module')),'execution':'bounded in-memory AST function subset','host_access':False,'scope':'Checks supplied function examples, not full module behaviour. Imports, startup code, host commands, files and networking are not executed. External globals and imported helpers are not inferred.'}
