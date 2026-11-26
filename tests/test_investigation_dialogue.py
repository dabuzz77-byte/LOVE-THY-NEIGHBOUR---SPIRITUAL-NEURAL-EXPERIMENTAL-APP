import copy,json,unittest
from neural_app.investigation_dialogue import respond,analyse
from neural_app.native_work import NativeWork

def model():return {'hypotheses':[{'name':'network','predictions':{'ping':False,'disk':True}},{'name':'storage','predictions':{'ping':True,'disk':False}},{'name':'application','predictions':{'ping':True,'disk':True}}],'observations':{},'probe_costs':{'ping':1,'disk':5}}

class Investigation(unittest.TestCase):
    def start(self,state,body=None):return respond('investigate: '+json.dumps(body or model()),state)
    def test_cost_breaks_equal_information_tie(self):self.assertEqual(analyse(model())['recommended_probe'],'ping')
    def test_observation_reduces_candidates_then_recommends_next_test(self):
        s={};self.start(s);r=respond('observation: ping = true',s)
        self.assertEqual(r['investigation']['remaining'],['storage','application']);self.assertEqual(r['investigation']['recommended_probe'],'disk')
        r=respond('observation: disk = false',s);self.assertEqual(r['investigation']['remaining'],['storage'])
        self.assertIn('do not treat a surviving explanation as a proven cause',r['answer'])
    def test_correction_restores_previously_eliminated_candidate(self):
        s={};self.start(s);respond('observation: ping = false',s)
        r=respond('correct observation: ping = true',s)
        self.assertEqual(r['investigation']['remaining'],['storage','application']);self.assertTrue(s['investigation']['history'][-1]['correction'])
    def test_conflicting_observation_requires_explicit_correction(self):
        s={};self.start(s);respond('observation: ping = false',s);before=copy.deepcopy(s)
        with self.assertRaises(ValueError):respond('observation: ping = true',s)
        self.assertEqual(s,before)
    def test_missing_predictions_are_not_eliminated(self):
        b=model();b['hypotheses'].append({'name':'unknown','predictions':{}});s={};self.start(s,b)
        r=respond('observation: ping = false',s);self.assertIn('unknown',r['investigation']['remaining'])
    def test_unknown_cost_under_budget_is_not_treated_as_free(self):
        b=model();b['max_probe_cost']=2;b['probe_costs']={}
        self.assertIsNone(analyse(b)['recommended_probe'])
    def test_blocked_tests_are_not_recommended(self):
        b=model();b['blocked_probes']=['ping'];self.assertEqual(analyse(b)['recommended_probe'],'disk')
    def test_unknown_probe_and_invalid_cost_leave_state_unchanged(self):
        s={};self.start(s);before=copy.deepcopy(s)
        with self.assertRaises(ValueError):respond('observation: imaginary = true',s)
        b=model();b['probe_costs']['ping']=-1
        with self.assertRaises(ValueError):self.start(s,b)
        self.assertEqual(s,before)
    def test_resume_after_unrelated_task_and_serialization(self):
        w=NativeWork();w.handle('investigate: '+json.dumps(model()));w.handle('sum: [2,3]')
        w=NativeWork(json.loads(json.dumps(w.state)));r=w.handle('resume investigation');self.assertEqual(r['investigation']['recommended_probe'],'ping')
    def test_no_command_execution_from_probe_names(self):
        b={'hypotheses':[{'name':'one','predictions':{'delete files':True}},{'name':'two','predictions':{'delete files':False}}]}
        r=analyse(b);self.assertEqual(r['recommended_probe'],'delete files');self.assertIn('No test, command',r['action_scope'])
