"""Bounded shared candidates, selection, feedback and episodic memory."""
import hashlib,math
STAGES=('hydrogen','stellar','earth')
class PossibilityModel:
 def __init__(self):self.tick=0;self.memory={};self.history=[];self.latest=None;self.case_memory={};self.case_latest=None;self.case_tick=0
 def choose(self,known,raw,urgent=()):
  self.tick+=1;candidates=[]
  seed=int(hashlib.sha256(bytes(raw[:256])).hexdigest()[:8],16)
  for index,stage in enumerate(STAGES):
   past=self.memory.get(stage,{});age=self.tick-past.get('last_tick',0);unresolved=stage not in known
   benefit=3. if unresolved else 1.;priority=5. if stage in urgent else 0.
   score=benefit+priority+min(age,12)*.35+(.5 if past.get('last_success') is False else 0)
   candidates.append({'id':stage,'operation':'learn' if unresolved else 'verify-transfer','expected_benefit':benefit,'urgency':priority,'age':age,'estimated_cost':1.,'score':score,'reason':'Missing or withdrawn model' if unresolved else 'Check retained model on a new input'})
  # Ambient bytes diversify exact ties only; evidence and age control priority.
  candidates.sort(key=lambda c:(c['score'],(seed+STAGES.index(c['id']))%3),reverse=True)
  chosen=candidates[0];self.latest={'tick':self.tick,'candidates':candidates,'selected':dict(chosen),'phase':'chosen','scope':'Registered numerical experiments only; scores are heuristics, not probabilities'}
  return chosen['id']
 def observe(self,stage,result):
  if not self.latest or self.latest['selected']['id']!=stage:return
  success=result.get('status')=='validated-model';old=self.memory.get(stage,{})
  self.memory[stage]={'last_tick':self.tick,'last_success':success,'attempts':old.get('attempts',0)+1,'successes':old.get('successes',0)+int(success),'last_status':result.get('status')}
  self.latest={**self.latest,'phase':'checked','observed_status':result.get('status'),'prediction_matched':success,'next_question':'Test a fresh input' if success else 'Resolve competing explanations or revise the model family'}
  self.history=(self.history+[dict(self.latest)])[-12:]
 def restore(self,data):
  if not isinstance(data,dict):return
  tick=data.get('tick',0)
  if type(tick)is not int or not 0<=tick<=100000000:return
  self.tick=tick
  case=data.get('case_coordination',{})
  if isinstance(case,dict) and type(case.get('tick',0))is int and 0<=case.get('tick',0)<=100000000:
   self.case_tick=case.get('tick',0)
   for key,item in case.get('memory',{}).items():
    if key in ('representation-check','numerical-study','procedure-study') and isinstance(item,dict) and all(type(item.get(k))is int and 0<=item[k]<=100000000 for k in ('last_tick','attempts','successes')) and item['last_tick']<=self.case_tick and type(item.get('last_success'))is bool:self.case_memory[key]=dict(item)
  for stage,item in data.get('memory',{}).items():
   if stage in STAGES and isinstance(item,dict) and all(type(item.get(k))is int and 0<=item[k]<=100000000 for k in ('last_tick','attempts','successes')) and item['last_tick']<=tick and type(item.get('last_success'))is bool:self.memory[stage]=dict(item)
 def view(self):return {'case_coordination':{'tick':self.case_tick,'memory':dict(self.case_memory),'latest':self.case_latest},'tick':self.tick,'memory':dict(self.memory),'latest':self.latest,'history':list(self.history)}

 def propose_case(self,source,digest,selected_predictor,evidence_status):
  self.case_tick+=1
  state={'source':source,'source_sha256':digest,'selected_predictor':selected_predictor,'evidence_status':evidence_status,'source_kind':'generated software capture'}
  definitions=[('representation-check','Check reversible transformations and corruption detection',1.,'Exact restoration and altered-copy detection','A transformation loses information'),('numerical-study','Learn or recheck the current numerical model',2.,'Reserved numerical predictions pass','Model remains ambiguous or fails a new observation'),('procedure-study','Learn or reuse a verified byte procedure',2.,'Held-out byte transformations pass','No verified procedure found')]
  candidates=[]
  for identity,question,cost,success,failure in definitions:
   past=self.case_memory.get(identity,{});age=self.case_tick-past.get('last_tick',0);benefit=2. if not past or past.get('last_success') is False else 1.
   score=(benefit+min(age,12)*.5)/cost
   candidates.append({'id':identity,'question':question,'cost':cost,'score':score,'branches':[{'outcome':'supported','expected_observation':success},{'outcome':'unresolved','expected_observation':failure}],'completion':'Use the actual operation receipt, not an imagined branch'})
  chosen=max(candidates,key=lambda c:c['score'])
  self.case_latest={'present_state':state,'candidates':candidates,'selected':chosen,'phase':'proposed','tick':self.case_tick,'scope':'Bounded focus among existing case operations; other background studies continue'}
  return chosen['id']
 def finish_case(self,receipts):
  if not self.case_latest:return
  identity=self.case_latest['selected']['id'];receipt=receipts.get(identity)
  if not receipt:return
  success=receipt.get('supported') is True;past=self.case_memory.get(identity,{})
  self.case_memory[identity]={'last_tick':self.case_tick,'last_success':success,'attempts':past.get('attempts',0)+1,'successes':past.get('successes',0)+int(success),'last_status':receipt.get('status')}
  self.case_latest={**self.case_latest,'phase':'checked','actual_result':receipt,'next_question':'Test transfer to another capture' if success else 'Gather discriminating evidence; do not assume success'}

 def checkpoint(self):return {'tick':self.tick,'memory':dict(self.memory),'case_coordination':{'tick':self.case_tick,'memory':dict(self.case_memory)}}
