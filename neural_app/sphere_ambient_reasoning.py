"""Shared generated-source reasoning cases; roles act on evidence, not raw commands."""
import copy,hashlib,json,time
from collections import OrderedDict
from .ambient_source_identity import source_key

class AmbientSphereReasoning:
 def __init__(self,expected_roles=0,skill_path=None):
  from .ambient_rule_lab import RuleLab
  self.rule_lab=RuleLab(skill_path)
  from .ambient_physics_discovery import PhysicsDiscovery
  self.physics_discovery=PhysicsDiscovery(skill_path.with_name('ambient-physics-models.json') if skill_path else None)
  self.expected_roles=expected_roles;self.cases=OrderedDict();self.latest=None;self.sequence=0;self.steps=0;self.deliveries={};self.results={};self.completed=OrderedDict();self.cursor=0
 def ingest(self,rows,checks):
  if self.latest and self.expected_roles and sum(identity[0]==self.latest['id'] for identity in self.deliveries.values())<self.expected_roles:return
  candidates=[r for r in rows if r.get('generated') and r.get('raw')]
  if not candidates:return
  root=candidates[self.cursor%len(candidates)];self.cursor+=1
  raw=bytes(root['raw'][:256]);source=root['source'];check=checks.get(source_key(source),{})
  signature=hashlib.sha256(json.dumps([source,root['digest'],check],sort_keys=True,default=str).encode()).hexdigest()
  if signature in self.cases:self.latest=self.cases[signature];return
  representation=check.get('representation_prediction') or {};representation_gain=representation.get('selected_gain_over_best_baseline');representation_ready=representation.get('prior_captures',0)>=2 and representation_gain is not None and representation_gain>.05
  temporal=check.get('temporal_prediction') or {};symbolic=check.get('adaptive_prediction') or {}
  temporal_gain=temporal.get('relative_error_reduction');symbolic_gain=symbolic.get('gain_over_frequency_bits_per_byte',0)
  temporal_ready=temporal.get('prior_captures',0)>=2 and temporal_gain is not None and temporal_gain>.05
  symbolic_ready=symbolic.get('prior_captures',0)>=2 and symbolic_gain>.1
  selected='representation/'+representation['next_selected'] if representation_ready else 'temporal' if temporal_ready else 'symbolic' if symbolic_ready else 'baseline'
  self.physics_discovery.possibilities.propose_case(source,root['digest'],selected,check.get('status','waiting-for-source-validation'))
  # Test reversible representations and deliberate corruption in memory only.
  inverse=bytes(v^255 for v in raw);restored=bytes(v^255 for v in inverse)
  reversed_bytes=raw[::-1];corrupted=bytes([raw[0]^1])+raw[1:]
  tests=[{'name':'invert / restore exact bytes','passed':restored==raw},{'name':'reverse / restore exact order','passed':reversed_bytes[::-1]==raw},{'name':'detect deliberately corrupted copy','passed':hashlib.sha256(corrupted).digest()!=hashlib.sha256(raw).digest()}]
  self.sequence+=1
  case={'id':signature[:24],'sequence':self.sequence,'source':source,'source_sha256':root['digest'],'sample_sha256':hashlib.sha256(raw).hexdigest(),'source_event':root.get('parent_event'),'sample_bytes':len(raw),'conditions':copy.deepcopy(root.get('conditions')),'updated_at':time.time(),'selected_predictor':selected,'alternatives':{'representation':{'eligible':representation_ready,'gain_over_best_baseline':representation_gain,'selected_before_test':representation.get('selected_before_test'),'same_target':representation.get('same_prediction_target',False)},'temporal':{'eligible':temporal_ready,'relative_error_reduction':temporal_gain,'prior_captures':temporal.get('prior_captures',0)},'symbolic':{'eligible':symbolic_ready,'gain_bits_per_byte':symbolic_gain,'prior_captures':symbolic.get('prior_captures',0)},'baseline':{'eligible':True}},'forecast':{'normalized_byte':representation.get('forecast_normalized_byte') if representation_ready else temporal.get('forecast_normalized_byte'),'byte':symbolic.get('proposed_next_byte'),'evaluated_before_update':temporal.get('prediction_before_current_test_training',False)},'physics_discovery':self.physics_discovery.study(source,raw),'rule_learning':self.rule_lab.study(source,raw),'experiments':tests,'passed':all(t['passed'] for t in tests),'evidence_status':check.get('status','waiting-for-source-validation'),'scope':'Generated software source; predictor choice uses recorded held-out evidence. Three in-memory representation tests are separate from forecasting accuracy. No generated command is executed.'}
  rule=case['rule_learning'];physics=case['physics_discovery']
  self.physics_discovery.possibilities.finish_case({'representation-check':{'supported':case['passed'],'status':'exact-copy-tests-passed' if case['passed'] else 'copy-test-failed','checks':tests},'numerical-study':{'supported':physics.get('status')=='validated-model','status':physics.get('status'),'stage':physics.get('stage')},'procedure-study':{'supported':rule.get('status') in ('verified-procedure-reused','verified-procedure-retained'),'status':rule.get('status'),'skill_id':rule.get('skill_id')}})
  case['possibility_coordination']=copy.deepcopy(self.physics_discovery.possibilities.case_latest)
  self.cases[signature]=case
  while len(self.cases)>32:self.cases.popitem(last=False)
  self.latest=case
 def process(self,lane,role):
  if self.latest is None:return {'status':'waiting-for-generated-source','completed_steps':self.steps}
  case=self.latest;identity=(case['id'],role);cache_key=(lane,case['id'])
  if cache_key in self.completed:
   self.deliveries[lane]=identity
   return copy.deepcopy(self.completed[cache_key])
  self.deliveries[lane]=identity;self.steps+=1
  question='What does this generated source support, and what should be tested next?'
  if role in ('selection','coordination'):
   finding={'possibility_coordination':case.get('possibility_coordination'),'learned_procedure':case['rule_learning'].get('skill_id'),'selected_predictor':case['selected_predictor'],'alternatives':case['alternatives'],'criterion':'Use at least two earlier captures and a measured gain; otherwise keep baseline.'}
  elif role in ('experiment','action','geometry','training'):
   finding={'physical_model_discovery':case['physics_discovery'],'rule_learning':case['rule_learning'],'executed_tests':case['experiments'],'all_passed':case['passed'],'execution_scope':'Isolated byte copies only; no system or network actions.'}
  elif role=='forecast':
   finding={'physical_model_transfer':case['physics_discovery'].get('retained_model_transfer'),'forecast':case['forecast'],'eligible_predictor':case['selected_predictor'],'limitation':'Predicts this source representation, not an arbitrary real-world event.'}
  elif role in ('diagnosis','improvement'):
   finding={'failed_tests':[t['name'] for t in case['experiments'] if not t['passed']],'needs_more_evidence':case['selected_predictor']=='baseline','next_experiment':'Collect fresh same-source captures and compare predictive loss with unchanged baselines.'}
  elif role=='topology':
   finding={'input_source':case['source'],'roles_reached':sorted(self.deliveries),'role_count':len(self.deliveries),'routing_scope':'Recorded software deliveries, not external connectivity.'}
  elif role in ('comparison','theory','research'):
   finding={'hypothesis':'Any apparent structure should survive fresh-data prediction and be distinguished from transformation-induced patterns.','evidence_status':case['evidence_status'],'conditions':case['conditions'],'next_test':'Compare matched ordered, shuffled and transformed rails; retain source attribution.'}
  else:
   finding={'source_sha256':case['source_sha256'],'source_event':case['source_event'],'sample_bytes':case['sample_bytes'],'selected_predictor':case['selected_predictor'],'representation_checks_passed':case['passed']}
  result={'status':'completed','case_id':case['id'],'source':case['source'],'source_sha256':case['source_sha256'],'case_sequence':case['sequence'],'role':role,'question':question,'finding':finding,'completed_steps':self.steps,'updated_at':time.time(),'scope':case['scope']}
  self.results[lane]=result;self.completed[cache_key]=result
  while len(self.completed)>1088:self.completed.popitem(last=False)
  return copy.deepcopy(result)
 def view(self):return {'physics_discovery':self.physics_discovery.view(),'rule_learning':self.rule_lab.view(),'generated_cases':self.sequence,'completed_role_steps':self.steps,'roles_reached':len(self.deliveries),'retained_cases':len(self.cases),'expected_roles':self.expected_roles,'current_case_roles':sum(identity[0]==self.latest['id'] for identity in self.deliveries.values()) if self.latest else 0,'latest':copy.deepcopy(self.latest),'scope':'Bounded generated-source reasoning workspace shared by sphere roles; no general-consciousness claim.'}
