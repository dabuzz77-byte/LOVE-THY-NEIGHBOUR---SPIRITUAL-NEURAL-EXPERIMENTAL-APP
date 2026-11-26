"""OS capability learning from supported diagnostics and system-file metadata."""
import os,shutil,time
from pathlib import Path
class OSLearning:
 def __init__(self,reasoner):self.r=reasoner;self.sequence=0;self.last=0;self.current={};self.error=None
 def sample(self,force=False):
  if not force and time.monotonic()-self.last<30:return self.current
  self.last=time.monotonic();self.sequence+=1
  from .system_access import SystemAccess
  tools={name:shutil.which(name) for name in ('python','java','javac','node','powershell','pwsh','cmd','bash','dotnet','ffmpeg')};files=[]
  system=Path(os.environ.get('SystemRoot','C:/Windows'))/'System32'
  try:
   names=sorted(p for p in system.iterdir() if p.is_file() and not p.is_symlink());start=((self.sequence-1)*96)%max(1,len(names))
   for p in names[start:start+96]:
    try:st=p.stat();files.append({'name':p.name,'extension':p.suffix,'bytes':st.st_size,'modified':st.st_mtime})
    except OSError:pass
  except OSError as e:self.error=str(e)[:180]
  self.current={'sequence':self.sequence,'time':time.time(),'tools':tools,'diagnostics':SystemAccess(self.r.runtime).view(),'system_metadata':files,'scope':'Read-only OS-supported capabilities and rotating System32 filename/size metadata; no private-document contents, credentials or command lines','error':self.error}
  with self.r.lock:self.r.s['os_learning']=self.current
  self.r.bus.publish({'origin':'os-learning','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'tools':{k:bool(v) for k,v in tools.items()},'system_metadata':files,'provenance':'observed-os-capabilities','stochastic':False,'bridge_direction':'all'}})
  return self.current
