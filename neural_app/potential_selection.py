"""Compact all/subset/one candidate views, with ordered and chaotic rails."""
import copy,hashlib,json,random,threading,time
class PotentialSelection:
 def __init__(self):self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.cursor=0;self.states={};self.rng=random.Random()
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  from .training_pace import interval
  self.next_at=now+interval(c,.25)
  with c.lock:layers=c.element_thinking.view()['layers'];pool=copy.deepcopy(list(c.generation_selector.pool.values())[-32:])
  if not layers:return
  stage=layers[self.cursor%len(layers)];self.cursor+=1
  candidates=[{'id':x['id'],'source':x['source'],'path':x['path'],'kind':x['kind'],'value_preview':str(x['value'])[:120],'parent_event':x.get('parent_event')} for x in pool]
  for i,fact in enumerate(stage.get('observations',[])[:12]):candidates.append({'id':'observation:'+str(i),'source':stage.get('source'),'path':fact.get('path',[]),'kind':type(fact.get('value')).__name__,'value_preview':str(fact.get('value'))[:120],'parent_event':stage.get('parent_event')})
  n=len(candidates);full=(1<<n)-1
  ordered_indices=sorted(range(n),key=lambda i:(candidates[i]['source']!=stage.get('source'),i));k=max(1,n//2) if n else 0
  ordered=sum(1<<i for i in ordered_indices[:k]);chaotic=self.rng.getrandbits(n) if n else 0
  if n and not chaotic:chaotic=1<<self.rng.randrange(n)
  single=1<<ordered_indices[0] if n else 0
  changed=stage.get('changes',0)!=self.states.get(stage['id'],{}).get('changes')
  chosen='none' if not n or (not changed and stage.get('attention',0)<=0 and self.sequence%4==0) else 'all' if changed and n<=8 else 'ordered_subset' if stage.get('attention',0)>0 else 'chaotic_subset'
  rails={'none':0,'all':full,'one':single,'ordered_subset':ordered,'chaotic_subset':chaotic}
  self.sequence+=1
  state={'stage':stage['id'],'cycle':self.sequence,'changes':stage.get('changes'),'candidate_count':n,'candidates':candidates,'potential_subsets_including_none':str(1<<n),'potential_nonempty_subsets':str(full),'representation':'Each mask bit addresses one retained candidate; all subsets represented by integers 0 through 2^n−1, with zero meaning none without enumeration.','parallel_views':{name:{'mask':str(mask),'count':mask.bit_count(),'candidate_ids':[row['id'] for i,row in enumerate(candidates) if mask&(1<<i)]} for name,mask in rails.items()},'selected_view':chosen,'selected_mask':str(rails[chosen]),'selection_basis':'Changed input, stage attention and bounded exploration; not a guarantee of optimal reasoning.','next_review_seconds':interval(c,.25)*len(layers),'action_scope':'Candidate attention only. Original values and action permissions unchanged.'}
  with self.lock:self.states[stage['id']]=state
  c.bus.publish({'origin':'potential-selection','target':'all','kind':'stage-output','payload':{'thinking_layers':[stage['id']],'cycle':self.sequence,'candidate_count':n,'selected_count':rails[chosen].bit_count(),'provenance':'compact-parallel-candidate-attention','selection_trace':True,'processing_receipt':True,'predefined_text':True,'stochastic':False}})
 def stage(self,key):
  with self.lock:return copy.deepcopy(self.states.get(key,{}))
 def view(self):
  with self.lock:return {'sequence':self.sequence,'stages':copy.deepcopy(self.states),'scope':'Bounded retained candidates at every registered stage. None/one/subset/all and chaotic/ordered views coexist; unobserved or infinite possibilities are not enumerated.'}
