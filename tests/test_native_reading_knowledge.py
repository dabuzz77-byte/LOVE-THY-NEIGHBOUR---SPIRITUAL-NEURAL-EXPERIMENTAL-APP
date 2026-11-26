import copy,hashlib,unittest
from neural_app.native_reading_knowledge import ReadingIndex,respond,installed_index
from neural_app.native_work import NativeWork
from neural_app.native_dialogue import NativeDialogue
from neural_app.deliberation import Deliberation
from neural_app.reasoning_engine import ReasoningEngine

class ReadingKnowledge(unittest.TestCase):
    def index(self):
        return ReadingIndex([
            {'id':'water','title':'Water cycles','text':'# Water cycles\n\n  Water evaporates from the lake during warmer conditions.\n\nWater vapour can condense and return as rain in this account.\n\nWater moves through soil and rivers before reaching the sea.','provenance':'Authored educational example'},
            {'id':'plants','title':'Plant growth','text':'# Plant growth\n\nPlant roots absorb water and obtain nutrients from the soil.\n\nPlants use sunlight as an energy source in this reading.','provenance':'Authored educational example'},
            {'id':'duplicate','title':'Water notes','text':'Water evaporates from the lake during warmer conditions.','provenance':'Duplicate educational example'}])

    def test_relevance_exact_spans_and_deduplication(self):
        index=self.index();rows=index.search('What does the text say about water?',5)
        self.assertTrue(rows)
        self.assertEqual(len({r['text'] for r in rows}),len(rows))
        for row in rows:
            original=index.documents[row['source_id']]['text']
            self.assertEqual(original[row['start']:row['end']],row['text'])
            self.assertEqual(row['text_sha256'],hashlib.sha256(original.encode()).hexdigest())

    def test_weak_keyword_match_does_not_answer_unrelated_question(self):
        self.assertEqual(self.index().search('What is the capital of Peru?',3),[])
        self.assertEqual(self.index().search('What is the water temperature on Jupiter?',3),[])

    def test_followup_more_sources_and_unknown_search(self):
        state={};index=self.index();first=respond('Explain water',state,index)
        self.assertEqual(first['status'],'source-answer')
        used={r['passage_sha256'] for r in first['source_knowledge']['passages']}
        second=respond('more',state,index)
        self.assertEqual(second['status'],'source-answer')
        self.assertTrue(used.isdisjoint(r['passage_sha256'] for r in second['source_knowledge']['passages']))
        self.assertIn('Authored',respond('show app sources',state,index)['answer'])
        self.assertEqual(respond('search app teachings: astrophotographic zebra',state,index)['status'],'needs-evidence')

    def test_inspect_specific_source_and_reject_arbitrary_paths(self):
        state={};index=self.index()
        self.assertEqual(respond('show app source water',state,index)['status'],'source-text')
        self.assertIsNone(respond('show app source ../../private',state,index))
        self.assertEqual(respond('show app source missing',state,index)['status'],'needs-input')

    def test_document_receipt_mismatch_is_not_silently_accepted(self):
        with self.assertRaises(ValueError):ReadingIndex([{'id':'bad','title':'Test','text':'Some source text that does not match its receipt.','text_sha256':'wrong'}])

    def test_public_readings_available_and_not_host_files(self):
        index=installed_index()
        self.assertGreaterEqual(len(index.documents),419)
        self.assertTrue(index.search('protective fear'))
        self.assertTrue(index.search('mustard seed'))

    def test_plain_native_questions_now_retrieve_source_answers(self):
        engine=Deliberation();chat=NativeDialogue(engine)
        try:
            for question in ('Explain protective fear','What does the app teach about the mustard seed?','How does the app relate the lion and lamb?'):
                with self.subTest(question=question):
                    result=chat.send({'text':question})
                    self.assertEqual(result['work']['status'],'source-answer',result)
                    self.assertTrue(result['work']['source_knowledge']['passages'])
                    self.assertIn('authored readings',result['answer'])
                    self.assertEqual(result['model_calls'],0)
            self.assertIn('20',chat.send({'text':'calculate 12 + 8'})['answer'])
        finally:engine.close()

    def test_main_reasoning_engine_uses_same_grounded_index(self):
        state={};engine=ReasoningEngine(state,lambda:None)
        result=engine.handle('Explain protective fear')
        self.assertEqual(result['status'],'source-answer')
        self.assertEqual(state['focus_kind'],'app-reading-answer')
        self.assertEqual(engine.handle('show app sources')['status'],'complete')

    def test_source_explanation_and_resumption_do_not_report_stale_math(self):
        work=NativeWork();work.handle('sum: [4,5]');work.handle('Explain protective fear')
        self.assertIn('retrieval evidence',work.handle('why is this verified')['answer'])
        work.handle('calculate 12 + 8')
        result=work.handle('resume app readings')
        self.assertEqual(result['status'],'source-answer')
        self.assertEqual(work.state['focus_kind'],'app-reading-answer')
        self.assertIn('protective fear',result['answer'].casefold())

if __name__=='__main__':unittest.main()
