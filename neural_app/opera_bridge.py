"""Paired local Opera ↔ desktop coordination. Browser content remains data."""
import collections,copy,threading,time
from urllib.parse import urlsplit
class OperaBridge:
 def __init__(self,runtime,circuit):
  self.runtime=runtime;self.circuit=circuit;self.lock=threading.RLock();self.sequence=0;self.messages=collections.deque(maxlen=64);self.clients={}
 def send(self,body):
  text=body.get('text');url=body.get('url','')
  if not isinstance(text,str) or not 1<=len(text)<=8000:raise ValueError('Use 1–8000 characters')
  if url:
   p=urlsplit(url)
   if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Optional link must be public HTTPS without credentials')
  with self.lock:
   self.sequence+=1;row={'id':self.sequence,'text':text,'url':url,'time':time.time(),'kind':'message-link' if url else 'message'};self.messages.append(row)
  return copy.deepcopy(row)
 def sync(self,body,ident):
  tabs=body.get('tabs',[]);after=body.get('after',0)
  if not isinstance(tabs,list) or len(tabs)>128 or type(after)is not int or after<0:raise ValueError('Use up to 128 tab records and a nonnegative cursor')
  clean=[]
  for tab in tabs:
   if not isinstance(tab,dict):raise ValueError('Tab must be an object')
   p=urlsplit(str(tab.get('url','')))
   if p.scheme!='https' or not p.hostname or p.username or p.password:continue
   clean.append({'url':'https://'+p.netloc+p.path[:1500],'title':str(tab.get('title',''))[:300],'active':tab.get('active')is True,'audible':tab.get('audible')is True,'pinned':tab.get('pinned')is True,'status':str(tab.get('status',''))[:30]})
  with self.lock:
   self.clients[ident]={'last_seen':time.time(),'tabs':clean,'reported_tabs':len(clean),'inventory_enabled':body.get('inventory_enabled')is True,'omitted_tabs':max(0,min(100000,int(body.get('omitted_tabs',0))))}
   reset=after>self.sequence
   rows=[copy.deepcopy(r) for r in self.messages if reset or r['id']>after]
   cursor=self.sequence
   gap=bool(self.messages and after and after<self.messages[0]['id']-1)
  # Private tab metadata is not published onto outward-facing subscribers.
  self.circuit.capture({'origin':'opera-bridge-local','kind':'input','target':'all','payload':{'open_tabs':len(clean),'inventory_enabled':body.get('inventory_enabled')is True,'provenance':'paired-local-browser-summary'}})
  with self.circuit.lock:goal=self.circuit.goal;events=self.circuit.sequence
  return {'connected':True,'time':time.time(),'messages':rows,'cursor':cursor,'history_gap':gap,'cursor_reset':reset,'app':{'goal':goal,'observed_events':events,'engine_layers':len(self.circuit.element_thinking.layers)},'scope':'Local paired bridge; messages displayed as text. Links open only when clicked in Opera. No remote script execution.'}
 def view(self):
  with self.lock:return {'sequence':self.sequence,'clients':copy.deepcopy(self.clients),'messages':copy.deepcopy(list(self.messages)),'direction':'Opera ↔ shared desktop engine','scope':'Permitted visible-page intake plus optional tab inventory; excludes credentials, cookies, private browsing and arbitrary browser commands.'}
