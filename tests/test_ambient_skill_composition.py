import unittest,tempfile,hashlib
from pathlib import Path
from neural_app.ambient_rule_lab import RuleLab,infer
from neural_app.ambient_skill_composition import compose,apply_program

class AmbientComposition(unittest.TestCase):
 def examples(self,program):
  train=[(x,apply_program(program,x)) for x in (1,7,19,31,63,80,127,197)]
  held=[(x,apply_program(program,x)) for x in (0,2,17,44,99,155,201,255)]
  return train,held
 def test_composes_learned_skills_for_task_no_single_rule_solves(self):
  atoms=[('xor',83,0),('affine',7,31),('rotate',3,0)];target=[atoms[0],atoms[1]];train,held=self.examples(target)
  self.assertEqual(infer(train,held)['status'],'no-supported-rule')
  result=compose(train,held,atoms,budget_seconds=1)
  self.assertEqual(result['status'],'validated-candidate');self.assertEqual(result['depth'],2)
  self.assertTrue(all(apply_program(result['program'],x)==apply_program(target,x) for x in range(256)))
 def test_order_of_plan_steps_matters(self):
  first=[('xor',83,0),('affine',7,31)];second=list(reversed(first))
  self.assertTrue(any(apply_program(first,x)!=apply_program(second,x) for x in range(256)))
 def test_impossible_labels_are_not_invented_into_a_plan(self):
  train=[(x,(x*x+17)%256) for x in range(8)];held=[(x,(x*x+17)%256) for x in range(10,18)]
  self.assertEqual(compose(train,held,[('xor',1,0)],budget_seconds=1)['status'],'no-supported-composition')
 def test_search_respects_work_budget(self):
  train,held=self.examples([('xor',83,0),('affine',7,31)])
  result=compose(train,held,[('xor',83,0),('affine',7,31)],max_states=0,budget_seconds=1)
  self.assertEqual(result['status'],'search-budget-reached');self.assertEqual(result['tested_programs'],0)
 def test_validation_never_reuses_training_inputs(self):
  train,_=self.examples([('xor',1,0)])
  self.assertEqual(compose(train,train,[('xor',1,0)])['status'],'invalid-split')
 def test_composed_program_roundtrips_through_skill_memory(self):
  program=[['xor',83,0],['affine',7,31]];ident=hashlib.sha256(bytes(apply_program(program,x) for x in range(256))).hexdigest()
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'skills.json';lab=RuleLab(path);lab.skills[ident]={'program':program,'verified_domain':256,'uses':1};lab.flush()
   restored=RuleLab(path);self.assertIsNone(restored.storage_error)
   self.assertEqual(restored.skills[ident]['program'],program)
 def test_task_curriculum_produces_verified_composed_work(self):
  lab=RuleLab();reports=[lab.study('s'+str(i),bytes([i])*64) for i in range(24)]
  self.assertTrue(any(r['task_kind']=='composed' for r in reports))
  self.assertGreater(lab.compositions,0)
  self.assertTrue(all(r.get('full_domain_check',{}).get('passed')==256 for r in reports if r.get('status','').startswith('verified')))
 def test_plan_trace_contains_actual_intermediate_results(self):
  from neural_app.ambient_skill_composition import trace_program
  program=[('xor',83,0),('affine',7,31)];trace=trace_program(program,17)
  self.assertEqual(trace['output'],apply_program(program,17))
  self.assertEqual(trace['steps'][0]['output'],trace['steps'][1]['input'])
  self.assertEqual(len(trace['steps']),2)
