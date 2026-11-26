"""Converted libraries share the app's controls, request boundary and receipts."""
import importlib,io,json,threading,time,types,hashlib
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from .runtime import ROOT,clean
from .python_components import PythonSections

class ComponentHost:
 def __init__(self,runtime):
  self.runtime=runtime;self.python=PythonSections(runtime);self.java=None;self.qt=None;self.ticks={};self.paused=set();self.adapter_lock=threading.RLock()
  from . import section_threads
  section_threads.ensure_pool()
  from .section_background import SectionBackground
  self.background=SectionBackground(self)
  from .original_lane import OriginalLane
  self.original_lane=OriginalLane(self)
  self.web=json.loads((ROOT/'web-sections.json').read_text(encoding='utf8'));self.java_index=json.loads((ROOT/'java-sections.json').read_text(encoding='utf8'));self.panels=json.loads((ROOT/'original-panels.json').read_text(encoding='utf8'));self.started=time.monotonic();runtime.component_host=self
  imported=ROOT/'references'/'desktop-java'/'panels.json'
  if imported.exists():
   additions=json.loads(imported.read_text(encoding='utf-8'));self.panels.extend(additions);self.java_index.update({p['id']:p for p in additions})
 def index(self):return [{'id':p['id'],'name':p['name'],'kind':'web' if p['id'] in self.web else 'java' if p['id'] in self.java_index else 'qt' if p['id']=='flux' else 'python','family':p['family']} for p in self.panels]
 def close(self):
  for item in self.python.loaded.values():
   for obj in (item['controller'],getattr(item['controller'],'rt',None),getattr(item['controller'],'session',None)):
    if obj is None:continue
    for name in ('stop','stop_event','halt'):
     event=getattr(obj,name,None)
     if isinstance(event,threading.Event):event.set()
  self.background.close()
  if hasattr(self,'services'):self.services.close()
  if self.java:self.java.close()
  if self.qt:self.qt.close()
  for item in self.python.loaded.values():
   scheduler=getattr(item['module'],'_shared_scheduler',None)
   if scheduler:scheduler.close()
   controller=item['controller']
   for obj in (controller,getattr(controller,'rt',None),getattr(controller,'session',None)):
    if obj is None:continue
    for name in ('stop','halt'):
     event=getattr(obj,name,None)
     if isinstance(event,threading.Event):event.set()
    if callable(getattr(type(obj),'close',None)):
     try:obj.close()
     except Exception:pass
   if item.get('embedded_ready') and item['module'].__name__.endswith('.server'):
    for name in ('autonomous','prompt_loop','native_research','federation'):
     obj=getattr(item['module'],name,None);event=getattr(obj,'stop',None)
     if isinstance(event,threading.Event):event.set()
  from . import section_threads
  section_threads.scheduled.clear();section_threads.pool.shutdown(wait=False,cancel_futures=True);section_threads.compute.shutdown(wait=False,cancel_futures=True)
  # Controllers own their database handles, including journals below engine/session.
  import sqlite3
  seen=set()
  def release(value,depth=0):
   if id(value) in seen or depth>8:return
   seen.add(id(value))
   if isinstance(value,sqlite3.Connection):
    try:value.close()
    except sqlite3.Error:pass
   elif isinstance(value,dict):
    for child in list(value.values()):release(child,depth+1)
   elif isinstance(value,(list,tuple)):
    for child in value:release(child,depth+1)
   elif type(value).__module__.startswith('neural_app.components') and hasattr(value,'__dict__'):
    for name,child in list(vars(value).items()):
     if name not in ('master','children','root','runtime','module'):release(child,depth+1)
  for item in self.python.loaded.values():release(item['controller'])
 def open(self,ident):
  if self.qt:self.qt.active(self.original_lane.enabled or ident=='flux')
  if ident=='academy':return {'id':ident,'kind':'curriculum','ui':{'type':'label','text':'Built-in curriculum: lessons, quizzes, notes, search, timer and backup.'}}
  if ident in self.web:return {'id':ident,'kind':'web','bundle':self.web[ident]}
  if ident in self.java_index:
   if self.java is None:
    from .java_components import JavaSections
    self.java=JavaSections(self.runtime)
   return {'kind':'controls',**self.java.open(ident)}
  if ident=='flux':
   if self.qt is None:
    from .qt_components import QtSections
    self.qt=QtSections(self.runtime,self.python.index['flux'])
   return {'kind':'controls',**self.qt.open()}
  return {'kind':'controls',**self.python.open(ident)}
 def pause(self,ident,value):
  if value:self.paused.add(ident)
  else:self.paused.discard(ident)
  if self.java and ident in self.java_index:self.java.pause(ident,value)
  if ident=='flux' and self.qt:self.qt.active(not value)
  return {'section':ident,'paused':bool(value)}
 def active(self,ident,value):
  # Page visibility controls painting, not the shared background calculation lane.
  if self.qt:self.qt.active(self.original_lane.enabled or ident=='flux' and value)
  return {'section':ident,'active':bool(value)}
 def action(self,b):
  b=self.checked(b)
  ident=b['section'];self.pause(ident,False)
  if ident in self.java_index:
   descriptor=self.open(ident)
   return self.java.action(b)
  if ident=='flux':self.open(ident);return self.qt.action(b)
  return self.python.action(b)
 def checked(self,value):
  from . import translation
  transport=self.runtime.transport_result(value)
  return json.loads(b''.join(translation.decode(packet) for packet in transport['packets']))
 def graphic(self,ident,control,width,height):
  if ident in self.java_index:self.open(ident);return self.java.graphic(ident,control,width,height),'image/svg+xml'
  if ident=='flux':self.open(ident);return self.qt.graphic(control,width,height),'image/svg+xml'
  return self.python.graphic(ident,control,width,height),'image/svg+xml'
 def adapter(self,ident):
  with self.adapter_lock:return self._adapter(ident)
 def _adapter(self,ident):
  if ident not in self.python.loaded:self.python.open(ident)
  item=self.python.loaded[ident];module=item['module'];controller=item['controller']
  if ident=='observatory' and not item.get('embedded_ready'):
   from .observatory_components import integrate
   controller=integrate(module.Runtime(module.APP.parent,self.runtime.data/'sections'/'observatory'),self.runtime);controller.config.update(port=8797,running=False,ingestion=False);item['controller']=controller;item['embedded_ready']=True
  if ident=='carrier':handler=module.Handler;server=types.SimpleNamespace(lab=controller,token='integrated',server_port=8797)
  elif ident=='observatory':handler=module.Handler;server=types.SimpleNamespace(runtime=item['controller'],server_port=8797)
  elif ident=='inference':
   if not item.get('embedded_ready'):
    from .inference_components import initialize
    initialize(module,self.runtime,self)
    from .inference_actions import install
    item['shutdown']=install(self,module);item['embedded_ready']=True
   handler=module.Handler;server=types.SimpleNamespace(server_port=8797)
  elif ident=='neural-lab':handler=module.make_handler(controller,'integrated');server=types.SimpleNamespace(server_port=8797)
  else:raise ValueError('No calculation request adapter')
  return handler,server,item
 def tick(self,ident,item):
  if ident in self.paused:return
  now=time.monotonic()
  if now-self.ticks.get(ident,0)<.5:return
  self.ticks[ident]=now
  if ident=='inference':item['module']._shared_tick()
  elif ident=='observatory':
   rt=item['controller'];rt.pulses+=1;rt.pulse_times.append(now);rt.v3.tick();rt.python.tick();rt.flux.tick()
   if rt.config.get('chiral_running'):rt.chiral_step()
   rt.publish('pulse',rt.carrier(),record=False)
 def services_instance(self):
  with self.adapter_lock:
   if not hasattr(self,'services'):
    from .integrated_services import Services
    self.services=Services(self.runtime)
   return self.services
 def invoke(self,ident,path,body=None):
  from email.message import Message
  headers=Message();headers['Host']='127.0.0.1:8797'
  captured=[]
  def capture(*args,**kwargs):
   status=args[0] if args and isinstance(args[0],int) else kwargs.get('status',200)
   value=args[1] if args and isinstance(args[0],int) else args[0] if args else None
   if status>=400:raise ValueError(str(value))
   captured.append(value);return value
  request=types.SimpleNamespace(headers=headers,server=types.SimpleNamespace(server_port=8797),client_address=('127.0.0.1',0),connection=types.SimpleNamespace(settimeout=lambda value:None),send=capture,_component_capture=capture)
  self.route(request,ident,path,'GET' if body is None else 'POST',body)
  return captured[-1] if captured else None
 def route(self,request,ident,path,method,body=None):
  if method=='POST' and not isinstance(body,bytes):body=self.checked(body or {})
  if ident in ('genesis','matrix'):
   with self.adapter_lock:
    if not hasattr(self,'services'):
     from .integrated_services import Services
     self.services=Services(self.runtime)
   return self.services.route(request,ident,path,method,body or {})
  if path.startswith('/bridge/'):
   self.python.open(ident);item=self.python.loaded[ident];controller=item['controller'];module=item['module'];name=path.split('/')[-1]
   if name=='__telemetry':
    if ident=='injector':
     if 'sampler' not in item:item['sampler']=module.CPUSampler()
     result={'cpu':item['sampler'].sample(),'state':controller._snapshot()}
    else:result={'telemetry':controller.live_telemetry(time.monotonic()-self.started,None,None)}
    return request.send(clean(result))
   allowed={m['name'] for m in self.python.describe(ident)['methods']}
   if name not in allowed:raise ValueError('Unknown calculation method')
   result=getattr(controller,name)(*(body or {}).get('args',[]));receipt=self.runtime.record('component:'+ident,{'method':name},clean(result),0)
   if isinstance(result,dict):result['receipt']=receipt
   return request.send(clean(result))
  handler,server,item=self.adapter(ident)
  server.server_port=request.server.server_port
  if ident=='observatory':item['controller'].config['port']=server.server_port
  if ident=='inference' and method=='POST' and path=='/api/shutdown':return request.send(item['shutdown']())
  proxy=object.__new__(handler);proxy.__dict__.update(request.__dict__);proxy.server=server;proxy.path=path
  # Shared host and session checks have already succeeded. No separate listener.
  proxy.authorized=lambda:True;proxy.allowed=lambda:True;proxy.valid_host=lambda:True;proxy.local_request=lambda:True
  if ident=='observatory' and path.split('?')[0]=='/api/events':
   request.send_response(200);request.send_header('Content-Type','text/event-stream');request.send_header('Cache-Control','no-store');request.end_headers()
   try:
    for _ in range(120):
     self.tick(ident,item);controller=item['controller'];event={'type':'pulse','data':controller.carrier()};request.wfile.write(('data: '+json.dumps(clean(event))+'\n\n').encode())
     if _%2==0:
      with controller.lock:rows=[{k:m.get(k) for k in ('id','status','runs','trit','gate','last_run','duration_ms','error')} for m in controller.modules.values()]
      event={'type':'shared-modules','data':{'modules':rows,'execution':controller.shared_execution()}};request.wfile.write(('data: '+json.dumps(clean(event))+'\n\n').encode())
     request.wfile.flush();time.sleep(1)
   except (OSError,ConnectionError):pass
   return
  send_name='send' if hasattr(handler,'send') else 'json_response'
  if hasattr(request,'_component_capture'):setattr(proxy,send_name,request._component_capture)
  original_send=getattr(proxy,send_name)
  if method=='POST':
   def send_result(*args,**kwargs):
    result=args[1] if args and isinstance(args[0],int) else args[0] if args else None
    if isinstance(result,(dict,list)):
     source={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()} if isinstance(body,bytes) else body
     receipt=self.runtime.component_result(ident,{'path':path,'input':source},result)
     if isinstance(result,dict):result['shared_receipt']=receipt
    return original_send(*args,**kwargs)
   setattr(proxy,send_name,send_result)
  for header in ('X-Lab-Token','X-Mesh-Token'):
   if header in proxy.headers:proxy.headers.replace_header(header,'integrated')
   else:proxy.headers[header]='integrated'
  if method=='POST':
   raw=body if isinstance(body,bytes) else json.dumps(body or {}).encode();proxy.rfile=io.BytesIO(raw)
   if 'Content-Length' in proxy.headers:proxy.headers.replace_header('Content-Length',str(len(raw)))
   else:proxy.headers['Content-Length']=str(len(raw))
   handler.do_POST(proxy)
  else:handler.do_GET(proxy)
