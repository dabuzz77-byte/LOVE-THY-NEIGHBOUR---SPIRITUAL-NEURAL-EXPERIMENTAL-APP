import unittest,math,random
from neural_app.ambient_noisy_learning import fit
class NoisyTests(unittest.TestCase):
 def fresh(self,h,scale=1.):return [(x*1.07,z,y*1.07*scale) for x,z,y in h]

 def data(self):
  rng=random.Random(42)
  train=[(x,z,7*x/z**2*math.exp(rng.uniform(-.02,.02))) for x in (1,2,3,4) for z in (1,2,3)]
  held=[(x,z,7*x/z**2) for x,z in ((1.5,4),(2.5,5),(3.5,6),(4.5,7))]
  return train,held
 def test_learns_noisy_power_product_on_reserved_combinations(self):
  t,h=self.data();r=fit(t,h);self.assertEqual(r['status'],'heldout-supported');self.assertAlmostEqual(r['model']['powers'][0],1,delta=.03);self.assertAlmostEqual(r['model']['powers'][1],-2,delta=.03);self.assertFalse(r['validation_used_for_fit'])
 def test_unvaried_factor_is_unidentifiable(self):
  t,h=self.data();t=[(x,1,y) for x,z,y in t];self.assertEqual(fit(t,h)['status'],'unidentifiable-inputs')
 def test_validation_change_cannot_change_fitted_model(self):
  t,h=self.data();a=fit(t,h);b=fit(t,[(x,z,y*10) for x,z,y in h]);self.assertEqual(a['model'],b['model']);self.assertEqual(b['status'],'not-supported')
 def test_overlap_rejected(self):
  t,h=self.data();self.assertEqual(fit(t,[t[0]]+h)['status'],'overlapping-validation')
 def test_all_reference_stages_run_robustness_trial(self):
  from neural_app.ambient_coupled_discovery import CoupledDiscovery
  lab=CoupledDiscovery()
  for stage in ('hydrogen','stellar','earth'):self.assertEqual(lab.study(stage,'s',b'abc')['noisy_learning']['status'],'heldout-supported')

 def test_new_model_waits_for_future_capture(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  t,h=self.data();memory=NoisyMemory()
  self.assertFalse(memory.observe('stellar',t,h)['eligible'])
  r=memory.observe('stellar',t,self.fresh(h));self.assertTrue(r['eligible']);self.assertTrue(r['fresh_capture_check']['evaluated_before_refit'])
 def test_changed_environment_revokes_model_before_replacement(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  t,h=self.data();memory=NoisyMemory();memory.observe('s',t,h);memory.observe('s',t,self.fresh(h))
  r=memory.observe('s',[(x,z,y*3) for x,z,y in t],self.fresh(h,3))
  self.assertFalse(r['eligible']);self.assertFalse(r['fresh_capture_check']['passed'])
  self.assertTrue(memory.observe('s',[(x,z,y*3) for x,z,y in t],[(x*1.13,z,y*1.13*3) for x,z,y in h])['eligible'])

 def test_repeated_capture_is_not_new_evidence(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  t,h=self.data();m=NoisyMemory();m.observe('s',t,h);r=m.observe('s',t,h)
  self.assertTrue(r['repeated_capture']);self.assertFalse(r['eligible'])

 def test_remeasuring_old_points_does_not_establish_transfer(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  t,h=self.data();m=NoisyMemory();m.observe('s',t,h)
  r=m.observe('s',t,[(x,z,y*1.001) for x,z,y in h]);self.assertFalse(r['eligible']);self.assertEqual(r['fresh_capture_check']['new_input_combinations'],0)
 def test_shuffled_controls_are_reported_and_beaten(self):
  from neural_app.ambient_noisy_learning import controlled_fit
  t,h=self.data();r=controlled_fit(t,h);self.assertEqual(len(r['shuffled_control_errors']),4);self.assertTrue(r['beats_all_shuffled_controls'])

 def test_successful_transfer_points_are_not_reused_as_fresh(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  t,h=self.data();m=NoisyMemory();m.observe('s',t,h);self.assertTrue(m.observe('s',t,self.fresh(h))['eligible'])
  r=m.observe('s',t,[(x,z,y*1.001) for x,z,y in self.fresh(h)]);self.assertFalse(r['eligible']);self.assertEqual(r['fresh_capture_check']['new_input_combinations'],0)

 def test_invalid_capture_suspends_previous_eligibility(self):
  from neural_app.ambient_noisy_learning import NoisyMemory
  t,h=self.data();m=NoisyMemory();m.observe('s',t,h);m.observe('s',t,self.fresh(h));self.assertIn('s',m.eligible)
  r=m.observe('s',[],[]);self.assertFalse(r['eligible']);self.assertNotIn('s',m.eligible)
 def test_duplicate_validation_points_rejected(self):
  t,h=self.data();self.assertEqual(fit(t,[h[0]]*4)['status'],'duplicate-validation-inputs')
 def test_random_labels_do_not_create_supported_models(self):
  from neural_app.ambient_noisy_learning import controlled_fit
  for seed in range(20):
   rng=random.Random(seed)
   t=[(x,z,math.exp(rng.uniform(-3,3))) for x in (1,2,3,4) for z in (1,2,3)]
   h=[(x,z,math.exp(rng.uniform(-3,3))) for x,z in ((1.5,4),(2.5,5),(3.5,6),(4.5,7))]
   self.assertNotEqual(controlled_fit(t,h)['status'],'heldout-supported')
 def test_numeric_overflow_is_reported_without_worker_exception(self):
  from neural_app.ambient_noisy_learning import fit
  t=[(1+i*1e-4,1+j*1e-4,math.exp((i-j)*10)) for i in range(3) for j in range(3)]
  h=[(10+i,2+i,1) for i in range(4)]
  self.assertEqual(fit(t,h)['status'],'numerically-unsupported')
