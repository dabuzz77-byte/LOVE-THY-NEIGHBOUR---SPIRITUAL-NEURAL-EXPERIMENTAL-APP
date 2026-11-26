"""Automatic bounded computations over registered engine observations."""
import collections, copy, hashlib, json, math, threading, time
class SectionMind:
 def __init__(self,saved=None):
  self.lock=threading.RLock();self.rows={};self.history=collections.deque(maxlen=96);self.sequence=0
  from .online_prediction import OnlinePrediction
  self.predictor=OnlinePrediction(saved)
 def process(self,row):
  key=row['id'];facts=row.get('observations',[])[:12]
  digest=hashlib.sha256(json.dumps([row.get('source'),facts],sort_keys=True,default=str).encode()).hexdigest()
  with self.lock:
   old=self.rows.get(key,{})
   if old.get('digest')==digest and old.get('parent_event')==row.get('parent_event'):return copy.deepcopy(old)
   numeric={};paths={};texts=[]
   for fact in facts:
    raw_path=fact.get('path',[]);path=json.dumps(raw_path,ensure_ascii=True);v=fact.get('value');paths[path]=raw_path
    if any(x in path.lower() for x in ('password','secret','token','credential','authorization')):continue
    if type(v) in (int,float) and math.isfinite(v) and abs(v)<=1e100:numeric[path]=v
    elif isinstance(v,str):texts.append(v[:512])
   previous=old.get('numeric',{}) if old.get('source')==row.get('source') else {}
   errors=[abs(v-previous[p]) for p,v in numeric.items() if p in previous]
   changed=sum(v!=previous.get(p) for p,v in numeric.items())
   forecasts=[self.predictor.observe(key,row.get('source'),paths[path],value,row.get('parent_event')) for path,value in numeric.items()]
   values=list(numeric.values());text=' '.join(texts)
   result={'numeric_count':len(values),'minimum':min(values) if values else None,'maximum':max(values) if values else None,'text_characters':len(text),'text_words':len(text.split()),'changed_numeric_paths':changed}
   # No aggregation of incompatible units: range is descriptive, never a physical total.
   check={'finite':all(math.isfinite(v) for v in numeric.values()),'count_matches':len(values)==result['numeric_count'],'previous_forecast_samples':len(errors),'previous_persistence_MAE':sum(errors)/len(errors) if errors else None}
   self.sequence+=1
   record={'id':key,'title':row.get('title',key),'sequence':self.sequence,'time':time.time(),'source':row.get('source'),'parent_event':row.get('parent_event'),'digest':digest,'numeric':numeric,'status':'checked' if facts else 'waiting','action':'Measure changed observations and check prior persistence forecast' if facts else 'Wait for source observations','result':result,'verification':check,'next_prediction':{json.dumps(f['path'],ensure_ascii=True):f['next_prediction'] for f in forecasts},'forecast_tests':forecasts,'memory_updates':old.get('memory_updates',0)+bool(facts),'model_calls':0}
   self.rows[key]=record
   if facts:self.history.append({k:copy.deepcopy(v) for k,v in record.items() if k not in ('numeric','next_prediction','digest')})
   return copy.deepcopy(record)
 def view(self):
  with self.lock:return {'sequence':self.sequence,'stages':[{k:copy.deepcopy(v) for k,v in r.items() if k not in ('numeric','next_prediction','digest')} for r in self.rows.values()],'recent':list(self.history)[-24:],'predictive_learning':self.predictor.view(),'scope':'Automatic observation computations and checked forecast feedback across registered engine stages. No arbitrary command execution.'}
