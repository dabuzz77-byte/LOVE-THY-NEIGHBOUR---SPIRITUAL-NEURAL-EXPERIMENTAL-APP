"""Bounded dataflow processor: generated input -> metrics -> predicates -> typed output."""
import math,hashlib,collections,time,random
class AmbientLogic:
 def __init__(self,rng=None):self.rng=rng or random.SystemRandom();self.depth=.5;self.threshold=.5;self.operator='entropy_above';self.last={};self.digest=None;self.sequence=0;self.ema=.5;self.previous=None;self.transitions=[[1,1],[1,1]];self.predictions=0;self.correct=0
 def configure(self,body):
  depth=float(body.get('depth',self.depth));threshold=float(body.get('threshold',self.threshold))
  if not math.isfinite(depth) or not math.isfinite(threshold):raise ValueError('Logic controls must be finite numbers')
  self.depth=max(0,min(1,depth));self.threshold=max(0,min(1,threshold))
  op=body.get('operator',self.operator)
  if op not in ('entropy_above','ones_above','repeat_above'):raise ValueError('Unknown logic predicate')
  self.operator=op;self.digest=None;return self.view()
 def process(self,streams):
  text=''.join(str(s.get('text',''))[:512] for s in streams if s.get('stochastic') is True and s.get('predefined_text') is False and s.get('contains_model_text') is False)[:16384]
  digest=hashlib.sha256((text+str((self.depth,self.threshold,self.operator))).encode()).hexdigest()
  if digest==self.digest:return None
  self.digest=digest;self.sequence+=1;raw=text.encode();counts=collections.Counter(raw);n=len(raw);entropy=-sum((v/n)*math.log2(v/n) for v in counts.values())/8 if n else 0;ones=sum(b.bit_count() for b in raw)/(n*8) if n else 0;repeat=sum(raw[i]==raw[i-1] for i in range(1,n))/max(1,n-1)
  metrics={'entropy':entropy,'ones':ones,'repeat':repeat,'bytes':n};value=metrics[self.operator.split('_')[0]];predicate=bool(n and value>self.threshold)
  instructions=[{'op':'capture','bytes':n}]
  if self.depth>=.25:instructions.append({'op':'measure','metrics':metrics})
  if self.depth>=.5:instructions.append({'op':'compare','predicate':self.operator,'threshold':self.threshold,'result':predicate})
  if self.depth>=.75:instructions.append({'op':'select','selected':1 if predicate else 0})
  # Every intermediate phase has a distinct bounded computation, blended with its neighbours.
  bits=[(byte>>shift)&1 for byte in raw for shift in range(7,-1,-1)]
  self.ema=self.ema*.8+ones*.2
  if bits:
   for a,b in zip(bits,bits[1:]):self.transitions[a][b]+=1
   if sum(sum(row) for row in self.transitions)>100000:self.transitions=[[max(1,v//2) for v in row] for row in self.transitions]
  transition=self.transitions[bits[-1] if bits else 0];prediction=int(transition[1]>=transition[0]);confidence=max(transition)/sum(transition)
  if self.previous is not None and bits:self.predictions+=1;self.correct+=int(self.previous==bits[0])
  self.previous=prediction
  random_bit=self.rng.getrandbits(1)
  majority=int(ones>=.5);smooth=int(self.ema>=.5);last_bit=bits[-1] if bits else 0
  candidates=[random_bit,majority,last_bit if repeat>.1 else majority,smooth,prediction,int(predicate),int(predicate) if confidence>=.6 else smooth,int(predicate)]
  names=['stochastic sampling','distribution vote','repetition / continuity','temporal smoothing','transition prediction','explicit predicate','confidence-gated rule','deterministic rule execution']
  position=self.depth*(len(names)-1);left=int(position);right=min(len(names)-1,left+1);fraction=position-left
  weights=[0.0]*len(names);weights[left]+=1-fraction;weights[right]+=fraction
  selected=right if fraction>0 and self.rng.random()<fraction else left
  phases=[{'phase':name,'weight':weights[i],'candidate_bit':candidates[i],'active':weights[i]>0} for i,name in enumerate(names)]
  output={'bit':candidates[selected],'mode':'stochastic' if selected==0 else 'logic','phase':names[selected],'logic_weight':self.depth,'stochastic_weight':1-self.depth,'source_sha256':digest} if n else None
  instructions.append({'op':'phase_blend','phases':phases,'selected':names[selected] if n else 'empty input'})
  feedback={'predict_next_bit':prediction,'transition_confidence':confidence,'observed_next_capture_accuracy':self.correct/self.predictions if self.predictions else None,'compared_captures':self.predictions,'smoothed_ones':self.ema}
  self.last={'sequence':self.sequence,'time':time.time(),'depth':self.depth,'instructions':instructions,'phases':phases,'feedback':feedback,'output':output,'scope':'bounded software dataflow; no dynamic source execution','changed':True};return self.last
 def view(self):return {'depth':self.depth,'threshold':self.threshold,'operator':self.operator,'sequence':self.sequence,'latest':self.last}
