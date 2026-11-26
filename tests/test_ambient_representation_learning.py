import unittest,random,math
from neural_app.ambient_representation_learning import RepresentationLearning,rows

def delayed(seed):
 rng=random.Random(seed);values=[rng.randrange(32,127) for _ in range(8)]
 for i in range(8,512):values.append(values[i-8])
 return bytes(values)

class SameTargetLearning(unittest.TestCase):
 def test_delay_memory_solves_original_target_with_longer_history(self):
  m=RepresentationLearning()
  for i in range(4):r=m.observe('delay',delayed(100+i))
  self.assertEqual(r['selected_before_test'],'delay-memory')
  self.assertGreater(r['selected_gain_over_best_baseline'],.95)
  self.assertTrue(r['same_prediction_target'])
 def test_random_input_does_not_get_guaranteed_gain(self):
  rng=random.Random(439);m=RepresentationLearning()
  for _ in range(4):r=m.observe('noise',bytes(rng.randrange(256) for i in range(512)))
  self.assertLess(r['selected_gain_over_best_baseline'],.05)
 def test_no_test_target_is_used_in_its_own_input_features(self):
  first=bytes(range(100));second=first[:50]+bytes([255])+first[51:]
  a=rows(first);b=rows(second)
  self.assertEqual(a[50-8][1],b[50-8][1])
  self.assertNotEqual(a[50-8][0],b[50-8][0])
 def test_new_source_starts_with_baseline_chosen_before_test(self):
  m=RepresentationLearning();m.observe('a',delayed(1));r=m.observe('b',delayed(2))
  self.assertEqual(r['selected_before_test'],'mean');self.assertEqual(r['prior_captures'],0)
 def test_constant_source_and_empty_source_remain_finite(self):
  m=RepresentationLearning();self.assertEqual(m.observe('none',b'')['status'],'insufficient-sample')
  r=m.observe('constant',b'A'*512);self.assertTrue(all(math.isfinite(v) for v in r['mse'].values()))
  self.assertIsNone(r['selected_gain_over_best_baseline'])
 def test_sphere_uses_validated_same_target_memory_forecast(self):
  from neural_app.sphere_ambient_reasoning import AmbientSphereReasoning
  import hashlib
  raw=b'ABCD'*64;root={'source':'s','raw':raw,'digest':hashlib.sha256(raw).hexdigest(),'generated':True}
  workspace=AmbientSphereReasoning();workspace.ingest([root],{'s':{'representation_prediction':{'prior_captures':3,'selected_gain_over_best_baseline':.8,'selected_before_test':'delay-memory','next_selected':'delay-memory','same_prediction_target':True,'forecast_normalized_byte':.25}}})
  self.assertEqual(workspace.latest['selected_predictor'],'representation/delay-memory')
  self.assertEqual(workspace.latest['forecast']['normalized_byte'],.25)
