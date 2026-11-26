import tempfile
import unittest
from neural_app.matter_spirit import catalogue, process
from neural_app.runtime import Runtime


class MatterSpiritTests(unittest.TestCase):
    def test_model_conserves_units_and_changes_with_intervention(self):
        idle = process({'care':0, 'restraint':0, 'repair':0})
        active = process({'care':1, 'restraint':1, 'repair':1})
        self.assertEqual(idle['unresolved'], .6)
        self.assertEqual(idle['restored'], 0)
        self.assertGreater(active['restored'], .5)
        self.assertLess(active['conservation_error'], 1e-12)
        self.assertTrue(all(0 <= t['unresolved'] <= .6 for t in active['trajectory']))

    def test_reject_invalid_inputs(self):
        for value in [float('nan'), float('inf'), -1, 2, True, '1']:
            with self.assertRaises(ValueError): process({'care':value})
        for value in [0, 61, 1.5, True]:
            with self.assertRaises(ValueError): process({'steps':value})
        with self.assertRaises(ValueError): process({'lesson':'not-listed'})

    def test_every_lesson_and_its_sources_resolve(self):
        data = catalogue()
        self.assertEqual(len(data['chapters']), 18)
        sources = {s['id'] for s in data['sources']}
        self.assertEqual(len({c['id'] for c in data['chapters']}),18)
        for chapter in data['chapters']:
            value = process({'lesson':chapter['id']})
            self.assertEqual(value['teaching'],chapter['paragraphs'])
            self.assertTrue(set(chapter['sources']) <= sources)

    def test_shared_pipeline_learns_and_transports_exactly(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = Runtime(folder, start=False)
            try:
                result = runtime.pipeline({'text':'Choose good in light and dark',
                    'sections':['matter_spirit','inference'],
                    'section_inputs':{'matter_spirit':{'lesson':'cross'}}})
                self.assertGreater(result['learning']['updates'],0)
                self.assertIn('inference',result['stages'])
                self.assertTrue(all(t['round_trip'] for t in result['transfers']))
                self.assertEqual(result['stages']['matter_spirit']['lesson'],'cross')
            finally: runtime.close()
