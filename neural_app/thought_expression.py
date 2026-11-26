"""Thought-derived procedural expression; displayed code is never executed."""
import ast,collections,hashlib,json,math,random,threading,time
from .translation import base3
class ThoughtExpression:
 def __init__(self,bus,cores,manifest,start=True):
  self.bus=bus;self.cores=cores;self.manifest=manifest;self.lock=threading.RLock();self.halt=threading.Event();self.worker=None;self.enabled=True;self.rate=24.;self.sequence=0;self.started=time.monotonic();self.points=collections.deque(maxlen=2400);self.counts=collections.Counter();self.coverage=collections.Counter();self.last=None;self.last_publish=0;self.error=None
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='thought-expression');self.worker.start()
 def configure(self,b):
  if 'enabled' in b:
   if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
   self.enabled=b['enabled']
  if 'rate' in b:
   v=float(b['rate'])
   if not math.isfinite(v):raise ValueError('Use a finite rate')
   self.rate=max(1,min(60,v))
  return self.view()
 def candidates(self):
  values=[]
  for core in self.cores:
   with core.lock:
    if core.goal_result:values.append({'source':core.name,'kind':'goal-result','value':dict(core.goal_result),'status':'calculated or checked; see verification fields','goal_priority':3})
    values.extend({'source':v.get('source',core.name),'kind':'working-memory','value':dict(v),'status':v.get('status','calculated fact' if v.get('verified') else 'unresolved')} for v in list(core.memory.values())[-16:])
    rows=sorted(core.observations.values(),key=lambda r:self.coverage[r['source']])[:4]
    for row in rows:
     if row['leaves']:
      leaf=row['leaves'][self.sequence%len(row['leaves'])];values.append({'source':row['source'],'kind':'captured-stage','path':leaf['path'],'value':leaf['value'],'status':'captured input; interpretation unresolved'})
  with self.manifest.lock:values.extend({'source':v['source'],'kind':'checked-representation','value':dict(v),'status':v['status']} for v in list(self.manifest.candidates)[-4:])
  return values
 def step(self):
  values=self.candidates()
  if not values:return None
  chosen=max(values,key=lambda v:(1+v.get('goal_priority',0))/(1+self.coverage[v['source']+'/'+v['kind']]));self.coverage[chosen['source']+'/'+chosen['kind']]+=1;value=chosen['value'];text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True);raw=text.encode()[:256];digest=hashlib.sha256(raw).hexdigest();rng=random.Random(int(digest,16)+self.sequence);kinds=['variable','string','ascii','bit','trit','word','sentence','code','geometry'];kind=min(kinds,key=lambda k:self.counts[k]);self.counts[kind]+=1
  bits=''.join(f'{byte:08b}' for byte in raw);trits=base3(int.from_bytes(raw,'big'));roundtrip=int(trits,3).to_bytes(len(raw),'big')==raw;words=text.split();code='observed = '+repr(value)+'\nprint(observed)\n';code_valid=True
  try:ast.parse(code)
  except (SyntaxError,ValueError):code_valid=False
  content={'variable':str(value),'string':text,'ascii':''.join(chr(byte&127) for byte in raw),'bit':bits,'trit':trits,'word':' '.join(words[:12]),'sentence':f"Source {chosen['source']} supplied {chosen['kind']}; status: {chosen['status']}.",'code':code,'geometry':'shape derived from source '+digest[:12]}[kind]
  forms=['plane','sphere','helix','torus','branch','lattice'];form=forms[(self.sequence//24+int(digest[:2],16))%len(forms)];morph=min(1,self.sequence/96);morph=morph*morph*(3-2*morph);new=[];now=time.time();symbols=list(content[:256]) or ['∅']
  for i in range(48):
   u=(i%8-3.5)/3.5;v=(i//8-2.5)/2.5;a=i/48*math.tau;plane=[u,0,v]
   if form=='sphere':target=[math.sqrt(max(0,1-v*v))*math.cos(a),v,math.sqrt(max(0,1-v*v))*math.sin(a)]
   elif form=='helix':target=[math.cos(a*2),v,math.sin(a*2)]
   elif form=='torus':target=[(1+.3*math.cos(a*3))*math.cos(a),.3*math.sin(a*3),(1+.3*math.cos(a*3))*math.sin(a)]
   elif form=='branch':target=[u*(1-abs(v)*.5),v,math.sin(a)*abs(v)]
   elif form=='lattice':target=[u,v,((i%3)-1)*.6]
   else:target=plane
   position=[plane[k]*(1-morph)+target[k]*morph for k in range(3)];speed=8*2**(3*i/47);vector=[rng.uniform(-1,1) for _ in range(3)];new.append({'point':position,'vector':vector,'rate':speed,'symbol':symbols[(self.sequence*48+i)%len(symbols)],'kind':kind,'form':form,'born':now,'source':chosen['source']})
  result={'source':chosen['source'],'source_kind':chosen['kind'],'path':chosen.get('path'),'status':chosen['status'],'kind':kind,'content':content[:6000],'source_sha256':digest,'represented_bytes':len(raw),'roundtrip_verified':roundtrip,'code_syntax_valid':code_valid if kind=='code' else None,'code_executed':False,'form':form,'morph_from_plane':morph,'selection_reason':'underused source/evidence type and representation; geometry derived from captured content','actual_updates_per_second':(self.sequence+1)/max(.001,time.monotonic()-self.started)}
  with self.lock:self.sequence+=1;self.points.extend(new);self.last=result
  if time.monotonic()-self.last_publish>=1:
   self.bus.publish({'origin':'thought-expression','target':'all','kind':'stage-output','payload':{'text':content[:1500],'bits':bits[:2048] or '0','classification':'unresolved; no inferred moral labels','expression':{k:v for k,v in result.items() if k!='content'},'point':new[0]['point'],'provenance':'observed-native-calculation','stochastic':False,'bridge_direction':'all','scope':'Source-labelled software expression; displayed code and sentences are not automatically executed or established facts'}});self.last_publish=time.monotonic()
  return result
 def view(self):
  with self.lock:return {'enabled':self.enabled,'rate':self.rate,'sequence':self.sequence,'points':list(self.points)[-600:],'last':self.last,'counts':dict(self.counts),'coverage':dict(self.coverage),'error':self.error}
 def loop(self):
  while not self.halt.is_set():
   started=time.monotonic()
   if self.enabled:
    try:self.step()
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:200]
   self.halt.wait(max(.002,1/self.rate-(time.monotonic()-started)))
 def close(self):
  self.halt.set()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(5)
