import unittest,tempfile
from pathlib import Path
from neural_app.ambient_coupled_discovery import discover,CoupledDiscovery
from neural_app.ambient_physics_discovery import PhysicsDiscovery

class CoupledLearning(unittest.TestCase):
 def test_isolates_two_effects_and_generalizes_to_new_combinations(self):
  r=discover(lambda p:7*p[0]**2/p[1]**2,(1.,1.),[(2.,1.),(4.,1.),(1.,2.),(1.,4.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)])
  self.assertEqual(r['status'],'validated-model');self.assertEqual(r['model']['powers'],[2.,-2.])
  self.assertEqual({p['changed_variable'] for p in r['controlled_probes']},{0,1})
  self.assertTrue(all(sum(a!=b for a,b in zip(p['inputs'],p['comparison_anchor']))==1 for p in r['controlled_probes']))
 def test_one_varying_input_cannot_resolve_an_uncontrolled_factor(self):
  r=discover(lambda p:7*p[0]/p[1]**2,(1.,1.),[(2.,1.),(4.,1.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)])
  self.assertEqual(r['status'],'ambiguous');self.assertGreater(r['remaining_models'],1)
 def test_an_irrelevant_factor_can_have_zero_exponent(self):
  r=discover(lambda p:7*p[0],(1.,1.),[(2.,1.),(4.,1.),(1.,2.),(1.,4.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)])
  self.assertEqual(r['status'],'validated-model');self.assertEqual(r['model']['powers'],[1.,0.])
 def test_probes_changing_both_inputs_are_rejected(self):
  r=discover(lambda p:7*p[0],(1.,1.),[(2.,2.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)])
  self.assertEqual(r['status'],'uncontrolled-probe')
 def test_holdout_inputs_are_not_used_to_choose_probes(self):
  calls=[];held=[(3.,5.),(5.,3.),(7.,2.),(2.,7.)]
  def oracle(p):calls.append(p);return 7*p[0]/p[1]**2
  r=discover(oracle,(1.,1.),[(2.,1.),(4.,1.),(1.,2.),(1.,4.)],held)
  self.assertFalse(r['validation_used_for_selection']);self.assertEqual(calls[-4:],held)
 def test_three_coupled_reference_models_and_new_transfer_inputs(self):
  lab=CoupledDiscovery()
  for _ in range(2):
   for stage in ('hydrogen','stellar','earth'):r=lab.study(stage,'source',b'ABCD')
  self.assertEqual(lab.models['hydrogen']['powers'],[2.,-2.]);self.assertEqual(lab.models['stellar']['powers'],[1.,-2.]);self.assertEqual(lab.models['earth']['powers'],[.25,.25])
  self.assertEqual(lab.transfers,3);self.assertTrue(r['retained_model_transfer']['new_input_combination'])
 def test_coupled_models_persist_with_existing_model_memory(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'models.json';lab=PhysicsDiscovery(path)
   for _ in range(3):lab.study('s',b'ABCD')
   lab.flush();loaded=PhysicsDiscovery(path)
   self.assertEqual(len(loaded.coupled.models),3);self.assertIsNone(loaded.storage_error)
 def test_unsupported_additive_interaction_is_not_accepted_as_power_product(self):
  r=discover(lambda p:p[0]+p[1],(1.,1.),[(2.,1.),(4.,1.),(1.,2.),(1.,4.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)])
  self.assertIn(r['status'],('no-supported-model','counterexample-found'))

 def test_information_choice_prefers_cheap_equally_informative_probe(self):
  from neural_app.ambient_coupled_discovery import rank_experiments
  models=[{'coefficient':1.,'powers':[p,0.]} for p in (1.,2.,3.)]
  ranked=rank_experiments(models,[(2.,1.),(4.,1.)],{(2.,1.):1.,(4.,1.):10.})
  self.assertEqual(ranked[0]['inputs'],(2.,1.));self.assertAlmostEqual(ranked[0]['expected_information_bits'],1.58496250072)
 def test_no_probe_budget_does_not_query_probes_or_holdout(self):
  calls=[]
  def oracle(p):calls.append(p);return p[0]/p[1]**2
  r=discover(oracle,(1.,1.),[(2.,1.),(1.,2.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)],experiment_budget=0)
  self.assertEqual(calls,[(1.,1.)]);self.assertEqual(r['status'],'ambiguous');self.assertEqual(r['probe_cost_spent'],0)
 def test_expensive_probes_never_exceed_budget(self):
  r=discover(lambda p:p[0]/p[1]**2,(1.,1.),[(2.,1.),(1.,2.)],[(3.,5.),(5.,3.),(7.,2.),(2.,7.)],experiment_budget=1,probe_costs={(2.,1.):2.,(1.,2.):1.})
  self.assertEqual(r['probe_cost_spent'],1);self.assertEqual(len(r['controlled_probes']),1)
 def test_zero_information_probe_does_not_spend_budget(self):
  from neural_app.ambient_coupled_discovery import rank_experiments
  r=rank_experiments([{'coefficient':1.,'powers':[1.,0.]},{'coefficient':1.,'powers':[2.,0.]}],[(1.,2.)])
  self.assertEqual(r[0]['expected_information_bits'],0)
