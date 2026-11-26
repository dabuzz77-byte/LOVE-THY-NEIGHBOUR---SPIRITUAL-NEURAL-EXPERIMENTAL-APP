import copy,json,unittest
from neural_app.native_work import NativeWork
from neural_app.native_requests import compile_request,execute_request

class RequestRepair(unittest.TestCase):
    def test_normal_entrypoint_requests_and_resumes_clarification(self):
        w=NativeWork();self.assertTrue(w.handle('sort: "z a"')['clarification'])
        w.handle('words');self.assertEqual(w.state['last'],['a','z'])
    def test_central_engine_preserves_clarification(self):
        from neural_app.reasoning_engine import ReasoningEngine
        engine=ReasoningEngine({},lambda:None)
        first=engine.handle('sort: "z a"')
        self.assertTrue(first.get('clarification'),first)
        self.assertEqual(engine.handle('words')['value'],['a','z'])
    def ask(self,w,text):
        compiled=compile_request(text,w.state)
        self.assertIsNotNone(compiled)
        return execute_request(compiled,w)
    def test_lines_answer_preserves_data_and_operations(self):
        w=NativeWork();r=self.ask(w,'sort: "z\\na\\nz"')
        self.assertTrue(r['clarification']);r=w.handle('lines')
        self.assertEqual(w.state['last'],['a','z','z']);self.assertEqual(r['clarification_resolved'],'lines')
    def test_words_and_multiple_operations(self):
        w=NativeWork();self.ask(w,'deduplicate then sort: "pear apple pear"');w.handle('words')
        self.assertEqual(w.state['last'],['apple','pear'])
    def test_unrelated_work_does_not_consume_pending_question(self):
        w=NativeWork();self.ask(w,'sort: "z a"');w.handle('sum: [2,3]')
        self.assertIn('request_clarification',w.state);w.handle('words');self.assertEqual(w.state['last'],['a','z'])
    def test_failed_resolution_is_transactional(self):
        w=NativeWork();w.handle('sum: [4,5]');self.ask(w,'sum: "a b"');before=copy.deepcopy(w.state)
        with self.assertRaises((ValueError,TypeError)):w.handle('words')
        self.assertEqual(w.state,before)
    def test_preview_remains_preview_after_answer(self):
        w=NativeWork();w.handle('sum: [4,5]');self.ask(w,'preview sort: "z a"');r=w.handle('words')
        self.assertEqual(r['status'],'planned');self.assertEqual(w.state['last'],9)
    def test_persistence_and_cancel(self):
        w=NativeWork();self.ask(w,'sort: "z a"');w=NativeWork(json.loads(json.dumps(w.state)))
        w.handle('cancel clarification');self.assertNotIn('request_clarification',w.state)
    def test_unknown_answer_does_not_guess(self):
        w=NativeWork();self.ask(w,'sort: "z a"');before=copy.deepcopy(w.state['request_clarification'])
        w.handle('letters');self.assertEqual(w.state['request_clarification'],before)
