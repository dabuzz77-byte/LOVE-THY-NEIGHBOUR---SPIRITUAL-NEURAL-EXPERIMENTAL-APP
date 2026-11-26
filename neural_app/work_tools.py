"""Revisioned local work files and explicitly reviewed PC commands for the work assistant."""
import hashlib,json,os,platform,shutil,subprocess,tempfile,time
from pathlib import Path
MODEL='hf.co/larped/llama3.2_1b_2025_uncensored_v2-Q3_K_M-GGUF:Q3_K_M'
class WorkTools:
 def __init__(self,runtime):
  self.runtime=runtime;self.root=(runtime.data/'talk-work/workspace').resolve();self.root.mkdir(parents=True,exist_ok=True);self.revisions=runtime.data/'talk-work/revisions';self.revisions.mkdir(parents=True,exist_ok=True)
  for name in ('graphics','audio','music','video','code','exports'):(self.root/name).mkdir(exist_ok=True)
 def path(self,name):
  name=str(name or '')
  if not name or Path(name).is_absolute():raise ValueError('Use a workspace-relative file path.')
  p=(self.root/name).resolve()
  if not p.is_relative_to(self.root) or p==self.root:raise ValueError('Path must stay inside the work workspace.')
  return p
 def view(self):
  files=[]
  for p in self.root.rglob('*'):
   if len(files)>=200:break
   if p.is_file() and p.resolve().is_relative_to(self.root):files.append({'path':str(p.relative_to(self.root)),'bytes':p.stat().st_size})
  return {'model':MODEL,'workspace':str(self.root),'files':files,'system':{'os':platform.platform(),'cpu_count':os.cpu_count(),'python':shutil.which('python'),'java':shutil.which('java'),'powershell':shutil.which('powershell')},'capabilities':['workspace list/read/write with revisions','app engines / source workbench','learning memory and public references','reviewed external reads / public web research','reviewed PowerShell commands','selected-window desktop controls'],'command_policy':'Commands require per-action review; the model cannot approve itself.'}
 def read(self,body):
  p=self.path(body.get('path'));size=p.stat().st_size
  if size>131072:raise ValueError('Read files up to 128 KiB.')
  raw=p.read_bytes();return {'path':str(p.relative_to(self.root)),'text':raw.decode('utf-8-sig'),'sha256':hashlib.sha256(raw).hexdigest()}
 def write(self,body):
  p=self.path(body.get('path'));text=body.get('text','')
  if not isinstance(text,str) or len(text.encode())>250000:raise ValueError('Use UTF-8 text below 250 KB.')
  old=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
  if old and body.get('expected_sha256')!=old:raise ValueError('Read the existing file and supply its expected_sha256 before replacing it.')
  if p.exists():(self.revisions/(str(time.time_ns())+'-'+p.name)).write_bytes(p.read_bytes())
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode('utf-8'));return {'written':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'revision_saved':old is not None}
 def command(self,body,cancelled=lambda:False):
  command=str(body.get('command',''));timeout=max(1,min(60,int(body.get('timeout',30))))
  if not command.strip() or len(command)>12000:raise ValueError('Use a command below 12,000 characters.')
  cwd=Path(str(body.get('cwd') or self.root)).resolve()
  if not cwd.is_dir():raise ValueError('Working directory is unavailable.')
  interpreter=str(body.get('shell','powershell'))
  if interpreter not in ('powershell','cmd'):raise ValueError('Choose powershell or cmd')
  shell=shutil.which('cmd') if interpreter=='cmd' else (shutil.which('powershell') or shutil.which('pwsh'))
  if not shell:raise ValueError('Requested interpreter is unavailable.')
  args=[shell,'-NoProfile','-NonInteractive','-Command',command]
  if interpreter=='cmd':
   script=self.revisions/('approved-'+str(time.time_ns())+'.cmd');script.write_text('@echo off\n'+command+'\n',encoding='utf-8');args=[shell,'/d','/c',str(script)]
  output=self.revisions/('command-'+str(time.time_ns())+'.txt');flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
  with output.open('wb') as stream:
   process=subprocess.Popen(args,cwd=cwd,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,creationflags=flags)
   start=time.monotonic();reason=None
   while process.poll() is None:
    if cancelled() or time.monotonic()-start>timeout or output.stat().st_size>2000000:reason='cancelled or time/output limit reached';subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,timeout=5) if os.name=='nt' else process.kill();break
    time.sleep(.1)
   process.wait(timeout=5)
  raw=output.read_bytes()[:64000];return {'exit_code':process.returncode,'output':raw.decode('utf-8',errors='replace'),'truncated':output.stat().st_size>64000,'limit':reason,'cwd':str(cwd),'executed':True,'receipt_file':str(output)}
 def write_external(self,body):
  raw_name=str(body.get('path',''));p=Path(raw_name).expanduser()
  if not p.is_absolute() or raw_name.startswith(('\\\\','//')):raise ValueError('Choose an absolute local file path')
  p=p.resolve()
  if any(part.lower() in ('.ssh','.aws','cookies','credentials','browser-profile','desktop-profile') for part in p.parts) or any(word in p.name.lower() for word in ('password','credential','providers.json','secret','token')):raise PermissionError('Credential stores are excluded')
  text=body.get('text')
  if not isinstance(text,str) or len(text.encode('utf-8'))>250000:raise ValueError('Use UTF-8 text below 250 KB')
  old=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None
  if p.exists() and not p.is_file():raise ValueError('Destination is not a file')
  if old and body.get('expected_sha256')!=old:raise ValueError('Read the file and supply its current expected_sha256 before replacement')
  if old:(self.revisions/(str(time.time_ns())+'-external-'+p.name)).write_bytes(p.read_bytes())
  p.parent.mkdir(parents=True,exist_ok=True)
  descriptor,temporary=tempfile.mkstemp(prefix='neural-write-',suffix='.tmp',dir=p.parent)
  try:
   with os.fdopen(descriptor,'wb') as stream:stream.write(text.encode('utf-8'));stream.flush();os.fsync(stream.fileno())
   os.replace(temporary,p)
  finally:
   if os.path.exists(temporary):os.unlink(temporary)
  return {'written':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'revision_saved':old is not None}
