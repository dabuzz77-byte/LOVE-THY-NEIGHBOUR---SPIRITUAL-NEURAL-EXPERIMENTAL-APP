import unittest
from neural_app.ambient_transfer_challenge import challenge
class TransferChallengeTests(unittest.TestCase):
 def test_thirty_unfamiliar_environments_transfer(self):
  for serial in range(30):
   r=challenge(b'generated-capture',serial);self.assertEqual(r['status'],'unfamiliar-task-transfer-supported');self.assertEqual(len(r['reserved_transfer']),4);self.assertFalse(r['target_parameters_supplied_to_learner']);self.assertFalse(r['fit']['validation_used_for_fit'])
 def test_tasks_are_reproducible_and_vary(self):
  a=challenge(b'abc',1);self.assertEqual(a,challenge(b'abc',1));self.assertNotEqual(a['task_digest'],challenge(b'abc',2)['task_digest'])
 def test_empty_capture_does_not_fabricate_learning(self):self.assertEqual(challenge(b'')['status'],'waiting-for-generated-input')
 def test_parent_schedules_bounded_challenges(self):
  from neural_app.ambient_coupled_discovery import CoupledDiscovery
  lab=CoupledDiscovery();results=[lab.study('stellar','s',b'abc')['unfamiliar_transfer_challenge'] for _ in range(4)]
  self.assertEqual(results[:3],[None]*3);self.assertEqual(results[3]['status'],'unfamiliar-task-transfer-supported')

 def test_selects_unlabelled_affine_and_power_families(self):
  for serial in range(20):
   r=challenge(b'mixed',serial)['family_selection'];self.assertEqual(r['status'],'reserved-test-supported');self.assertEqual(r['selected_model']['family'],'affine' if serial%2 else 'power-product');self.assertFalse(r['test_used_for_selection'])
 def test_test_labels_cannot_change_family_choice(self):
  from neural_app.ambient_family_selection import select
  train=[(x,z,2+x+3*z) for x in (1,2,3) for z in (1,2,3)]
  choose=[(x,z,2+x+3*z) for x,z in ((4,2),(5,3),(6,4),(7,5))]
  test=[(x,z,2+x+3*z) for x,z in ((8,1),(9,2),(10,3),(11,4))]
  a=select(train,choose,test);b=select(train,choose,[(x,z,y*10) for x,z,y in test]);self.assertEqual(a['selected_model'],b['best_unverified_candidate']);self.assertIsNone(b['selected_model']);self.assertEqual(b['status'],'not-supported')

 def test_unsupported_family_abstains_without_reading_final_outcomes(self):
  from neural_app.ambient_family_selection import select
  f=lambda x,z:2+x*x+3*z*z
  t=[(x,z,f(x,z)) for x in (1,2,3,4) for z in (1,2,3)]
  v=[(x,z,f(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))]
  h=[(x,z,f(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))]
  a=select(t,v,h);b=select(t,v,[(x,z,y*9) for x,z,y in h])
  self.assertEqual(a['status'],'unresolved-model-family');self.assertIsNone(a['selected_model']);self.assertEqual(a['reserved_checks'],[]);self.assertEqual(a,b);self.assertFalse(a['next_experiment']['observation_received'])
 def test_limits_oversized_batches(self):
  from neural_app.ambient_family_selection import select
  self.assertEqual(select([(1,1,1)]*129,[],[])['status'],'input-budget-exceeded')

 def test_running_challenge_exercises_abstention(self):
  r=challenge(b'abc',1)['unsupported_family_trial'];self.assertEqual(r['status'],'unresolved-model-family');self.assertIsNone(r['selected_model'])

 def test_simulator_experiments_run_within_budget_without_forcing_answer(self):
  r=challenge(b'abc',1)['active_family_investigation'];self.assertEqual(r['experiment_count'],2);self.assertEqual(r['status'],'unresolved-model-family');self.assertIsNone(r['result']['selected_model']);self.assertFalse(r['external_action']);self.assertTrue(all(not t['hypothesis_family_expanded'] for t in r['trace']))
 def test_zero_budget_does_not_observe_anything(self):
  from neural_app.ambient_family_selection import investigate
  calls=[];f=lambda x,z:2+x*x+3*z*z
  t=[(x,z,f(x,z)) for x in (1,2,3,4) for z in (1,2,3)];v=[(x,z,f(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))];h=[(x,z,f(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))]
  r=investigate(t,v,h,lambda x,z:calls.append((x,z)),budget=0);self.assertEqual(calls,[]);self.assertEqual(r['experiment_count'],0)
 def test_failed_final_test_is_not_recycled_for_adaptation(self):
  from neural_app.ambient_family_selection import investigate
  f=lambda x,z:2+x+3*z;t=[(x,z,f(x,z)) for x in (1,2,3) for z in (1,2,3)];v=[(x,z,f(x,z)) for x,z in ((4,2),(5,3),(6,4),(7,5))];h=[(x,z,f(x,z)*10) for x,z in ((8,1),(9,2),(10,3),(11,4))]
  calls=[];r=investigate(t,v,h,lambda x,z:calls.append((x,z)));self.assertEqual(r['status'],'not-supported');self.assertEqual(calls,[])

 def test_challenge_evidence_survives_non_challenge_steps_and_is_bounded(self):
  from neural_app.ambient_coupled_discovery import CoupledDiscovery
  lab=CoupledDiscovery()
  for _ in range(4):lab.study('stellar','s',b'abc')
  digest=lab.view()['last_challenge']['task_digest'];lab.study('stellar','s',b'abc');self.assertEqual(lab.view()['last_challenge']['task_digest'],digest)
  for _ in range(67):lab.study('stellar','s',b'abc')
  self.assertEqual(len(lab.view()['challenge_history']),16)

 def test_bounded_family_expansion_resolves_quadratic_trial(self):
  r=challenge(b'abc',1)['family_expansion'];self.assertTrue(r['expanded']);self.assertEqual(r['result']['status'],'reserved-test-supported');self.assertEqual(r['result']['selected_model']['family'],'quadratic')
 def test_simple_model_is_not_replaced_by_unnecessary_expansion(self):
  from neural_app.ambient_family_selection import expand_family
  f=lambda x,z:2+x+3*z;t=[(x,z,f(x,z)) for x in (1,2,3,4) for z in (1,2,3)];v=[(x,z,f(x,z)) for x,z in ((4,4),(5,3),(6,4),(7,5))];h=[(x,z,f(x,z)) for x,z in ((8,1),(9,2),(10,3),(11,4))]
  r=expand_family(t,v,h);self.assertFalse(r['expanded']);self.assertEqual(r['result']['selected_model']['family'],'affine')

 def test_varied_quadratic_relationships_generalise(self):
  import random
  from neural_app.ambient_family_selection import expand_family
  for seed in range(25):
   rng=random.Random(seed);weights=[rng.uniform(.3,2) for _ in range(6)]
   def f(x,z):return sum(a*b for a,b in zip(weights,(1,x,z,x*x,x*z,z*z)))
   t=[(x,z,f(x,z)) for x in (1,2,3,4) for z in (1,2,3)];v=[(x,z,f(x,z)) for x,z in ((.5,4),(5,.5),(6,4),(4,6))];h=[(x,z,f(x,z)) for x,z in ((7,2),(8,3),(9,4),(10,5))]
   r=expand_family(t,v,h);self.assertTrue(r['expanded']);self.assertEqual(r['result']['status'],'reserved-test-supported');self.assertEqual(r['result']['selected_model']['family'],'quadratic')
 def test_expansion_still_abstains_on_higher_order_relationship(self):
  r=challenge(b'abc',1);self.assertNotEqual(r['higher_order_trial']['result']['status'],'reserved-test-supported');self.assertTrue(r['learning_summary']['remaining_unknown']);self.assertTrue(r['learning_summary']['expansion_verified'])

 def test_source_ablation_holds_environment_fixed(self):
  from neural_app.ambient_source_ablation import compare
  a=compare(bytes(range(64)),7);b=compare(bytes(reversed(range(64))),7)
  self.assertEqual(a['environment_id'],b['environment_id']);self.assertNotEqual(a['arms'][0]['training_inputs'],b['arms'][0]['training_inputs']);self.assertEqual(a['arms'][1],b['arms'][1]);self.assertTrue(a['same_environment_and_reserved_inputs'])
 def test_all_sampling_arms_learn_without_presumed_ambient_advantage(self):
  from neural_app.ambient_source_ablation import compare
  for serial in range(12):
   r=compare(bytes(range(64)),serial)
   for arm in r['arms']:self.assertEqual(arm['status'],'heldout-supported');self.assertLess(arm['heldout_log_error'],1e-8)

 def test_budget_comparison_charges_equal_observation_counts(self):
  from neural_app.ambient_source_ablation import budget_comparison
  r=budget_comparison(b'abc',3);self.assertEqual(len(r['rows']),9);self.assertFalse(r['test_used_for_sampling'])
  for row in r['rows']:self.assertEqual(row['observation_budget'],row['observations_used']);self.assertEqual(row['test_observations'],4)
 def test_budget_controls_are_independent_of_capture(self):
  from neural_app.ambient_source_ablation import budget_comparison
  a=budget_comparison(b'abc',4);b=budget_comparison(b'def',4)
  self.assertEqual(a['environment_id'],b['environment_id']);self.assertEqual([r for r in a['rows'] if r['arm']!='capture'],[r for r in b['rows'] if r['arm']!='capture']);self.assertEqual(a,budget_comparison(b'abc',4))
