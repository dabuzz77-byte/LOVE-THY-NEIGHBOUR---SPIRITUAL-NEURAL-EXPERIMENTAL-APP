"""Silent official-camera context sampling; never labels page text as video motion."""
import copy, hashlib, os, re, threading, time
from pathlib import Path

class VideoAmbience:
 def __init__(self):
  self.lock=threading.RLock();self.closed=False;self.enabled=True;self.next_at=0;self.next_fetch=0;self.busy=False;self.cursor=0;self.sequence=0;self.latest={};self.records={}
  text=(Path(__file__).resolve().parent.parent/'assets'/'animal_cams.js').read_text(encoding='utf-8')
  self.catalog=[{'id':i,'name':n,'lat':float(a),'lon':float(b),'url':u} for i,n,a,b,u in re.findall(r"id:'([^']+)',name:'([^']+)'.*?lat:([-\d.]+),lon:([-\d.]+),page:'([^']+)'",text)]
 def read(self,row):
  record={**row,'checked':time.time(),'video_measurements':False,'audio_measurements':False}
  try:
   from .reviewed_web import read_page
   page=read_page(row['url']);text=page['text'];record.update(status='source-page-retrieved',bytes=page['bytes'],digest=hashlib.sha256(text.encode()).hexdigest(),context_excerpt=text[:500],scope='Provider page context only; no decoded frames, sound or live animal activity.')
  except Exception as e:record.update(status='unavailable',error=type(e).__name__+': '+str(e)[:180])
  finally:
   with self.lock:self.records[row['id']]=record;self.busy=False
 def tick(self,c):
  now=time.monotonic()
  if self.closed or not self.enabled or now<self.next_at:return
  self.next_at=now+5
  if not self.busy and now>=self.next_fetch and self.catalog:
   row=self.catalog[self.cursor%len(self.catalog)];self.cursor+=1;self.next_fetch=now+300;self.busy=True
   threading.Thread(target=self.read,args=(row,),daemon=True,name='silent-camera-context').start()
  with self.lock:records=[copy.deepcopy(r) for r in self.records.values() if r.get('status')=='source-page-retrieved' and time.time()-r['checked']<3600]
  raw=bytearray(v&127 for v in os.urandom(128));influenced=raw.copy();features=[]
  for row in records:
   local_hour=(time.time()/3600+row['lon']/15)%24
   features.append({'camera':row['id'],'source':row['url'],'checked':row['checked'],'local_solar_hour_approx':round(local_hour,2),'daylight_proxy':6<=local_hour<18,'digest':row['digest'],'basis':'provider context and longitude/time estimate; not measured daylight or motion'})
  if features:
   seed=hashlib.sha256(repr(features).encode()).digest()
   for j in range(0,len(influenced),16):influenced[j]^=seed[j%len(seed)]&127
  self.sequence+=1
  with self.lock:self.latest={'sequence':self.sequence,'active_sources':len(features),'features':features,'influence_fraction':.0625 if features else 0,'video_playing':False,'scope':'Silent inferred camera context; source text never treated as decoded video.'}
  c.bus.publish({'origin':'ambient-video-context','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'sources':[{'name':'untouched-random','text':raw.decode('ascii'),'stochastic':True,'contains_model_text':False},{'name':'camera-context-influenced','text':influenced.decode('ascii'),'stochastic':True,'contains_model_text':False}],'context':self.latest,'provenance':'OS randomness plus explicitly inferred public camera context','video_measurements':False}})
 def view(self):
  with self.lock:return {'enabled':self.enabled,'busy':self.busy,'latest':copy.deepcopy(self.latest),'sources':copy.deepcopy(list(self.records.values())),'refresh_seconds':300,'playback_required':False}
 def close(self):self.closed=True
