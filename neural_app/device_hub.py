"""Optional, minimal TLS companion gateway. No full desktop API is exposed."""
import hashlib,hmac,json,secrets,socket,ssl,threading,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs

class DeviceHub:
 def __init__(self,runtime):
  self.runtime=runtime;self.lock=threading.RLock();self.folder=runtime.data/'devices';self.folder.mkdir(exist_ok=True)
  self.path=self.folder/'paired.json';self.devices=json.loads(self.path.read_text(encoding='utf8')) if self.path.exists() else {}
  self.server=None;self.thread=None;self.port=None;self.fingerprint=None;self.jobs={};self.limits={};self.slots=threading.BoundedSemaphore(8)
 def save(self):
  temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.devices),encoding='utf8');temp.replace(self.path)
 def invite(self,name,can_send=False):
  if not isinstance(name,str) or not 1<=len(name.strip())<=60:raise ValueError('Name this invitation in 1–60 characters')
  if type(can_send) is not bool:raise ValueError('Choose whether selected bits may be sent')
  with self.lock:
   if len(self.devices)>=64:raise ValueError('Revoke an unused invitation before adding another (limit 64)')
   ident=secrets.token_hex(8);key=secrets.token_urlsafe(32)
   self.devices[ident]={'name':name.strip(),'key_hash':hashlib.sha256(key.encode()).hexdigest(),'send':can_send,'created':time.time(),'used':False}
   self.save();return {'id':ident,'key':ident+'.'+key,'name':name.strip(),'send':can_send,'note':'Show this key privately to its intended participant. It is displayed only once.'}
 def revoke(self,ident):
  with self.lock:
   if ident not in self.devices:raise ValueError('Invitation not found')
   del self.devices[ident];self.jobs.pop(ident,None);self.limits.pop(ident,None);self.save()
 def authenticate(self,credential):
  if not isinstance(credential,str) or len(credential)>120:raise PermissionError('Enter a valid invitation key')
  ident,sep,key=credential.partition('.')
  with self.lock:
   item=self.devices.get(ident)
   if not sep or not item or not hmac.compare_digest(item['key_hash'],hashlib.sha256(key.encode()).hexdigest()):raise PermissionError('Invitation invalid or revoked')
   now=time.monotonic();recent=[t for t in self.limits.get(ident,[]) if now-t<60]
   if len(recent)>=30:raise ValueError('Please wait: 30 requests per minute per invitation')
   recent.append(now);self.limits[ident]=recent
   if not item['used']:item['used']=True;self.save()
   return ident,dict(item)
 def packet(self):
  trace=self.runtime.causal.evaluate('01'*32)
  # No source text, source digest, event labels, other device details or receipts.
  return {'type':'neural-device-signal-v1','bit':trace['output_bit'],'trit':trace['output_trit'],'signal':round(trace['signal'],6),'weight':round(trace['neural_weight'],6),'tick':self.runtime.causal.ticks,'meaning':'Configured lesson signal.'}
 def submit(self,ident,bits):
  if not isinstance(bits,str) or not 1<=len(bits)<=256 or any(x not in '01' for x in bits):raise ValueError('Send 1–256 binary digits only')
  return self.submit_input(ident,{'bits':bits,'sections':[]})
 def submit_intent(self,ident,text):
  from .intent_packet import prepare_intent
  packet=prepare_intent(text)
  result=self.submit_input(ident,{'text':packet['text'],'sections':[],'intent':{'format':packet['format'],'sha256':packet['sha256'],'method':packet['method']}})
  return {**result,'intent_sha256':packet['sha256'],'intent_bytes':packet['bytes']}
 def submit_input(self,ident,body):
  with self.lock:
   device=self.devices.get(ident)
   if not device or not device['send']:raise PermissionError('This invitation receives signals only')
   previous=self.jobs.setdefault(ident,[])
   for jobid in previous:
    try:status=self.runtime.result(jobid)['status']
    except ValueError:continue
    if status in ('queued','running'):raise ValueError('Wait for your previous bits to finish')
   value=self.runtime.submit('pipeline',body)
   previous.append(value['id']);self.jobs[ident]=previous[-8:];return {'id':value['id'],'status':value['status']}
 def result(self,ident,jobid):
  with self.lock:
   if ident not in self.devices or jobid not in self.jobs.get(ident,[]):raise PermissionError('Only your own submitted result is available')
  value=self.runtime.result(jobid);result={'id':jobid,'status':value['status']}
  if value['status']=='complete':
   trace=value['result']['stages']['causal']
   result.update(receipt=value['receipt'],input_bits=trace['input_bits'],working_bits=trace['working_bits'],xor_mask=trace['xor_mask'],changed_bits=trace['changed_bits'],classifier_probability=value['result']['stages']['classifier']['probability'])
  elif value['status']=='error':result['error']='The selected bits could not be processed.'
  return result
 def certificate(self):
  from cryptography import x509
  from cryptography.x509.oid import NameOID
  from cryptography.hazmat.primitives import hashes,serialization
  from cryptography.hazmat.primitives.asymmetric import rsa
  certpath=self.folder/'gateway-cert.pem';keypath=self.folder/'gateway-key.pem'
  if not certpath.exists() or not keypath.exists():
   key=rsa.generate_private_key(public_exponent=65537,key_size=2048);name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Neural App private companion')]);now=datetime.now(timezone.utc)
   cert=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=365)).sign(key,hashes.SHA256())
   keypath.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));certpath.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
  cert=x509.load_pem_x509_certificate(certpath.read_bytes());self.fingerprint=cert.fingerprint(hashes.SHA256()).hex()
  return certpath,keypath
 def start(self,port=8800,lan=True):
  if type(port) is not int or not 0<=port<=65535:raise ValueError('Choose a valid companion port')
  if type(lan) is not bool:raise ValueError('Choose local or LAN scope')
  with self.lock:
   if self.server:return self.info()
   cert,key=self.certificate();owner=self
   class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.0'
    def log_message(self,*args):pass
    def setup(self):
     self.request.settimeout(8);super().setup()
    def send(self,value,status=200,kind='application/json'):
     raw=value if isinstance(value,bytes) else json.dumps(value,allow_nan=False).encode()
     self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Frame-Options','DENY');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'none'; base-uri 'none'");self.end_headers();self.wfile.write(raw)
    def handle_request(self,post=False):
     try:
      url=urlsplit(self.path)
      if not post and url.path in ('/','/companion.html'):return self.send((Path(__file__).resolve().parents[1]/'ui'/'companion.html').read_bytes(),kind='text/html; charset=utf-8')
      public={'/manifest.webmanifest':('pwa/manifest.webmanifest','application/manifest+json'),'/sw.js':('pwa/sw.js','text/javascript'),'/icon-192.png':('pwa/icon-192.png','image/png'),'/icon-512.png':('pwa/icon-512.png','image/png')}
      if not post and url.path in public:
       file,kind=public[url.path];return self.send((Path(__file__).resolve().parents[1]/'ui'/file).read_bytes(),kind=kind)
      # Reject cross-site browser submissions; the gateway exposes no desktop token.
      origin=self.headers.get('Origin')
      if origin and origin!='https://'+self.headers.get('Host',''):raise PermissionError('Use this companion page to connect')
      if self.headers.get('Sec-Fetch-Site')=='cross-site':raise PermissionError('Cross-site connection rejected')
      auth=self.headers.get('Authorization','')
      if not auth.startswith('Bearer '):raise PermissionError('An invitation is required')
      ident,item=owner.authenticate(auth[7:])
      if not post and url.path=='/signal':return self.send({'signal':owner.packet(),'can_send':item['send']})
      if not post and url.path=='/result':return self.send(owner.result(ident,parse_qs(url.query).get('id',[''])[0]))
      if post and url.path=='/intent':
       size=int(self.headers.get('Content-Length','0'))
       if not 0<size<=4096:raise ValueError('Intent request too large')
       body=json.loads(self.rfile.read(size));return self.send(owner.submit_intent(ident,body.get('text')))
      if post and url.path=='/bits':
       size=int(self.headers.get('Content-Length','0'))
       if not 0<size<=1024:raise ValueError('The selected-bit request is too large')
       body=json.loads(self.rfile.read(size));return self.send(owner.submit(ident,body.get('bits')))
      if post and url.path=='/leave':owner.revoke(ident);return self.send({'disconnected':True,'invitation_revoked':True})
      return self.send({'error':'Not found'},404)
     except PermissionError as error:return self.send({'error':str(error)},403)
     except (ValueError,KeyError,TypeError,json.JSONDecodeError) as error:return self.send({'error':str(error)},400)
     except (BrokenPipeError,ConnectionError,TimeoutError):pass
     except Exception:return self.send({'error':'Companion request unavailable'},503)
    def do_GET(self):self.handle_request()
    def do_POST(self):self.handle_request(True)
   class Server(ThreadingHTTPServer):
    daemon_threads=True;request_queue_size=8
    def get_request(self):
     # Handshake in the bounded request worker, not in the accept loop.
     sock,address=super().get_request();sock.settimeout(8)
     return sock,address
    def process_request(self,request,address):
     if not owner.slots.acquire(False):self.shutdown_request(request);return
     super().process_request(request,address)
    def process_request_thread(self,request,address):
     try:
      wrapped=context.wrap_socket(request,server_side=True);super().process_request_thread(wrapped,address)
     except (OSError,ssl.SSLError):self.shutdown_request(request)
     finally:owner.slots.release()
   context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(str(cert),str(key))
   self.server=Server(('0.0.0.0' if lan else '127.0.0.1',port),Handler);self.port=self.server.server_address[1];self.lan=lan
   self.thread=threading.Thread(target=self.server.serve_forever,name='neural-companion-tls',daemon=True);self.thread.start();return self.info()
 def info(self):
  with self.lock:
   try:addresses=sorted({row[4][0] for row in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET)}) if self.server and self.lan else ['127.0.0.1']
   except OSError:addresses=[]
   return {'running':self.server is not None,'port':self.port,'scope':'LAN' if getattr(self,'lan',False) else 'This computer','addresses':addresses,'certificate_sha256':self.fingerprint,'devices':[{'id':ident,**{k:v for k,v in item.items() if k!='key_hash'}} for ident,item in self.devices.items()],'privacy':'No analytics, contacts, location, personal files or raw source accounts. Only explicit bits enter the shared pipeline; those bits are saved in the host’s receipts.','platforms':['Android browser','iPhone Safari','Linux browser','Windows browser'],'limits':'Requires a browser with JavaScript and, for live mode, TLS 1.2+. Offline mode requires no connection. Physical-device compatibility remains to be tested.'}
 def close(self):
  with self.lock:server=self.server;thread=self.thread;self.server=None;self.thread=None
  if server:server.shutdown();server.server_close()
  if thread:thread.join(2)
