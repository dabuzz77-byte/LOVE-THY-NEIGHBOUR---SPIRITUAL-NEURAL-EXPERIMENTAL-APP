import unittest,random,math
from neural_app.ambient_temporal_models import TemporalModels,solve

def logistic(seed):
 values=[];x=seed
 for _ in range(1024):x=3.9*x*(1-x);values.append(round(255*x))
 return bytes(values)

class TemporalLearning(unittest.TestCase):
 def test_nonlinear_dynamics_prediction_beats_simple_baselines(self):
  model=TemporalModels();first=model.observe('dynamics',logistic(.173));second=model.observe('dynamics',logistic(.217))
  self.assertEqual(first['status'],'within-capture-heldout')
  self.assertEqual(second['status'],'cross-capture-evaluated')
  self.assertGreater(second['relative_error_reduction'],.95)
  self.assertTrue(second['evaluation_model_frozen'])
 def test_random_stream_is_not_assumed_predictable(self):
  rng=random.Random(372);model=TemporalModels()
  for _ in range(3):r=model.observe('random',bytes(rng.randrange(256) for _ in range(1024)))
  self.assertLess(r['relative_error_reduction'],.05)
 def test_constant_stream_does_not_claim_gain_over_perfect_baseline(self):
  r=TemporalModels().observe('constant',b'A'*1024)
  self.assertIsNone(r['relative_error_reduction'])
  self.assertLessEqual(r['gain_over_best_baseline'],0)
 def test_contexts_do_not_cross_sources(self):
  model=TemporalModels();model.observe('a',logistic(.1));r=model.observe('b',logistic(.2))
  self.assertEqual(r['prior_captures'],0)
 def test_rank_deficient_input_is_regularized(self):
  weights=solve([[0.]*6 for _ in range(6)],[0.]*6)
  self.assertTrue(all(math.isfinite(v) for v in weights))
 def test_short_and_bounded_sources(self):
  model=TemporalModels();self.assertEqual(model.observe('short',b'')['status'],'insufficient-sample')
  for i in range(35):model.observe(str(i),b'A'*100)
  self.assertEqual(len(model.sources),32)
