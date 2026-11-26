import copy,json,unittest
from neural_app import relational_induction as ri
from neural_app.native_work import NativeWork

def lesson():
    return {'name':'service','target':'services','facts':[[n,'type',t] for n,t in [('ada','tech'),('bo','tech'),('cy','visitor'),('dee','tech'),('eve','visitor'),('fox','tech')]],'positive':[['ada','radios'],['bo','radios']],'negative':[['cy','radios']],'validation':[{'subject':'dee','object':'radios','expected':True},{'subject':'eve','object':'radios','expected':False}]}

class RelationalInduction(unittest.TestCase):
    def teach(self,state,body=None):return ri.respond('learn relation model: '+json.dumps(body or lesson()),state)
    def test_discovers_rule_and_predicts_unseen_case(self):
        state={};self.teach(state)
        result=ri.respond('predict relation service: fox | radios',state)
        self.assertTrue(result['prediction']);self.assertEqual(result['model_calls'],0)
        self.assertEqual(result['votes'][0]['support_fact_ids'],[6])
    def test_discovers_variable_two_hop_relation(self):
        body=lesson();body['facts']=[]
        for n,obj in [('ada','radio'),('bo','pump'),('dee','clock'),('fox','camera')]:body['facts'] += [[n,'assigned',n+'team'],[n+'team','maintains',obj]]
        body['facts'] += [['cy','type','visitor'],['eve','type','visitor']]
        body['positive']=[['ada','radio'],['bo','pump']];body['negative']=[['cy','radio']]
        body['validation']=[{'subject':'dee','object':'clock','expected':True},{'subject':'eve','object':'pump','expected':False}]
        state={};self.teach(state,body)
        self.assertTrue(ri.respond('predict relation service: fox | camera',state)['prediction'])
    def test_validation_is_not_used_to_select_a_winner(self):
        body=lesson();body['facts'] += [[n,'badge','blue'] for n in ('ada','bo','eve')]
        state={};before=copy.deepcopy(state)
        with self.assertRaises(ValueError):self.teach(state,body)
        self.assertEqual(state,before)
    def test_ambiguous_new_case_abstains(self):
        body=lesson();body['facts'] += [[n,'badge','blue'] for n in ('ada','bo','dee')]
        state={};self.teach(state,body)
        self.assertIsNone(ri.respond('predict relation service: fox | radios',state)['prediction'])
    def test_counterexample_revokes_model(self):
        state={};self.teach(state)
        result=ri.respond('check relation service: '+json.dumps({'subject':'fox','object':'radios','expected':False}),state)
        self.assertFalse(result['model_active'])
        with self.assertRaises(ValueError):ri.respond('predict relation service: fox | radios',state)
    def test_unknown_subject_does_not_revoke_model(self):
        state={};self.teach(state)
        result=ri.respond('check relation service: '+json.dumps({'subject':'unknown','object':'radios','expected':True}),state)
        self.assertEqual(result['status'],'needs-observations');self.assertTrue(result['model_active'])
    def test_background_update_rechecks_old_labels(self):
        state={};self.teach(state)
        result=ri.respond('add relation facts service: [["cy","type","tech"]]',state)
        self.assertFalse(result['model_active'])
    def test_leakage_and_reused_validation_rejected(self):
        for variant in ('leak','reuse'):
            body=lesson()
            if variant=='leak':body['facts'].append(['ada','services','radios'])
            else:body['validation'][0]['subject']='ada'
            with self.assertRaises(ValueError):self.teach({},body)
    def test_receipt_tampering_detected(self):
        state={};self.teach(state);state['learned_relation_models']['service']['facts'][0][2]='visitor'
        with self.assertRaises(ValueError):ri.respond('predict relation service: ada | radios',state)
    def test_native_work_and_serialized_state(self):
        work=NativeWork();work.handle('learn relation model: '+json.dumps(lesson()))
        restored=NativeWork(json.loads(json.dumps(work.state)))
        self.assertTrue(restored.handle('predict relation service: fox | radios')['prediction'])
    def test_arbitrary_vocabulary_transfer(self):
        body=lesson();body['facts']=[[a,'r77',{'tech':'v11','visitor':'v22'}[c]] for a,b,c in body['facts']]
        state={};self.teach(state,body)
        self.assertTrue(ri.respond('predict relation service: fox | radios',state)['prediction'])
    def test_controller_routes_model_predictions(self):
        from neural_app.shared_controller import route,outcome,succeeded
        work=NativeWork();route('learn relation model: '+json.dumps(lesson()),work)
        result=route('predict relation service: fox | radios',work)
        self.assertTrue(outcome(result));self.assertTrue(succeeded(result))
