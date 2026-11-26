"""Link explicitly selected local pure helpers for bounded multi-file tests."""
import ast,copy,hashlib
from .function_testing import test_function

class Linker:
 def __init__(self,tools,folder):
  self.tools=tools;self.root=tools.path(folder);self.modules={};self.functions={};self.linked=[];self.bytes=0
  if not self.root.is_dir():raise ValueError('Choose an existing workspace project folder')
 def module(self,name):
  if name in self.modules:return self.modules[name]
  if len(self.modules)>=16:raise ValueError('Local module budget reached')
  relative=name.replace('.','/');paths=[self.root/(relative+'.py'),self.root/relative/'__init__.py']
  path=next((p for p in paths if p.is_file()),None)
  if path is None:raise ValueError('Missing local helper module: '+name)
  path=self.tools.path(str(path.relative_to(self.tools.root)))
  if not path.is_relative_to(self.root):raise ValueError('Helper must remain inside the selected project')
  row=self.tools.read({'path':str(path.relative_to(self.tools.root))});self.bytes+=len(row['text'].encode())
  if self.bytes>262144:raise ValueError('Project source byte budget reached')
  tree=ast.parse(row['text']);package=name if path.name=='__init__.py' else name.rpartition('.')[0];imports={};modules={};constants={};bound_names=set()
  for node in tree.body:
   if isinstance(node,ast.ImportFrom):
    if any(alias.name=='*' for alias in node.names):raise ValueError('Star imports cannot be resolved as a closed local function graph')
    parts=package.split('.') if package else []
    if node.level>len(parts)+1:raise ValueError('Relative import escapes the selected project')
    base='.'.join(parts[:len(parts)-node.level+1]) if node.level else ''
    target='.'.join(x for x in (base,node.module or '') if x)
    for alias in node.names:imports[alias.asname or alias.name]=(target,alias.name)
   elif isinstance(node,ast.Import):
    for alias in node.names:modules[alias.asname or alias.name.split('.')[0]]=alias.name if alias.asname else alias.name.split('.')[0]
   elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
    bound_names.add(node.targets[0].id);constants.pop(node.targets[0].id,None)
    try:value=ast.literal_eval(node.value)
    except (ValueError,TypeError,SyntaxError):continue
    if type(value) in (str,int,float,bool,type(None)):constants[node.targets[0].id]=value
   elif isinstance(node,ast.ClassDef):bound_names.add(node.name)
  result={'path':row['path'],'sha256':row['sha256'],'functions':{n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)},'imports':imports,'modules':modules,'constants':constants,'bound_names':bound_names};self.modules[name]=result;return result
 def function(self,module,name):
  key=(module,name)
  if key in self.functions:return self.functions[key]
  if len(self.functions)>=32:raise ValueError('Reachable helper-function budget reached')
  data=self.module(module)
  if name in data['bound_names']:raise ValueError('Selected helper name is rebound by module-level state: '+name)
  if name not in data['functions']:
   if name in data['imports']:return self.function(*data['imports'][name])
   raise ValueError('Local function was not found: '+module+'.'+name)
  node=copy.deepcopy(data['functions'][name]);new_name='linked_'+str(len(self.functions))+'_'+name;self.functions[key]=new_name
  locals_={a.arg for a in node.args.posonlyargs+node.args.args}|{n.id for n in ast.walk(node) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
  linker=self
  class Rewrite(ast.NodeTransformer):
   def visit_Name(self,n):
    if isinstance(n.ctx,ast.Load) and n.id not in locals_ and n.id in data['constants']:return ast.copy_location(ast.Constant(value=data['constants'][n.id]),n)
    if isinstance(n.ctx,ast.Load) and n.id not in locals_ and n.id in data['bound_names']:raise ValueError('Unresolved module-level state: '+n.id)
    return n
   def visit_Call(self,n):
    # Resolve statically named local helpers only; imported code is never run.
    if isinstance(n.func,ast.Name) and n.func.id not in locals_:
     called=n.func.id
     if called in data['functions']:n.func=ast.copy_location(ast.Name(id=linker.function(module,called),ctx=ast.Load()),n.func)
     elif called in data['imports']:n.func=ast.copy_location(ast.Name(id=linker.function(*data['imports'][called]),ctx=ast.Load()),n.func)
    elif isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id in data['modules'] and n.func.value.id not in locals_:
     n.func=ast.copy_location(ast.Name(id=linker.function(data['modules'][n.func.value.id],n.func.attr),ctx=ast.Load()),n.func)
    return self.generic_visit(n)
  node.name=new_name;node=Rewrite().visit(node);self.linked.append(ast.fix_missing_locations(node));return new_name

def test_project(tools,body):
 if not isinstance(body,dict) or not all(isinstance(body.get(k),str) for k in ('folder','module','function')):raise ValueError('Provide folder, module, function and argument/expected cases')
 if not body['module'] or any(not part.isidentifier() for part in body['module'].split('.')):raise ValueError('Use a dotted local module name')
 linker=Linker(tools,body['folder']);name=linker.function(body['module'],body['function']);source=ast.unparse(ast.Module(body=linker.linked,type_ignores=[]))+'\n'
 result=test_function({'source':source,'function':name,'cases':body.get('cases')})
 result.update(project_sources=[{'path':r['path'],'sha256':r['sha256']} for r in linker.modules.values()],linked_helpers=len(linker.functions),module_initialization_executed=False,source_files_changed=False,scope='Selected pure functions and statically resolved local helpers only. Module startup, imports, external packages, classes and dynamic dispatch are not executed. Passing cases is not full application validation.')
 return result
