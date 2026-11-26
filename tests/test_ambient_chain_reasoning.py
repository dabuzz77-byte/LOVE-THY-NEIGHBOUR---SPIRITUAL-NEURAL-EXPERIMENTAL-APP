import unittest
from neural_app.ambient_chain_reasoning import reason
class ChainTests(unittest.TestCase):
 def models(self):return {'stellar':{'coefficient':1361.,'powers':[1.,-2.]},'earth':{'coefficient':(1/(4*5.670374419e-8))**.25,'powers':[.25,.25]}}
 def test_missing_model_waits(self):self.assertEqual(reason({},1)['status'],'waiting-for-learned-stages')
 def test_fresh_combinations_and_inverse_goals(self):
  for i in range(50):
   r=reason(self.models(),i);self.assertEqual(r['status'],'composition-and-goal-verified');self.assertTrue(r['goal_plan']['passed']);self.assertFalse(r['goal_plan']['external_action'])
 def test_wrong_model_fails_goal_check(self):
  m=self.models();m['stellar']['coefficient']*=2
  self.assertEqual(reason(m,3)['status'],'counterexample-found')
 def test_irrelevant_control_is_not_inverted(self):
  m=self.models();m['stellar']['powers'][1]=0
  r=reason(m,3);self.assertEqual(r['status'],'counterexample-found');self.assertIsNone(r['goal_plan']);self.assertEqual(r['relearn_stages'],['stellar'])

 def test_isolates_upstream_without_blaming_downstream(self):
  m=self.models();m['stellar']['coefficient']*=2
  r=reason(m,2);self.assertEqual(r['relearn_stages'],['stellar']);self.assertIsNone(r['goal_plan']);self.assertFalse(r['plan_eligible'])
 def test_isolates_downstream_error(self):
  m=self.models();m['earth']['coefficient']*=1.1
  self.assertEqual(reason(m,2)['relearn_stages'],['earth'])
 def test_cancelling_errors_do_not_hide_bad_components(self):
  m=self.models();m['stellar']['coefficient']*=16;m['earth']['coefficient']/=2
  r=reason(m,2);self.assertTrue(r['checks'][0]['passed']);self.assertEqual(r['relearn_stages'],['stellar','earth']);self.assertFalse(r['plan_eligible'])
 def test_parent_quarantines_and_prioritises_relearning(self):
  from neural_app.ambient_physics_discovery import PhysicsDiscovery
  lab=PhysicsDiscovery()
  for _ in range(3):lab.study('s',b'ABC')
  lab.coupled.models['earth']['coefficient']*=2
  lab.relearn_queue=['hydrogen']
  r=lab.study('s',b'DEF');self.assertEqual(r['chain_reasoning']['relearn_stages'],['earth']);self.assertNotIn('earth',lab.coupled.models)
  r=lab.study('s',b'GHI');self.assertEqual(r['stage'],'earth');self.assertEqual(r['chain_reasoning']['status'],'composition-and-goal-verified')

 def test_noisy_chain_waits_for_fresh_transfer(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  from neural_app.ambient_chain_reasoning import reason_noisy
  self.assertEqual(reason_noisy(NoisyMemory(),1)['status'],'waiting-for-transfer-checked-models')
 def test_noisy_chain_runs_through_parent_on_generated_captures(self):
  from neural_app.ambient_physics_discovery import PhysicsDiscovery
  lab=PhysicsDiscovery()
  for i in range(9):r=lab.study('source',bytes([65+i])*32)
  self.assertEqual(r['noisy_chain_reasoning']['status'],'approximate-chain-supported')
  self.assertEqual(len(r['noisy_chain_reasoning']['checks']),3);self.assertFalse(r['noisy_chain_reasoning']['external_action'])
 def test_noisy_chain_checks_components_even_if_errors_cancel(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  from neural_app.ambient_chain_reasoning import reason_noisy
  m=NoisyMemory();m.models=self.models();m.eligible={'stellar','earth'}
  m.models['stellar']['coefficient']*=16;m.models['earth']['coefficient']/=2
  r=reason_noisy(m,2);self.assertTrue(r['checks'][-1]['passed']);self.assertEqual(r['status'],'approximate-chain-counterexample');self.assertEqual(set(r['withdrawn_stages']),{'stellar','earth'});self.assertFalse(m.eligible)

 def test_learned_counterfactuals_distinguish_two_controls(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  from neural_app.ambient_chain_reasoning import reason_noisy
  m=NoisyMemory();m.models=self.models();m.eligible={'stellar','earth'}
  r=reason_noisy(m,4);a,b=r['counterfactuals'];self.assertGreater(a['predicted_change_kelvin'],0);self.assertLess(b['predicted_change_kelvin'],0);self.assertTrue(all(c['passed'] for c in r['counterfactuals']))
