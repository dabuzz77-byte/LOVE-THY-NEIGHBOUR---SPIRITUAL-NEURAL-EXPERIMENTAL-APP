"""Frozen held-out byte prediction with matched shuffled controls, not semantics."""
from collections import Counter,defaultdict
import hashlib,math,random

def score(raw):
 cut=max(32,int(len(raw)*.6));train,test=raw[:cut],raw[cut:]
 unigram=Counter(train);pairs=defaultdict(Counter)
 for a,b in zip(train,train[1:]):pairs[a][b]+=1
 baseline=conditional=0.;correct=0;previous=train[-1]
 for value in test:
  counts=pairs.get(previous,{});n=sum(counts.values())
  baseline-=math.log2((unigram[value]+1)/(len(train)+256))
  conditional-=math.log2((counts.get(value,0)+1)/(n+256))
  if counts:correct+=min(counts,key=lambda k:(-counts[k],k))==value
  previous=value
 return {'test_bytes':len(test),'baseline_bits_per_byte':baseline/len(test),'transition_bits_per_byte':conditional/len(test),'gain_bits_per_byte':(baseline-conditional)/len(test),'correct':correct,'training_bytes':len(train)}

def validate(raw):
 raw=bytes(raw[:1024])
 if len(raw)<96:return {'status':'insufficient-sample','bytes':len(raw),'minimum_bytes':96}
 measured=score(raw);seed=int.from_bytes(hashlib.sha256(raw).digest()[:8],'big');rng=random.Random(seed);controls=[]
 for _ in range(4):
  shuffled=list(raw);rng.shuffle(shuffled);controls.append(score(bytes(shuffled))['gain_bits_per_byte'])
 gain=measured['gain_bits_per_byte']
 return {**measured,'status':'candidate-structure' if gain>0 and gain>max(controls) else 'no-validated-gain',
         'source_sha256':hashlib.sha256(raw).hexdigest(),'shuffled_control_gains':controls,'gain_above_best_control':gain-max(controls),
         'model_frozen_during_test':True,'scope':'Byte-transition prediction on a later part of this captured sample; four deterministic shuffled controls preserve its byte histogram. A candidate is not a significance result, meaning, consciousness measurement or proof of physical origin. Test multiple fresh captures before retaining a general rule.'}

def predict_capture(training, later):
 """Score a previous capture's frozen model on a distinct later capture."""
 training,later=bytes(training[:1024]),bytes(later[:1024])
 if len(training)<96 or len(later)<96:return {'status':'insufficient-sample'}
 counts=Counter(training);pairs=defaultdict(Counter)
 for a,b in zip(training,training[1:]):pairs[a][b]+=1
 baseline=conditional=0.;correct=0
 # No invented continuity across the capture boundary.
 for previous,value in zip(later,later[1:]):
  row=pairs.get(previous,{});n=sum(row.values())
  baseline-=math.log2((counts[value]+1)/(len(training)+256))
  conditional-=math.log2((row.get(value,0)+1)/(n+256))
  if row:correct+=min(row,key=lambda k:(-row[k],k))==value
 size=len(later)-1;gain=(baseline-conditional)/size
 return {'status':'predictive-gain' if gain>0 else 'no-predictive-gain','gain_bits_per_byte':gain,'test_bytes':size,'correct':correct,'training_sha256':hashlib.sha256(training).hexdigest(),'test_sha256':hashlib.sha256(later).hexdigest(),'model_frozen_during_test':True,'scope':'Previous capture predicts this distinct capture from the same named source. Gain is relative to its frequency baseline; it does not establish meaning or independent physical origin.'}
