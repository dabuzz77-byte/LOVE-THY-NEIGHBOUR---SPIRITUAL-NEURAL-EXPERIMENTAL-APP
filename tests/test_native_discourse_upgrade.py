import copy,itertools,random,unittest
from fractions import Fraction
from neural_app.practical_decisions import respond
from neural_app.grounded_reading_dialogue import respond as read
from neural_app.native_work import NativeWork
from neural_app.native_dialogue import NativeDialogue
from neural_app.deliberation import Deliberation

class Decisions(unittest.TestCase):
    def ask(self,text):
        state={};report=respond(text,state)
        self.assertIsNotNone(report,text)
        return state,report

    def test_cheapest_with_deadline_filters_cheaper_late_option(self):
        state,result=self.ask('Atlas costs £40 and takes 3 days. Birch costs £30 and takes 5 days. Which is cheapest if I need it within 4 days?')
        self.assertEqual(result['decision']['selected'],['atlas'])
        self.assertIn('exceeds',result['answer'])
        self.assertIn('above',respond('why not Birch?',state)['answer'])
        self.assertIn('24 hours',respond('what could change that conclusion?',state)['answer'])

    def test_different_units_are_exactly_converted(self):
        _,result=self.ask('Atlas costs £10 and takes 120 minutes. Birch costs £11 and takes 1 hour. Which is fastest?')
        self.assertEqual(result['decision']['selected'],['birch'])

    def test_tradeoff_without_priority_and_followup_selection(self):
        state,result=self.ask('Atlas costs £40 and takes 3 days. Birch costs £30 and takes 5 days. Which is better?')
        self.assertEqual(result['status'],'trade-off')
        self.assertCountEqual(result['decision']['frontier'],['atlas','birch'])
        self.assertEqual(respond('Which is cheapest?',state)['decision']['selected'],['birch'])

    def test_followup_budget_and_correction(self):
        state,_=self.ask('Atlas costs £40. Birch costs £30. Which is cheapest?')
        before=copy.deepcopy(state['practical_decision'])
        result=respond('Atlas costs £20',state)
        self.assertEqual(result['status'],'needs-clarification')
        self.assertEqual(state['practical_decision'],before)
        self.assertEqual(respond('actually, Atlas costs £20',state)['decision']['selected'],['atlas'])
        self.assertEqual(respond('my budget is £15',state)['status'],'no-feasible-option')

    def test_hypothesis_is_not_committed_as_a_fact(self):
        state,_=self.ask('Atlas costs £40. Birch costs £30. Which is cheapest?')
        before=copy.deepcopy(state['practical_decision'])
        result=respond('What if Atlas costs £20?',state)
        self.assertTrue(result['hypothetical'])
        self.assertEqual(result['decision']['selected'],['atlas'])
        self.assertEqual(state['practical_decision'],before)

    def test_ties_missing_data_currency_and_unknown_constraints(self):
        cases=[('Atlas costs £30. Birch costs £30. Which is cheapest?','selected'),
            ('Atlas costs £30. Birch costs $20. Which is cheapest?','needs-clarification'),
            ('Atlas costs £30. Birch costs £20. Which is fastest?','needs-evidence'),
            ('Atlas costs £30. Birch costs £20. Which is cheapest within four business days?','needs-clarification'),
            ('Atlas costs £30. Birch costs £20. Which is cheapest and safe?','needs-clarification')]
        for text,status in cases:
            with self.subTest(text=text):self.assertEqual(self.ask(text)[1]['status'],status)

    def test_priority_does_not_require_unasked_missing_metrics(self):
        _,result=self.ask('Atlas costs £30 and takes 5 days. Birch costs £20. Which is cheapest?')
        self.assertEqual(result['decision']['selected'],['birch'])

    def test_strict_budget_and_unparsed_qualifications(self):
        _,result=self.ask('Atlas costs £30. Birch costs £20. Which is cheapest under £20?')
        self.assertEqual(result['status'],'no-feasible-option')
        _,result=self.ask('Atlas costs £30 and takes 2 days. Birch costs £20 and takes 3 days. Which is cheapest within 3 working days?')
        self.assertEqual(result['status'],'needs-clarification')

    def test_name_order_and_price_transfers(self):
        rng=random.Random(91873)
        for index in range(120):
            names=rng.sample(['Cedar','Delta','Orion','Linden','Nova','Falcon'],3)
            prices=rng.sample(range(10,150),3);times=[rng.randrange(1,8) for _ in names];maximum=rng.randrange(1,8)
            text=' '.join(f'{name} costs £{price} and takes {days} days.' for name,price,days in zip(names,prices,times))+' Which is cheapest within '+str(maximum)+' days?'
            result=self.ask(text)[1]['decision']
            feasible=[i for i,t in enumerate(times) if t<=maximum]
            expected=[names[min(feasible,key=lambda i:prices[i])].casefold()] if feasible else []
            self.assertEqual(result['selected'],expected,text)

class Reading(unittest.TestCase):
    SOURCE='The clinic opens at nine. The library closes at five. The clinic has two entrances. The museum is closed.'
    def test_summary_focus_and_attribution(self):
        state={};reply=read('summarise this: '+self.SOURCE,state)
        self.assertEqual(len(reply['reading']['extracts']),3)
        result=read('focus on clinic',state)
        self.assertEqual(len(result['reading']['extracts']),2)
        self.assertTrue(all('clinic' in row['text'] for row in result['reading']['extracts']))
        self.assertIn('verbatim',read('why',state)['answer'])
        self.assertEqual(read('show original text',state)['answer'],self.SOURCE)

    def test_length_and_unknown_topic(self):
        state={};read('summarize: '+self.SOURCE,state)
        self.assertEqual(len(read('make that shorter',state)['reading']['extracts']),2)
        self.assertEqual(len(read('give me 1 sentence',state)['reading']['extracts']),1)
        self.assertEqual(read('focus on dolphins',state)['status'],'needs-evidence')

    def test_read_question_compiles_sources_and_preserves_proof(self):
        state={};result=read('Read this: Nova is a generator. Every generator produces electricity.\nQuestion: What does Nova produce?',state)
        self.assertIn('electricity',result['answer'])
        self.assertTrue(result['research']['deduction']['proof_graph'])

class Integrated(unittest.TestCase):
    def test_multiple_topic_types_do_not_repeat_old_answer(self):
        engine=Deliberation();chat=NativeDialogue(engine)
        try:
            reply=chat.send({'text':'Atlas costs £40. Birch costs £30. Which is cheapest?'})
            self.assertEqual(reply['work']['decision']['selected'],['birch'])
            reply=chat.send({'text':'summarise this: Trees need water. Plants use light.'})
            self.assertIn('Trees',reply['answer'])
            reply=chat.send({'text':'calculate 12 + 8'})
            self.assertIn('20',reply['answer'])
            self.assertNotIn('Trees',reply['answer'])
        finally:engine.close()

if __name__=='__main__':unittest.main()
