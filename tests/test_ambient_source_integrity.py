import unittest
from neural_app.ascii_chain import AsciiChain

class SourceIntegrity(unittest.TestCase):
    def test_named_streams_do_not_overwrite_one_another_at_shared_origin(self):
        chain=AsciiChain()
        for name in ('pure','influenced','sand'):
            chain.observe({'origin':'ambient-source-stream','payload':{'name':name,'text':'AB'*100,'stochastic':True}})
        self.assertEqual(len(chain.sources),3);self.assertEqual({v['source'] for v in chain.sources.values()},{'ambient-source-stream/'+s for s in ('pure','influenced','sand')})
    def test_receipts_model_text_and_authored_text_do_not_become_random_training(self):
        for flag in ('processing_receipt','predefined_text','contains_model_text'):
            chain=AsciiChain();chain.observe({'origin':'ambient-test','payload':{'text':'A'*100,'stochastic':True,flag:True}})
            self.assertEqual(len(chain.sources),0)
    def test_utf8_preserves_non_ascii_symbols(self):
        chain=AsciiChain();text='星☯😀01';chain.observe({'origin':'ambient-test','payload':{'text':text,'stochastic':True}})
        self.assertEqual(chain.sources['ambient-test']['raw'].decode('utf-8'),text)
    def test_processor_text_is_not_mislabelled_random(self):
        chain=AsciiChain();chain.observe({'origin':'ambient-observation','payload':{'text':'123'}})
        self.assertFalse(chain.sources['ambient-observation']['generated'])
    def test_generated_sources_survive_processor_pressure(self):
        chain=AsciiChain()
        chain.observe({'origin':'ambient-kept','payload':{'text':'AB'*100,'stochastic':True}})
        for i in range(100):
            chain.observe({'origin':'processor-'+str(i),'payload':{}},{'facts':['observation']})
        self.assertIn('ambient-kept',chain.sources)
        self.assertLessEqual(len(chain.sources),64)
        self.assertTrue(any(r['generated'] for r in chain.view()['source_inventory']))

    def test_restored_duplicate_still_gets_fresh_validation(self):
        import hashlib
        from neural_app.emergence_learning import EmergenceLearning
        learner=EmergenceLearning();raw=b'AB'*200
        learner.seen[('ambient-test',hashlib.sha256(raw).hexdigest())]=True
        result=learner.observe('ambient-test',raw)
        self.assertFalse(result['fresh'])
        self.assertIn('ambient-test',result['heldout_pattern_checks'])
        self.assertEqual(learner.sources,0)
    def test_generated_learning_completes_under_observation_pressure(self):
        from types import SimpleNamespace
        selector=SimpleNamespace(last={},choose=lambda *args: {'value':'test'})
        chain=AsciiChain()
        for name,text in [('alternating','AB'*500),('varying',''.join(chr(32+(i*37)%95) for i in range(1000)))]:
            chain.observe({'origin':'ambient-control','payload':{'name':name,'text':text,'stochastic':True}})
        for i in range(100):chain.observe({'origin':'processor-'+str(i),'payload':{}},{'facts':['observation']})
        learned=set()
        for _ in range(8):
            chain.next_at=0;packet=chain.step(selector,'source-test')
            self.assertTrue(packet['verified'])
            learned.update(chain.emergence.view()['heldout_pattern_checks'])
        self.assertTrue({'ambient-control/alternating','ambient-control/varying'}<=learned)
    def test_nested_stream_retains_its_own_rail_conditions(self):
        chain=AsciiChain()
        chain.observe({'origin':'cosmic-chain-modulator','payload':{'conditions':{'scope':'parent'},'sources':[{'name':'ordered','text':'AB'*100,'stochastic':True,'conditions':{'rail':'ordered-source','source':'original','capture_tick':4}}]}})
        chain.emergence.drain()
        conditions=chain.emergence.view()['heldout_pattern_checks']['cosmic-chain-modulator/ordered']['conditions']
        self.assertEqual(conditions['rail'],'ordered-source')
        self.assertEqual(conditions['capture_tick'],4)
        self.assertEqual(conditions['scope'],'parent')
    def test_chain_learning_payload_contains_only_current_source_evidence(self):
        import json
        from types import SimpleNamespace
        chain=AsciiChain();selector=SimpleNamespace(last={},choose=lambda *args:{'value':'test'})
        for i in range(12):chain.observe({'origin':'ambient-'+str(i),'payload':{'text':'ABCD'*64,'stochastic':True}})
        chain.emergence.drain(12);packet=chain.step(selector,'test')
        self.assertIn('source_check',packet['emergence_learning'])
        self.assertNotIn('heldout_pattern_checks',packet['emergence_learning'])
        self.assertLess(len(json.dumps(packet).encode()),24000)
    def test_long_names_with_identical_prefixes_keep_distinct_learners(self):
        from neural_app.ambient_source_identity import source_key
        from neural_app.emergence_learning import EmergenceLearning
        first='ambient-'+('x'*120)+'/a';second='ambient-'+('x'*120)+'/b'
        learner=EmergenceLearning();learner.enqueue(first,b'AB'*100);learner.enqueue(second,b'CD'*100);learner.drain()
        keys=learner.view()['heldout_pattern_checks']
        self.assertNotEqual(source_key(first),source_key(second));self.assertIn(source_key(first),keys);self.assertIn(source_key(second),keys)
        self.assertLessEqual(len(source_key(first)),100)
