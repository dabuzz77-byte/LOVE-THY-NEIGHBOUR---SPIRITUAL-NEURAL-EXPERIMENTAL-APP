"""Fixed public scientific/audio sources. No arbitrary URL proxy or uploads."""
import json,time,urllib.request,urllib.parse,threading
from datetime import datetime,timezone
from pathlib import Path

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def fetch(url,limit=2_000_000):
 request=urllib.request.Request(url,headers={'User-Agent':'NeuralApp/1.0 (local educational recording player)'})
 with urllib.request.build_opener(NoRedirect()).open(request,timeout=10) as response:
  raw=response.read(limit+1)
  if len(raw)>limit:raise ValueError('Source response exceeded the size limit')
  return raw

class EarthFieldSources:
 def __init__(self,data):
  self.data=Path(data)/'earth-field';self.data.mkdir(parents=True,exist_ok=True);self.lock=threading.Lock();self.last=0;self.magnetic=None;self.stations=[];self.station_at=0
 def geomagnetic(self):
  with self.lock:
   if self.magnetic and time.monotonic()-self.last<55:return self.magnetic
   errors=[]
   for role in ['primary','secondary']:
    url=f'https://services.swpc.noaa.gov/json/goes/{role}/magnetometers-6-hour.json'
    try:
     rows=json.loads(fetch(url));valid=[r for r in rows if isinstance(r,dict) and isinstance(r.get('total'),(int,float)) and r.get('time_tag') and not r.get('arcjet_flag',False)]
     if not valid:raise ValueError('No valid magnetometer samples')
     latest=max(valid,key=lambda r:r['time_tag']);stamp=datetime.fromisoformat(latest['time_tag'].replace('Z','+00:00'));age=max(0,time.time()-stamp.timestamp())
     value={'mode':'recent' if age<900 else 'stale','source':url,'units':'nT','sample':latest,'sample_age_seconds':round(age),'retrieved_at':datetime.now(timezone.utc).isoformat(),'fallback':role!='primary','errors':errors}
     (self.data/'magnetic-cache.json').write_text(json.dumps(value),encoding='utf-8');self.last=time.monotonic();self.magnetic=value;return value
    except Exception as exc:errors.append(role+': '+str(exc)[:130])
   file=self.data/'magnetic-cache.json'
   if file.exists():
    value=json.loads(file.read_text(encoding='utf-8'));value.update(mode='cached',errors=errors);self.last=time.monotonic();self.magnetic=value;return value
   return {'mode':'unavailable','errors':errors,'sample':None}
 def catalogue(self):
  if time.monotonic()-self.station_at<300 and self.stations:return {'stations':self.stations,'source':'https://locusonus.org/soundmap/'}
  rows=json.loads(fetch('https://locus.creacast.com:9443/status-json.xsl')).get('icestats',{}).get('source',[]);rows=rows if isinstance(rows,list) else [rows];stations=[]
  for item in rows:
   parsed=urllib.parse.urlsplit(item.get('listenurl',''));name=parsed.path.lstrip('/')
   if parsed.hostname=='locus.creacast.com' and '/' not in name and name.endswith(('.mp3','.ogg')) and len(name)<180:
    stations.append({'id':name,'name':item.get('server_name',name),'type':item.get('server_type','audio/mpeg')})
  self.stations=stations;self.station_at=time.monotonic();return {'stations':stations,'source':'https://locusonus.org/soundmap/'}
 def stream(self,handler,station):
  self.catalogue()
  if station not in {s['id'] for s in self.stations}:raise ValueError('Select an available listed station')
  url='https://locus.creacast.com:9443/'+urllib.parse.quote(station,safe='._-')
  with urllib.request.build_opener(NoRedirect()).open(url,timeout=10) as response:
   kind=response.headers.get('Content-Type','audio/mpeg')
   if not ('audio/' in kind or 'ogg' in kind):raise ValueError('The source did not return audio')
   handler.send_response(200);handler.send_header('Content-Type',kind);handler.send_header('Cache-Control','no-store');handler.send_header('Connection','close');handler.end_headers();handler.close_connection=True
   deadline=time.monotonic()+90;total=0
   while time.monotonic()<deadline and total<8_000_000:
    data=response.read(4096)
    if not data:break
    try:handler.wfile.write(data);handler.wfile.flush()
    except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):break
    total+=len(data)


def chant_recording(ident):
 import base64
 sources={'om':'https://www.buddhanet.net/filelib/audio/omm.wav','gelug':'https://www.buddhanet.net/filelib/audio/gelug_chant.wav',
 'bottlenose':'https://www.fisheries.noaa.gov/s3/2023-04/Tutr-multisound-NOAA-PAGroup-03-bottlenose-dolphin-clip.mp3',
 'spotted':'https://www.fisheries.noaa.gov/s3/2023-04/Stfr-Multisound-NOAA-PAGroup-01-atlantic-spotted-dolphin-clip.mp3',
 'white-sided':'https://www.fisheries.noaa.gov/s3/2023-04/Laac-whistles-NOAA-PAGroup-01-atlantic-white-sided-dolphin-clip.mp3',
 'humpback':'https://www.fisheries.noaa.gov/s3/2023-04/Meno-song-NOAA-PAGroup-13-humpback-clip.mp3',
 'minke':'https://www.fisheries.noaa.gov/s3/2023-04/Baac-pulsetrains-NOAA-PAGroup-25-minke-clip.mp3',
 'blue-x8':'https://www.fisheries.noaa.gov/s3/2023-04/Cornell-NY-LongIsland-20090123-000000-LPfilter20-amplified-x8speed-blue-clip.mp3',
 'beluga':'https://www.fisheries.noaa.gov/s3/2023-04/Dele-multisound-NOAA-Castellote-01-beluga-clip.mp3',
 'sperm':'https://www.fisheries.noaa.gov/s3/2023-04/Phma-clicks-NOAA-PAGroup-01-sperm-clip.mp3',
 'rain':'https://www.fisheries.noaa.gov/s3/2023-04/Rain-GRNMS-NOAA-PAGroup-02-rain-clip.mp3',
 'beach':'https://upload.wikimedia.org/wikipedia/commons/b/b9/Small_sea_waves_at_rocky_beach.opus',
 'ice-singing':'https://www.fisheries.noaa.gov/s3/2023-04/Ice-singing-AWI-Van-Opzeeland-02-ice-singing-clip.mp3',
 'ice-calving':'https://www.fisheries.noaa.gov/s3/2023-04/Ice-Calving-AWI-Van-Opzeeland-03-ice-calving-clip.mp3',
 'cat-purr':'https://upload.wikimedia.org/wikipedia/commons/c/c8/Cat_purring.ogg',
 'dog-bark':'https://upload.wikimedia.org/wikipedia/commons/c/ce/Sound-of-dog.ogg',
 'robin':'https://upload.wikimedia.org/wikipedia/commons/8/8d/Erithacus_rubecula.ogg',
 'nightingale':'https://upload.wikimedia.org/wikipedia/commons/6/64/Thrush_Nightingale_song.ogg'}
 if ident not in sources:raise ValueError('Choose a listed chant recording')
 raw=fetch(sources[ident],2_000_000)
 if not ((raw[:4]==b'RIFF' and raw[8:12]==b'WAVE') or raw[:4]==b'OggS' or raw[:3]==b'ID3' or (len(raw)>2 and raw[0]==255 and raw[1]&224==224)):raise ValueError('Provider did not return recognized WAV/MP3/Ogg audio')
 original_bytes=len(raw)
 if raw[:4]==b'RIFF':
  from .audio_decode import browser_wav
  raw=browser_wav(raw)
 credits={'rain':'NOAA Fisheries / Gray’s Reef National Marine Sanctuary','beach':'mnalis / Wikimedia Commons · CC BY 3.0','ice-singing':'Alfred Wegener Institute / Ilse van Opzeeland, via NOAA Fisheries','ice-calving':'Alfred Wegener Institute / Ilse van Opzeeland, via NOAA Fisheries','cat-purr':'Peter Hull / Wikimedia Commons · CC BY-SA 4.0','dog-bark':'Kriplozoik / Wikimedia Commons · CC BY-SA 3.0','robin':'Vladimir Yu. Arkhipov / Wikimedia Commons · CC BY-SA 3.0','nightingale':'Martin Vavrik / Wikimedia Commons · CC BY 3.0'}
 return {'base64':base64.b64encode(raw).decode('ascii'),'source':sources[ident],'credit':credits[ident] if ident in credits else 'BuddhaNet / original recording owners' if ident in ('om','gelug') else 'NOAA Fisheries / credited original recordist; blue sample credited to Cornell and presented at 8× speed','bytes':len(raw),'original_bytes':original_bytes,'pcm_conversion':original_bytes!=len(raw),'kind':'real recording, not synthesized speech'}
