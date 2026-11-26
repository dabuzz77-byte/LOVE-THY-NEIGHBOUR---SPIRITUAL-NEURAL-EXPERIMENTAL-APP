"""Fast self-selected scalar/string/ASCII/bit/trit expression with checked conversions."""
import collections,hashlib,json,math,random,threading,time
from .translation import base3
class RecursiveManifest:
 def __init__(self,bus,core,start=True):
  self.bus=bus;self.core=core;self.cores=[core];self.lock=threading.RLock();self.halt=threading.Event();self.worker=None;self.enabled=True;self.rate=24.;self.sequence=0;self.started=time.monotonic();self.points=collections.deque(maxlen=2400);self.choices=collections.Counter();self.last=None;self.last_publish=0;self.error=None;self.candidates=collections.deque(maxlen=24);self.source_counts=collections.Counter()
  if start:self.worker=threading.Thread(target=self.loop,daemon=True,name='recursive-manifest');self.worker.start()
 def configure(self,b):
  if 'enabled' in b:
   if type(b['enabled']) is not bool:raise ValueError('Enabled must be boolean')
   self.enabled=b['enabled']
  if 'rate' in b:
   rate=float(b['rate'])
   if not math.isfinite(rate):raise ValueError('Use a finite rate')
   self.rate=max(1,min(60,rate))
  return self.view()
 def step(self):
  selected_core=self.cores[self.sequence%len(self.cores)]
  with selected_core.lock:
   observations=list(selected_core.observations.values());goal=selected_core.goal;core_sequence=selected_core.sequence
   if not observations:return None
   chosen=min(observations,key=lambda row:self.source_counts[row['source']]);leaves=chosen['leaves'];leaf=leaves[self.sequence%len(leaves)];self.source_counts[chosen['source']]+=1
  value=leaf['value'];text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False);raw=text.encode()[:256];digest=hashlib.sha256(raw).hexdigest();rng=random.Random(int(digest,16)+self.sequence);modes=['variable','string','ascii','bit','ternary'];representation=max(modes,key=lambda mode:1/(1+self.choices[mode])+.25*int(mode in goal.lower()));self.choices[representation]+=1
  trits=base3(int.from_bytes(raw,'big'));verified=int(trits,3).to_bytes(len(raw),'big')==raw
  bits=''.join(f'{byte:08b}' for byte in raw);codes=list(raw);styles=['orbit','lattice','helix','radial','cloud'];style=styles[(rng.randrange(5)+self.sequence)%5]
  symbols=list(text[:64]) if representation in ('variable','string') else [chr(byte&127) for byte in codes] if representation=='ascii' else list(bits) if representation=='bit' else list(trits)
  if not symbols:symbols=['∅']
  new=[];born=time.time()
  for i in range(32):
   a=self.sequence*.11+i*.19;z=rng.uniform(-1,1);radius=rng.random()**(1/3);r=math.sqrt(max(0,1-z*z));random_point=[radius*r*math.cos(a),radius*z,radius*r*math.sin(a)]
   if style=='orbit':position=[math.cos(a),math.sin(a),math.sin(a*.3)*.3]
   elif style=='lattice':position=[((i%4)-1.5)/1.5,((i//4%4)-1.5)/1.5,((self.sequence%4)-1.5)/1.5]
   elif style=='helix':position=[math.cos(a),((i%16)-8)/8,math.sin(a)]
   elif style=='radial':position=[v*(1+(self.sequence%20)/20) for v in random_point]
   else:position=random_point
   rate=8*2**(3*(i/31));vector=[rng.uniform(-1,1)*(.2+rate/64) for _ in range(3)];new.append({'point':position,'vector':vector,'symbol':symbols[(self.sequence*32+i)%len(symbols)],'rate':rate,'representation':representation,'born':born,'source':chosen['source'],'path':leaf['path']})
  counts=collections.Counter(raw);entropy=-sum((n/len(raw))*math.log2(n/len(raw)) for n in counts.values()) if raw else 0;insight={'source':chosen['source'],'path':leaf['path'],'input_sha256':digest,'representation':representation,'byte_length':len(raw),'distinct_bytes':len(counts),'entropy_bits_per_byte':entropy,'roundtrip_verified':verified,'status':'checked representation and descriptive pattern; meaning unresolved','core_sequence':core_sequence,'core':selected_core.name}
  with self.lock:self.sequence+=1;self.points.extend(new);self.last={**insight,'style':style,'selection_reason':'underused representation + explicit goal relevance; underused source coverage','bits':bits,'ternary':trits,'ascii_codes':codes,'actual_updates_per_second':self.sequence/max(.001,time.monotonic()-self.started),'particle_rate_median':sorted(p['rate'] for p in new)[len(new)//2]};self.candidates.append(insight)
  if time.monotonic()-self.last_publish>=1:
   self.bus.publish({'origin':'recursive-manifest','target':'all','kind':'stage-output','payload':{'text':''.join(p['symbol'] for p in new),'bits':bits[:2048] or '0','classification':'unresolved; no inferred moral labels','point':new[0]['point'],'thought_candidate':insight,'provenance':'observed-native-calculation','stochastic':False,'bridge_direction':'all','scope':'Self-selected representations of captured data; no external-message decoding or generated host action'}});self.last_publish=time.monotonic()
  return self.last
 def view(self):
  with self.lock:return {'enabled':self.enabled,'rate':self.rate,'sequence':self.sequence,'actual_updates_per_second':self.sequence/max(.001,time.monotonic()-self.started),'points':list(self.points)[-600:],'last':self.last,'choices':dict(self.choices),'source_coverage':dict(self.source_counts),'thought_candidates':list(self.candidates)[-8:],'error':self.error}
 def loop(self):
  while not self.halt.is_set():
   start=time.monotonic()
   if self.enabled:
    try:self.step()
    except Exception as e:self.error=type(e).__name__+': '+str(e)[:240]
   self.halt.wait(max(.002,1/self.rate-(time.monotonic()-start)))
 def close(self):
  self.halt.set()
  if self.worker and self.worker is not threading.current_thread():self.worker.join(5)
