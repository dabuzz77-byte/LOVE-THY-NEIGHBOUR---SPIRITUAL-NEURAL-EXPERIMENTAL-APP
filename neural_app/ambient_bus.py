"""Bounded, authenticated local publish/subscribe bus for ambient stages."""
import json,threading,time,secrets
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from collections import deque

STAGES=('engine-controls','cognitive-circuit','generation-cognition','thought-expression','recursive-core-2','recursive-core-3','recursive-core','recursive-manifest','expression-field/yin-order-chaos','expression-field/yin-chaos-order','expression-field/inverted','expression-field/plus90','expression-field/minus90','parallel-native-lanes','os-learning','expression-field','native-workbench','native-trainer','bit-command','process-ascii-grid','vector-ascii-grid','grounded-reasoner','native-matrix-rain','potential-sphere','tesseract','tesseract-1','tesseract-2','tesseract-3','tesseract-combined','ambient-combined','llama-selector','flow-incurrence','logic-search','stochastic-sequences','stochastic-discovery','wordsearch','sentence-search','llama','binary','qutrit','random-bit','identity','resonance','ternary','phase','hydrogen','stellar','dyson','earth','organic','life','karma','silicon')
from .sphere_functions import PROFILES as SPHERE_PROFILES
STAGES=tuple(dict.fromkeys((*STAGES,'intelligence-engine','reasoning-episode','self-improvement-engine',*SPHERE_PROFILES)))
class AmbientBus:
 def __init__(self):
  self.lock=threading.RLock();self.events=deque(maxlen=256);self.sequence=0;self.server=None;self.port=None;self.error=None;self.on_event=None;self.control_handler=None
 def start(self,port,token):
  port=int(port)
  if not 1024<=port<=65535:raise ValueError('Choose a port from 1024 to 65535')
  if self.server and self.port==port:return self.view(self.sequence)
  bus=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def send(self,value,status=200):
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
   def allowed(self):
    if not secrets.compare_digest(self.headers.get('X-Neural-Token',''),token):self.send({'error':'Current app session token required'},403);return False
    if self.headers.get('Host','').split(':')[0] not in ('localhost','127.0.0.1'):self.send({'error':'Invalid host'},403);return False
    if self.headers.get('Origin'):self.send({'error':'Use the authenticated main-app API for browser requests'},403);return False
    return True
   def do_GET(self):
    if not self.allowed():return
    try:self.send(bus.view(max(0,int(parse_qs(urlsplit(self.path).query).get('after',['0'])[0]))))
    except (ValueError,TypeError) as e:self.send({'error':str(e)},400)
   def do_POST(self):
    if not self.allowed():return
    try:
     size=int(self.headers.get('Content-Length','0'))
     if not 0<size<=32768:raise ValueError('Use a JSON message below 32 KB')
     self.send(bus.publish(json.loads(self.rfile.read(size))))
    except (ValueError,TypeError) as e:self.send({'error':str(e)},400)
  server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True
  old=self.server;self.server=server;self.port=server.server_address[1];self.error=None
  threading.Thread(target=server.serve_forever,daemon=True,name='ambient-input-bus').start()
  if old:old.shutdown();old.server_close()
  return self.view(self.sequence)
 def stop(self):
  server=self.server;self.server=None;self.port=None
  if server:server.shutdown();server.server_close()
 def publish(self,value):
  if not isinstance(value,dict):raise ValueError('Expected a JSON object')
  target=value.get('target','all')
  if target not in ('all',*STAGES):raise ValueError('Unknown stage target')
  kind=value.get('kind','input')
  if kind not in ('input','reference','bit-input','stage-output','control'):raise ValueError('Unknown event kind')
  payload=value.get('payload','')
  control_receipt=None
  if kind=='control':
   if self.control_handler is None:raise ValueError('Control registry is not available')
   control_receipt=self.control_handler(payload);payload={**control_receipt,'processing_receipt':True,'provenance':'typed engine control request; value remains in private control queue'}
  if len(json.dumps(payload,ensure_ascii=False,allow_nan=False).encode())>24000:raise ValueError('Bus payload exceeds 24 KB from '+str(value.get('origin','local-client'))[:80])
  with self.lock:
   self.sequence+=1
   event={'sequence':self.sequence,'time':time.time(),'target':target,'kind':kind,'origin':str(value.get('origin','local-client'))[:80],'payload':payload}
   self.events.append(event)
   if self.on_event:self.on_event(event)
   return {'accepted':True,'broadcast':True,'event':event,'control_receipt':control_receipt,'scope':'authenticated local subscribers'}
 def activity(self):
  with self.lock:
   rows={}
   for event in self.events:
    origin=event['origin'];rows[origin]={'sequence':event['sequence'],'time':event['time'],'kind':event['kind'],'target':event['target']}
   return rows
 def view(self,after=0):
  with self.lock:
   oldest=self.events[0]['sequence'] if self.events else self.sequence+1
   return {'listening':self.server is not None,'port':self.port,'error':self.error,'broadcast':True,'transport':'authenticated HTTP publish / polling','endpoint':'http://127.0.0.1:'+str(self.port)+'/events' if self.port else None,'stages':STAGES,'sequence':self.sequence,'oldest':oldest,'gap':after<oldest-1,'events':[e for e in self.events if e['sequence']>after],'retained_limit':256,'scope':'loopback'}
