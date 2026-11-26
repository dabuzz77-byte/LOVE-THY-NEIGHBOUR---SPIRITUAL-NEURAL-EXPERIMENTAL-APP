"""Long-lived, local source instances. Web text remains data, never executable code."""
import ast,base64,collections,contextlib,hashlib,hmac,io,json,math,os,pathlib,secrets,sys,time,typing,uuid,copy
from typing import *
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
ROOT=pathlib.Path(__file__).resolve().parent
SAFE={'get_public_bytes','sign_inference_payload','log_node_telemetry','update_node_metrics','route_inference_chunk','validate_routing_path','verify_node_privilege','llmd_endpoint_picker','evaluate_inference_intent','evaluate_systemic_alignment','dispatch_action','execute_high_velocity_conceptual_stream','resolve_star_tracker_attitude'}
SENSITIVE=('secret','private','password','key','token')
def safe(x):
 if isinstance(x,bytes):return {'hex':x.hex(),'encoding':'bytes'}
 if isinstance(x,set):return sorted(x)
 if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items() if not any(s in str(k).lower() for s in SENSITIVE)}
 if isinstance(x,(list,tuple)):return [safe(v) for v in x]
 if x is None or isinstance(x,(str,int,bool)):return x
 if isinstance(x,float):return x if math.isfinite(x) else str(x)
 return '<'+type(x).__name__+'>'
def find(payload,name):
 todo=[payload];count=0
 while todo and count<250:
  obj=todo.pop(0);count+=1
  if isinstance(obj,dict):
   if name in obj:return True,obj[name]
   todo.extend(v for v in obj.values() if isinstance(v,(dict,list)))
  elif isinstance(obj,list):todo.extend(obj[:40])
 return False,None
class ResidentEngines:
 def __init__(self,root=ROOT):
  self.root=root;self.catalog=json.loads((root/'inference_catalog.json').read_text(encoding='utf8'))['modules'];self.instances={};self.started=time.time();self.count=0
  folder=pathlib.Path(__file__).resolve().parents[3]/'data'/'inference';folder.mkdir(exist_ok=True);keyfile=folder/'autonomous.key'
  if not keyfile.exists():keyfile.write_bytes(secrets.token_bytes(32))
  master=keyfile.read_bytes()
  for m in self.catalog:
   item={'id':m['id'],'name':m['name'],'received':0,'source_calls':0,'status':'listening','last_result':None};self.instances[m['id']]=item
   ns=dict(globals());ns['genai']=None
   try:
    with contextlib.redirect_stdout(io.StringIO()):
     exec(compile(m['source'],m['id'],'exec'),ns)
     target=ns[m['name']]
     if m['kind']=='class':
      init=next((f for f in m['methods'] if f['name']=='__init__'),{'args':[]});args={}
      for a in init['args']:
       n=a['name']
       if a['type']=='bytes':args[n]=hmac.new(master,m['id'].encode(),hashlib.sha256).digest()
       elif any(v in n for v in ['reserve','pool']):args[n]=0.0
       elif a['default'] is not None:args[n]=ast.literal_eval(a['default'])
       elif n=='node_id':args[n]='inference-observatory'
       elif n=='max_allowed_latency_ms':args[n]=150
       elif n=='min_available_vram_gb':args[n]=0.0
       else:raise ValueError('Missing initialization field: '+n)
      target=target(**args)
    item['_target']=target
    if m['name']=='FractalFluxDispatcher':
     item['_dispatch']=[];target.register_store_pipeline(lambda packet,out=item['_dispatch']:out.append(safe(packet)))
   except Exception as e:item.update(status='initialization_error',error=type(e).__name__+': '+str(e))
 def process(self,envelope):
  self.count+=1;raw=envelope.get('text','').encode();digest=hashlib.sha256(raw).digest();payload=envelope.get('data',{});results=[]
  for m in self.catalog:
   item=self.instances[m['id']];item['received']+=1;calls=[];waiting=[];out=io.StringIO();target=item.get('_target');error=item.get('error');status='waiting_for_fields'
   try:
    with contextlib.redirect_stdout(out):
     if target is None:status='initialization_error'
     elif m['name']=='MeshSecurityController':
      node=str(envelope.get('producer','unknown-source'))[:180]
      if node not in target.active_mesh:target.register_node(node)
      reported=payload.get('status') if isinstance(payload,dict) else None
      if reported in ['complete','error','success','failed']:
       target.log_node_telemetry(node,reported in ['complete','success']);calls.append({'method':'log_node_telemetry','result':safe(target.active_mesh[node]),'basis':'Reported local producer status; quarantine affects only this source instance'})
      else:waiting.append({'method':'log_node_telemetry','fields':['explicit producer success/failure status']})
     else:
      for method in m['methods']:
       name=method['name']
       if name not in SAFE:continue
       args={};missing=[]
       for a in method['args']:
        n=a['name'];found,value=find(payload,n)
        if n=='workload_hash':found,value=True,digest
        elif n=='abstract_prompt':found,value=True,envelope.get('text','')
        elif n=='cognitive_velocity':found,value=True,self.count/max(time.time()-self.started,1)
        elif n=='payload':found,value=True,copy.deepcopy(payload)
        elif n=='action_type':found,value=True,'INPUT_OBSERVED'
        if found:args[n]=value
        elif a['default'] is not None:args[n]=ast.literal_eval(a['default'])
        else:missing.append(n)
       # This source explicitly dereferences resource_efficiency. Never invent an ethical score or hardware measurement.
       if name=='evaluate_inference_intent' and 'resource_efficiency' not in args.get('payload',{}):missing.append('payload.resource_efficiency')
       if missing:waiting.append({'method':name,'fields':missing});continue
       value=target(**args) if m['kind']=='function' else getattr(target,name)(**args)
       calls.append({'method':name,'result':safe(value),'basis':'Original algorithm operating on identified live data; numeric resource effects are local software calculations'})
     if calls:status='executed'
     if target is not None and not calls and not waiting:waiting=[{'method':'typed domain methods','fields':['Compatible structured source fields; automatic transfers/privilege changes are disabled']}]
   except Exception as e:status='source_error';error=type(e).__name__+': '+str(e)
   item['source_calls']+=len(calls);item['status']=status
   result={'id':m['id'],'name':m['name'],'status':status,'received':item['received'],'source_calls':item['source_calls'],'input_id':envelope['id'],'source':envelope['source'],'input_sha256':digest.hex(),'input_bytes':len(raw),'methods':calls,'awaiting':waiting,'error':error,'stdout':out.getvalue()[:12000],'timestamp':time.time()}
   item['last_result']=result;results.append(result)
   if item.get('_dispatch'):item['_dispatch'].clear()
  return {'input_id':envelope['id'],'engines':results,'actual_source_calls':sum(len(r['methods']) for r in results),'processed':time.time()}
if __name__=='__main__':
 engines=ResidentEngines()
 print(json.dumps({'ready':True,'engines':len(engines.instances)}),flush=True)
 for line in sys.stdin:
  try:print(json.dumps(engines.process(json.loads(line)),ensure_ascii=True,allow_nan=False),flush=True)
  except Exception as e:print(json.dumps({'error':str(e)}),flush=True)
