"""Installed local assistant selection, independent of background workers."""
import os,json
from pathlib import Path
from .work_tools import MODEL
def installed():
 root=Path(os.environ.get('OLLAMA_MODELS',str(Path.home()/'.ollama/models')))/'manifests'
 rows=[]
 if root.is_dir():
  for p in root.rglob('*'):
   if not p.is_file():continue
   parts=p.relative_to(root).parts
   if len(parts)<3:continue
   if parts[0]=='registry.ollama.ai' and len(parts)>=4:name='/'.join(parts[2:-1])+':'+parts[-1]
   else:name='/'.join(parts[:-1])+':'+parts[-1]
   try:
    manifest=json.loads(p.read_text(encoding='utf-8'));size=sum(int(layer.get('size',0)) for layer in manifest.get('layers',[]))
   except (OSError,ValueError,TypeError):size=0
   rows.append({'name':name,'label':name,'size_bytes':size,'family':'Qwen' if 'qwen' in name.lower() else 'Gemma' if 'gemma' in name.lower() else 'Llama' if 'llama' in name.lower() else 'Other'})
 return sorted(rows,key=lambda r:r['name'].lower())
def view(reasoner):
 with reasoner.lock:selected=reasoner.s.get('assistant_model',MODEL)
 return {'selected':selected,'models':installed(),'generation':reasoner.s.get('assistant_generation',{'context_tokens':131072,'max_output_tokens':32768}),'scope':'Main Native AI conversational assistant; background native processing stays unchanged'}
def select(reasoner,body):
 name=str(body.get('model',''));names={r['name'] for r in installed()}
 if name not in names:raise ValueError('Choose an installed model from the list')
 generation={}
 for key,default,lo,hi in [('context_tokens',131072,4096,131072),('max_output_tokens',32768,256,32768)]:
  value=body.get(key,reasoner.s.get('assistant_generation',{}).get(key,default))
  if type(value) is not int or not lo<=value<=hi:raise ValueError('Choose a valid '+key.replace('_',' '))
  generation[key]=value
 if generation['max_output_tokens']>=generation['context_tokens']:raise ValueError('Output limit must leave room for input context')
 with reasoner.lock:
  reasoner.s['assistant_model']=name;reasoner.s['assistant_generation']=generation;reasoner.s['model_cache'].clear();reasoner.controller.save()
 return view(reasoner)
