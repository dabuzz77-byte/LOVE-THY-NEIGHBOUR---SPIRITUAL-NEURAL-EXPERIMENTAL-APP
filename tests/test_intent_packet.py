import unittest
from neural_app.intent_packet import prepare_intent


class IntentTests(unittest.TestCase):
    def test_whitespace_normalization_and_utf8_digest(self):
        import hashlib
        p=prepare_intent('  Care\n for\tall 🌍  ')
        self.assertEqual(p['text'],'Care for all 🌍')
        self.assertEqual(p['bytes'],len(p['text'].encode('utf-8')))
        self.assertEqual(p['sha256'],hashlib.sha256(p['text'].encode()).hexdigest())

    def test_empty_or_oversized_intent_is_rejected(self):
        for text in ['', '   ', 'x'*513, '🌍'*129]:
            with self.assertRaises(ValueError):prepare_intent(text)

    def test_maximum_input_is_retained_without_truncation(self):
        self.assertEqual(prepare_intent('x'*512)['text'],'x'*512)
