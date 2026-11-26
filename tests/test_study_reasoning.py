import copy,json,random,unittest
from fractions import Fraction
from neural_app import study_reasoning as sr
from neural_app.native_work import NativeWork
from neural_app.native_dialogue import NativeDialogue
from neural_app.deliberation import Deliberation

def body(a=30,n=100,b=20,m=100):return {'groups':[{'name':'A','events':a,'total':n},{'name':'B','events':b,'total':m}]}

class StudyReasoning(unittest.TestCase):
    def test_denominators_reverse_raw_counts(self):
        r=sr.analyse(body(30,100,20,40));self.assertEqual(r['comparison']['exact_difference'],'-1/5')
    def test_wilson_known_reference_and_boundaries(self):
        r=sr.group({'name':'x','events':5,'total':10})
        self.assertAlmostEqual(r['wilson_95'][0],.23659309,places=7)
        for events in (0,10):
            interval=sr.group({'name':'x','events':events,'total':10})['wilson_95']
            self.assertTrue(0<=interval[0]<=interval[1]<=1)
    def test_zero_reference_rate_does_not_invent_ratio(self):self.assertIsNone(sr.analyse(body(4,10,0,10))['comparison']['rate_ratio'])
    def test_missing_outcomes_can_reverse_direction(self):
        b=body(6,10,4,10);b['groups'][1]['missing']=20
        lo,hi=sr.analyse(b)['comparison']['missing_difference_bounds'];self.assertLess(lo,0);self.assertGreater(hi,0)
    def test_simpson_reversal_detected(self):
        b=body(81+234,87+270,234+55,270+80)
        b['strata']=[{'name':'one','groups':body(81,87,234,270)['groups']},{'name':'two','groups':body(234,270,55,80)['groups']}]
        # A wins in stratum one, loses in two: not Simpson.
        self.assertFalse(sr.analyse(b)['aggregation_reversal'])
        b=body(9+1,10+10,80+9,100+10)
        b['strata']=[{'groups':body(9,10,80,100)['groups']},{'groups':body(1,10,9,10)['groups']}]
        self.assertFalse(sr.analyse(b)['aggregation_reversal'])
        b=body(81+234,87+270,234+55,270+80)
        b['strata']=[{'groups':body(81,87,234,270)['groups']},{'groups':body(234,270,55,80)['groups']}]
        # Construct classic treatment example: 81/87 > 234/270; 192/263 > 55/80.
        b=body(81+192,87+263,234+55,270+80)
        b['strata']=[{'groups':body(81,87,234,270)['groups']},{'groups':body(192,263,55,80)['groups']}]
        self.assertTrue(sr.analyse(b)['aggregation_reversal'])
    def test_malformed_updates_are_transactional(self):
        state={};sr.respond('study: A: 3 of 10 events. B: 4 of 10 events.',state);before=copy.deepcopy(state)
        for b in [body(11,10),body(True,10),{'groups':[]}]:
            with self.assertRaises(ValueError):sr.respond('analyse study: '+json.dumps(b),state)
            self.assertEqual(state,before)
    def test_strata_must_reconcile(self):
        b=body();b['strata']=[{'groups':body()['groups']},{'groups':body()['groups']}]
        with self.assertRaises(ValueError):sr.analyse(b)
    def test_causal_and_uncertainty_followups(self):
        state={};sr.respond('analyse study: '+json.dumps(body()),state)
        self.assertIn('does not establish causation',sr.respond('does that prove causation?',state)['answer'])
        self.assertIn('selection effects',sr.respond('how certain is that?',state)['answer'])
        self.assertIn('own denominator',sr.respond('why?',state)['answer'])
    def test_randomized_label_does_not_certify_causality(self):
        b=body();b['design']='randomized';state={};sr.respond('analyse study: '+json.dumps(b),state)
        self.assertIn('allocation integrity',sr.respond('is that causal?',state)['answer'])
    def test_clusters_withhold_binomial_intervals(self):
        b=body();b['independent']=False;r=sr.respond('analyse study: '+json.dumps(b),{})
        self.assertIsNone(r['study_analysis']['groups'][0]['wilson_95']);self.assertIn('withheld',r['answer'])
    def test_unparsed_qualifications_are_not_discarded(self):
        with self.assertRaises(ValueError):sr.respond('study: A: 4 of 10 events. B: 3 of 10 events. But 20 are missing.',{})
    def test_unrelated_question_not_hijacked_and_topic_resumes(self):
        w=NativeWork();w.handle('study: A: 4 of 10 events. B: 3 of 10 events.')
        self.assertEqual(w.handle('sum: [2,3]')['value'],5)
        self.assertIn('study_analysis',w.handle('resume study analysis'))
    def test_generated_exact_fraction_transfers(self):
        rng=random.Random(2893)
        for _ in range(150):
            n,m=rng.randint(1,10000),rng.randint(1,10000);a,b=rng.randint(0,n),rng.randint(0,m)
            r=sr.analyse(body(a,n,b,m));self.assertEqual(Fraction(r['comparison']['exact_difference']),Fraction(a,n)-Fraction(b,m))
    def test_chat_followups_stay_on_current_evidence(self):
        chat=NativeDialogue(Deliberation());chat.send({'text':'study: A: 30 of 100 events. B: 20 of 40 events.'})
        r=chat.send({'text':'does that prove causation?'})
        self.assertIn('does not establish causation',json.dumps(r))
    def test_central_engine_and_composed_followup_share_evidence(self):
        from neural_app.reasoning_engine import ReasoningEngine
        engine=ReasoningEngine({},lambda:None)
        engine.handle('study: A: 30 of 100 events. B: 20 of 40 events.')
        result=engine.handle('How certain is that? Also, what is 3 times 4?')
        self.assertTrue(result['committed']);self.assertIn('selection effects',result['answer']);self.assertEqual(result['value'],12)
    def test_exported_python_executes_and_reproduces_exact_report(self):
        import subprocess,sys,tempfile
        from pathlib import Path
        state={};b=body(3,7,2,11);sr.respond('analyse study: '+json.dumps(b),state)
        result=sr.respond('write Python for this study',state)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'study.py';path.write_text(result['code'],encoding='utf-8')
            run=subprocess.run([sys.executable,'-I',str(path)],capture_output=True,text=True,timeout=5,check=True)
        self.assertEqual(json.loads(run.stdout),sr.analyse(b))
    def test_code_like_group_name_remains_data(self):
        import ast
        b=body();b['groups'][0]['name']='A\"; __import__(\"os\").system(\"oops\")'
        state={};sr.respond('analyse study: '+json.dumps(b),state)
        code=sr.respond('export study as Python',state)['code'];tree=ast.parse(code)
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertFalse(any(n.func.id in ('exec','eval','__import__') for n in calls))
