import copy,unittest
from neural_app.native_work import NativeWork
from neural_app.reasoning_engine import ReasoningEngine

class ComposedReasoning(unittest.TestCase):
    def test_fact_rule_answer_count_and_arithmetic_share_actual_output(self):
        work=NativeWork();result=work.handle('Work request:\n1. conversation facts: Mira is a technician; Every technician repairs radios\n2. What does Mira repair?\n3. count\n4. double\nExpect final: 2')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['value'],2)
        self.assertEqual(result['controller']['stages'][1]['outcome'],['radios'])
        self.assertEqual(work.state['last'],2)
        self.assertIn('Step 2',result['answer'])
        self.assertIn('radios',result['answer'])

    def test_document_summary_can_be_counted(self):
        work=NativeWork();result=work.handle('Answer these:\n- summarise this: Trees need water. Birds build nests.\n- count')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['value'],2)

    def test_decision_result_can_feed_next_stage(self):
        work=NativeWork();result=work.handle('Do the following:\n1) Atlas costs £40 and takes 3 days. Birch costs £30 and takes 5 days. Which is cheapest within 4 days?\n2) count')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['controller']['stages'][0]['outcome'],['atlas'])
        self.assertEqual(result['value'],1)

    def test_unknown_conclusion_blocks_without_partial_memory_commit(self):
        work=NativeWork();work.handle('sum: [4,5]');before=copy.deepcopy(work.state)
        result=work.handle('Work request:\n1. conversation facts: Mira repairs radios\n2. Does Mira build rockets?\n3. double')
        self.assertEqual(result['status'],'blocked')
        self.assertFalse(result['committed'])
        self.assertEqual(work.state['last'],before['last'])
        self.assertNotIn('concept_conversation',work.state)
        self.assertIn('unknown',result['answer'])

    def test_conflicted_conclusion_does_not_feed_later_work(self):
        result=NativeWork().handle('Work request:\n1. conversation facts: Mira repairs radios; Mira does not repair radios\n2. Does Mira repair radios?\n3. count')
        self.assertEqual(result['status'],'blocked')
        self.assertEqual(len(result['controller']['stages']),2)

    def test_explicit_sequence_and_revision_recovery(self):
        work=NativeWork();result=work.handle('First, calculate 12 + 8\nThen, double\nFinally, halve')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(str(result['value']),'20')
        result=work.handle('Work request:\n1. sum: [1,2]\n2. unsupported operation')
        self.assertEqual(result['status'],'blocked')
        work.handle('revise controller step 2: double')
        result=work.handle('retry controller')
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['value'],6)

    def test_final_acceptance_failure_keeps_original_value(self):
        work=NativeWork();work.handle('sum: [4,5]')
        result=work.handle('Work request:\n1. count: [1,2]\n2. double\nExpect final: 99')
        self.assertEqual(result['status'],'acceptance-failed')
        self.assertEqual(work.state['last'],9)

    def test_fact_recording_does_not_feed_a_stale_list_to_count(self):
        work=NativeWork({'last':['old','data'],'has_last':True})
        result=work.handle('Work request:\n1. conversation facts: Mira repairs radios\n2. count')
        self.assertEqual(result['status'],'blocked')
        self.assertEqual(work.state['last'],['old','data'])

    def test_fractional_calculation_survives_several_steps_exactly(self):
        result=NativeWork().handle('First, calculate 1 / 3\nThen, multiply by 3\nFinally, add 2')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['value'],'3')

    def test_main_engine_continues_context_created_in_composed_request(self):
        state={};engine=ReasoningEngine(state,lambda:None)
        result=engine.handle('Work request:\n1. conversation facts: Mira is a technician; Every technician repairs radios\n2. What does Mira repair?')
        self.assertEqual(result['status'],'complete',result)
        result=engine.handle('Does Mira repair radios?')
        self.assertEqual(result['status'],'answered',result)
        self.assertEqual(result['model_calls'],0)

if __name__=='__main__':unittest.main()
