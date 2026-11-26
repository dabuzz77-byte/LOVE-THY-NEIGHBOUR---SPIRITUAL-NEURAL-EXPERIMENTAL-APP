"""Map original script-launch controls to sections or the approved command runner."""
import hashlib,os,sys,time,uuid
from pathlib import Path

def install(host,module):
 def script_run(ident):
  item=next((r for r in module.registry if r['id']==ident),None)
  if item is None:raise ValueError('Choose a scanned source file')
  path=Path(item['path']);path=(path if path.is_absolute() else module.APPS/path).resolve()
  if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Source changed; rescan before running')
  normal=path.as_posix().lower()
  for panel in host.panels:
   entry=str(panel['entry']).replace('\\','/').lower()
   main=panel.get('main','').split('.')[-1]
   exact=normal.endswith('/'+entry)
   java_main=panel['kind'].startswith('java') and ('/'+entry+'/') in normal and path.stem==main
   if exact or java_main:
    host.open(panel['id']);result={'id':ident,'status':'complete','output':'Opened the built-in '+panel['name']+' section.','navigate':panel['id'],'shared_process':True};module.runs[ident]=result;return result
  _,_,obs=host.adapter('observatory');rt=obs['controller']
  for name,definition in rt.modules.items():
   if normal.endswith('/postscarcity observatory v4/'+definition['file'].lower()):
    rt.schedule(name);result={'id':ident,'status':'queued','output':'Queued the original calculation in the shared runtime.','module':name,'navigate':'observatory','shared_process':True};module.runs[ident]=result;return result
  services=host.services_instance()
  if path.suffix.lower()=='.py':
   interpreter=Path(sys.executable).with_name('python.exe');executable=interpreter if interpreter.is_file() else Path(sys.executable)
  elif path.suffix.lower()=='.java':
   candidates=sorted(Path('C:/Program Files/Java').glob('jdk-*/bin/java.exe'),reverse=True)
   if not candidates:raise ValueError('Java runtime was not found')
   executable=candidates[0]
  else:raise ValueError('Choose a Python or Java source file')
  def quoted(value):return "'"+str(value).replace("'","''")+"'"
  result={'id':ident,'status':'running','started':time.time(),'path':str(path),'output':''};module.runs[ident]=result
  def observe(kind,event):
   if kind!='command' or event['id']!=job:return
   if event['state']=='output':result['output']=(result['output']+event.get('text',''))[-100000:]
   elif event['state']=='end':
    result.update(status='complete' if event.get('code')==0 else 'error',exit_code=event.get('code'),receipt=event.get('receipt'));services.command_observers.pop(job,None)
  with services.event_lock:
   job=services.console.start('& '+quoted(executable)+' '+quoted(path))['id'];result['command_id']=job
   services.command_observers[job]=observe
  return result
 module.script_run=script_run
 def shutdown():
  module.autonomous.configure({'enabled':False,'web_enabled':False});module.prompt_loop.update({'enabled':False});module.native_research.configure({'enabled':False});return {'status':'stopped','scope':'Inference section; shared app remains active'}
 return shutdown
