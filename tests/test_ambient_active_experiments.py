import unittest
from neural_app.ambient_active_experiments import identify
from neural_app.ambient_rule_lab import candidates

class ActiveExperiments(unittest.TestCase):
 def test_discriminating_question_eliminates_competing_rules(self):
  r=identify([[rule] for rule in candidates()],lambda x:x^83,[0],[200,201,202,203])
  self.assertEqual(r['status'],'validated-candidate');self.assertTrue(r['queries'])
  self.assertTrue(all(q['hypotheses_after']<q['hypotheses_before'] and q['expected_information_bits']>0 for q in r['queries']))
  self.assertFalse(r['validation_used_for_selection'])
 def test_holdout_inputs_are_never_used_as_active_queries(self):
  held=[200,201,202,203];calls=[]
  def oracle(x):calls.append(x);return x^83
  r=identify([[rule] for rule in candidates()],oracle,[0],held)
  self.assertFalse(set(q['input'] for q in r['queries'])&set(held))
  self.assertEqual(calls[-4:],held)
 def test_insufficient_query_budget_keeps_uncertainty(self):
  r=identify([[rule] for rule in candidates()],lambda x:x^83,[0],[200,201,202,203],max_queries=0)
  self.assertEqual(r['status'],'ambiguous-query-budget');self.assertGreater(r['remaining_behaviours'],1)
 def test_equivalent_rules_do_not_generate_wasteful_questions(self):
  r=identify([[('xor',128,0)],[('affine',1,128)]],lambda x:x^128,[0],[200,201,202,203])
  self.assertEqual(r['status'],'validated-candidate');self.assertEqual(r['queries'],[])
 def test_failed_unseen_cases_reject_the_candidate(self):
  def oracle(x):return 0 if x>=200 else x^83
  r=identify([[('xor',83,0)],[('affine',1,83)]],oracle,[0],[200,201,202,203])
  self.assertEqual(r['status'],'counterexample-found')
 def test_repeated_holdout_input_is_not_counted_as_four_examples(self):
  self.assertEqual(identify([],lambda x:x,[0],[1,1,1,1])['status'],'invalid-split')
