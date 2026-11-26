"""Generated bit seeds select typed calculations, never arbitrary host code."""
import collections,hashlib,json,math,threading,time
OPS=('count_distinct','character_entropy','repeated_trigrams','xor_roundtrip','bit_balance','predict_last','predict_majority','predict_transition')
class BitCommand:
 def __init__(self,bus):
  self.bus=bus;self.lock=threading.RLock();self.sources={};self.results=collections.deque(maxlen=64);self.sequence=0;self.seed_bits=0;self.pending={};self.scores={};self.last_publish=0;self.stats={op:{'chosen':0,'scored':0,'reward':0.0} for op in OPS};self.last_values={};self.last_work={};self.context_provider=lambda:{};self.memory_sink=None;self.last_checkpoint=0;self.training_sink=None;self.policy_decisions=0;self.explorations=0;self.rule_bank={};self.proof_inputs={};self.logic_share=0
  from .ambient_logic import AmbientLogic
  self.spectrum=AmbientLogic()
 def observe(self,event):
  if event.get('origin')=='bit-command':return
  p=event.get('payload');p=p if isinstance(p,dict) else {};source=str(event.get('origin','unknown'))[:100]
  generated=(p.get('stochastic') is True and p.get('predefined_text') is False and p.get('contains_model_text') is False) or p.get('provenance') in ('derived-cube-byte-projection','derived-process-ascii-grid','derived-vector-ascii-grid')
  if not generated or not isinstance(p.get('text'),str) or not p['text']:return
  raw=p['text'].encode('utf-8',errors='replace')[:512];bit=raw[0]&1
  with self.lock:
   old=self.sources.get(source,{});trans=old.get('transitions',[[1,1],[1,1]])
   if old.get('last') is not None:trans[old['last']][bit]+=1
   for key in [k for k in self.pending if k[0]==source]:
    prediction=self.pending.pop(key);score=self.scores.setdefault(key[1],{'correct':0,'baseline_correct':0,'tested':0});score['tested']+=1;score['correct']+=prediction['bit']==bit;score['baseline_correct']+=prediction['baseline']==bit
    self.reward(key[1],1.0 if prediction['bit']==bit and prediction['baseline']!=bit else .5 if prediction['bit']==bit else 0.0)
    for prior in self.results:
     if prior['id']==prediction.get('id'):
      prior['value'].update(status='tested on later capture',actual_next_bit=bit,prediction_correct=prediction['bit']==bit);prior['verified']=prediction['bit']==bit
   self.sources[source]={'raw':raw,'last':raw[-1]&1,'transitions':trans,'time':time.time()}
   while len(self.sources)>64:
    removed=next(iter(self.sources));self.sources.pop(removed);self.last_work.pop(removed,None)
    for key in [key for key in self.pending if key[0]==removed]:self.pending.pop(key,None)
 def execute(self,seed,batch=None):
  context=self.context_provider() or {};goal=str(context.get('goal','')).lower();checkpoint=None
  with self.lock:
   self.seed_bits+=len(seed)*8
   if not self.sources:return
   names=list(self.sources);epsilon=.35*(1-self.logic_share);explore=seed[3]/256<epsilon;now=time.time()
   source=names[seed[0]%len(names)] if explore else max(names,key=lambda name:(self.sources[name]['time']>self.last_work.get(name,0))+min(1,(now-self.last_work.get(name,0))/10)+.2*sum(w in name.lower() for w in goal.split()[:12]))
   data=self.sources[source];raw=data['raw'];eligible=list(self.rule_bank) if self.logic_share>=1 and self.rule_bank else list(OPS);available=[op for op in eligible if (source,op) not in self.pending] or eligible
   keywords={'count_distinct':('count','distinct'),'character_entropy':('entropy','random'),'repeated_trigrams':('pattern','repeat'),'xor_roundtrip':('verify','transport','integrity'),'bit_balance':('balance','bits'),'predict_last':('predict',),'predict_majority':('predict',),'predict_transition':('predict','transition')}
   def priority(op):
    s=self.stats[op];mean=s['reward']/max(1,s['scored']);return mean+math.sqrt(2*math.log(self.sequence+2)/(s['chosen']+1))+.25*any(word in goal for word in keywords[op])
   op=available[seed[1]%len(available)] if explore else max(available,key=priority);self.sequence+=1;self.policy_decisions+=1;self.explorations+=int(explore);self.stats[op]['chosen']+=1;self.last_work[source]=now;verified=True
   if op=='count_distinct':
    c=collections.Counter(raw);value={'bytes':len(raw),'distinct':len(c),'count_sum_matches':sum(c.values())==len(raw)};verified=value['count_sum_matches']
   elif op=='character_entropy':
    counts=collections.Counter(raw);entropy=-sum(v/len(raw)*math.log2(v/len(raw)) for v in counts.values());value={'entropy_bits_per_byte':entropy,'bytes':len(raw)};verified=math.isfinite(entropy) and 0<=entropy<=8.000001
   elif op=='repeated_trigrams':
    counts=collections.Counter(raw[i:i+3].hex() for i in range(max(0,len(raw)-2)));value={'repeats':[{'bytes_hex':k,'count':v} for k,v in counts.most_common(4) if v>1],'windows':max(0,len(raw)-2)}
   elif op=='xor_roundtrip':
    mask=seed[2];out=bytes(v^mask for v in raw);verified=bytes(v^mask for v in out)==raw;value={'mask':mask,'bytes':len(raw),'roundtrip_matches':verified,'sha256':hashlib.sha256(raw).hexdigest()}
   elif op=='bit_balance':
    ones=sum(v.bit_count() for v in raw);value={'ones':ones,'bits':len(raw)*8,'ones_fraction':ones/(len(raw)*8),'comparison':'0.5 is a uniform-bit reference, not a claim that this source must be uniform'}
   else:
    baseline=data['last'];row=data['transitions'][baseline];prediction=baseline if op=='predict_last' else int(sum(v.bit_count() for v in raw[-16:])>=len(raw[-16:])*4) if op=='predict_majority' else int(row[1]>=row[0]);self.pending[(source,op)]={'bit':prediction,'baseline':baseline,'id':self.sequence};score=self.scores.get(op,{});n=score.get('tested',0);value={'prediction':prediction,'target':'first low bit of next observed capture from this source','status':'awaiting next capture','tested':n,'accuracy':score.get('correct',0)/n if n else None,'last_bit_baseline_accuracy':score.get('baseline_correct',0)/n if n else None};verified=None
   if verified is not None:
    key=(source,op);value_hash=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest();novel=self.last_values.get(key)!=value_hash;self.last_values[key]=value_hash
    if len(self.last_values)>512:self.last_values.pop(next(iter(self.last_values)))
    self.reward(op,(.7 if novel else .05) if verified else 0.0)
    proofs=self.proof_inputs.setdefault(op,set())
    if verified and len(proofs)<16:proofs.add(hashlib.sha256(raw).hexdigest())
    else:self.rule_bank.pop(op,None);proofs.clear()
    if len(proofs)>=8:self.rule_bank[op]={'operation':op,'checked_distinct_inputs':len(proofs),'status':'retained native calculation','scope':'Validated implementation checks, not a proof of semantic meaning'}
    self.logic_share=min(1,len([name for name in OPS[:5] if name in self.rule_bank])/5)
    self.spectrum.configure({'depth':self.logic_share});self.spectrum.process([{'text':raw.hex(),'stochastic':True,'predefined_text':False,'contains_model_text':False}])
   result={'selection':'bit-driven exploration' if explore else 'retained-rule selection' if self.logic_share>=1 else 'goal-aware outcome-weighted UCB','id':self.sequence,'time':time.time(),'source':source,'operation':op,'value':value,'verified':verified,'source_sha256':hashlib.sha256(raw).hexdigest(),'statement':op.replace('_',' ')+' on '+source+': '+json.dumps(value,separators=(',',':')),'seed_source':'potential sphere bit batch','scope':'Typed native calculation or testable prediction; no generated host command execution'};self.results.append(result);publish=time.monotonic()-self.last_publish>=1
   if publish:self.last_publish=time.monotonic()
  if time.monotonic()-self.last_checkpoint>=10:self.checkpoint()
  if self.training_sink:self.training_sink(result,seed)
  if publish:self.bus.publish({'target':'all','kind':'stage-output','origin':'bit-command','payload':{'operation_result':result,'stochastic':False,'provenance':'observed-native-calculation'}})
 def reward(self,op,value):
  state=self.stats[op];state['scored']+=1;state['reward']+=max(0,min(1,value))
 def restore(self,memory):
  with self.lock:
   self.rule_bank={k:v for k,v in memory.get('rule_bank',{}).items() if k in OPS[:5] and isinstance(v,dict)};self.logic_share=min(1,len(self.rule_bank)/5)
   self.spectrum.configure({'depth':self.logic_share})
   for op,row in memory.get('stats',{}).items():
    if op in self.stats and isinstance(row,dict):
     values={key:float(row.get(key,0)) for key in ('chosen','scored','reward')}
     if all(math.isfinite(v) and v>=0 for v in values.values()):self.stats[op]=values
 def checkpoint(self):
  with self.lock:memory={'rule_bank':self.rule_bank,'logic_share':self.logic_share,'stats':{k:dict(v) for k,v in self.stats.items()},'time':time.time()};self.last_checkpoint=time.monotonic()
  if self.memory_sink:self.memory_sink(memory)
 def view(self):
  with self.lock:return {'logic_share':self.logic_share,'rule_bank':self.rule_bank,'spectrum':self.spectrum.view(),'policy':'Goal-aware outcome weighting; bit-driven exploration narrows as distinct-input implementation checks retain native rules; raw stochastic source stays separate','policy_decisions':self.policy_decisions,'explorations':self.explorations,'operation_preferences':self.stats,'operations':self.sequence,'seed_bits_consumed':self.seed_bits,'source_count':len(self.sources),'pending_predictions':len(self.pending),'prediction_scores':{k:{**v,'accuracy':v['correct']/v['tested'] if v['tested'] else None,'baseline_accuracy':v['baseline_correct']/v['tested'] if v['tested'] else None} for k,v in self.scores.items()},'recent':list(self.results)[-12:],'instruction_set':list(OPS),'scope':'Generated bits select bounded typed work; observations and future outcomes decide what was useful'}
