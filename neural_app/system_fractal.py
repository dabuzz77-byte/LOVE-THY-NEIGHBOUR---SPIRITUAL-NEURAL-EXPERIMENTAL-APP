"""Local read-only process and connection census; bounded bus projection."""
import platform,time,threading,hashlib,json,ipaddress,subprocess,os
class SystemFractal:
 def __init__(self,runtime,bus,start=True):
  self.runtime=runtime;self.bus=bus;self.lock=threading.RLock();self.stop=threading.Event();self.sequence=0;self.state={'status':'waiting','processes':[],'connections':[]};self.thread=None
  if start:
   self.thread=threading.Thread(target=self.loop,daemon=True,name='system-fractal');self.thread.start()
 def sample(self):
  errors=[];processes=[];connections=[];metrics={}
  try:
   import psutil
   for p in psutil.process_iter(['pid','ppid','name','status','memory_info','num_threads']):
    try:
     v=p.info;mem=v.get('memory_info');processes.append({'pid':v['pid'],'parent':v['ppid'],'name':v.get('name') or 'unavailable','status':v.get('status'),'memory_bytes':mem.rss if mem else None,'threads':v.get('num_threads')})
    except (psutil.NoSuchProcess,psutil.AccessDenied):continue
   try:
    for c in psutil.net_connections(kind='inet'):
     remote=c.raddr;address=remote.ip if remote else None
     connections.append({'pid':c.pid,'state':c.status,'remote':address,'remote_port':remote.port if remote else None,'scope':'private/local' if address and ipaddress.ip_address(address).is_private else 'public endpoint' if address else 'listener / no remote'})
   except (psutil.AccessDenied,OSError) as e:errors.append('Connection ownership unavailable: '+type(e).__name__)
   m=psutil.virtual_memory();metrics={'cpu_percent':psutil.cpu_percent(interval=None),'memory_percent':m.percent,'memory_bytes':m.total,'logical_cpus':psutil.cpu_count(),'boot_time':psutil.boot_time()}
  except ImportError:
   if os.name=='nt':
    try:
     script="$p=@(Get-CimInstance Win32_Process | Select-Object @{n='pid';e={$_.ProcessId}},@{n='parent';e={$_.ParentProcessId}},@{n='name';e={$_.Name}},@{n='memory_bytes';e={[long]$_.WorkingSetSize}},@{n='threads';e={$_.ThreadCount}});$c=@(Get-NetTCPConnection -ErrorAction SilentlyContinue | Select-Object @{n='pid';e={$_.OwningProcess}},@{n='state';e={[string]$_.State}},@{n='remote';e={$_.RemoteAddress}},@{n='remote_port';e={$_.RemotePort}});@{processes=$p;connections=$c}|ConvertTo-Json -Depth 4 -Compress"
     result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],capture_output=True,text=True,timeout=20,creationflags=0x08000000)
     if result.returncode:raise OSError('Windows census command unavailable')
     native=json.loads(result.stdout);processes=native.get('processes',[]);connections=native.get('connections',[])
     for c in connections:
      address=c.get('remote');c['scope']='listener / no remote' if not address or address in ('0.0.0.0','::') else 'private/local' if ipaddress.ip_address(address).is_private else 'public endpoint'
     errors.append('Windows native census: aggregate CPU/memory counters unavailable without psutil; TCP endpoints only')
    except Exception as e:errors.append('Windows census: '+type(e).__name__)
   else:errors.append('Install psutil for process and connection measurements')
  except Exception as e:errors.append(type(e).__name__+': '+str(e)[:180])
  if not processes:errors.append('No processes visible to this execution context; run the desktop app to use its local permissions')
  with self.runtime.lock:
   receipts={k:v.get('receipt') for k,v in self.runtime.latest.items() if isinstance(v,dict)}
  with self.lock:
   self.sequence+=1
   self.state={'sequence':self.sequence,'time':time.time(),'status':'measured' if processes else 'unavailable','kernel':{'system':platform.system(),'release':platform.release(),'version':platform.version(),'machine':platform.machine(),'scope':'OS-reported identity and aggregate counters; kernel memory is not inspected'},'metrics':metrics,'processes':processes,'connections':connections,'errors':errors,'app_receipts':receipts,'interval_seconds':10,'scope':'local observation; remote endpoints do not establish access beyond them'}
  # Full local addresses stay in the local view. Shared processing receives hashed endpoints.
  projection={'system_fractal':True,'sequence':self.sequence,'metrics':metrics,'processes':[{'pid':p['pid'],'parent':p['parent'],'memory_bytes':p['memory_bytes'],'threads':p['threads']} for p in processes],'connections':[{'pid':c['pid'],'state':c['state'],'scope':c['scope'],'endpoint_hash':hashlib.sha256(str((c['remote'],c['remote_port'])).encode()).hexdigest()[:16]} for c in connections],'app_receipts':receipts,'provenance':'observed-system','stochastic':False}
  raw=json.dumps(projection,separators=(',',':'));parts=[raw[i:i+10000] for i in range(0,len(raw),10000)]
  for i,part in enumerate(parts):self.bus.publish({'origin':'system-fractal','target':'all','kind':'input','payload':{'system_fractal_frame':self.sequence,'part':i,'parts':len(parts),'data':part,'provenance':'observed-system','stochastic':False}})
  return self.view()
 def loop(self):
  while not self.stop.is_set():
   try:self.sample()
   except Exception as e:
    with self.lock:self.state['errors']=[type(e).__name__+': '+str(e)[:180]]
   self.stop.wait(10)
 def view(self):
  with self.lock:return dict(self.state)
 def close(self):self.stop.set()
