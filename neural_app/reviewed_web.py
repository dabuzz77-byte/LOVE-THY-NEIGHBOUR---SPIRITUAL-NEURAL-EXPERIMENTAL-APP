"""Read one reviewed public HTTPS page with pinned DNS and bounded output."""
import http.client,ipaddress,socket,ssl
from urllib.parse import urlsplit,urljoin
from html.parser import HTMLParser
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript'):self.skip+=1
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript'):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip and data.strip():self.parts.append(data.strip())
def read_page(url,redirects=2):
 parsed=urlsplit(str(url));host=parsed.hostname
 if parsed.scheme!='https' or not host or parsed.username or parsed.password or parsed.port not in (None,443):raise ValueError('Use a public HTTPS URL without credentials or custom ports')
 addresses=list(dict.fromkeys(row[4][0] for row in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)))
 if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):raise PermissionError('Private, local and reserved network addresses are excluded')
 address=addresses[0]
 class Pinned(http.client.HTTPSConnection):
  def connect(self):
   raw=socket.create_connection((address,443),timeout=10)
   self.sock=ssl.create_default_context().wrap_socket(raw,server_hostname=host)
 connection=Pinned(host,443,timeout=10)
 try:
  path=(parsed.path or '/')+('?' +parsed.query if parsed.query else '')
  connection.request('GET',path,headers={'Host':host,'User-Agent':'NeuralAppReviewedResearch/1.0','Accept':'text/html,text/plain,application/json','Accept-Encoding':'identity'})
  response=connection.getresponse()
  if response.status in (301,302,303,307,308):
   location=response.getheader('Location')
   if redirects<=0 or not location:raise ValueError('Public source redirect limit reached or no destination supplied')
   destination=urljoin(url,location);result=read_page(destination,redirects-1);result['redirect_chain']=[url]+result.get('redirect_chain',[]);result['requested_url']=url;return result
  if response.status!=200:raise ValueError('Page returned HTTP '+str(response.status))
  kind=response.getheader('Content-Type','').lower()
  if not any(v in kind for v in ('text/','application/json','application/xml','application/rss+xml','application/atom+xml')):raise ValueError('Choose a text, HTML or JSON page')
  raw=response.read(262145)
  byte_truncated=len(raw)>262144;raw=raw[:262144]
  text=raw.decode('utf-8',errors='replace')
  if 'html' in kind:parser=Text();parser.feed(text);text='\n'.join(parser.parts)
  return {'url':url,'bytes':len(raw),'text':text[:64000],'text_truncated':byte_truncated or len(text)>64000,'byte_truncated':byte_truncated,'kind':'reviewed public HTTPS text'}
 finally:connection.close()
