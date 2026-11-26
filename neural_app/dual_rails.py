"""Dual raw/rolling-median telemetry with bounded storage and exact bus framing."""
import collections,hashlib,json,math,statistics,threading,time
class DualRails:
 def __init__(self,bus=None):self.bus=bus;self.lock=threading.RLock();self.sources={};self.windows={};self.window=9;self.sequence=0
 def numeric(self,value,path='',out=None):
  out={} if out is None else out
  if len(out)>=2048:return out
  if isinstance(value,str):
   try:value=float(value)
   except ValueError:return out
  if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):
   if path.lower().split('.')[-1] not in ('time','time_tag','stamp','lat','lon','latitude','longitude','sequence','id','age','age_seconds','status','active','sample_size'):out[path]=float(value)
  elif isinstance(value,dict):
   for key,v in list(value.items())[:128]:
    if key not in ('hours','forecast','coordinates','samples','waveform'):self.numeric(v,(path+'.' if path else '')+str(key),out)
  elif isinstance(value,list):
   for i,v in enumerate(value[:128]):self.numeric(v,path+'.'+str(i),out)
  return out
 def ingest(self,source,raw,units=None,measured_at=None):
  encoded=json.dumps(raw,ensure_ascii=True,allow_nan=False,sort_keys=True);digest=hashlib.sha256(encoded.encode()).hexdigest()
  with self.lock:
   old=self.sources.get(source)
   if old and old['sha256']==digest:return old
   metrics=self.numeric(raw);windows=self.windows.setdefault(source,{})
   for key,val in metrics.items():windows.setdefault(key,collections.deque(maxlen=self.window)).append(val)
   medians={key:(min(windows[key],key=lambda a:sum(abs((a-b+180)%360-180) for b in windows[key])) if 'wind_direction' in key else statistics.median(windows[key])) for key in metrics};self.sequence+=1
   row={'source':source,'sequence':self.sequence,'time':time.time(),'measured_at':measured_at,'sha256':digest,'units':units or {},'raw':raw,'median':medians,'median_samples':{k:len(windows[k]) for k in metrics},'window':self.window,'scope':'raw retained source values; medians exclude coordinates, timestamps and forecast steps'};self.sources[source]=row
   if len(self.sources)>32:
    oldest=next(iter(self.sources));self.sources.pop(oldest);self.windows.pop(oldest,None)
  if self.bus:
   for rail,value in [('raw',raw),('median',medians)]:
    text=json.dumps(value,ensure_ascii=True,allow_nan=False);parts=[text[i:i+10000] for i in range(0,len(text),10000)]
    if len(parts)>96:raise ValueError('Rail snapshot too large')
    for i,part in enumerate(parts):self.bus.publish({'target':'all','kind':'input','origin':'ambience-dual-rail','payload':{'ambience_rail':rail,'source':source,'snapshot':row['sequence'],'sha256':hashlib.sha256(text.encode()).hexdigest(),'part':i,'parts':len(parts),'data':part,'measured_at':measured_at,'units':units or {},'predefined_text':True,'contains_model_text':False,'stochastic':False}})
  return row
 def view(self,source=None):
  with self.lock:
   rows={source:self.sources[source]} if source in self.sources else self.sources if source is None else {}
   return json.loads(json.dumps({'sequence':self.sequence,'window':self.window,'sources':rows},default=list))
