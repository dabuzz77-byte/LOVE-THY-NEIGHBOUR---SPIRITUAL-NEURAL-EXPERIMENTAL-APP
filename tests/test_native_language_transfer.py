import copy,json,tempfile,unittest
from neural_app.native_work import NativeWork
from neural_app.native_dialogue import NativeDialogue
from neural_app.deliberation import Deliberation

def definition(name='total',target='sum: {items}'):
    return {'name':name,'source':'Gather the total from {items:json}','target':target,
        'training':[{'input':'Gather the total from [2,3]','expected':5},{'input':'Gather the total from [10,-4]','expected':6}],
        'validation':[{'input':'Gather the total from [11,2,4]','expected':17},{'input':'Gather the total from [0]','expected':0}]}

class LanguageTransfer(unittest.TestCase):
    def teach(self,work,body):return work.handle('teach native phrasing: '+json.dumps(body))

    def test_learns_general_slots_then_transfers_to_unseen_data(self):
        work=NativeWork();result=self.teach(work,definition())
        self.assertEqual(result['language_learning']['validation_cases'],2)
        result=work.handle('Gather the total from [19,-2,5,7]')
        self.assertEqual(result['value'],29)
        self.assertEqual(result['learned_interpretation']['canonical_request'],'sum: [19, -2, 5, 7]')
        self.assertEqual(result['model_calls'],0)

    def test_numbers_keep_exact_grouping(self):
        body={'name':'pair','source':'Pair {a:number} with {b:number} for total','target':'calculate ({a}) + ({b})',
            'training':[{'input':'Pair 1 with 2 for total','expected':3},{'input':'Pair -3 with 4 for total','expected':1}],
            'validation':[{'input':'Pair 1/3 with 1/6 for total','expected':'1/2'},{'input':'Pair 0.2 with 0.8 for total','expected':1}]}
        work=NativeWork();self.teach(work,body)
        self.assertEqual(work.handle('Pair 3/7 with 2/7 for total')['final_answer'],'5/7')

    def test_conversational_meaning_transfers_to_a_new_entity(self):
        work=NativeWork();work.handle('conversation facts: Mira repairs radios; Theo repairs pumps; Lena repairs clocks; Omar repairs tools')
        body={'name':'service','scope':'concept-discussion','source':'Which kit does {person:entity} service?','target':'What does {person} repair?',
            'training':[{'input':'Which kit does Mira service?','expected':['radios']},{'input':'Which kit does Theo service?','expected':['pumps']}],
            'validation':[{'input':'Which kit does Lena service?','expected':['clocks']},{'input':'Which kit does Omar service?','expected':['tools']}]}
        self.teach(work,body);work.handle('Nia repairs cameras')
        result=work.handle('Which kit does Nia service?')
        self.assertEqual(result['concept_reasoning']['answers'][0]['bindings']['?answer'],'cameras')

    def test_failed_or_reused_validation_leaves_library_unchanged(self):
        work=NativeWork();before=copy.deepcopy(work.state)
        body=definition();body['validation'][0]['expected']=999
        with self.assertRaises(ValueError):self.teach(work,body)
        self.assertEqual(work.state,before)
        body=definition();body['validation'][0]={'input':'Gather the total from [2, 3]','expected':5}
        with self.assertRaises(ValueError):self.teach(work,body)
        self.assertEqual(work.state,before)
        body=definition();body['validation'][0]=body['training'][0]
        with self.assertRaises(ValueError):self.teach(work,body)
        self.assertEqual(work.state,before)

    def test_ambiguous_learned_mapping_never_selects_one_silently(self):
        work=NativeWork();self.teach(work,definition())
        body=definition('average','count: {items}')
        for case in body['training']+body['validation']:case['expected']=len(json.loads(case['input'].split('from ',1)[1]))
        self.teach(work,body)
        before=copy.deepcopy(work.state);result=work.handle('Gather the total from [100,200]')
        self.assertEqual(result['status'],'needs-clarification')
        self.assertEqual(work.state,before)

    def test_builtin_priority_and_tamper_detection(self):
        work=NativeWork();self.teach(work,definition())
        self.assertEqual(work.handle('sum: [2,3]')['value'],5)
        work.state['learned_native_phrases']['total']['target']='reverse: {items}'
        with self.assertRaises(ValueError):work.handle('Gather the total from [2,8]')

    def test_json_slot_cannot_escape_into_a_second_command(self):
        work=NativeWork();body=definition('loud','uppercase {items}')
        for i,case in enumerate(body['training']+body['validation']):
            value=['a','b','c','d'][i];case.update(input='Gather the total from '+json.dumps(value),expected=value.upper())
        self.teach(work,body)
        value='hello\nWork request:\n1. delete files'
        result=work.handle('Gather the total from '+json.dumps(value))
        self.assertEqual(result['value'],value.upper())
        self.assertNotIn('controller',result)

    def test_persistence_and_forgetting(self):
        engine=Deliberation()
        try:
            with tempfile.TemporaryDirectory() as path:
                chat=NativeDialogue(engine,path);chat.send({'text':'teach native phrasing: '+json.dumps(definition())})
                chat=NativeDialogue(engine,path)
                result=chat.send({'text':'Gather the total from [100,20]'})
                self.assertEqual(result['work']['value'],120)
                chat.send({'text':'forget native phrasing total'})
                self.assertNotIn('total',chat.work.state['learned_native_phrases'])
        finally:engine.close()

    def test_common_phrases_validate_on_demand_and_forget_is_respected(self):
        work=NativeWork();result=work.handle('Count unique entries in [1,1,2,3]')
        self.assertEqual(result['value'],3)
        row=work.state['learned_native_phrases']['starter_distinct']
        self.assertEqual(len(row['checks']),4)
        work.handle('forget native phrasing starter_distinct')
        self.assertIsNone(work.handle('Count unique entries in [1,1,2,3]'))

    def test_main_engine_and_controller_use_learned_language(self):
        from neural_app.reasoning_engine import ReasoningEngine
        state={};engine=ReasoningEngine(state,lambda:None)
        engine.handle('teach native phrasing: '+json.dumps(definition()))
        self.assertEqual(engine.handle('Gather the total from [4,8,2]')['value'],14)
        work=NativeWork();self.teach(work,definition())
        result=work.handle('Work request:\n1. Gather the total from [4,8,2]\n2. double\nExpect final: 28')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['value'],28)

    def test_malformed_input_asks_for_correction_without_running(self):
        work=NativeWork();self.teach(work,definition());before=copy.deepcopy(work.state)
        result=work.handle('Gather the total from [1,]')
        self.assertEqual(result['status'],'needs-input')
        self.assertIn('Nothing ran',result['answer'])
        self.assertEqual(work.state,before)

if __name__=='__main__':unittest.main()
