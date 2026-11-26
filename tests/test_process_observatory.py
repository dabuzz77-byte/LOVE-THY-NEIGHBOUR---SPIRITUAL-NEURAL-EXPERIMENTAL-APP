import unittest
from neural_app.process_observatory import ProcessObservatory


class ObservatoryTests(unittest.TestCase):
    def test_actual_results_reviews_and_errors_are_separate(self):
        o=ProcessObservatory();o.observe('inference','abc',10.,1);o.observe('care','abc',20.,2);o.fail('inference');o.review(1.)
        v=o.view();self.assertEqual(v['completed'],2);self.assertEqual(v['failed'],1);self.assertEqual(v['reviews'],1)
        self.assertAlmostEqual(v['result_diversity'],.5);self.assertAlmostEqual(v['success_fraction'],2/3)
        self.assertAlmostEqual(v['latency_ewma_ms'],12.)
        self.assertEqual(v['sections']['care']['last_receipt'],2)

    def test_bounded_history_and_snapshot_copy(self):
        o=ProcessObservatory()
        for n in range(200):o.observe('inference',str(n),1.,n)
        v=o.view();self.assertEqual(v['diversity_window'],128);self.assertEqual(len(v['events']),32)
        v['sections']['inference']['completed']=0
        self.assertEqual(o.view()['sections']['inference']['completed'],200)

    def test_nonfinite_latency_rejected(self):
        with self.assertRaises(ValueError):ProcessObservatory().observe('x','d',float('nan'),1)
