"""Process-local memory bounds for Nexus-owned Ollama HTTP requests."""
import functools,json,urllib.request
from urllib.parse import urlsplit

def bound_payload(url,data):
 try:
  address=urlsplit(str(url))
  if address.hostname not in ('127.0.0.1','localhost','::1') or address.port!=11434 or address.path not in ('/api/chat','/api/generate') or data is None:return data
  payload=json.loads(data)
  if not isinstance(payload,dict):return data
  options=dict(payload.get('options') or {})
  def bounded(value,default,limit):
   try:return max(1,min(limit,int(value))) if not isinstance(value,bool) else default
   except (ValueError,TypeError,OverflowError):return default
  options['num_ctx']=bounded(options.get('num_ctx',4096),4096,8192)
  options['num_batch']=bounded(options.get('num_batch',128),128,128)
  payload['options']=options
  if payload.get('keep_alive') not in (0,'0','0s'):payload['keep_alive']='30s'
  return json.dumps(payload,ensure_ascii=False).encode('utf8')
 except (ValueError,TypeError,AttributeError,UnicodeError):return data

def install():
 """Patch the existing Request class in place, including previously imported aliases."""
 original=urllib.request.Request.__init__
 if getattr(original,'_nexus_memory_bounded',False):return
 @functools.wraps(original)
 def initialize(self,url,data=None,*args,**kwargs):
  return original(self,url,bound_payload(url,data),*args,**kwargs)
 initialize._nexus_memory_bounded=True
 urllib.request.Request.__init__=initialize
