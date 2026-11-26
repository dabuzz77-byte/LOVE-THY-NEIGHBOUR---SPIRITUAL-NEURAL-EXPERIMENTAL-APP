from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from neural_app.research_intake import ResearchIntake,parse_news,research_input,TOPICS


class FakeRuntime:
    def __init__(self,path):self.data=Path(path);self.sent=[]
    def submit(self,section,body):self.sent.append((section,body));return {'id':str(len(self.sent))}
    def result(self,ident):return {'status':'complete','receipt':int(ident)}


class IntakeTests(unittest.TestCase):
    def test_plight_feed_preserves_attribution_and_routes_through_shared_engines(self):
        rows=parse_news(b'<rss><channel><item><title>Human rights reporting</title><link>https://news.google.com/rss/articles/test</link><source>Test publisher</source><pubDate>Mon, 09 Nov 2026 12:00:00 GMT</pubDate></item></channel></rss>')
        self.assertEqual(rows[0]['publisher'],'Test publisher')
        self.assertIn('not automatically read',rows[0]['reading_status'])
        body=research_input('falun_plight',rows)
        self.assertIn('inference',body['sections'])
        self.assertEqual(body['research']['records'],rows)
        with self.assertRaises(ValueError):parse_news(b'<!DOCTYPE rss><rss/>')
        with tempfile.TemporaryDirectory() as d:
            runtime=FakeRuntime(d);intake=ResearchIntake(runtime);intake.configure(True)
            intake.index=next(i for i,t in enumerate(TOPICS) if t[0]=='falun_plight')
            with patch('neural_app.research_intake.fetch_plight',return_value=rows):intake.cycle()
            self.assertEqual(runtime.sent[0][1]['research']['topic'],'falun_plight')

    def test_new_metadata_processed_once_and_repeat_deduplicated(self):
        with tempfile.TemporaryDirectory() as d:
            runtime=FakeRuntime(d);intake=ResearchIntake(runtime);intake.configure(True)
            metadata_index=next(i for i,t in enumerate(TOPICS) if t[0]=='inference');intake.index=metadata_index
            with patch('neural_app.research_intake.fetch_metadata',return_value=[{'title':'Measured research','doi':'test','url':'https://example.org'}]):
                intake.cycle();self.assertEqual(len(runtime.sent),1);intake.cycle()
                self.assertEqual(intake.view()['completed_topics'],1)
                intake.index=metadata_index;intake.cycle();self.assertEqual(len(runtime.sent),1)
            self.assertEqual(runtime.sent[0][1]['sections'],[])

    def test_pause_and_failure_do_not_invent_results(self):
        with tempfile.TemporaryDirectory() as d:
            runtime=FakeRuntime(d);intake=ResearchIntake(runtime)
            intake.index=next(i for i,t in enumerate(TOPICS) if t[0]=='inference')
            with patch('neural_app.research_intake.fetch_metadata',side_effect=ValueError('test unavailable')) as fetch:
                intake.cycle();fetch.assert_not_called();intake.configure(True);intake.cycle()
            self.assertEqual(runtime.sent,[]);self.assertEqual(intake.view()['topics']['inference']['processing'],'error')
