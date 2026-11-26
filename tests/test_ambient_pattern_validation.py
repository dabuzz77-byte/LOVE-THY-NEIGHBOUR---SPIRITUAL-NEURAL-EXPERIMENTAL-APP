import random,unittest
from neural_app.ambient_pattern_validation import validate
from neural_app.emergence_learning import EmergenceLearning

class PatternChecks(unittest.TestCase):
    def test_learns_alternation_on_untouched_later_bytes(self):
        r=validate(b'AB'*512);self.assertEqual(r['status'],'candidate-structure');self.assertGreater(r['gain_above_best_control'],0)
    def test_constant_source_is_not_claimed_as_transition_intelligence(self):
        self.assertEqual(validate(b'A'*1024)['status'],'no-validated-gain')
    def test_random_source_has_no_guaranteed_gain(self):
        rng=random.Random(173);r=validate(bytes(rng.randrange(256) for _ in range(1024)))
        self.assertLess(r['gain_bits_per_byte'],.2);self.assertEqual(len(r['shuffled_control_gains']),4)
    def test_short_capture_requests_more_observations(self):self.assertEqual(validate(b'AB')['status'],'insufficient-sample')
    def test_checks_are_reproducible_and_wired_to_source_learning(self):
        self.assertEqual(validate(b'ABC'*200),validate(b'ABC'*200))
        learner=EmergenceLearning();r=learner.observe('generated-fixture',b'AB'*512)
        self.assertIn('generated-fixture',r['heldout_pattern_checks']);self.assertFalse(learner.observe('generated-fixture',b'AB'*512)['fresh'])
    def test_recurring_candidate_requires_distinct_captures(self):
        learner=EmergenceLearning()
        for i in range(3):r=learner.observe('pattern',b'AB'*500+bytes([i])*24)
        review=r['heldout_pattern_checks']['pattern']['fresh_capture_review']
        self.assertEqual(review['checked_captures'],3);self.assertEqual(review['status'],'recurring-candidate')
        learner.observe('pattern',b'AB'*500+bytes([2])*24)
        self.assertEqual(learner.view()['heldout_pattern_checks']['pattern']['fresh_capture_review']['checked_captures'],3)
    def test_previous_capture_predicts_later_capture_without_update(self):
        from neural_app.ambient_pattern_validation import predict_capture
        result=predict_capture(b'AB'*512,b'AB'*500+b'CD'*12)
        self.assertEqual(result['status'],'predictive-gain')
        self.assertTrue(result['model_frozen_during_test'])
        self.assertNotEqual(result['training_sha256'],result['test_sha256'])

    def test_changed_pattern_loses_prediction_gain(self):
        from neural_app.ambient_pattern_validation import predict_capture
        self.assertEqual(predict_capture(b'AB'*512,b'BAAA'*256)['status'],'no-predictive-gain')

    def test_future_capture_evidence_is_source_specific(self):
        learner=EmergenceLearning()
        learner.observe('a',b'AB'*512)
        first=learner.observe('b',b'CD'*512)['heldout_pattern_checks']['b']
        self.assertNotIn('next_capture_prediction',first)
        second=learner.observe('a',b'AB'*500+b'CD'*12)['heldout_pattern_checks']['a']
        self.assertEqual(second['next_capture_prediction']['status'],'predictive-gain')
    def test_validation_worker_drains_without_main_chain_step(self):
        import time
        learner=EmergenceLearning();learner.enqueue('separate-source',b'AB'*512);learner.start()
        try:
            deadline=time.monotonic()+2
            while time.monotonic()<deadline and not learner.view()['heldout_pattern_checks']:time.sleep(.02)
            self.assertIn('separate-source',learner.view()['heldout_pattern_checks'])
        finally:learner.close()
        self.assertFalse(learner.worker.is_alive())

    def test_pending_capture_queue_is_bounded_and_coalesces(self):
        learner=EmergenceLearning()
        for i in range(100):learner.enqueue('source-'+str(i),b'AB'*512)
        self.assertEqual(len(learner.pending),32)
        learner.enqueue('source-99',b'CD'*512)
        self.assertEqual(len(learner.pending),32)
        learner.drain(2);self.assertEqual(len(learner.pending),30)
    def test_learning_broadcast_is_coalesced_and_not_on_intake_thread(self):
        learner=EmergenceLearning();updates=[];learner.on_update=lambda *args:updates.append(args)
        learner.observe('one',b'AB'*100);learner.observe('two',b'CD'*100)
        self.assertEqual(updates,[])
        learner.tick(None);self.assertEqual(updates,[])
        learner.tick(object());self.assertEqual(len(updates),1)
        self.assertEqual(updates[0][0],'two')
        learner.tick(object());self.assertEqual(len(updates),1)
