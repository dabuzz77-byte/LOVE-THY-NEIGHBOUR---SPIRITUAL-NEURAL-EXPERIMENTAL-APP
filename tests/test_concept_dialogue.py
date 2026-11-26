import copy,random,tempfile,unittest
from neural_app.concept_dialogue import respond
from neural_app.native_dialogue import NativeDialogue
from neural_app.deliberation import Deliberation
from neural_app.native_work import NativeWork

class Concepts(unittest.TestCase):
    def test_open_vocabulary_and_multi_hop_category_deduction(self):
        state={};respond('conversation facts: Mira is a technician. Every technician is a mechanic. Every mechanic repairs radios.',state)
        result=respond('What does Mira repair?',state)
        self.assertEqual(result['concept_reasoning']['answers'][0]['bindings']['?answer'],'radios')
        self.assertIn('F1',result['answer']);self.assertIn('R1',result['answer']);self.assertIn('R2',result['answer'])
        self.assertEqual(result['model_calls'],0)

    def test_regular_verb_inflections_and_quoted_subjects(self):
        for source,question,answer in [('Mira studies biology','What does Mira study?','biology'),('Mira teaches coding','Who teaches coding?','mira'),('"The red robot" carries parcels','What does the red robot carry?','parcels')]:
            with self.subTest(source=source):
                state={};respond('note that '+source,state);result=respond(question,state)
                self.assertEqual(result['concept_reasoning']['answers'][0]['bindings']['?answer'],answer)

    def test_explicit_conjunction_rule_and_query_join(self):
        state={};respond('conversation facts: Mira repairs radios; Mira teaches coding; Theo repairs radios; If someone repairs radios and teaches coding then they qualify certification',state)
        result=respond('Who both repairs radios and teaches coding?',state)
        self.assertEqual([a['bindings']['?answer'] for a in result['concept_reasoning']['answers']],['mira'])
        result=respond('Does Mira qualify certification?',state)
        self.assertEqual(result['status'],'answered')

    def test_contradiction_does_not_prove_unrelated_claim(self):
        state={};respond('conversation facts: Mira repairs radios; Mira does not repair radios; Mira builds robots',state)
        self.assertEqual(respond('Does Mira repair radios?',state)['status'],'conflicting-support')
        result=respond('Does Mira build rockets?',state)
        self.assertEqual(result['status'],'unknown')
        self.assertFalse(result['concept_reasoning']['answers'])

    def test_explicit_replacement_invalidates_derived_answer(self):
        state={};respond('conversation facts: Mira is a technician; Every technician repairs radios',state)
        self.assertEqual(respond('Does Mira repair radios?',state)['status'],'answered')
        respond('replace F1: Mira is an artist',state)
        self.assertEqual(respond('Does Mira repair radios?',state)['status'],'unknown')
        self.assertEqual(len(state['concept_conversation']['withdrawn']),1)

    def test_bad_clause_does_not_partially_commit(self):
        state={};respond('note that Mira repairs radios',state);before=copy.deepcopy(state)
        with self.assertRaises(ValueError):respond('conversation facts: Mira builds robots; an unclear fragment',state)
        self.assertEqual(state,before)

    def test_hypothetical_and_premise_sensitivity(self):
        state={};respond('conversation facts: Mira is a technician; Every technician repairs radios',state)
        respond('Does Mira repair radios?',state);before=copy.deepcopy(state['concept_conversation'])
        result=respond('What if F1 were: Mira is an artist?',state)
        self.assertTrue(result['hypothetical']);self.assertEqual(result['status'],'unknown')
        self.assertEqual(state['concept_conversation'],before)
        self.assertIn('F1',respond('which premises matter',state)['answer'])

    def test_pronoun_and_other_topic_not_guessed(self):
        state={};respond('note that Mira repairs radios',state)
        self.assertIsNone(respond('What is 12 times 5?',state))
        self.assertEqual(respond('Does she repair radios?',state)['status'],'needs-clarification')
        self.assertIn('Mira repairs radios',respond('Tell me about Mira',state)['answer'])

    def test_persistent_native_conversation_and_skill_switch(self):
        with tempfile.TemporaryDirectory() as path:
            engine=Deliberation();chat=NativeDialogue(engine,path)
            try:
                self.assertIn('Recorded',chat.send({'text':'Mira repairs radios.'})['answer'])
                self.assertIn('radios',chat.send({'text':'What does Mira repair?'})['answer'])
                self.assertIn('60',chat.send({'text':'calculate 12 * 5'})['answer'])
                chat=NativeDialogue(engine,path)
                chat.send({'text':'resume discussion'})
                result=chat.send({'text':'Does Mira repair radios?'})
                self.assertEqual(result['work']['status'],'answered')
                self.assertEqual(result['model_calls'],0)
            finally:engine.close()

    def test_generated_novel_vocabulary_and_chain_depth(self):
        rng=random.Random(22719)
        for i in range(100):
            n=rng.randrange(2,10);name='entity'+str(i);classes=['class'+str(i)+'_'+str(j) for j in range(n)]
            clauses=[name+' is a '+classes[0]]+['Every '+a+' is a '+b for a,b in zip(classes,classes[1:])]+['Every '+classes[-1]+' tunes instrument'+str(i)]
            state={};respond('conversation facts: '+'; '.join(clauses),state)
            result=respond('What does '+name+' tune?',state)
            self.assertEqual(result['concept_reasoning']['answers'][0]['bindings']['?answer'],'instrument'+str(i))

if __name__=='__main__':unittest.main()
