"""Read-only local adapter/router sampling. No credentials or configuration writes."""
import ctypes as C,json,os,socket,struct,threading,time,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from ctypes import wintypes as W

def gateway_ipv4():
 if os.name!='nt':return None
 dll=C.WinDLL('iphlpapi');size=W.ULONG(0);dll.GetIpForwardTable(None,C.byref(size),False);buf=C.create_string_buffer(size.value)
 if dll.GetIpForwardTable(buf,C.byref(size),False):return None
 count=struct.unpack_from('<I',buf.raw)[0];routes=[]
 for i in range(min(count,256)):
  row=struct.unpack_from('<14I',buf.raw,4+i*56)
  if row[0]==0 and row[3] and row[5]==4:routes.append((row[9],socket.inet_ntoa(struct.pack('<I',row[3]))))
 return min(routes)[1] if routes else None

def ping_router(address):
 if not address:return {'status':'no default IPv4 gateway','latency_ms':None,'attempted':False}
 dll=C.WinDLL('iphlpapi');dll.IcmpCreateFile.restype=C.c_void_p;handle=dll.IcmpCreateFile()
 if not handle or handle==C.c_void_p(-1).value:return {'status':'ICMP handle unavailable','latency_ms':None,'attempted':False}
 dll.IcmpSendEcho.argtypes=[C.c_void_p,W.DWORD,C.c_void_p,W.WORD,C.c_void_p,C.c_void_p,W.DWORD,W.DWORD];dll.IcmpCloseHandle.argtypes=[C.c_void_p]
 reply=C.create_string_buffer(512);payload=C.create_string_buffer(b'NeuralApp-read-only-probe')
 try:
  n=dll.IcmpSendEcho(handle,struct.unpack('<I',socket.inet_aton(address))[0],payload,len(payload)-1,None,reply,len(reply),1000)
  if not n:return {'status':'no ICMP reply','latency_ms':None,'attempted':True}
  _,status,rtt=struct.unpack_from('<III',reply.raw);return {'status':'reply' if status==0 else 'ICMP status '+str(status),'latency_ms':rtt if status==0 else None,'attempted':True}
 finally:dll.IcmpCloseHandle(handle)

def tcp_router(address):
 if not address:return {'status':'no gateway','connect_ms':None}
 for port in (80,443):
  start=time.perf_counter()
  try:
   with socket.create_connection((address,port),timeout=.7):pass
   return {'status':'web port reachable','port':port,'connect_ms':round((time.perf_counter()-start)*1000,3),'kind':'TCP connection time, not ICMP RTT'}
  except OSError:pass
 return {'status':'web ports unavailable / filtered','connect_ms':None}

def wlan_reading():
 if os.name!='nt':return {'available':False,'reason':'Windows WLAN API required'}
 try:
  dll=C.WinDLL('wlanapi');handle=C.c_void_p();version=W.DWORD();code=dll.WlanOpenHandle(2,None,C.byref(version),C.byref(handle))
  if code:return {'available':False,'reason':'WLAN API status '+str(code)}
  ptr=C.c_void_p()
  class GUID(C.Structure):_fields_=[('a',W.DWORD),('b',W.WORD),('c',W.WORD),('d',C.c_ubyte*8)]
  class IFACE(C.Structure):_fields_=[('guid',GUID),('description',W.WCHAR*256),('state',W.DWORD)]
  class SSID(C.Structure):_fields_=[('length',W.ULONG),('bytes',C.c_ubyte*32)]
  class ASSOC(C.Structure):_fields_=[('ssid',SSID),('bss',W.DWORD),('bssid',C.c_ubyte*6),('phy',W.DWORD),('phy_index',W.ULONG),('quality',W.ULONG),('rx',W.ULONG),('tx',W.ULONG)]
  class CONNECTION(C.Structure):_fields_=[('state',W.DWORD),('mode',W.DWORD),('profile',W.WCHAR*256),('assoc',ASSOC),('security',C.c_ubyte*16)]
  try:
   code=dll.WlanEnumInterfaces(handle,None,C.byref(ptr))
   if code:return {'available':False,'reason':'WLAN interface status '+str(code)}
   count=C.cast(ptr,C.POINTER(W.DWORD))[0];items=[]
   for i in range(min(count,8)):
    iface=IFACE.from_address(ptr.value+8+i*C.sizeof(IFACE))
    if iface.state!=1:continue
    data=C.c_void_p();size=W.DWORD();op=W.DWORD();code=dll.WlanQueryInterface(handle,C.byref(iface.guid),7,None,C.byref(size),C.byref(data),C.byref(op))
    if not code and data.value:
     try:
      v=CONNECTION.from_address(data.value);items.append({'signal_percent':int(v.assoc.quality),'receive_mbps':v.assoc.rx/1000,'transmit_mbps':v.assoc.tx/1000,'kind':'WLAN driver link report'})
     finally:dll.WlanFreeMemory(data)
   return {'available':bool(items),'interfaces':items,'reason':None if items else 'No connected Wi-Fi interface reported'}
  finally:
   if ptr.value:dll.WlanFreeMemory(ptr)
   dll.WlanCloseHandle(handle,None)
 except Exception as e:return {'available':False,'reason':str(e)[:180]}

def router_description(gateway):
 if not gateway:return {'available':False,'reason':'No IPv4 gateway'}
 sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.settimeout(1.5)
 try:
  msg=b'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 1\r\nST: upnp:rootdevice\r\n\r\n';sock.sendto(msg,(gateway,1900));reply,peer=sock.recvfrom(8192)
  if peer[0]!=gateway:raise ValueError('Response is not from selected gateway')
  headers=dict(line.split(':',1) for line in reply.decode(errors='replace').split('\r\n') if ':' in line);location=next((v.strip() for k,v in headers.items() if k.lower()=='location'),None);url=urllib.parse.urlsplit(location or '')
  if url.scheme not in ('http','https') or url.hostname!=gateway or url.username:raise ValueError('Router description URL is not gateway-local')
  class NoRedirect(urllib.request.HTTPRedirectHandler):
   def redirect_request(self,*args,**kwargs):return None
  with urllib.request.build_opener(NoRedirect).open(location,timeout=3) as r:raw=r.read(262145)
  if len(raw)>262144 or b'<!DOCTYPE' in raw.upper():raise ValueError('Invalid device description')
  root=ET.fromstring(raw);find=lambda key:next((x.text for x in root.iter() if x.tag.split('}')[-1]==key),'')
  return {'available':True,'manufacturer':find('manufacturer'),'model':find('modelName'),'service_types':[x.text for x in root.iter() if x.tag.split('}')[-1]=='serviceType'][:12],'scope':'read-only SSDP/device description; no router changes'}
 except Exception as e:return {'available':False,'reason':str(e)[:180]}
 finally:sock.close()
class RouterMonitor:
 def __init__(self,start=True,rails=None):
  self.rails=rails
  self.lock=threading.RLock();self.halt=threading.Event();self.enabled=True;self.history=[];self.sequence=0;self.description={};self.last_discovery=0;self.previous=None;self.worker=None
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='local-router-measurements');self.worker.start()
 def sample(self):
  now=time.time();gateway=gateway_ipv4();row={'time':now,'gateway':gateway,'wifi':wlan_reading(),'probe':ping_router(gateway),'tcp':tcp_router(gateway),'bytes_sent_per_second':None,'bytes_received_per_second':None}
  try:
   import psutil
   io=psutil.net_io_counters()
   if self.previous:
    dt=max(.001,now-self.previous[0]);row['bytes_sent_per_second']=max(0,io.bytes_sent-self.previous[1])/dt;row['bytes_received_per_second']=max(0,io.bytes_recv-self.previous[2])/dt
   self.previous=(now,io.bytes_sent,io.bytes_recv)
  except ImportError:row['traffic_reason']='Adapter byte counters not available in this runtime'
  if now-self.last_discovery>900:self.description=router_description(gateway);self.last_discovery=now
  with self.lock:self.history=(self.history+[row])[-120:];self.sequence+=1
  if self.rails:self.rails.ingest('local_router',{'probe':row['probe'],'tcp':row['tcp'],'wifi':row['wifi'],'bytes_sent_per_second':row['bytes_sent_per_second'],'bytes_received_per_second':row['bytes_received_per_second']},{'latency_ms':'ms','signal_percent':'%','receive_mbps':'Mbps','transmit_mbps':'Mbps','traffic':'bytes/s'},now)
 def configure(self,b):self.enabled=b.get('enabled',True) is True;return self.view()
 def view(self):
  with self.lock:
   attempts=[r for r in self.history if r['probe'].get('attempted')];replies=sum(r['probe']['latency_ms'] is not None for r in attempts);return {'enabled':self.enabled,'sequence':self.sequence,'interval_seconds':5,'history':list(self.history),'latest':self.history[-1] if self.history else None,'router':self.description,'packet_loss_percent':100*(1-replies/len(attempts)) if attempts else None,'scope':'local PC / selected default gateway only; signal metric is not a spatial RF scan'}
 def loop(self):
  while not self.halt.is_set():
   began=time.monotonic()
   if self.enabled:
    try:self.sample()
    except Exception as e:
     with self.lock:self.description={'available':False,'reason':str(e)[:180]}
   self.halt.wait(max(.2,5-(time.monotonic()-began)))
 def close(self):self.halt.set()
