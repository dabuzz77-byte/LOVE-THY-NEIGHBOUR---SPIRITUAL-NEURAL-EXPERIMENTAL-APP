"""App-owned source calls and revisioned AI workspace, using the retained call schema."""
import ast,hashlib,importlib,inspect,io,json,threading,time
from pathlib import Path
from .runtime import ROOT,clean
from .capture_output import redirect_stdout,redirect_stderr

class SourceWorkspace:
 def __init__(self,runtime,catalog):
  self.runtime=runtime;self.catalog=catalog
  with runtime.lock:
   if not hasattr(runtime,'source_call_lock'):runtime.source_call_lock=threading.Lock()
   self.lock=runtime.source_call_lock
 def record(self,ident):
  row=next((r for r in self.catalog['sources'] if str(r['id'])==str(ident)),None)
  if row is None:raise ValueError('Unknown source id')
  return row
 def host(self):
  if not hasattr(self.runtime,'component_host'):
   from .component_host import ComponentHost
   ComponentHost(self.runtime)
  return self.runtime.component_host
 def active(self,row):
  host=self.host();source=Path(row['path']);app=source.parts[0]
  for panel in host.panels:
   if panel['id'] in host.python.index and Path(panel['entry']).parts[0]==app:
    entry=host.python.index[panel['id']];package=entry['package'];base=ROOT/Path(package.replace('.','/'));target=base/Path(*source.parts[1:])
    if target.is_file():return target,package+'.'+'.'.join(source.parts[1:]).removesuffix('.py')
  for panel in host.panels:
   if panel['id'] in host.java_index and Path(panel['entry']).parts[0]==app:
    family=host.java_index[panel['id']]['family'];target=ROOT/'neural_app'/'java_library'/family/'src'/Path(*source.parts[1:])
    if target.is_file():return target,None
  return None,None
 def read(self,ident,offset=0):
  row=self.record(ident);active,_=self.active(row);path=active or ROOT/'preserved'/'sources'/row['path'];raw=path.read_bytes();text=raw.decode('utf-8-sig',errors='replace')
  from nexus_conversations import scrub
  return {'id':row['id'],'path':row['path'],'active_path':str(path.relative_to(ROOT)) if active else None,'sha256':hashlib.sha256(raw).hexdigest(),'offset':offset,'total_characters':len(text),'text':scrub(text[offset:offset+12000]),'scope':'Active integrated source; edits require an app restart' if active else 'Preserved read-only source reference'}
 def edit(self,b):
  with self.runtime.lock:return self._edit(b)
 def _edit(self,b):
  row=self.record(b.get('id'));path,_=self.active(row)
  if path is None:raise ValueError('This entry is a preserved reference; choose an active integrated source')
  text=b.get('text')
  if not isinstance(text,str) or len(text)>250000:raise ValueError('Provide complete source text, up to 250,000 characters')
  raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
  if b.get('expected_sha256')!=digest:raise ValueError('Read the active source again and supply its current sha256')
  if path.suffix=='.py':ast.parse(text,str(path))
  folder=self.runtime.data/'ai-revisions';folder.mkdir(exist_ok=True);backup=folder/(str(time.time_ns())+'-'+path.name);backup.write_bytes(raw)
  temporary=path.with_name(path.name+'.neural-tmp');temporary.write_text(text,encoding='utf8');temporary.replace(path)
  return {'ok':True,'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'backup':str(backup),'note':'Active code saved. Restart Neural App to load changed Python code; For Java, close the app, run Rebuild Java sections.cmd, then reopen it. Preserved originals were not changed.'}
 def execute(self,b):
  row=self.record(b.get('id'));host=self.host()
  if b.get('mode')=='script':
   panel=next((p for p in host.panels if str(p['entry']).replace('\\','/')==row['path'] or p['kind'].startswith('java') and row['path'].startswith(str(p['entry']).replace('\\','/')+'/') and Path(row['path']).stem==p.get('main','').split('.')[-1]),None)
   if panel is None and row['language']=='JavaScript':
    panel=next((p for p in host.panels if p['kind']=='node' and row['path'].startswith(str(p['entry']).replace('\\','/')+'/') and Path(row['path']).name in ('server.js','app.js','index.js','main.js')),None)
   if panel:
    host.open(panel['id']);return {'ok':True,'result':{'navigate':panel['id'],'shared_process':True},'summary':'Opened built-in '+panel['name']}
  if row['language']!='Python':
   if b.get('mode')!='script':raise ValueError('Call plans are for Python; choose script mode for native source')
   return self.script(row,b)
  path,name=self.active(row)
  if b.get('mode')=='script':
   rt=host.adapter('observatory')[2]['controller']
   for ident,definition in rt.modules.items():
    if row['path'].endswith('/'+definition['file']):
     rt.run_module(ident);return {'ok':True,'result':rt.results.get(ident),'source':row['path'],'shared_process':True}
   return self.script(row,b)
  if path is None:raise ValueError('Choose an active integrated Python source')
  if not self.lock.acquire(False):raise ValueError('A source call is already running')
  class Limited(io.StringIO):
   def write(self,value):
    if self.tell()+len(value)>100000:raise ValueError('Output exceeded 100,000 characters')
    return super().write(value)
  out=Limited()
  try:
   with redirect_stdout(out),redirect_stderr(out):
    module=importlib.import_module(name)
    if b.get('mode')=='script':
     # Original catalogue computations have their own shared, bounded adapter.
     for ident,definition in host.adapter('observatory')[2]['controller'].modules.items():
      if row['path'].endswith('/'+definition['file']):
       rt=host.adapter('observatory')[2]['controller'];rt.run_module(ident);result=rt.results.get(ident);break
     else:raise ValueError('Choose a declared public class/function call plan for this library')
    else:
     target_name=b.get('target','');declared={n.name for n in ast.parse(path.read_text(encoding='utf-8-sig')).body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and not n.name.startswith('_')}
     if target_name not in declared:raise ValueError('Choose a declared public class or function')
     target=getattr(module,target_name)(**b.get('init',{}));calls=b.get('calls',[]);result=[]
     for call in calls:
      method=call['method']
      if method.startswith('_'):raise ValueError('Choose a public method')
      result.append({'method':method,'result':getattr(target,method)(**call.get('args',{}))})
     if not calls:result=target if isinstance(target,(dict,list,str,int,float,bool,type(None))) else {k:v for k,v in vars(target).items() if not k.startswith('_') and isinstance(v,(dict,list,str,int,float,bool,type(None)))}
   response={'ok':True,'result':clean(result),'stdout':out.getvalue(),'source':row['path'],'shared_process':True}
  except Exception as error:response={'ok':False,'error':type(error).__name__+': '+str(error),'stdout':out.getvalue(),'source':row['path'],'shared_process':True}
  finally:self.lock.release()
  response['receipt']=self.runtime.component_result('source-workbench',{'id':row['id'],'target':b.get('target')},response);return response
 def script(self,row,b):
  import sys,shutil
  host=self.host();services=host.services_instance();path,name=self.active(row);path=path or ROOT/'preserved'/'sources'/row['path'];language=row['language'];args=b.get('args',[])
  if not isinstance(args,list) or len(args)>20 or not all(isinstance(x,str) and len(x)<2000 for x in args):raise ValueError('Use up to 20 text arguments')
  if language=='Python':
   code="import sys,runpy;sys.path[:0]="+repr([str(ROOT),str(ROOT/'runtime')])+";sys.argv="+repr([str(path),*args])+";runpy.run_module("+repr(name)+",run_name='__main__')" if name else "import runpy;runpy.run_path("+repr(str(path))+",run_name='__main__')"
   interpreter=Path(sys.executable).with_name('python.exe');command=[str(interpreter if interpreter.is_file() else Path(sys.executable)),'-c',code]
  elif language=='Java':
   candidates=sorted(Path('C:/Program Files/Java').glob('jdk-*/bin/java.exe'),reverse=True)
   if not candidates:raise ValueError('Java runtime was not found')
   libraries=[str(ROOT/'neural_app'/'java_library'/'common')]+[str(p) for p in (ROOT/'neural_app'/'java_library').glob('family_*/classes')]
   command=[str(candidates[0]),'-Djava.awt.headless=true','--class-path',';'.join(libraries),str(path),*args]
  else:
   executable=shutil.which('node')
   if not executable:raise ValueError('JavaScript runtime was not found')
   command=[executable,str(path),*args]
  def quote(value):return "'"+str(value).replace("'","''")+"'"
  done=threading.Event();response={'ok':False,'stdout':'','stderr':'','source':row['path'],'experimental_job':True}
  def observe(kind,event):
   if event['state']=='output':
    field='stderr' if event.get('type')=='stderr' else 'stdout';response[field]=(response[field]+event.get('text',''))[-32000:]
   elif event['state']=='end':response.update(ok=event.get('code')==0,exit_code=event.get('code'));services.command_observers.pop(event['id'],None);done.set()
  with services.event_lock:
   job=services.console.start('& '+' '.join(quote(v) for v in command),timeout=20)['id'];services.command_observers[job]=observe
  if not done.wait(25):
   try:services.console.cancel(job)
   except ValueError:pass
   response['error']='Source job exceeded its 20-second execution limit'
  response['receipt']=self.runtime.component_result('source-workbench',{'id':row['id'],'mode':'script'},response);return response
 def workflow(self,b):
  steps=b.get('steps',[])
  if not isinstance(steps,list) or not 1<=len(steps)<=12:raise ValueError('Choose 1–12 workflow steps')
  context={'input':b.get('input',{}),'previous':None,'steps':[]};results=[]
  def resolve(value):
   if isinstance(value,str) and value.startswith('$'):
    current=context
    for key in value[1:].split('.'):current=current[int(key)] if isinstance(current,list) else current[key]
    return current
   if isinstance(value,dict):return {k:resolve(v) for k,v in value.items()}
   if isinstance(value,list):return [resolve(v) for v in value]
   return value
  for step in steps:
   result=self.execute(resolve(step));results.append(result);context['previous']=result.get('result');context['steps'].append(result)
   if not result.get('ok'):break
  response={'ok':len(results)==len(steps) and all(r.get('ok') for r in results),'results':results,'summary':str(len(results))+' of '+str(len(steps))+' source steps attempted'};response['receipt']=self.runtime.component_result('workflow',{},response);return response
