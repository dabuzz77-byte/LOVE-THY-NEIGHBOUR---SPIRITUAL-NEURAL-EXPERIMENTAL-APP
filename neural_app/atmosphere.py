"""Cached global atmosphere/ambience intake; bounded public requests, no model work."""
import copy,json,math,threading,time,hashlib
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from datetime import datetime,timezone
from .earth_baseline import summarize
GRID=[(lat,lon) for lat in (-75,-45,-15,15,45,75) for lon in range(-165,180,30)]
VARS=('temperature_2m','relative_humidity_2m','surface_pressure','wind_speed_10m','wind_direction_10m','cloud_cover','precipitation')
EXTRAS={'solar_magnetic':('https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json','spacecraft measurements'),'solar_plasma':('https://services.swpc.noaa.gov/json/rtsw/rtsw_wind_1m.json','spacecraft measurements'),'geomagnetic_kp':('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json','derived geomagnetic index'),'solar_xray':('https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json','GOES measured X-ray flux'),'earthquakes':('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson','reported seismic measurements')}
def finite(v):return float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) else None
def read_json(url):
 with urlopen(Request(url,headers={'User-Agent':'NeuralApp-Atmosphere/1.0','Accept':'application/json'}),timeout=18) as r:
  raw=r.read(4500001)
  if len(raw)>4500000:raise ValueError('Public feed exceeds size limit')
  return json.loads(raw,parse_constant=lambda _:None)
def normalize_weather(rows,grid=GRID):
 if isinstance(rows,dict):rows=[rows]
 if not isinstance(rows,list) or len(rows)!=len(grid):raise ValueError('Weather grid response count mismatch')
 result=[]
 for loc,(lat,lon) in zip(rows,grid):
  current=loc.get('current',{});hourly=loc.get('hourly',{});values={k:finite(current.get(k)) for k in VARS}
  if all(v is None for v in values.values()):continue
  result.append({'lat':lat,'lon':lon,'model_lat':loc.get('latitude'),'model_lon':loc.get('longitude'),'time':current.get('time'),'values':values,'hours':[{'time':stamp,'values':{k:finite((hourly.get(k) or [])[i]) if i<len(hourly.get(k) or []) else None for k in VARS}} for i,stamp in enumerate(hourly.get('time',[])[:24])]})
 if not result:raise ValueError('No usable weather cells')
 return result
class AtmosphereFeed:
 def __init__(self,data,bus=None,core=None,start=True,fetch=read_json,rails=None):
  self.rails=rails
  self.path=data/'atmosphere-cache.json';self.bus=bus;self.core=core;self.fetch=fetch;self.lock=threading.RLock();self.stop=threading.Event();self.wake=threading.Event();self.enabled=True;self.routing=True;self.influence=.01;self.weather_interval=1800;self.sequence=0;self.weather=[];self.air=[];self.extra={};self.sources={};self.last_weather=0;self.last_air=0;self.worker=None
  if self.path.exists():
   try:
    old=json.loads(self.path.read_text());self.weather=old.get('weather',[]);self.air=old.get('air',[]);self.extra=old.get('extra',{});self.sources=old.get('sources',{});self.sequence=old.get('sequence',0);self.last_weather=old.get('last_weather',0);self.last_air=old.get('last_air',0)
    for s in self.sources.values():s['status']='cached'
   except (OSError,ValueError):pass
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='global-atmosphere-intake');self.worker.start()
 def configure(self,b):
  with self.lock:
   self.enabled=b.get('enabled',self.enabled) is True;self.routing=b.get('routing',self.routing) is True
   value=float(b.get('influence',self.influence))
   if not math.isfinite(value):raise ValueError('Influence must be finite')
   self.influence=max(0,min(.05,value));self.weather_interval=max(1800,min(7200,int(b.get('interval',self.weather_interval))))
  if b.get('refresh') and time.time()-self.last_weather>300:self.last_weather=0;self.wake.set()
  return self.view()
 def source(self,name,url,kind,work):
  try:
   value=work(self.fetch(url));self.sources[name]={'url':url,'kind':kind,'status':'received','fetched':time.time(),'error':None};return value
  except Exception as e:
   prior=self.sources.get(name,{});self.sources[name]={**prior,'url':url,'kind':kind,'status':'cached / stale' if prior.get('fetched') else 'unavailable','error':str(e)[:180]};return None
 def refresh(self):
  with self.lock:
   if not self.enabled:return
  now=time.time()
  if now-self.last_weather>=self.weather_interval:
   params={'latitude':','.join(str(p[0]) for p in GRID),'longitude':','.join(str(p[1]) for p in GRID),'current':','.join(VARS),'hourly':','.join(VARS),'forecast_hours':24,'wind_speed_unit':'ms','timezone':'GMT'}
   url='https://api.open-meteo.com/v1/forecast?'+urlencode(params);weather=self.source('weather',url,'modelled current conditions and forecast',normalize_weather)
   if weather is None:
    fallback='https://api.open-meteo.com/v1/gfs?'+urlencode(params);weather=self.source('weather_gfs',fallback,'GFS model fallback via same Open-Meteo service',normalize_weather)
   if weather is not None:
    with self.lock:self.weather=weather;self.last_weather=now;self.sequence+=1
  if now-self.last_air>=3600:
   p={'latitude':','.join(str(p[0]) for p in GRID),'longitude':','.join(str(p[1]) for p in GRID),'current':'pm2_5,pm10,ozone,nitrogen_dioxide','timezone':'GMT'};url='https://air-quality-api.open-meteo.com/v1/air-quality?'+urlencode(p)
   def air_rows(rows):
    if not isinstance(rows,list) or len(rows)!=len(GRID):raise ValueError('Air grid mismatch')
    return [{'lat':p[0],'lon':p[1],'time':r.get('current',{}).get('time'),'values':{k:finite(r.get('current',{}).get(k)) for k in ('pm2_5','pm10','ozone','nitrogen_dioxide')}} for r,p in zip(rows,GRID)]
   value=self.source('air_quality',url,'CAMS modelled pollutant concentrations',air_rows)
   if value is not None:
    with self.lock:self.air=value;self.last_air=now;self.sequence+=1
  for name,(url,kind) in EXTRAS.items():
   if self.stop.is_set():return
   def parse(value,name=name):
    if name=='earthquakes':return [{'id':r.get('id'),'lat':r['geometry']['coordinates'][1],'lon':r['geometry']['coordinates'][0],'depth_km':r['geometry']['coordinates'][2],'magnitude':r['properties'].get('mag'),'time':r['properties'].get('time'),'place':r['properties'].get('place')} for r in value.get('features',[])[:100]]
    if isinstance(value,list) and value and isinstance(value[0],list):return [dict(zip(value[0],row)) for row in value[-60:] if row is not value[0]]
    if isinstance(value,list):
     eligible=[r for r in value if isinstance(r,dict) and (r.get('active') is not False)]
     return sorted(eligible,key=lambda r:str(r.get('time_tag','')))[-60:]
    raise ValueError('Unrecognised feed format')
   value=self.source(name,url,kind,parse)
   if value is not None:
    with self.lock:self.extra[name]=value
  with self.lock:
   self.sequence+=1;self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps({'weather':self.weather,'air':self.air,'extra':self.extra,'sources':self.sources,'sequence':self.sequence,'last_weather':self.last_weather,'last_air':self.last_air}),encoding='utf-8');tmp.replace(self.path)
  if self.rails:
   units={'temperature_2m':'C','relative_humidity_2m':'%','surface_pressure':'hPa','wind_speed_10m':'m/s','wind_direction_10m':'degrees meteorological','cloud_cover':'%','precipitation':'mm/provider interval'}
   if self.weather:self.rails.ingest('global_weather',self.weather,units,self.weather[0].get('time'))
   if self.air:self.rails.ingest('air_quality',self.air,{'pollutant_concentrations':'microgram/m3'},self.air[0].get('time'))
   for name,value in self.extra.items():
    units={'solar_magnetic':{'bt':'nT','bx_gsm':'nT','by_gsm':'nT','bz_gsm':'nT'},'solar_plasma':{'proton_speed':'km/s','proton_density':'cm^-3','proton_temperature':'K'},'geomagnetic_kp':{'Kp':'index'},'solar_xray':{'flux':'W/m^2'},'earthquakes':{'magnitude':'provider magnitude scale','depth_km':'km'}}.get(name,{})
    self.rails.ingest(name,value,units,value[-1].get('time_tag') if value else None)
  signal=self.signal()
  if self.routing and signal['cells'] and self.bus:
   for target in ('earth','organic','life','silicon'):self.bus.publish({'origin':'global-atmosphere','target':target,'kind':'input','payload':{'atmosphere':signal}})
  if self.core:self.core.ingest({'source':'global-atmosphere','provenance':'observed','kind':'public-environment','outcome':json.dumps({k:v for k,v in signal.items() if k!='samples'})[:1200]})
 def signal(self):
  with self.lock:
   rows=list(self.weather);source=self.sources.get('weather',{});age=time.time()-self.last_weather if self.last_weather else None;values=[]
   stamp=min((r['time'] for r in rows if r.get('time')),default=None)
   try:data_age=max(0,time.time()-datetime.fromisoformat(stamp.replace('Z','+00:00')).replace(tzinfo=timezone.utc).timestamp())
   except (ValueError,AttributeError):data_age=None
   usable=bool(rows) and age is not None and age<10800 and data_age is not None and data_age<10800
   for p in rows:
    v=p['values'];values.extend([(v.get('temperature_2m') or 0)/50,(v.get('relative_humidity_2m') or 0)/100*2-1,((v.get('surface_pressure') or 1013)-1013)/80,(v.get('wind_speed_10m') or 0)/50,(v.get('cloud_cover') or 0)/100*2-1,(v.get('precipitation') or 0)/20])
   samples=[max(-1,min(1,float(v))) for v in values][:512];digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
   return {'balanced_baseline':summarize(rows,GRID),'sequence':self.sequence,'cells':len(rows),'samples':samples if usable and self.routing else [],'influence':self.influence,'usable':usable,'routing':self.routing,'age_seconds':age,'measurement_age_seconds':data_age,'data_kind':'modelled weather; actual published values','source_sha256':digest,'source_time':min((r['time'] for r in rows if r.get('time')),default=None),'weather_received':self.last_weather,'earth_targets':['earth','organic','life','silicon']}
 def view(self):
  with self.lock:return copy.deepcopy({'sequence':self.sequence,'enabled':self.enabled,'routing':self.routing,'influence':self.influence,'interval':self.weather_interval,'grid_degrees':30,'balanced_baseline':summarize(self.weather,GRID),'weather':self.weather,'air_quality':self.air,'extra':self.extra,'sources':self.sources,'signal':self.signal(),'credit':'Weather / air quality: Open-Meteo and contributing national services, CC BY 4.0. Free endpoint for non-commercial use. NOAA SWPC; USGS.','updated':time.time()})
 def loop(self):
  while not self.stop.is_set():
   try:self.refresh()
   except Exception as e:self.sources['worker']={'status':'error','error':str(e)[:200]}
   self.wake.wait(300);self.wake.clear()
 def close(self):self.stop.set();self.wake.set()
