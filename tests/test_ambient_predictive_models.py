import unittest,random
from neural_app.ambient_predictive_models import PredictiveModels

class AdaptiveSourceModels(unittest.TestCase):
 def test_selects_longer_context_from_previous_errors(self):
  models=PredictiveModels()
  for _ in range(5):r=models.observe('structured',b'AABB'*256)
  self.assertEqual(r['selected_order'],2)
  self.assertGreater(r['gain_over_frequency_bits_per_byte'],.5)
  self.assertTrue(r['model_frozen_during_capture'])
  self.assertFalse(r['proposal_is_command'])
 def test_first_capture_has_no_retrospective_model_choice(self):
  r=PredictiveModels().observe('new',b'AB'*512)
  self.assertEqual(r['selected_order'],0)
  self.assertEqual(r['gain_over_frequency_bits_per_byte'],0)
  self.assertEqual({v['bits_per_byte'] for v in r['experts']},{8.})
 def test_random_data_does_not_get_assumed_prediction_gain(self):
  models=PredictiveModels();rng=random.Random(98)
  for _ in range(6):r=models.observe('random',bytes(rng.randrange(256) for _ in range(1024)))
  self.assertLess(r['gain_over_frequency_bits_per_byte'],.2)
 def test_sources_do_not_share_models(self):
  models=PredictiveModels();models.observe('a',b'AABB'*256)
  self.assertEqual(models.observe('b',b'AABB'*256)['prior_captures'],0)
 def test_memory_and_context_tables_are_bounded(self):
  models=PredictiveModels();rng=random.Random(88)
  for i in range(40):r=models.observe(str(i),bytes(rng.randrange(256) for _ in range(1024)))
  self.assertEqual(len(models.sources),32)
  self.assertTrue(all(v<=128 for v in r['context_counts']))
 def test_short_samples_wait(self):self.assertEqual(PredictiveModels().observe('empty',b'')['status'],'insufficient-sample')
 def test_full_active_source_set_keeps_learned_contexts(self):
     models=PredictiveModels()
     for _ in range(4):
         for i in range(32):r=models.observe('stream-'+str(i),b'AABB'*256)
     self.assertEqual(r['prior_captures'],3)
     self.assertEqual(r['selected_order'],2)

 def test_matched_rails_require_all_three_same_capture(self):
     from neural_app.ambient_rail_evidence import compare_rails
     checks={}
     for rail in ('ordered-source','random-sample','chain-transformed'):
         checks[rail]={'status':'candidate-structure','conditions':{'source':'original','rail':rail,'capture_tick':3}}
     self.assertEqual(compare_rails(checks)[0]['status'],'matched-capture')
     checks['random-sample']['conditions']['capture_tick']=4
     self.assertEqual(compare_rails(checks)[0]['status'],'waiting-for-matched-rails')
 def test_transformed_predictability_is_not_claimed_as_source_intelligence(self):
     from neural_app.ambient_rail_evidence import compare_rails
     rows={rail:{'status':'candidate-structure','conditions':{'source':'s','rail':rail,'capture_tick':1},'temporal_prediction':{'prior_captures':3,'relative_error_reduction':gain}} for rail,gain in [('ordered-source',-.01),('random-sample',-.02),('chain-transformed',.8)]}
     assessment=compare_rails(rows)[0]['representation_assessment']
     self.assertEqual(assessment['status'],'predictability-only-in-transformed-rail')
     self.assertFalse(assessment['same_prediction_target'])
