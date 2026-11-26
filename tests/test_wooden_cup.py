import tempfile
import unittest
from neural_app.wooden_cup import catalogue, process
from neural_app.runtime import Runtime

class WoodenCupTests(unittest.TestCase):
    def test_complete_prayer_and_all_lessons(self):
        data = catalogue()
        self.assertEqual(len(data['chapters']),15)
        prayer = next(c for c in data['chapters'] if c['id']=='prayer')['quote']
        self.assertIn('Give us this day our daily bread.',prayer)
        self.assertTrue(prayer.endswith('Amen.'))
        self.assertEqual(process({'lesson':'prayer'})['supplied_passage'],prayer)
        for chapter in data['chapters']:
            self.assertEqual(process({'lesson':chapter['id']})['teaching'],chapter['paragraphs'])

    def test_shared_learning_includes_prayer(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = Runtime(folder,start=False)
            try:
                value = runtime.pipeline({'text':'The humble cup: love made useful',
                    'sections':['wooden_cup','inference'],
                    'section_inputs':{'wooden_cup':{'lesson':'prayer'}}})
                self.assertEqual(value['stages']['wooden_cup']['lesson'],'prayer')
                self.assertGreater(value['learning']['updates'],0)
                self.assertTrue(all(t['round_trip'] for t in value['transfers']))
            finally:runtime.close()
