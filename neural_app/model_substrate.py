"""Read-only, bounded GGUF structure and weight-sample observations.

Format reference: https://github.com/ggml-org/ggml/blob/master/docs/gguf.md
Packed quantized bytes are never presented as decoded neural activations.
"""
import collections,hashlib,json,math,os,re,struct,threading,time
from pathlib import Path

SCALARS={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
class Header:
 def __init__(self,path):
  self.path=Path(path);self.size=self.path.stat().st_size;self.file=self.path.open('rb');self.read_bytes=0;self.deadline=time.monotonic()+120;self.cpu_deadline=time.thread_time()+8;self.items=0
 def read(self,n):
  if n<0 or n>1048576 or self.file.tell()+n>self.size or self.read_bytes+n>16777216 or time.monotonic()>self.deadline or time.thread_time()>self.cpu_deadline:raise ValueError('GGUF header read budget or file bounds reached')
  raw=self.file.read(n);self.read_bytes+=len(raw)
  if len(raw)!=n:raise ValueError('Truncated GGUF')
  return raw
 def number(self,fmt):return struct.unpack('<'+fmt,self.read(struct.calcsize('<'+fmt)))[0]
 def skip(self,n):
  if n<0 or self.file.tell()+n>self.size or time.monotonic()>self.deadline or time.thread_time()>self.cpu_deadline:raise ValueError('GGUF skip outside file or time budget')
  self.file.seek(n,1)
 def string(self,keep=True):
  n=self.number('Q')
  if n>16777216:raise ValueError('GGUF string length exceeds budget')
  if keep and n<=4096:return self.read(n).decode('utf-8',errors='replace')
  self.skip(n);return {'bytes':n,'omitted':True}
 def value(self,kind,keep=True,depth=0):
  self.items+=1
  if self.items>2000000 or depth>4:raise ValueError('GGUF metadata item budget reached')
  if kind in SCALARS:
   if kind==7:
    value=self.number('B')
    if value not in (0,1):raise ValueError('Invalid GGUF boolean')
    return bool(value)
   value=self.number(SCALARS[kind]);return value if not isinstance(value,float) or math.isfinite(value) else None
  if kind==8:return self.string(keep)
  if kind!=9:raise ValueError('Unknown GGUF metadata type')
  subtype=self.number('I');count=self.number('Q')
  if count>1000000:raise ValueError('GGUF array exceeds budget')
  if subtype in SCALARS:self.skip(count*struct.calcsize('<'+SCALARS[subtype]))
  else:
   for _ in range(count):self.value(subtype,False,depth+1)
  return {'type':subtype,'count':count,'values_omitted':True}
 def parse(self):
  try:
   if self.read(4)!=b'GGUF':raise ValueError('Not a little-endian GGUF model')
   version=self.number('I')
   if version not in (2,3):raise ValueError('Unsupported GGUF version')
   count=self.number('Q');metadata_count=self.number('Q')
   if count>50000 or metadata_count>10000:raise ValueError('GGUF table exceeds budget')
   metadata={}
   for _ in range(metadata_count):
    key=self.string();kind=self.number('I')
    if not isinstance(key,str):raise ValueError('Metadata key too long')
    value=self.value(kind,not key.startswith('tokenizer.'))
    if key.startswith(('general.','llama.','qwen')) or key.endswith(('context_length','embedding_length','block_count')):metadata[key]=value
   tensors=[]
   for _ in range(count):
    name=self.string();dims=self.number('I')
    if not isinstance(name,str) or not 1<=dims<=4:raise ValueError('Invalid tensor descriptor')
    shape=[self.number('Q') for _ in range(dims)];kind=self.number('I');offset=self.number('Q')
    if any(not 0<n<=10**9 for n in shape) or math.prod(shape)>10**14:raise ValueError('Invalid tensor shape')
    tensors.append({'name':name,'shape':shape,'type_code':kind,'offset':offset,'elements':math.prod(shape)})
   alignment=metadata.get('general.alignment',32)
   if type(alignment)is not int or not 1<=alignment<=1048576 or alignment&(alignment-1):raise ValueError('Invalid GGUF alignment')
   start=(self.file.tell()+alignment-1)//alignment*alignment
   ordered=sorted(tensors,key=lambda r:r['offset'])
   for i,tensor in enumerate(ordered):
    end=ordered[i+1]['offset'] if i+1<len(ordered) else self.size-start
    if tensor['offset']%alignment or end<=tensor['offset'] or start+end>self.size:raise ValueError('Tensor offset is outside its weight region')
    tensor['file_offset']=start+tensor['offset'];tensor['storage_span']=end-tensor['offset']
   return {'version':version,'bytes':self.size,'mtime_ns':self.path.stat().st_mtime_ns,'header_bytes_read':self.read_bytes,'metadata':metadata,'tensors':tensors,'data_offset':start}
  finally:self.file.close()

def artifacts():
 root=Path(os.environ.get('OLLAMA_MODELS',str(Path.home()/'.ollama/models'))).resolve();rows=[]
 for path in (root/'manifests').rglob('*'):
  if not path.is_file() or path.stat().st_size>262144:continue
  rel=path.relative_to(root/'manifests').parts
  if len(rel)<3:continue
  name=('/'.join(rel[2:-1]) if rel[0]=='registry.ollama.ai' else '/'.join(rel[:-1]))+':'+rel[-1]
  if not any(tag in name.casefold() for tag in ('llama3.2','qwen')):continue
  manifest=json.loads(path.read_text(encoding='utf-8'))
  for layer in manifest.get('layers',[]):
   digest=layer.get('digest','')
   if layer.get('mediaType')!='application/vnd.ollama.image.model' or not re.fullmatch(r'sha256:[0-9a-f]{64}',digest):continue
   blob=(root/'blobs'/digest.replace(':','-')).resolve()
   if blob.is_relative_to(root/'blobs') and blob.is_file():rows.append({'model':name,'path':str(blob),'manifest_digest':digest,'bytes':blob.stat().st_size,'family':'llama' if 'llama3.2' in name.casefold() else 'qwen'})
 selected=[]
 for family in ('llama','qwen'):
  candidates=[r for r in rows if r['family']==family]
  if candidates:selected.append(min(candidates,key=lambda r:(0 if any(x in r['model'].casefold() for x in ('uncensored','abliterated')) else 1,r['bytes'])))
 return selected

class ModelSubstrate:
 def __init__(self,data=None):
  self.lock=threading.RLock();self.models=[];self.latest={};self.sequence=0;self.index=0;self.worker=None;self.closed=False;self.next_at=time.monotonic()+20;self.error=None
  self.cache_path=Path(data)/'local-model-structure.json' if data else None
  if self.cache_path:
   try:
    if self.cache_path.stat().st_size>16777216:raise ValueError('Model structure cache exceeds budget')
    saved=json.loads(self.cache_path.read_text(encoding='utf-8'));allowed={r['path']:r for r in artifacts()}
    if not isinstance(saved,list):raise ValueError('Invalid model cache')
    for row in saved[:2]:
     path=row.get('path');artifact=allowed.get(path)
     if artifact and row.get('manifest_digest')==artifact['manifest_digest'] and row.get('bytes')==artifact['bytes'] and row.get('mtime_ns')==Path(path).stat().st_mtime_ns and isinstance(row.get('tensors'),list) and len(row['tensors'])<=50000:self.models.append(row)
   except (OSError,ValueError,TypeError,KeyError,AttributeError):self.models=[]
 def initialise(self):
  loaded=[]
  for artifact in artifacts():
   if self.closed:return
   try:loaded.append({**artifact,**Header(artifact['path']).parse()})
   except Exception as exc:loaded.append({**artifact,'error':str(exc)[:200],'tensors':[]})
  with self.lock:self.models=loaded
  if self.cache_path and any(m['tensors'] for m in loaded):
   temporary=self.cache_path.with_suffix('.tmp');temporary.write_text(json.dumps([m for m in loaded if m['tensors']],allow_nan=False),encoding='utf-8');os.replace(temporary,self.cache_path)
 def tick(self,circuit):
  if self.closed or time.monotonic()<self.next_at or self.worker and self.worker.is_alive():return
  self.next_at=time.monotonic()+5
  self.worker=threading.Thread(target=self.cycle,args=(circuit,),daemon=True,name='local-model-weight-data');self.worker.start()
 def cycle(self,circuit=None):
  node=getattr(circuit,'thin_inference',None)
  if node and node.route=='off':return
  try:
   if not self.models:self.initialise()
   with self.lock:
    valid=[m for m in self.models if m['tensors']]
    if node and node.selected_model:valid=[m for m in valid if m['model']==node.selected_model]
    elif node and node.route in ('llama','qwen'):valid=[m for m in valid if m['family']==node.route]
    if not valid:self.error='No usable tensor index: '+str([m.get('error') for m in self.models])[:180];return
    # Llama gets seven out of eight samples; Qwen supplements sparingly.
    model=next((m for m in valid if m['family']=='qwen'),valid[0]) if self.sequence%8==7 else next((m for m in valid if m['family']=='llama'),valid[0])
    tensor=model['tensors'][self.index%len(model['tensors'])];self.index+=1
   length=min(512,tensor['storage_span']);position=tensor['file_offset']
   stat=Path(model['path']).stat()
   if stat.st_size!=model['bytes'] or stat.st_mtime_ns!=model['mtime_ns']:raise ValueError('Model artifact changed; restart the reader before resampling')
   if tensor['type_code'] in (0,1):length=min(length,tensor['elements']*(4 if tensor['type_code']==0 else 2))
   with Path(model['path']).open('rb') as file:file.seek(position);raw=file.read(length)
   if len(raw)!=length:raise ValueError('Model changed or sample was truncated')
   counts=collections.Counter(raw);entropy=-sum((n/length)*math.log2(n/length) for n in counts.values()) if length else 0
   sample={'model':model['model'],'family':model['family'],'tensor':tensor['name'],'shape':tensor['shape'],'type_code':tensor['type_code'],'file_offset':position,'sample_bytes':length,'sample_sha256':hashlib.sha256(raw).hexdigest(),'manifest_digest':model['manifest_digest'],'full_file_digest_verified':False,'byte_entropy':entropy,'raw_weight_sample_hex':raw.hex(),'provenance':'read-only local GGUF tensor storage sample; not generated text or an activation trace','stochastic':False,'model_calls':0,'semantic_weight_transfer':False}
   if tensor['type_code'] in (0,1):
    size=4 if tensor['type_code']==0 else 2;values=[v[0] for v in struct.iter_unpack('<'+('f' if size==4 else 'e'),raw[:len(raw)//size*size]) if math.isfinite(v[0])]
    sample['decoded_float_summary']={'count':len(values),'minimum':min(values) if values else None,'maximum':max(values) if values else None,'mean':sum(values)/len(values) if values else None}
   else:sample['decoding']='Packed quantization bytes retained; not treated as decoded floating-point weights'
   with self.lock:self.sequence+=1;sample['sequence']=self.sequence;self.latest=sample;self.error=None
   if circuit is not None and not self.closed:circuit.bus.publish({'origin':'local-model-weight-data','target':'all','kind':'stage-output','payload':sample})
  except Exception as exc:
   with self.lock:self.error=str(exc)[:240]
 def close(self):self.closed=True
 def view(self):
  with self.lock:return {'sequence':self.sequence,'busy':bool(self.worker and self.worker.is_alive()),'latest':dict(self.latest),'error':self.error,'models':[{k:v for k,v in m.items() if k not in ('tensors','path')}|{'tensor_count':len(m['tensors'])} for m in self.models],'policy':'Read-only local structure plus up to 512 tensor-storage bytes per five-second cycle; Llama-first, sparse Qwen. No duplicated weight files, weight mutation, model inference or automatic acquisition of model capabilities.'}
