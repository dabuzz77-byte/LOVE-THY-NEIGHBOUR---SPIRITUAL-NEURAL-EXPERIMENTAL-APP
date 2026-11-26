"""Genesis generation and Matrix telemetry on the shared HTTP boundary."""
import json,os,platform,socket,time,uuid,urllib.request,threading,collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import psutil
from .runtime import ROOT,clean

class Services:
 def __init__(self,runtime):
  self.runtime=runtime;self.started=time.monotonic();self.events=collections.deque(maxlen=256);self.previous=None;self.event_lock=threading.RLock();self.sequence=0;self.matrix_stopped=False;self.previous_processes={};self.command_observers={}
  from .command_console import CommandConsole
  self.console=CommandConsole(runtime,self.publish)
  from .chat import Chat
  self.chat=Chat(runtime)
 def publish(self,kind,value):
  with self.event_lock:
   self.sequence+=1;self.events.append({'seq':self.sequence,'kind':kind,'value':value})
  if kind=='command':
   callback=self.command_observers.get(value.get('id'))
   if callback:callback(kind,value)
 def session(self):return {'token':'integrated',**self.console.session()}
 def close(self):self.matrix_stopped=True;self.console.close()
 def snapshot(self):
  rows=[];now=time.monotonic();net=psutil.net_io_counters();delta=max(.1,now-(self.previous[0] if self.previous else now));rx=(net.bytes_recv-self.previous[1])/delta if self.previous else 0;tx=(net.bytes_sent-self.previous[2])/delta if self.previous else 0;self.previous=(now,net.bytes_recv,net.bytes_sent)
  for p in psutil.process_iter(['pid','name','memory_info','num_threads','create_time']):
   try:
    name=(p.info.get('name') or '').lower();language='python' if 'python' in name else 'java' if 'java' in name else None
    if language:
     cpu=None;io_rate=None;memory=p.info.get('memory_info');created=p.info.get('create_time')
     try:
      times=p.cpu_times();cpu_seconds=times.user+times.system;io=p.io_counters();io_bytes=io.read_bytes+io.write_bytes;old=self.previous_processes.get(p.pid)
      if old:
       elapsed=max(.001,now-old[0]);cpu=max(0,(cpu_seconds-old[1])/elapsed*100/max(1,os.cpu_count() or 1));io_rate=max(0,(io_bytes-old[2])/elapsed)
      self.previous_processes[p.pid]=(now,cpu_seconds,io_bytes)
     except (psutil.AccessDenied,psutil.NoSuchProcess,OSError):pass
     rows.append({'pid':p.pid,'label':p.info['name'],'runtime':language,'cpu':cpu,'memoryBytes':memory.rss if memory else None,'threads':p.info.get('num_threads'),'ageSeconds':time.time()-created if created else None,'ioRate':io_rate})
   except (psutil.NoSuchProcess,psutil.AccessDenied):pass
  mem=psutil.virtual_memory();disk=psutil.disk_usage(str(ROOT.anchor))
  return {'at':time.time()*1000,'processes':rows,'totals':{'python':sum(p['runtime']=='python' for p in rows),'java':sum(p['runtime']=='java' for p in rows),'cpu':sum(p['cpu'] or 0 for p in rows),'memory':sum(p['memoryBytes'] or 0 for p in rows),'io':sum(p['ioRate'] or 0 for p in rows)},'system':{'cpu':psutil.cpu_percent(),'memoryTotal':mem.total,'memoryUsed':mem.used,'networkRx':rx,'networkTx':tx,'hostname':socket.gethostname(),'platform':platform.platform(),'cpuModel':platform.processor(),'cores':os.cpu_count(),'uptime':time.time()-psutil.boot_time(),'totalProcesses':len(psutil.pids()),'disk':{'name':ROOT.anchor,'freeBytes':disk.free}}}
 def status(self):
  settings=self.chat.settings()
  if time.monotonic()-getattr(self,'last_ollama',0)>10:
   self.last_ollama=time.monotonic();self.ollama={'running':False,'ready':False}
   try:
    with urllib.request.urlopen(settings['llama']['endpoint']+'/api/tags',timeout=2) as response:models=json.load(response).get('models',[])
    self.ollama={'running':True,'ready':any(str(m.get('name','')).removesuffix(':latest')==settings['llama']['model'].removesuffix(':latest') for m in models),'models':[m.get('name') for m in models]}
   except (OSError,ValueError):pass
  return {'checkedAt':time.time()*1000,'settings':{'llamaModel':settings['llama']['model'],'geminiModel':settings['gemini']['model'],'openaiModel':settings['chatgpt']['model'],'geminiConfigured':settings['gemini'].get('configured',False),'openaiConfigured':settings['chatgpt'].get('configured',False)},'ollama':self.ollama,'processes':[],'connections':[{'id':k,'name':name,'connected':True,'language':'integrated','pid':os.getpid()} for k,name in self.runtime.snapshot(False)['sections'].items()]}
 def generate(self,b):
  prompt=str(b.get('prompt','')).strip()
  if not prompt:raise ValueError('Enter a prompt')
  mode=b.get('mode','llama');chosen=b.get('providers',['llama']) if mode=='fusion' else [mode];started=time.monotonic();settings=self.chat.settings()
  def ask(name,text):
   stamp=time.monotonic();provider='chatgpt' if name=='openai' else name
   try:return {'id':name,'ok':True,'text':self.chat.request(provider,settings[provider]['model'],[{'role':'user','content':text}],'You are a helpful assistant.'),'elapsedMs':(time.monotonic()-stamp)*1000}
   except Exception as e:return {'id':name,'ok':False,'error':str(e),'elapsedMs':(time.monotonic()-stamp)*1000}
  with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lambda name:ask(name,prompt),chosen[:3]))
  good=[r for r in results if r['ok']];synthesized=False;output=good[0]['text'] if good else ''
  if mode=='fusion' and len(good)>1:
   fusion=ask('llama','Synthesize the following perspectives, resolving disagreements and noting uncertainty. Original question: '+prompt+'\n'+ '\n'.join(r['id']+': '+r['text'] for r in good))
   if fusion['ok']:output=fusion['text'];synthesized=True
  result={'ok':bool(output),'output':output,'results':results,'synthesized':synthesized,'elapsedMs':(time.monotonic()-started)*1000,'error':'' if output else 'No provider returned an answer.'};result['receipt']=self.runtime.record('genesis',{'prompt':prompt,'providers':chosen},result,0);return result
 def route(self,request,ident,path,method,b):
  if path=='/api/session':return request.send(self.session())
  if ident=='genesis':
   if path=='/api/status':return request.send(self.status())
   if path=='/api/generate' and method=='POST':return request.send(self.generate(b))
   if path=='/api/settings' and method=='POST':
    for name,provider in (('llama','llama'),('gemini','gemini'),('openai','chatgpt')):
     current=self.chat.settings()[provider];self.chat.save_settings({'provider':provider,'model':b.get(name+'Model',current['model']),'key':b.get(name+'Key',''),'clear_key':b.get('clear_'+name+'Key',False),'endpoint':current.get('endpoint')})
    return request.send(self.status())
   if path=='/api/program/send' and method=='POST':
    section=str(b.get('id',''));text=str(b.get('text',''))
    if section not in self.runtime.snapshot(False)['sections']:raise ValueError('Choose a connected built-in section')
    job=self.runtime.submit(section,{'text':text})
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
     result=self.runtime.result(job['id'])
     if result['status']!='queued' and result['status']!='running':return request.send({'output':json.dumps(result,indent=2),'receipt':result.get('receipt'),'ok':result['status']=='complete'})
     time.sleep(.05)
    return request.send({'output':'Calculation queued; inspect Results for completion.','job':job['id'],'ok':True})
  elif ident=='matrix':
   if path=='/api/snapshot':return request.send({'snapshot':self.snapshot(),'connected':not self.matrix_stopped,'error':None})
   if path=='/api/events':
    self.matrix_stopped=False;request.send_response(200);request.send_header('Content-Type','text/event-stream');request.send_header('Cache-Control','no-store');request.end_headers()
    def emit(name,v,sequence=None):request.wfile.write(((('id: '+str(sequence)+'\n') if sequence is not None else '')+'event: '+name+'\ndata: '+json.dumps(clean(v))+'\n\n').encode());request.wfile.flush()
    try:
     cursor=int(request.headers.get('Last-Event-ID',0));emit('session',self.session())
     while not self.matrix_stopped:
      emit('snapshot',self.snapshot());emit('status',{'connected':True})
      with self.event_lock:events=list(self.events)
      for event in events:
       if event['seq']>cursor:emit(event['kind'],event['value'],event['seq']);cursor=event['seq']
      time.sleep(.25 if self.console.active else 1)
    except (OSError,ConnectionError):pass
    return
   if path=='/api/command' and method=='POST':
    command=b.get('command','')
    if not isinstance(command,str) or not command.strip() or len(command)>8000:raise ValueError('Enter a command (maximum 8,000 characters).')
    parts=command.strip().split(maxsplit=1);name=parts[0].lower()
    if name in (':help',':status',':sections',':checkpoint',':pipeline','pipeline'):
     if name==':help':out='Windows PowerShell commands run here. Shared commands: :status, :sections, :checkpoint, :pipeline <text>.'
     elif name==':status':out=json.dumps(self.runtime.snapshot(False)['metrics'],indent=2)
     elif name==':sections':out=json.dumps(self.runtime.snapshot(False)['sections'],indent=2)
     elif name==':checkpoint':out=json.dumps(self.runtime.checkpoint())
     else:out=json.dumps(self.runtime.submit('pipeline',{'text':parts[1] if len(parts)>1 else ''}))
     job=uuid.uuid4().hex
     for state,extra in (('start',{'command':command}),('output',{'text':out,'type':'stdout'}),('end',{'code':0})):
      self.publish('command',{'id':job,'state':state,**extra})
     return request.send({'id':job,'ok':True})
    return request.send(self.console.start(command),202)
   if path=='/api/cancel' and method=='POST':return request.send(self.console.cancel(b.get('id')))
   if path=='/api/shutdown' and method=='POST':
    self.matrix_stopped=True
    if self.console.active:self.console.cancel()
    return request.send({'ok':True,'scope':'Matrix section; shared runtime remains active'})
  return request.send({'error':'Section operation has not been integrated: '+path},404)
