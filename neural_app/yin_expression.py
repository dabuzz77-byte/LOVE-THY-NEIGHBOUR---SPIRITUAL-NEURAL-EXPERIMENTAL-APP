"""Complementary order/chaos byte-and-vector branches with whole-capture lineage."""
import hashlib,json,math,random
REFERENCE='https://www.falundafa.org/intro/0-falun.htm'
def derive(rows,points,cycle,state=None):
 state=state if state is not None else {}
 digest=hashlib.sha256();size=0
 for row in sorted(rows,key=lambda r:r['id']):
  raw=row['text'].encode();size+=len(raw);digest.update(row['id'].encode());digest.update(len(raw).to_bytes(8,'big'));digest.update(raw)
 aggregate=digest.digest();rng=random.Random(int.from_bytes(aggregate,'big')+cycle);ordered=bytes(sorted(aggregate));noise=bytes(rng.randrange(256) for _ in range(32));phase=(cycle%17)/16;frames=[]
 for name,chaos in [('yin-order-chaos',phase),('yin-chaos-order',1-phase)]:
  if frames:
   first=frames[0];data=bytes(value^255 for value in first['data_bytes']);mirror=state.setdefault('mirror',{'rounds':0});mirror['rounds']+=1
   particles=[{**p,'point':[-v for v in p['point']],'vector':[-v for v in p['vector']],'bit':1-p['bit'],'raw_candidate':1-p['raw_candidate'],'logic_candidate':1-p['logic_candidate'],'rate_scale':4/p['rate_scale'],'state_source':'exact inverse of paired field'} for p in first['particle_states']]
   frames.append({**first,'id':name,'geometry':[p['point'] for p in particles],'data_bytes':list(data),'bits':''.join(f'{v:08b}' for v in data),'text':''.join(chr(v&127) for v in data),'rule':'exact byte complement, vector/position inversion and opposite rate spectrum of paired field','sha256':hashlib.sha256(data).hexdigest(),'chaos':1-first['chaos'],'rate_scale':4/first['rate_scale'],'processing_rounds_this_tick':1,'actual_processing_rounds':mirror['rounds'],'particle_states':particles,'paired_with':first['id'],'inverse_verified':all(a^b==255 for a,b in zip(first['data_bytes'],data)),'core':{**first['core'],'rotation':'opposite to paired field'}})
   continue
  entry=state.setdefault(name,{'credit':0.,'rounds':0,'last_data':None,'data_cycle':0,'data_aggregate':None})
  rate=2**(-5+12*chaos);entry['credit']=min(128,entry['credit']+rate);rounds=min(64,int(entry['credit']));entry['credit']-=rounds
  if entry['last_data'] is None:rounds=max(1,rounds)
  data=bytearray(entry['last_data'] or ordered)
  for a,b in zip(ordered,noise):
   value=0
   for bit in range(8):value|=(((b if rng.random()<chaos else a)>>bit)&1)<<bit
   data.append(value)
  proposed=bytes(data[-32:]);data=entry['last_data'] or ordered
  for turn in range(rounds):data=hashlib.sha256(data+proposed+aggregate+turn.to_bytes(2,'big')).digest()
  if rounds:entry.update(last_data=data,data_cycle=cycle,data_aggregate=aggregate.hex());entry['rounds']+=rounds
  text=''.join(chr(v&127) for v in data);geometry=[];particles=[]
  from .ambient_logic import AmbientLogic
  if 'logic' not in entry:entry['logic']=AmbientLogic()
  entry['logic'].configure({'depth':1-chaos});analysis=entry['logic'].process([{'text':text,'stochastic':True,'predefined_text':False,'contains_model_text':False}]);rule_bit=((analysis or {}).get('output') or {}).get('bit',0)
  for i,p in enumerate(points):
   angle=i/max(1,len(points))*math.tau;order=[math.cos(angle),0,math.sin(angle)];jitter=[rng.uniform(-2,2) for _ in range(3)];raw_bit=(data[(i//8)%len(data)]>>(7-i%8))&1;use_stochastic=rng.random()<chaos;bit=raw_bit if use_stochastic else rule_bit;particle_rate=2**(-5+12*((i+cycle)%17)/16);vector=[(1 if bit else -1)*((1-chaos)*order[k]+chaos*jitter[k]) for k in range(3)];position=[max(-3,min(3,((1-chaos)*order[k]+chaos*jitter[k])+.08*particle_rate*vector[k])) for k in range(3)];geometry.append(position);particles.append({'point':position,'vector':vector,'bit':bit,'rate_scale':particle_rate,'state_source':'stochastic byte bit' if use_stochastic else 'AmbientLogic phase blend','raw_candidate':raw_bit,'logic_candidate':rule_bit})
  frames.append({'id':name,'axis':'native','geometry':geometry,'data_bytes':list(data),'bits':''.join(f'{v:08b}' for v in data),'text':text,'source_indices':list(range(32)),'rule':'complementary order/chaos mixture of aggregate-derived bytes','source_id':'whole-registered-capture-aggregate','aggregate_sha256':aggregate.hex(),'input_sources':len(rows),'input_bytes':size,'clock_cycle':cycle,'sha256':hashlib.sha256(data).hexdigest(),'chaos':chaos,'rate_scale':rate,'processing_rounds_this_tick':rounds,'actual_processing_rounds':entry['rounds'],'data_cycle':entry['data_cycle'],'data_input_aggregate_sha256':entry['data_aggregate'],'particle_states':particles,'core':{'type':'Falun-inspired symbolic core','reference':REFERENCE,'rotation':'opposite directions in paired fields','scope':'Religious-inspired software motif, not a physical energy measurement'}})
 return frames
