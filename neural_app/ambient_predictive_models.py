"""Source-specific adaptive prediction. Proposals are data, never commands."""
from collections import Counter, OrderedDict
import math

class PredictiveModels:
 def __init__(self):self.sources=OrderedDict()
 def observe(self,source,raw):
  raw=bytes(raw[:1024])
  if len(raw)<3:return {'status':'insufficient-sample'}
  state=self.sources.setdefault(source,{'tables':[OrderedDict() for _ in range(3)],'loss':[0.,0.,0.],'tested':0,'captures':0,'positive_captures':0,'previous_selected_loss':None})
  self.sources.move_to_end(source)
  while len(self.sources)>32:self.sources.popitem(last=False)
  chosen=min(range(3),key=lambda i:(state['loss'][i]/max(1,state['tested']),i))
  losses=[0.,0.,0.];correct=[0,0,0];tested=0
  # Freeze all three experts on this capture; update only after its entire test.
  for index in range(2,len(raw)):
   value=raw[index];tested+=1
   for order in range(3):
    key=raw[index-order:index] if order else b''
    counts=state['tables'][order].get(key,{})
    losses[order]-=math.log2((counts.get(value,0)+1)/(sum(counts.values())+256))
    if counts:correct[order]+=min(counts,key=lambda k:(-counts[k],k))==value
  prior_captures=state['captures']
  experts=[{'order':i,'bits_per_byte':losses[i]/tested,'correct':correct[i],'selected_before_capture':i==chosen} for i in range(3)]
  gain=(losses[0]-losses[chosen])/tested
  progress=None if state['previous_selected_loss'] is None else state['previous_selected_loss']-losses[chosen]/tested
  state['previous_selected_loss']=losses[chosen]/tested
  state['positive_captures']=state['positive_captures']+1 if prior_captures and gain>.05 else 0
  state['tested']+=tested;state['captures']+=1
  state['loss']=[a+b for a,b in zip(state['loss'],losses)]
  # Keep adaptation responsive rather than letting ancient totals dominate forever.
  if state['tested']>32768:
   state['tested']/=2;state['loss']=[v/2 for v in state['loss']]
  for index,value in enumerate(raw):
   for order in range(min(2,index)+1):
    key=raw[index-order:index] if order else b'';table=state['tables'][order]
    counts=table.setdefault(key,Counter());table.move_to_end(key);counts[value]+=1
    if sum(counts.values())>2048:table[key]=Counter({k:max(1,v//2) for k,v in counts.items()})
    while len(table)>128:table.popitem(last=False)
  next_order=min(range(3),key=lambda i:(state['loss'][i]/state['tested'],i))
  key=raw[-next_order:] if next_order else b'';counts=state['tables'][next_order].get(key,{})
  next_byte=min(counts,key=lambda k:(-counts[k],k)) if counts else None
  return {'status':'learning' if prior_captures==0 else 'evaluated','learning_progress_bits_per_byte':progress,'consecutive_gain_captures':state['positive_captures'],'recommendation':'retain-predictive-representation' if state['positive_captures']>=3 else 'frequency-baseline-sufficient' if prior_captures>=4 and gain<=.05 else 'collect-fresh-captures','prior_captures':prior_captures,'tested_bytes':tested,'selected_order':chosen,'gain_over_frequency_bits_per_byte':gain,'experts':experts,'next_order':next_order,'proposed_next_byte':next_byte,'proposal_is_command':False,'model_frozen_during_capture':True,'context_counts':[len(t) for t in state['tables']],'scope':'Adaptive selection among frequency, one-byte and two-byte context models, chosen using previous errors. Proposals predict captured symbols, not intent, meaning, consciousness or physical origin.'}
