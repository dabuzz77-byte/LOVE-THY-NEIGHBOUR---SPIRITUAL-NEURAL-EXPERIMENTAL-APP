import unittest,tempfile,math
from pathlib import Path
from neural_app.ambient_physics_discovery import discover,PhysicsDiscovery,predict

class PhysicsModelDiscovery(unittest.TestCase):
 def test_recovers_unknown_scale_and_exponent_from_observations(self):
  r=discover(lambda x:7.3*x**-.5,[2.,3.,5.,8.],[1.5,2.5,4.5,9.],1.)
  self.assertEqual(r['status'],'validated-model');self.assertEqual(r['model']['exponent'],-.5)
  self.assertAlmostEqual(r['model']['coefficient'],7.3)
  self.assertFalse(r['validation_used_for_selection'])
 def test_all_three_cosmic_reference_models_are_rediscovered(self):
  lab=PhysicsDiscovery();rows=[lab.study('source',b'ABCD'*20) for _ in range(3)]
  self.assertEqual({r['stage']:r['model']['exponent'] for r in rows},{'hydrogen':-2.,'stellar':-2.,'earth':.25})
  self.assertTrue(all(r['status']=='validated-model' and all(c['passed'] for c in r['heldout_checks']) for r in rows))
 def test_unrepresented_equation_is_not_falsely_accepted(self):
  r=discover(lambda x:x*x+3,[2.,3.,5.,8.],[1.5,2.5,4.5,9.],1.)
  self.assertIn(r['status'],('no-supported-equation','counterexample-found'))
 def test_reserved_inputs_are_only_observed_after_model_selection(self):
  calls=[];held=[1.5,2.5,4.5,9.]
  def oracle(x):calls.append(x);return 7.3/x**2
  r=discover(oracle,[2.,3.,5.,8.],held,1.)
  self.assertEqual(calls[-4:],held);self.assertFalse(set(p['input'] for p in r['active_probes'])&set(held))
 def test_retained_model_transfers_to_unseen_input(self):
  lab=PhysicsDiscovery()
  for _ in range(6):r=lab.study('source',b'ABCD'*20)
  self.assertEqual(lab.transfers,3);self.assertTrue(r['retained_model_transfer']['passed'])
 def test_persistent_model_is_rechecked_in_environment(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'physics.json';lab=PhysicsDiscovery(path);lab.study('s',b'ABCD');lab.flush()
   loaded=PhysicsDiscovery(path);loaded.relearn_queue=list(loaded.models);r=loaded.study('s',b'EFGH')
   self.assertTrue(r['retained_model_transfer']['passed']);self.assertIsNone(loaded.storage_error)
 def test_invalid_domains_do_not_produce_equations(self):
  self.assertEqual(discover(lambda x:x,[0.,2.],[3.,4.,5.,6.],1.)['status'],'invalid-input')
  self.assertEqual(discover(lambda x:x,[2.],[3.,4.,5.,1.],1.)['status'],'invalid-split')
  with self.assertRaises(ValueError):predict({'coefficient':1,'exponent':2},0)
 def test_missing_source_does_not_fabricate_an_experiment(self):self.assertEqual(PhysicsDiscovery().study('s',b'')['status'],'waiting-for-input')
 def test_transfer_probe_is_new_and_survives_restart(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'physics.json';lab=PhysicsDiscovery(path);first=lab.study('s',b'ABCD')
   for _ in range(3):later=lab.study('s',b'ABCD')
   old=later['retained_model_transfer']['input'];lab.flush()
   loaded=PhysicsDiscovery(path);new=loaded.study('s',b'ABCD')['retained_model_transfer']['input']
   self.assertNotEqual(old,new)
   self.assertNotIn(old,[c['input'] for c in first['heldout_checks']])
   self.assertNotIn(old,[c['input'] for c in first['observations']])
 def test_wrong_retained_coefficient_is_detected_and_relearned(self):
  lab=PhysicsDiscovery();lab.models['hydrogen']={'coefficient':27.,'exponent':-2.};lab.relearn_queue=['hydrogen']
  r=lab.study('s',b'ABCD')
  self.assertFalse(r['retained_model_transfer']['passed'])
  self.assertEqual(r['status'],'validated-model')
  self.assertAlmostEqual(lab.models['hydrogen']['coefficient'],13.598433)
