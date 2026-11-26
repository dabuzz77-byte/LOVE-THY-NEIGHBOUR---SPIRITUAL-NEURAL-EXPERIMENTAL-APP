import copy,json,unittest
from neural_app.conversational_requests import normalize,questions
from neural_app.native_work import NativeWork
from neural_app.native_dialogue import NativeDialogue
from neural_app.deliberation import Deliberation

class ConversationalRequests(unittest.TestCase):
    def test_nested_polite_prefixes(self):
        for prefix in ('Could you please ','I would like you to please ','Would you please ','I need you to '):
            w=NativeWork();self.assertEqual(w.handle(prefix+'sum: [3,5]')['value'],8)
    def test_multiple_questions_run_atomically_with_each_answer(self):
        w=NativeWork();result=w.handle('What is 7 times 8? Also, what is 9 times 4?')
        self.assertTrue(result['committed']);self.assertEqual(len(result['controller']['stages']),2)
        self.assertEqual(result['controller']['stages'][0]['outcome'],56)
        self.assertEqual(result['controller']['stages'][1]['outcome'],36)
    def test_unknown_second_request_does_not_commit_first(self):
        w=NativeWork();w.handle('sum: [2,3]');before=copy.deepcopy(w.state['last'])
        result=w.handle('What is 7 times 8? Also, predict every event tomorrow?')
        self.assertFalse(result['committed']);self.assertEqual(w.state['last'],before)
    def test_preserves_quoted_and_structured_data(self):
        for text in ['uppercase "why? Also, hello"','sum: ["why? Also, hello"]','summarise this: Why? Also, hello.','research brief: Why? Also, hello','write Python to print "why? Also, hi"']:
            self.assertIsNone(questions(text),text)
    def test_contractions_do_not_break_boundary_detection(self):
        self.assertEqual(len(questions("What is 2 times 3? Also, could you please sum: [1,2]")),2)
        self.assertEqual(normalize("I'd like you to sum: [1,2]"),'sum: [1,2]')
    def test_chat_capabilities_accept_polite_forms(self):
        chat=NativeDialogue(Deliberation());result=chat.send({'text':'Could you please tell me what you can do?'})
        self.assertIn('Native chat and work',json.dumps(result))
    def test_two_question_new_names_and_arithmetic(self):
        w=NativeWork();w.handle('conversation facts: Mira repairs radios')
        r=w.handle('What does Mira repair? Also, what is 4 times 5?')
        self.assertTrue(r['committed']);self.assertIn('radios',r['answer']);self.assertEqual(r['value'],20)
    def test_question_limit_and_unbalanced_input(self):
        self.assertIsNone(questions('What is [2? Also, 3?'))
        self.assertIsNone(questions('? Also, '.join(['What is 2']*10)))
