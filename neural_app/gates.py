"""Trainable external engine gates for Llama context, not Llama transformer weights."""
import json,math,threading,time
from dataclasses import asdict,is_dataclass
from pathlib import Path
class EngineWeights:
 def __init__(self,data,modules):
  self.path=Path(data)/'engine-weights.json';self.lock=threading.RLock();self.enabled=True;self.rows={id:{'logit':0.,'samples':0,'successes':0,'errors':0,'delivered':0,'loss_sum':0.,'evidence':None,'updated':None} for id in modules};self.updates=0;self.last_save=0
  try:
   saved=json.loads(self.path.read_text());self.enabled=bool(saved.get('enabled',True));self.updates=int(saved.get('updates',0))
   for id,row in saved.get('rows',{}).items():
    if id in self.rows and math.isfinite(float(row.get('logit',0))):self.rows[id].update(row)
  except (OSError,ValueError,TypeError):pass
 def compact(self,v,depth=0):
  if depth>3:return '<detail available through source/receipt retrieval>'
  if is_dataclass(v) and not isinstance(v,type):return self.compact(asdict(v),depth)
  if hasattr(type(v),'tolist'):return self.compact(v.tolist(),depth)
  if isinstance(v,dict):return {str(k):self.compact(x,depth+1) for k,x in list(v.items())[:18] if not any(w in str(k).lower() for w in ('password','secret','token','api_key')) and (not isinstance(x,list) or len(x)<=12)}
  if isinstance(v,list):return [self.compact(x,depth+1) for x in v[:12]]
  if v is None or isinstance(v,(str,int,float,bool)):return v[:500] if isinstance(v,str) else v
  return str(v)[:500]
 def observe(self,item):
  id=item.get('module');status=item.get('status')
  if id not in self.rows:return
  with self.lock:
   row=self.rows[id]
   if status in ('input-available','delivered-to-input'):row['delivered']+=1;return
   if status not in ('processed','error'):return
   row['evidence']={'status':status,'result':self.compact(item.get('result')),'time':item.get('time',time.time()),'message_id':item.get('message_id')};row['updated']=time.time()
   if not self.enabled:return
   prediction=1/(1+math.exp(-row['logit']));target=1. if status=='processed' else 0.;row['loss_sum']+=-(target*math.log(max(prediction,1e-9))+(1-target)*math.log(max(1-prediction,1e-9)));row['logit']=max(-6,min(6,row['logit']+.05*(target-prediction)));row['samples']+=1;row['successes']+=int(target);row['errors']+=int(not target);self.updates+=1
   if time.monotonic()-self.last_save>30:self.save()
 def view(self):
  with self.lock:
   denominator=sum(math.exp(r['logit']) for r in self.rows.values()) or 1
   rows=[{'id':id,'weight':math.exp(r['logit'])/denominator,'reliability':1/(1+math.exp(-r['logit'])),'samples':r['samples'],'successes':r['successes'],'errors':r['errors'],'delivered':r['delivered'],'mean_online_loss':r['loss_sum']/r['samples'] if r['samples'] else None,'updated':r['updated']} for id,r in self.rows.items()]
   return {'enabled':self.enabled,'updates':self.updates,'engines':sorted(rows,key=lambda x:x['weight'],reverse=True),'scope':'External learned reliability gates select engine evidence for Llama. These are not Llama internal weights. Processing success is not semantic correctness; delivered-only inputs do not train the gate.'}
 def context(self,limit=6):
  with self.lock:
   ranked=self.view()['engines'];return {'layer':'Nexus external engine-weight adapter','scope':self.view()['scope'],'updates':self.updates,'engine_weights':[{k:r[k] for k in ('id','weight','reliability','samples')} for r in ranked],'weighted_evidence':[{'module':r['id'],'weight':r['weight'],'evidence':json.dumps(self.rows[r['id']]['evidence'],default=str)[:1400]} for r in ranked if self.rows[r['id']]['evidence'] is not None][:limit]}
 def configure(self,b):
  if type(b.get('enabled')) is not bool:raise ValueError('Choose enabled true or false')
  with self.lock:self.enabled=b['enabled'];self.save()
  return self.view()
 def save(self):
  with self.lock:
   temporary=self.path.with_suffix('.tmp');temporary.write_text(json.dumps({'format':'nexus-external-engine-gates-v1','enabled':self.enabled,'updates':self.updates,'rows':self.rows}),encoding='utf8');temporary.replace(self.path);self.last_save=time.monotonic()
