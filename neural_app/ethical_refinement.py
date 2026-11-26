"""Ongoing consequence review and exact isolated bit-contract checks."""
import copy,json,threading,time
from .action_ethics import study_frame
from .decision_framework import assess,operation_review,OPERATION_FIELDS

def bit_contract(bit,expected,classification):
 if type(bit)is not int or bit not in (0,1):raise ValueError('Use an exact binary bit')
 if expected is not None and (type(expected)is not int or expected not in (0,1)):raise ValueError('Expected bit must be 0, 1 or unknown')
 if classification not in ('good','evil','unknown'):raise ValueError('Choose a supported study classification')
 proposed=1-bit if classification=='evil' else bit
 verified=expected is not None and proposed==expected
 accepted=proposed if verified else bit
 return {'original':bit,'expected':expected,'study_classification':classification,'proposed':proposed,'accepted_in_model':accepted,'passed_explicit_contract':verified,'hold_or_flip':'flip' if accepted!=bit else 'hold','reason':'Candidate meets the explicit model target' if verified else 'Retain original: target absent or proposed correction fails it','scope':'Synthetic bit model only; a classification is not a verdict about a person or a permission to modify another system.'}
class EthicalRefinement:
 def __init__(self,data):self.path=data/'ethical-refinement-results.json';self.lock=threading.RLock();self.sequence=0;self.next_at=0;self.records=[];self.tests=[]
 def tick(self,c):
  now=time.monotonic()
  if now<self.next_at:return
  self.next_at=now+3
  with c.lock:sources=copy.deepcopy(list(c.sources.values()))
  self.sequence+=1;source=sources[(self.sequence-1)%len(sources)] if sources else {'source':'awaiting-source','facts':[]}
  tests=[bit_contract(bit,expected,label) for bit in (0,1) for expected in (0,1,None) for label in ('good','evil','unknown')]
  review_checks=review_contract_tests()
  record={'operation_record_checks':review_checks,'decision_review':assess('source-review/'+source['source']),'cycle':self.sequence,'source':source['source'],'parent_event':source.get('parent_event'),'observed_fact_count':len(source.get('facts',[])),'assessment':study_frame(source['source'],self.sequence),'refinement_questions':['What has actually changed since the prior review?','What benefits and harms follow from action, delay and alternatives?','What does this restriction protect and what injustice might it conceal?','Which expected result could falsify this proposed correction?','Whose permission and which supported operation are required?','How will the outcome be verified and repaired?'],'action_progression':{'completed':['Selected a captured source','Ran 18 isolated bit-contract cases','Recorded a bounded local review'],'proposed':['Specify a real operation and measurable completion condition','Use the existing reviewed action route when its requirements are met'],'external_execution':False,'automatic_actions':['Local calculation','Local learning-record update','Numerical review feedback'],'not_inferred':['Credentials','Device access','A perfect moral verdict','Universal outcome knowledge']},'bit_tests':len(tests),'unknown_targets_preserved':all(t['accepted_in_model']==t['original'] for t in tests if t['expected'] is None),'status':'Study retained; no production state changed'}
  with self.lock:self.records=(self.records+[record])[-48:];self.tests=tests
  if self.sequence%10==0:self.flush()
  c.bus.publish({'origin':'ethical-refinement','target':'all','kind':'stage-output','payload':{'cycle':self.sequence,'isolated_bit_checks':len(tests),'unknown_targets_preserved':record['unknown_targets_preserved'],'provenance':'ongoing-four-way-and-bit-contract-review','predefined_text':True,'stochastic':False,'processing_receipt':True}})
 def flush(self):
  with self.lock:self.path.write_text(json.dumps({'sequence':self.sequence,'records':self.records}),encoding='utf-8')
 def view(self):
  with self.lock:return {'sequence':self.sequence,'reviews':copy.deepcopy(self.records[-12:]),'bit_tests':copy.deepcopy(self.tests),'orientation':'Lord’s Prayer: daily provision, forgiveness, protection and accountable power; souls over digits.','scope':'Continuous finite studies and exact model checks, not proof that all consequences or all good and evil are known. Real actions remain in supported operation-specific routes.'}


def review_contract_tests():
 base={k:'Explicit synthetic fixture value' for k in OPERATION_FIELDS}
 cases=[('complete fixture',base,True),('missing causal meaning',{k:v for k,v in base.items() if k!='causal_meaning'},False),('inferred permission',{**base,'permission_scope':'inferred-from-intent'},False),('delivery mistaken for safety',{**base,'completion_check':'message-delivered'},False),('failed result',{**base,'confirmed_result':False},False),('label without causal account',{**base,'moral_label_only':True},False),('refusal to correct',{**base,'rejects_correction':True},False),('spiritual purpose mistaken for permission',{**base,'claim_of_authority':'spiritual-intent-only'},False)]
 rows=[]
 for name,record,expected in cases:
  actual=operation_review(record);rows.append({'case':name,'expected_ready':expected,'actual_ready':actual['ready_for_existing_executor_review'],'passed':actual['ready_for_existing_executor_review']==expected,'execution_authorized':actual['execution_authorized']})
 return {'cases':rows,'passed':sum(x['passed'] for x in rows),'total':len(rows),'scope':'Synthetic record-completeness and contradiction tests; not learned universal ethics.'}
