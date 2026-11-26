import tempfile
import unittest
from neural_app.theology import compare,THEMES
from neural_app.runtime import Runtime


class TheologyTests(unittest.TestCase):
    def test_all_themes_have_distinct_sources_and_steps(self):
        for topic in THEMES:
            r=compare({'topic':topic,'records':[]})
            self.assertEqual(len(r['transition_plan']),5)
            self.assertGreaterEqual(len(r['primary_sources']),2)
            self.assertIn('islam',r['comparison']);self.assertIn('christianity',r['comparison'])

    def test_research_titles_are_not_reported_as_read(self):
        r=compare({'topic':'light','records':[{'title':'Light and theology','url':'https://example.org/paper'}]})
        self.assertIn('not automatically reviewed',r['research_records'][0]['reading_status'])
        self.assertEqual(r['compact_public']['research_record_count'],1)

    def test_bad_sources_and_topics_rejected(self):
        with self.assertRaises(ValueError):compare({'topic':'unknown'})
        with self.assertRaises(ValueError):compare({'records':[{'title':'bad','url':'javascript:alert(1)'}]})

    def test_runtime_receipt_learning_and_compact_context(self):
        with tempfile.TemporaryDirectory() as d:
            r=Runtime(d,start=False)
            try:
                value=r.engine('theology',{'topic':'unity','records':[]})
                r.learn({'theology':value})
                receipt=r.record('theology',{'topic':'unity'},value,1.)
                self.assertEqual(r.theology_public['receipt'],receipt)
                self.assertNotIn('research_records',r.theology_public)
                self.assertGreater(r.learning_view()['updates'],0)
                self.assertTrue(r.feedback({'receipt':receipt,'target':1})['reviewed'])
                with self.assertRaises(ValueError):r.feedback({'receipt':receipt,'target':1})
            finally:r.close()
