"""User-approved local PowerShell runner with the original Matrix limits."""
import codecs,base64,collections,hashlib,os,subprocess,threading,time,uuid
from pathlib import Path
from .runtime import ROOT

class CommandConsole:
 def __init__(self,runtime,publish,timeout=120,output_limit=1024*1024):
  self.runtime=runtime;self.publish=publish;self.timeout=timeout;self.output_limit=output_limit;self.lock=threading.RLock();self.active=None;self.closed=False;self.completed=collections.OrderedDict()
 def session(self):
  with self.lock:
   job=self.active
   return {'cwd':str(ROOT),'shell':'Windows PowerShell','commandsTimeout':self.timeout,'activeCommand':{'id':job['id'],'command':job['command']} if job else None}
 def start(self,command,timeout=None):
  if not isinstance(command,str) or not command.strip() or len(command)>8000:raise ValueError('Enter a command (maximum 8,000 characters).')
  with self.lock:
   if self.closed:raise ValueError('Console is closed')
   if self.active:raise ValueError('A command is already running. Stop it before starting another.')
   job={'id':uuid.uuid4().hex,'command':command.strip(),'bytes':0,'started':time.monotonic(),'process':None,'cancelled':False,'limited':False}
   job['timeout']=self.timeout if timeout is None else timeout
   self.active=job;self.publish('command',{'id':job['id'],'state':'start','command':job['command']})
   threading.Thread(target=self._run,args=(job,),name='neural-console-command',daemon=True).start()
   return {'id':job['id'],'ok':True}
 def _output(self,job,kind,data,decoder):
  with self.lock:
   room=max(0,self.output_limit-job['bytes']);chunk=data[:room];job['bytes']+=len(chunk)
   if chunk:self.publish('command',{'id':job['id'],'state':'output','type':kind,'text':decoder.decode(chunk)})
   over=len(data)>room and not job['limited'];job['limited']=job['limited'] or over
  if over:
   self.publish('command',{'id':job['id'],'state':'output','type':'stderr','text':'\nOutput limit reached; stopping command.\n'});self._kill(job)
 def _kill(self,job):
  with self.lock:job['cancelled']=True;process=job['process']
  if process is None or process.poll() is not None:return
  try:
   subprocess.run([str(Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'taskkill.exe'),'/PID',str(process.pid),'/T','/F'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  except (OSError,subprocess.TimeoutExpired):pass
  if process.poll() is None:
   try:process.kill()
   except OSError:pass
 def cancel(self,ident=None):
  with self.lock:job=self.active
  if not job or ident is not None and ident!=job['id']:raise ValueError('Command has already finished.')
  self._kill(job);return {'ok':True}
 def _run(self,job):
  code=-1;timer=None;readers=[]
  try:
   executable=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
   script="[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n$ErrorActionPreference = 'Stop'\ntry {\n"+job['command']+"\nif (-not $?) { exit 1 }; if ($null -ne $LASTEXITCODE) { exit $LASTEXITCODE }\n} catch { [Console]::Error.WriteLine($_.ToString()); exit 1 }"
   encoded=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
   process=subprocess.Popen([str(executable),'-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',encoded],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
   with self.lock:job['process']=process;cancelled=job['cancelled']
   if cancelled:self._kill(job)
   def read(stream,kind):
    decoder=codecs.getincrementaldecoder('utf8')('replace')
    try:
     while True:
      block=stream.read1(4096)
      if not block:break
      self._output(job,kind,block,decoder)
    finally:stream.close()
   for stream,kind in ((process.stdout,'stdout'),(process.stderr,'stderr')):
    thread=threading.Thread(target=read,args=(stream,kind),name='neural-console-'+kind,daemon=True);thread.start();readers.append(thread)
   def expire():
    self.publish('command',{'id':job['id'],'state':'output','type':'stderr','text':'\nTwo-minute limit reached; stopping command.\n'});self._kill(job)
   timer=threading.Timer(job['timeout'],expire);timer.daemon=True;timer.start();code=process.wait()
   for thread in readers:thread.join(3)
  except Exception as error:self.publish('command',{'id':job['id'],'state':'output','type':'stderr','text':str(error)})
  finally:
   if timer:timer.cancel()
   result={'status':'COMPLETE' if code==0 else 'ERROR','exit_code':code,'output_bytes':job['bytes'],'duration_ms':(time.monotonic()-job['started'])*1000,'cancelled':job['cancelled'],'output_limited':job['limited']}
   try:result['receipt']=self.runtime.component_result('matrix',{'command_sha256':hashlib.sha256(job['command'].encode()).hexdigest()},result)
   except Exception:pass
   with self.lock:
    self.completed[job['id']]=result
    while len(self.completed)>20:self.completed.popitem(last=False)
    if self.active is job:self.active=None
   self.publish('command',{'id':job['id'],'state':'end','code':code,'receipt':result.get('receipt')})
 def close(self):
  with self.lock:self.closed=True;job=self.active
  if job:self._kill(job)
