"""Native procedural media primitives, exports and objective training exercises."""
import array,hashlib,html,io,json,math,random,struct,wave,xml.etree.ElementTree as ET
from pathlib import Path
CURRICULA={
 'graphics':['coordinate transforms','rotation invariants','orthographic projection','perspective depth','sphere sampling','Bezier endpoints','easing monotonicity','vector paths','layout bounds','RGB interpolation','scene serialization','frame budgets'],
 'sound':['sample rates','PCM encoding','oscillator frequency','phase continuity','amplitude envelopes','clipping prevention','chord mixing','note frequencies','rhythm scheduling','RMS levels','WAV roundtrip','duration verification'],
 'video':['frame timing','trajectory continuity','loop closure','keyframe interpolation','camera projection','scene composition','motion paths','responsive viewport','play/pause controls','duration accounting','frame budgets','animation export']}
def ease(t):return t*t*(3-2*t)
def rotate(p,a):return [p[0]*math.cos(a)-p[2]*math.sin(a),p[1],p[0]*math.sin(a)+p[2]*math.cos(a)]
def project(p,depth=5):
 if depth+p[2]<=.1:raise ValueError('Point is outside camera near plane')
 return [p[0]*depth/(depth+p[2]),p[1]*depth/(depth+p[2])]
def bezier(p0,p1,p2,p3,t):return [(1-t)**3*p0[k]+3*(1-t)**2*t*p1[k]+3*(1-t)*t*t*p2[k]+t**3*p3[k] for k in range(2)]
def frame(index,total=48,radius=90):
 a=2*math.pi*index/total
 return {'x':160+radius*math.cos(a),'y':120+radius*math.sin(a),'time':index/24,'phase':a}
def svg_scene(seed=0):
 rng=random.Random(seed);points=[]
 for i in range(80):
  p=rotate([rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)],.4);x,y=project(p);points.append(f'<circle cx="{160+x*80:.3f}" cy="{120+y*80:.3f}" r="2" fill="#6295b3"/>')
 return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 240"><rect width="320" height="240" fill="#f4f7f9"/><path d="M20 120H300M160 20V220" stroke="#9eafb9"/>'+''.join(points)+'</svg>'
def pcm(frequency=440,duration=.25,rate=22050,chord=False):
 if not 20<=frequency<=4000 or not .05<=duration<=4:raise ValueError('Use 20–4000 Hz and .05–4 seconds')
 data=array.array('h');frequencies=[frequency,frequency*1.25,frequency*1.5] if chord else [frequency]
 for i in range(int(duration*rate)):
  t=i/rate;envelope=min(1,i/(rate*.01),(duration*rate-i)/(rate*.03));value=sum(math.sin(2*math.pi*f*t) for f in frequencies)/len(frequencies)
  data.append(round(7000*envelope*value))
 out=io.BytesIO()
 with wave.open(out,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(data.tobytes())
 return out.getvalue()
def music():
 rate=22050;parts=[]
 for freq in [261.6256,220.,349.2282,391.9954]:
  with wave.open(io.BytesIO(pcm(freq,.5,rate,True)),'rb') as f:parts.append(f.readframes(f.getnframes()))
 out=io.BytesIO()
 with wave.open(out,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(parts))
 return out.getvalue()
def animation():
 frames=[frame(i) for i in range(48)]
 return '<!doctype html><meta charset="utf-8"><title>Native orbit animation</title><style>body{background:#edf2f6;font:16px system-ui;text-align:center}svg{width:min(90vw,900px)}button{padding:12px}</style><h1>Native orbit · 24 fps · 2-second loop</h1><svg viewBox="0 0 320 240"><rect width="320" height="240" fill="#f7fafc"/><circle cx="160" cy="120" r="90" fill="none" stroke="#bacbd5"/><circle id="dot" r="7" fill="#397da3"/></svg><p><button id="toggle">Pause</button></p><script>const frames='+json.dumps(frames)+';let playing=true,time=0,last=0;function draw(now){if(last&&playing)time+=(now-last)/1000;last=now;const f=frames[Math.floor(time*24)%frames.length],dot=document.getElementById("dot");dot.setAttribute("cx",f.x);dot.setAttribute("cy",f.y);requestAnimationFrame(draw)}requestAnimationFrame(draw);document.getElementById("toggle").onclick=()=>{playing=!playing;document.getElementById("toggle").textContent=playing?"Pause":"Play"};</script>'
def export(tools,kind,name):
 suffix={'graphics':'.svg','sound':'.wav','music':'.wav','video':'.html'}.get(kind)
 if not suffix or Path(name).suffix.lower()!=suffix:raise ValueError('Use the corresponding .svg, .wav or .html filename')
 folder={'graphics':'graphics','sound':'audio','music':'music','video':'video'}[kind];p=tools.path(folder+'/'+name)
 if p.exists():raise ValueError('Choose a new export filename to preserve existing work')
 raw=svg_scene().encode() if kind=='graphics' else pcm(440,1.) if kind=='sound' else music() if kind=='music' else animation().encode()
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);actual=p.read_bytes()
 return {'path':p.relative_to(tools.root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(actual).hexdigest(),'verified':actual==raw,'kind':kind,'format':'WAV PCM' if suffix=='.wav' else 'animated HTML/SVG' if kind=='video' else 'SVG','scope':'Procedural native media export; video is an HTML animation, not an MP4 encoder'}
def trial(kind,seed,step):
 rng=random.Random(int.from_bytes(seed,'big')+step);rows=[]
 for i in range(8):
  if kind=='graphics':
   p=[rng.uniform(-2,2) for _ in range(3)];rot=rotate(p,rng.random()*6);norm=lambda v:sum(x*x for x in v)
   tree=ET.fromstring(svg_scene(rng.randrange(1000000)));values=[ease(j/20) for j in range(21)]
   passed=abs(norm(p)-norm(rot))<1e-9 and all(a<=b for a,b in zip(values,values[1:])) and bezier([0,0],[1,2],[3,4],[5,6],0)==[0,0] and bezier([0,0],[1,2],[3,4],[5,6],1)==[5,6] and len(list(tree))==82
   rows.append({'passed':passed,'rotation_error':abs(norm(p)-norm(rot)),'svg_elements':len(list(tree))})
  elif kind=='sound':
   hz=rng.randrange(200,900);duration=.1;raw=pcm(hz,duration)
   with wave.open(io.BytesIO(raw),'rb') as f:rate=f.getframerate();n=f.getnframes();samples=array.array('h',f.readframes(n))
   rms=math.sqrt(sum(s*s for s in samples)/len(samples));cross=sum(a<=0<b for a,b in zip(samples,samples[1:]));estimated=cross/duration
   passed=rate==22050 and n==2205 and max(abs(s) for s in samples)<=7000 and 0<rms<7000 and abs(estimated-hz)<=15
   rows.append({'passed':passed,'frequency':hz,'estimated_Hz':estimated,'frames':n,'rms':rms,'clipped':False})
  else:
   radius=rng.randrange(20,100);frames=[frame(j,48,radius) for j in range(49)];first,last=frames[0],frames[-1];errors=[abs(math.hypot(f['x']-160,f['y']-120)-radius) for f in frames];passed=max(errors)<1e-8 and abs(first['x']-last['x'])<1e-8 and abs(first['y']-last['y'])<1e-8 and frames[-1]['time']==2
   rows.append({'passed':passed,'frames':48,'fps':24,'duration':2,'max_radius_error':max(errors),'loop_verified':passed})
 return {'training_passed':all(x['passed'] for x in rows[:4]),'validation_passed':all(x['passed'] for x in rows[4:]),'lesson':kind+' / procedural-media invariants','training_cases':rows[:4],'fresh_validation_cases':rows[4:],'curriculum':CURRICULA[kind],'retained':False,'actual_media_checks':True,'scope':'Objective procedural media checks; aesthetic quality and human preference require review; no image/audio/video model weight update'}


def midi_music():
 def vlq(n):
  out=[n&127];n>>=7
  while n:out.insert(0,(n&127)|128);n>>=7
  return bytes(out)
 track=bytearray([0,255,81,3,7,161,32])
 for chord in ((60,64,67),(57,60,64),(53,57,60),(55,59,62)):
  for note in chord:track+=bytes([0,144,note,72])
  for i,note in enumerate(chord):track+=vlq(480 if i==0 else 0)+bytes([128,note,0])
 track+=bytes([0,255,47,0])
 return b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(track))+track

def studio_info(tools):
 import os
 candidates=[]
 for root in (Path(os.environ.get('ProgramFiles','C:/Program Files'))/'Image-Line',Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Image-Line'):
  if root.is_dir():candidates.extend(root.glob('FL Studio*/FL64.exe'))
 return {'installed':bool(candidates),'executable':str(sorted(candidates)[-1]) if candidates else None,'workspace':str(tools.root/'music'),'connection':'WAV/MIDI file handoff; live controller bridge not configured','references':['https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm','https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_other_mid.htm']}

def export_midi(tools,name):
 if not name.lower().endswith('.mid'):raise ValueError('Use a .mid filename')
 p=tools.path('music/'+name)
 if p.exists():raise ValueError('Choose a new filename')
 raw=midi_music();p.write_bytes(raw)
 return {'path':p.relative_to(tools.root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'verified':p.read_bytes()==raw,'format':'Standard MIDI type 0','tempo_bpm':120,'ppq':480,'notes':12,'next':'Import the MIDI file into FL Studio; existing projects are unchanged.'}

def workspace_view(tools):
 files=[]
 for folder in ('graphics','audio','music','video','code','exports'):
  for p in sorted((tools.root/folder).iterdir()):
   if p.is_file() and not p.is_symlink() and len(files)<150:files.append({'path':p.relative_to(tools.root).as_posix(),'bytes':p.stat().st_size,'extension':p.suffix})
 return {'root':str(tools.root),'spaces':['graphics','audio','music','video','code','exports'],'files':files,'studio':studio_info(tools)}

def read_media(tools,name):
 import base64
 p=tools.path(name)
 if p.suffix.lower() not in ('.wav','.mid','.svg','.html'):raise ValueError('Choose a media export')
 if p.stat().st_size>3000000:raise ValueError('Preview limit is 3 MB')
 types={'.wav':'audio/wav','.mid':'audio/midi','.svg':'image/svg+xml','.html':'text/html'};raw=p.read_bytes()
 return {'path':name,'mime':types[p.suffix.lower()],'base64':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}
