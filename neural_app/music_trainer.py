"""Native music practice and read-only installed plugin inventory."""
import time,threading,collections,io,wave,math,copy
from pathlib import Path
from .media_skills import pcm
LESSONS=[('Rhythm and sequencing','Build a 16-step pattern; compare pulse, subdivision, syncopation and rests.'),('Pitch and harmony','Use MIDI note numbers, intervals, scales and chord voicings.'),('Synthesis','Compare sine, triangle, sawtooth and square oscillators with amplitude envelopes.'),('Sampling','Study sample rate, pitch, envelopes, looping and source permissions.'),('Arrangement','Develop patterns into sections with contrast and continuity.'),('Mixing','Balance levels and panning; preserve headroom and compare masking.'),('Equalisation','Study frequency balance and the difference between gain and filtering.'),('Dynamics','Study compression, limiting, transient shape and loudness.'),('Space','Study delay, reverberation and stereo placement.'),('Automation','Change a parameter over time and inspect the resulting envelope.'),('Plugin workflow','Distinguish instrument, effect and host; inventory presence does not establish activation or licence.'),('Export and review','Render PCM WAV and compare timing, peak level and duration.')]
ROOTS=['C:/Program Files/Common Files/VST3','C:/Program Files/VstPlugins','C:/Program Files/Steinberg/VstPlugins','C:/Program Files/Image-Line/FL Studio 2025/Plugins','C:/Users/USER/Documents/Image-Line/FL Studio/Presets/Plugin database']
def inventory():
 result=[];seen=set();visited=0
 for base in ROOTS:
  root=Path(base)
  if not root.is_dir():continue
  stack=[(root,0)]
  while stack and visited<12000 and len(result)<2000:
   folder,depth=stack.pop()
   try:entries=list(folder.iterdir())
   except OSError:continue
   for p in entries:
    if visited>=12000 or len(result)>=2000:break
    visited+=1
    if p.is_symlink():continue
    suffix=p.suffix.lower()
    if suffix in ('.vst3','.dll','.fst'):
     key=str(p).casefold()
     if key not in seen:seen.add(key);result.append({'name':p.stem,'format':suffix[1:],'basis':'FL plugin database preset' if suffix=='.fst' else 'Installed plugin file or bundle','status':'Discovered; not loaded or licence-verified'})
    elif p.is_dir() and depth<7:stack.append((p,depth+1))
 return {'plugins':sorted(result,key=lambda x:x['name'].casefold()),'visited_entries':visited,'bounded':visited>=12000 or len(result)>=2000,'scope':'Read-only standard folders and FL plugin database. Custom paths may contain additional plugins. No plugin binary executed.'}
class MusicTrainer:
 def __init__(self):self.lock=threading.RLock();self.plugins=None;self.sequence=0;self.next_at=0;self.latest={};self.history=collections.deque(maxlen=24)
 def scan(self):
  try:
   result=inventory()
   with self.lock:self.plugins=result
  except Exception as e:
   with self.lock:self.plugins={'plugins':[],'status':type(e).__name__+': '+str(e)[:200]}
  finally:
   with self.lock:self.scanning=False
 def view(self,refresh=False):
  with self.lock:
   if (self.plugins is None or refresh) and not getattr(self,'scanning',False):
    self.scanning=True;threading.Thread(target=self.scan,daemon=True,name='music-plugin-inventory').start()
   return {'lessons':[{'title':a,'exercise':b} for a,b in LESSONS],'inventory':copy.deepcopy(self.plugins or {'plugins':[],'status':'Background inventory scanning'}),'inventory_scanning':getattr(self,'scanning',False),'sequence':self.sequence,'latest':copy.deepcopy(self.latest),'sources':[{'title':'FL Studio workflow','url':'https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_workflow.htm'},{'title':'Image-Line plugin reference','url':'https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/generator_plugins.htm'}],'scope':'Native automatic audio practice and oscillator workspace; no VST or FL engine embedded.'}
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  from .training_pace import interval
  self.next_at=time.monotonic()+interval(c);note=36+self.sequence%60;freq=440*2**((note-69)/12);raw=pcm(freq,.1)
  with wave.open(io.BytesIO(raw),'rb') as f:passed=f.getnframes()==2205 and f.getframerate()==22050
  with self.lock:self.sequence+=1;self.latest={'frequency':freq,'duration':.1,'passed':passed,'test':'Native PCM duration and sample-rate round trip'};self.history.append(self.latest.copy())
  c.bus.publish({'origin':'music-trainer','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'frequency':freq,'passed':passed,'provenance':'native-audio-format-practice','predefined_text':True,'stochastic':False}})
