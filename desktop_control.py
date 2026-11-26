"""Selected-window UI Automation with explicit action review, for local Llama."""
import json,subprocess,threading,time,uuid
from pathlib import Path
class DesktopControl:
 def __init__(self,root):self.root=Path(root);self.pending={};self.lock=threading.RLock()
 def call(self,b):
  result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(self.root/'desktop_control.ps1')],input=json.dumps(b),capture_output=True,text=True,timeout=35,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  try:data=json.loads(result.stdout.lstrip('\ufeff'))
  except ValueError:raise ValueError('Windows control inspection was unavailable; select a standard desktop app')
  if data.get('ok') is False:raise ValueError(data.get('error','Desktop operation failed'))
  return data
 def windows(self):return self.call({'op':'windows'})
 def read(self,target):return self.call({'op':'read',**target})
 def propose(self,job,request):
  if request.get('action') not in ('click','invoke','set_text','scroll','focus'):raise ValueError('Supported desktop actions: click, invoke, set_text, scroll, focus')
  ident=uuid.uuid4().hex;pending={'id':ident,'target':job['desktop_target'],'action':request['action'],'control':str(request.get('control','')),'text':str(request.get('text',''))[:12000],'direction':request.get('direction','down'),'reason':str(request.get('reason',''))[:1000],'status':'awaiting-review'}
  with self.lock:self.pending[ident]=pending;job['desktop_pending']=pending
  deadline=time.monotonic()+180
  while time.monotonic()<deadline:
   if job.get('status')!='running' or not job.get('desktop_access'):
    pending['status']='cancelled';raise ValueError('Desktop access was stopped')
   if pending['status']=='approved':
    result=self.call({'op':pending['action'],**pending['target'],'control':pending['control'],'text':pending['text'],'direction':pending['direction'],'reviewed':True});pending['status']='complete';return result
   if pending['status']=='rejected':raise ValueError('User declined this desktop action')
   time.sleep(.2)
  pending['status']='expired';raise ValueError('Desktop action review expired')
 def review(self,b):
  with self.lock:
   pending=self.pending.get(b.get('id'))
   if not pending or pending['status']!='awaiting-review':raise ValueError('Desktop action is no longer pending')
   pending['status']='approved' if b.get('approve') else 'rejected'
  return {'ok':True,'status':pending['status']}
