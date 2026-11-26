import unittest
from neural_app.ambient_possibilities import PossibilityModel
class PossibilityTests(unittest.TestCase):
 def test_missing_stages_take_priority_and_all_receive_attention(self):
  m=PossibilityModel();known={};seen=[]
  for _ in range(3):
   stage=m.choose(known,b'abc');seen.append(stage);known[stage]={};m.observe(stage,{'status':'validated-model'})
  self.assertEqual(set(seen),{'hydrogen','stellar','earth'})
 def test_urgent_relearning_wins(self):
  m=PossibilityModel();self.assertEqual(m.choose(dict.fromkeys(('hydrogen','stellar','earth')),b'abc',['earth']),'earth')
 def test_history_bounded_and_feedback_real(self):
  m=PossibilityModel()
  for _ in range(20):
   stage=m.choose({},b'abc');m.observe(stage,{'status':'ambiguous'})
  self.assertEqual(len(m.history),12);self.assertFalse(m.latest['prediction_matched'])
 def test_memory_round_trip(self):
  m=PossibilityModel();stage=m.choose({},b'abc');m.observe(stage,{'status':'validated-model'});n=PossibilityModel();n.restore(m.view());self.assertEqual(m.memory,n.memory);self.assertEqual(m.tick,n.tick)

 def test_every_known_stage_gets_repeated_verification(self):
  m=PossibilityModel();known=dict.fromkeys(('hydrogen','stellar','earth'));counts=dict.fromkeys(known,0)
  for _ in range(30):
   stage=m.choose(known,b'abc');counts[stage]+=1;m.observe(stage,{'status':'validated-model'})
  self.assertTrue(all(v>=8 for v in counts.values()))
 def test_parent_persists_actual_decision_memory(self):
  import tempfile
  from pathlib import Path
  from neural_app.ambient_physics_discovery import PhysicsDiscovery
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'memory.json';m=PhysicsDiscovery(path);m.study('s',b'abc');m.flush();n=PhysicsDiscovery(path)
   self.assertEqual(m.possibilities.memory,n.possibilities.memory);self.assertIsNone(n.storage_error)

 def test_case_candidates_have_distinct_possible_outcomes(self):
  m=PossibilityModel();m.propose_case('source','digest','baseline','waiting')
  self.assertEqual(len(m.case_latest['candidates']),3)
  for candidate in m.case_latest['candidates']:self.assertEqual([b['outcome'] for b in candidate['branches']],['supported','unresolved'])
 def test_case_feedback_uses_actual_receipt_and_preserves_uncertainty(self):
  m=PossibilityModel();chosen=m.propose_case('s','d','baseline','waiting');m.finish_case({chosen:{'supported':False,'status':'ambiguous'}})
  self.assertFalse(m.case_memory[chosen]['last_success']);self.assertEqual(m.case_latest['actual_result']['status'],'ambiguous')
 def test_case_focus_covers_all_existing_operation_types(self):
  m=PossibilityModel();seen=set()
  for _ in range(30):
   chosen=m.propose_case('s','d','baseline','waiting');seen.add(chosen);m.finish_case({chosen:{'supported':True,'status':'checked'}})
  self.assertEqual(seen,{'representation-check','numerical-study','procedure-study'})

 def test_case_memory_persists_without_copying_runtime_histories(self):
  m=PossibilityModel();key=m.propose_case('s','d','baseline','waiting');m.finish_case({key:{'supported':True,'status':'checked'}})
  saved=m.checkpoint();self.assertNotIn('latest',saved['case_coordination']);n=PossibilityModel();n.restore(saved);self.assertEqual(n.case_memory,m.case_memory)
