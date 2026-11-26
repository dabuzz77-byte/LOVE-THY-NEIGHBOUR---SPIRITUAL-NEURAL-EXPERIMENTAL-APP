"""Original launch controls open built-in sections instead of separate apps."""
from pathlib import Path
from . import component_ui as ui

def open_path(runtime,path):
 host=runtime.component_host;normal=Path(path).as_posix().lower()
 for panel in host.panels:
  entry=str(panel['entry']).replace('\\','/').lower()
  directory=entry.split('/')[0]
  if normal.endswith('/'+entry) or normal.endswith('/'+directory) or normal.endswith('/'+directory+'/'+directory+'.exe') or ('/'+entry+'/') in normal:
   host.python.navigation=panel['id'];return {'navigate':panel['id'],'shared_process':True}
 if 'fluxbus-v2' in normal:host.python.navigation='flux';return {'navigate':'flux','shared_process':True}
 if 'postscarcity observatory' in normal:host.python.navigation='observatory';return {'navigate':'observatory','shared_process':True}
 raise ValueError('Select one of the 45 built-in sections. Custom commands are available in the common command console.')

def install(module,ident,runtime):
 if ident=='hydrogen':
  module.Runtime.launch=lambda self,item:open_path(runtime,item['path'])
  def external(self,which):return open_path(runtime,'/FluxBus-v2' if which=='flux' else '/Postscarcity Observatory v4')
  module.App.launch_external=external
 if ident=='dualrail':
  module.PostscarcityObservatoryV4.open_observatory=lambda self:open_path(runtime,'/Postscarcity Observatory v4')
 if ident=='atelier':
  from .runtime import ROOT
  module.APPS=ROOT/'preserved'/'sources'
  def open_app(self):
   selection=self.appslist.curselection()
   if selection:return open_path(runtime,self.apps[selection[0]])
  def add_worker(self,path=None):
   path=path or ui.filedialog.askopenfilename(title='Select a worker')
   if not path:return
   if Path(path).name=='feedback_worker.py':self.shared_feedback=True;self.log('WORKER','Feedback oscillator connected to the shared field');return
   try:return open_path(runtime,path)
   except ValueError:pass
   import hashlib,math,sys
   path=Path(path).resolve()
   if not path.is_file() or path.suffix.lower()!='.py':raise ValueError('Select a Python worker file')
   services=runtime.component_host.services_instance()
   def quote(value):return "'"+str(value).replace("'","''")+"'"
   def observe(kind,event):
    if event['state']=='output':
     text=event.get('text','');self.log('WORKER',text[-2000:])
     try:value=float(text.strip().splitlines()[-1]);signal=math.tanh(value) if math.isfinite(value) else 0
     except (ValueError,IndexError):signal=int.from_bytes(hashlib.blake2s(text.encode(),digest_size=4).digest(),'big')/(2**32-1)*2-1
     with self.engine.lock:self.engine.script_signal=.8*self.engine.script_signal+.2*signal;self.engine.script_at=__import__('time').monotonic();self.engine.script_samples+=1
    elif event['state']=='end':services.command_observers.pop(event['id'],None);self.shared_command=None
   with services.event_lock:
    job=services.console.start('& '+quote(sys.executable)+' '+quote(path))['id'];self.shared_command=job;services.command_observers[job]=observe
   self.log('WORKER','Worker connected through the common command runner');return {'id':job}
  def stop_workers(self):
   self.shared_feedback=False
   if vars(self).get('shared_command'):
    try:runtime.component_host.services_instance().console.cancel(self.shared_command)
    except ValueError:pass
    self.shared_command=None
   self.log('WORKER','Shared workers stopped')
  module.App.open_app=open_app;module.App.add_worker=add_worker;module.App.stop_workers=stop_workers
