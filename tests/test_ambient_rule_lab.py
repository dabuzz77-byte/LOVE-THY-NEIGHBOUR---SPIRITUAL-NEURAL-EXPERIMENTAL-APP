import unittest,random,tempfile,json
from pathlib import Path
from neural_app.ambient_rule_lab import RuleLab,infer,apply

class AmbientRuleLearning(unittest.TestCase):
 def test_infers_rules_and_generalizes_to_unseen_domain(self):
  for target in [('affine',7,31),('xor',83,0),('rotate',3,0)]:
   training=[(x,apply(target,x)) for x in (1,7,19,31,63,80,127,197)]
   validation=[(x,apply(target,x)) for x in (0,2,17,44,99,155,201,255)]
   result=infer(training,validation);self.assertEqual(result['status'],'validated-candidate')
   self.assertTrue(all(apply(tuple(result['rule']),x)==apply(target,x) for x in range(256)))
 def test_random_labels_do_not_become_an_invented_rule(self):
  rng=random.Random(8);pairs=[(x,rng.randrange(256)) for x in range(16)]
  self.assertEqual(infer(pairs[:8],pairs[8:])['status'],'no-supported-rule')
 def test_validation_cannot_overlap_training(self):
  self.assertEqual(infer([(x,x) for x in range(8)],[(x,x) for x in range(4)])['status'],'invalid-split')
 def test_failed_holdout_prevents_retention(self):
  train=[(x,x^71) for x in range(8)];validation=[(x,0) for x in range(10,18)]
  self.assertEqual(infer(train,validation)['status'],'no-supported-rule')
 def test_verified_procedure_is_reused_without_candidate_search(self):
  lab=RuleLab();first=lab.study('fixture',b'ABCD'*64);second=lab.study('fixture',b'ABCD'*64)
  self.assertEqual(first['status'],'verified-procedure-retained')
  self.assertEqual(second['status'],'verified-procedure-reused')
  self.assertEqual(second['discovery']['tested_candidates'],0)
  self.assertEqual(first['full_domain_check']['passed'],256)
 def test_saved_skills_restore_as_registered_pure_functions(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'skills.json';lab=RuleLab(path);lab.study('fixture',b'ABCD'*64);lab.flush()
   restored=RuleLab(path);self.assertEqual(len(restored.skills),1)
   self.assertEqual(restored.study('fixture',b'ABCD'*64)['discovery']['tested_candidates'],0)
 def test_tampered_skill_checksum_is_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'skills.json';path.write_text(json.dumps({'version':1,'skills':{'bad':{'rule':['xor',1,0],'verified_domain':256}}}))
   lab=RuleLab(path);self.assertFalse(lab.skills);self.assertIsNotNone(lab.storage_error)
 def test_empty_source_creates_no_task(self):self.assertEqual(RuleLab().study('none',b'')['status'],'waiting-for-input')
