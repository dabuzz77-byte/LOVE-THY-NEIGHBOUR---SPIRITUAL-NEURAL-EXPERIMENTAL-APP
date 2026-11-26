import copy,unittest
from neural_app.native_work import NativeWork

class WorkflowRevision(unittest.TestCase):
    def setup_work(self):
        w=NativeWork();w.handle('sort then deduplicate: [3,1,3]');return w
    def test_transfer_without_saving_a_named_workflow(self):
        w=self.setup_work();r=w.handle('same task with: [7,2,7,4]')
        self.assertTrue(r['committed']);self.assertEqual(r['value'],[2,4,7])
    def test_explanation_uses_verified_steps_and_retains_state(self):
        w=NativeWork();w.handle('keep rows where price is at most 20 then pick the price column then add up all values: [{"price":10},{"price":30},{"price":5}]')
        before=copy.deepcopy(w.state);r=w.handle('explain that')
        self.assertEqual(len(r['data_explanation']),3)
        self.assertEqual(r['data_explanation'][0]['input_count'],3)
        self.assertEqual(r['data_explanation'][0]['output_count'],2)
        self.assertEqual(w.state,before)
    def test_hypothesis_preserves_every_state_field(self):
        w=self.setup_work();before=copy.deepcopy(w.state)
        r=w.handle('what if the input were: [9,8,9]')
        self.assertEqual(r['workflow_comparison']['candidate_output'],[8,9]);self.assertEqual(w.state,before)
    def test_replace_one_step_reexecutes_entire_workflow(self):
        w=self.setup_work();r=w.handle('replace data step 1 with: sort descending')
        self.assertEqual(r['value'],[3,1]);self.assertEqual(w.state['workflow']['input'],[3,1,3])
    def test_bad_input_and_bad_edits_preserve_previous_results(self):
        for query in ('same task with: {}','replace data step 99 with: sort','replace data step 1 with: sort then sum'):
            w=self.setup_work();before=copy.deepcopy(w.state)
            with self.assertRaises((ValueError,TypeError)):w.handle(query)
            self.assertEqual(w.state,before)
    def test_tampered_baseline_is_not_reused(self):
        w=self.setup_work();w.state['workflow']['input']=[99]
        with self.assertRaises(ValueError):w.handle('same task with: [1,2]')
    def test_absent_workflow_requests_input(self):self.assertEqual(NativeWork().handle('same task with: [1,2]')['status'],'needs-input')
    def test_composed_work_can_transfer_and_then_calculate(self):
        w=self.setup_work();r=w.handle('Work request:\n1. same task with: [9,2,9]\n2. sum')
        self.assertTrue(r['committed']);self.assertEqual(r['value'],11)
