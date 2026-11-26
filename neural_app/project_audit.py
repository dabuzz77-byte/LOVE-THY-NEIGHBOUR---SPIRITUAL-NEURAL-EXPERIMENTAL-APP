"""Read-only multi-file Python project structure and local dependency audit."""
import ast,hashlib,os,time

def audit(tools,folder='code'):
 root=tools.path(folder)
 if not root.is_dir():raise ValueError('Choose an existing workspace project directory')
 modules={};files=[];skipped=[];deadline=time.monotonic()+3
 for parent,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if d not in ('.git','.venv','venv','node_modules','__pycache__') and not (root/str(os.path.relpath(parent,root))/d).is_symlink())
  for name in sorted(names):
   if not name.endswith('.py'):continue
   if time.monotonic()>deadline or len(files)>=64:skipped.append('File/time budget reached');break
   from pathlib import Path
   path=Path(parent)/name
   if path.is_symlink():skipped.append(str(path.relative_to(root)));continue
   path=tools.path(str(path.relative_to(tools.root)))
   if path.stat().st_size>65536:skipped.append(str(path.relative_to(root)));continue
   raw=path.read_bytes();relative=str(path.relative_to(root)).replace('\\','/');module=relative[:-3].replace('/','.')
   if module.endswith('.__init__'):module=module[:-9]
   elif module=='__init__':module=''
   row={'path':str(path.relative_to(tools.root)),'module':module,'sha256':hashlib.sha256(raw).hexdigest(),'imports':[],'functions':[],'tests':[],'diagnostics':[]}
   try:
    tree=ast.parse(raw.decode('utf-8-sig'));compile(tree,relative,'exec')
    row['functions']=[{'name':n.name,'line':n.lineno,'parameters':[a.arg for a in n.args.posonlyargs+n.args.args],'async':isinstance(n,ast.AsyncFunctionDef)} for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    row['tests']=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')][:80]
    for n in ast.walk(tree):
     if isinstance(n,ast.Import):row['imports'] += [{'module':a.name,'level':0,'names':[],'line':n.lineno} for a in n.names]
     elif isinstance(n,ast.ImportFrom):row['imports'].append({'module':n.module or '','level':n.level,'names':[a.name for a in n.names],'line':n.lineno})
    row['syntax_passed']=True
   except (SyntaxError,UnicodeError,ValueError,RecursionError) as e:row.update(syntax_passed=False);row['diagnostics'].append(str(e)[:400])
   modules[module]=row;files.append(row)
  if skipped and skipped[-1]=='File/time budget reached':break
 edges=[];issues=[]
 for row in files:
  package=row['module'] if row['path'].replace('\\','/').endswith('/__init__.py') else row['module'].rpartition('.')[0]
  for item in row['imports']:
   if item['level']:
    parts=package.split('.') if package else [];level=item['level']
    if level>max(1,len(parts)):issues.append({'path':row['path'],'line':item['line'],'kind':'relative-import-above-project-package','module':item['module']});continue
    base='.'.join(parts[:len(parts)-level+1]);target='.'.join(p for p in (base,item['module']) if p)
   else:target=item['module']
   candidates=[target]+[target+'.'+n if target else n for n in item['names']]
   local=[v for v in candidates if v in modules]
   for dest in local:edges.append({'from':row['module'],'to':dest,'line':item['line']})
   if item['level'] and not local:issues.append({'path':row['path'],'line':item['line'],'kind':'unresolved-local-import','module':target})
 adjacency={name:set() for name in modules}
 for edge in edges:adjacency[edge['from']].add(edge['to'])
 # A bounded DFS reports back edges; cycles are warnings, not automatic defects.
 state={};cycles=[]
 def visit(name,trail):
  state[name]=1
  for dest in sorted(adjacency[name]):
   if state.get(dest)==1:cycles.append(trail[trail.index(dest):]+[dest])
   elif state.get(dest,0)==0:visit(dest,trail+[dest])
  state[name]=2
 for name in sorted(adjacency):
  if not state.get(name):visit(name,[name])
 return {'files':files,'local_dependency_edges':edges,'local_import_issues':issues,'cycle_warnings':cycles[:32],'skipped':skipped,'syntax_passed':bool(files) and all(r['syntax_passed'] for r in files),'test_definitions':sum(len(r['tests']) for r in files),'program_executed':False,'scope':'Bounded static Python structure. Imports and tests are not executed; external dependency availability and dynamic imports are not inferred. A missing relative import may refer to a compiled extension or omitted file. Cycles can be intentional.'}
