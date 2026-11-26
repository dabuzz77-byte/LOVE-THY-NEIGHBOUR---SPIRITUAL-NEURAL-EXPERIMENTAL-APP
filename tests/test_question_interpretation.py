import copy,unittest
from neural_app.concept_dialogue import respond
from neural_app.native_work import NativeWork

class QuestionInterpretation(unittest.TestCase):
    def state(self):
        state={};respond('conversation facts: Mira is a technician; Theo is a technician; Every technician repairs radios; Mira builds robots; "The red robot" carries parcels',state)
        return state
    def answer(self,text,expected):
        result=respond(text,self.state())
        self.assertIsNotNone(result,text)
        self.assertEqual(result['status'],'answered',result)
        self.assertEqual([a['bindings'].get('?answer') for a in result['concept_reasoning']['answers']],expected)

    def test_paraphrased_object_question(self):
        for q in ('Tell me what Mira repairs','Which things does Mira repair?','I would like to know what Mira repairs','Could you tell me what Mira repairs?'):
            with self.subTest(q=q):self.answer(q,['radios'])

    def test_paraphrased_subject_question(self):
        for q in ('Name everyone who repairs radios','Who is it that repairs radios?','Tell me who repairs radios','Which entities repair radios?'):
            with self.subTest(q=q):self.answer(q,['mira','theo'])

    def test_truth_question_and_own_source_recall(self):
        state=self.state()
        for q in ('Is it true that Mira repairs radios?','Tell me whether Mira repairs radios','Do we know whether Mira repairs radios?'):
            with self.subTest(q=q):
                result=respond(q,state);self.assertIsNotNone(result,q);self.assertEqual(result['status'],'answered',result)
        self.assertIn('Mira builds robots',respond('What did I say about Mira?',state)['answer'])

    def test_elliptical_followup_copies_question_not_facts(self):
        state=self.state();respond('What does Mira repair?',state);before=copy.deepcopy(state['concept_conversation']['facts'])
        for q in ('What about Theo?','And Theo?','Actually, I meant Theo'):
            with self.subTest(q=q):
                result=respond(q,state);self.assertIsNotNone(result,q);self.assertEqual(result['concept_reasoning']['answers'][0]['bindings']['?answer'],'radios')
        self.assertEqual(state['concept_conversation']['facts'],before)

    def test_missing_reference_is_not_invented(self):
        state=self.state();respond('Who repairs radios?',state)
        result=respond('What about Theo?',state)
        self.assertIsNotNone(result)
        self.assertEqual(result['status'],'needs-clarification')

    def test_category_query_and_counts(self):
        state=self.state();result=respond('Which technicians repair radios?',state)
        self.assertIsNotNone(result);self.assertEqual(len(result['concept_reasoning']['answers']),2)
        result=respond('How many technicians repair radios?',state)
        self.assertIsNotNone(result);self.assertEqual(result['count'],2)
        result=respond('How many things does Mira build?',state)
        self.assertEqual(result['count'],1)

    def test_modality_and_unstated_synonyms_are_not_silently_rewritten(self):
        state=self.state()
        result=respond('Is it true that Mira might repair radios?',state)
        self.assertTrue(result is None or result['status']!='answered')
        result=respond('Does Mira mend radios?',state)
        self.assertEqual(result['status'],'unknown')

    def test_known_multiword_subject_in_unquoted_statement(self):
        state=self.state();result=respond('The red robot carries tools',state)
        self.assertIsNotNone(result)
        result=respond('What does the red robot carry?',state)
        self.assertEqual([a['bindings']['?answer'] for a in result['concept_reasoning']['answers']],['parcels','tools'])

    def test_count_can_feed_composed_work(self):
        result=NativeWork().handle('Work request:\n1. conversation facts: Mira is a technician; Theo is a technician; Every technician repairs radios\n2. How many technicians repair radios?\n3. double\nExpect final: 4')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['value'],4)

    def test_count_conflicts_are_not_hidden_or_used_as_certain_input(self):
        state=self.state();respond('Mira does not repair radios',state)
        result=respond('How many technicians repair radios?',state)
        self.assertEqual(result['status'],'conflicting-support')
        self.assertIn('Resolve',result['answer'])
        result=NativeWork().handle('Work request:\n1. conversation facts: Mira is a technician; Mira repairs radios; Mira does not repair radios\n2. How many technicians repair radios?\n3. double')
        self.assertEqual(result['status'],'blocked')

    def test_ambiguous_followup_and_unknown_count_are_explicit(self):
        state=self.state();respond('What does Mira repair?',state)
        self.assertEqual(respond('And she?',state)['status'],'needs-clarification')
        result=respond('How many artists repair radios?',state)
        self.assertEqual(result['count'],0)
        self.assertIn('retained premises',result['answer'])

if __name__=='__main__':unittest.main()
