import unittest,hashlib
from neural_app.sphere_ambient_reasoning import AmbientSphereReasoning
from neural_app.sphere_functions import SphereFunctions,PROFILES

def row(text=b'AABB'*64,source='ambient-fixture'):
 return {'source':source,'raw':text,'digest':hashlib.sha256(text).hexdigest(),'parent_event':12,'generated':True}

def checks(source='ambient-fixture',prior=3):
 return {source:{'status':'candidate-structure','adaptive_prediction':{'prior_captures':prior,'gain_over_frequency_bits_per_byte':1.},'temporal_prediction':{'prior_captures':prior,'relative_error_reduction':.8,'forecast_normalized_byte':.2,'prediction_before_current_test_training':True}}}

class AmbientSphereTests(unittest.TestCase):
 def test_every_role_works_on_traceable_generated_input(self):
  w=AmbientSphereReasoning();w.ingest([row()],checks())
  for lane,(role,_) in PROFILES.items():
   r=w.process(lane,role);self.assertEqual(r['status'],'completed');self.assertEqual(r['source_sha256'],row()['digest'])
  self.assertEqual(w.view()['roles_reached'],len(PROFILES))
  self.assertEqual(w.view()['completed_role_steps'],len(PROFILES))
 def test_choice_action_consequence_have_distinct_findings(self):
  w=AmbientSphereReasoning();w.ingest([row()],checks())
  choice=w.process('choice-study','selection');action=w.process('action-study','action');consequence=w.process('consequence-study','forecast')
  self.assertEqual(choice['finding']['selected_predictor'],'temporal')
  self.assertTrue(action['finding']['all_passed'])
  self.assertTrue(consequence['finding']['forecast']['evaluated_before_update'])
  self.assertEqual(len({r['case_id'] for r in (choice,action,consequence)}),1)
 def test_revisiting_old_case_does_not_inflate_reasoning(self):
  w=AmbientSphereReasoning();one=row();two=row(b'CCDD'*64)
  for r in (one,two,one):w.ingest([r],checks());w.process('choice-study','selection')
  self.assertEqual(w.steps,2);self.assertEqual(w.sequence,2)
 def test_missing_or_untrained_predictions_fall_back(self):
  w=AmbientSphereReasoning();w.ingest([row()],checks(prior=0))
  self.assertEqual(w.process('choice-study','selection')['finding']['selected_predictor'],'baseline')
 def test_non_generated_input_does_not_become_stochastic_evidence(self):
  w=AmbientSphereReasoning();r=row();r['generated']=False;w.ingest([r],checks())
  self.assertEqual(w.process('choice-study','selection')['status'],'waiting-for-generated-source')
 def test_new_case_changes_actual_sphere_record_and_nodes(self):
  functions=SphereFunctions();functions.ambient_reasoning.ingest([row()],checks())
  record=functions.process('choice-study',{},{});frame=functions.decorate('choice-study',{'particles':[]})
  self.assertEqual(record['status'],'processed');self.assertEqual(len(frame['ambient_reasoning_nodes']),6)
  self.assertTrue(all(p['source_digest']==row()['digest'] for p in frame['ambient_reasoning_nodes']))
 def test_storage_is_bounded(self):
  w=AmbientSphereReasoning()
  for n in range(50):w.ingest([row(bytes([n])*100)],{});w.process('choice-study','selection')
  self.assertEqual(len(w.cases),32)
 def test_case_stays_active_until_all_expected_roles_receive_it(self):
  w=AmbientSphereReasoning(expected_roles=2);w.ingest([row()],checks());first=w.latest['id']
  w.process('choice','selection');w.ingest([row(b'CCDD'*64)],checks())
  self.assertEqual(w.latest['id'],first)
  w.process('action','action');w.ingest([row(b'CCDD'*64)],checks())
  self.assertNotEqual(w.latest['id'],first)
 def test_long_cosmic_source_finds_its_canonical_learning_result(self):
  from neural_app.ambient_source_identity import source_key
  source='cosmic-chain/'+('very-long-source-'*10);w=AmbientSphereReasoning();r=row(source=source)
  w.ingest([r],checks(source=source_key(source)))
  self.assertEqual(w.latest['selected_predictor'],'temporal')
