import hashlib,json,tempfile,time,unittest
from pathlib import Path
from neural_app.runtime import Runtime,ROOT
from neural_app.gnostic_four import CHECKS,decide,FourTexts
from neural_app.discipline import process as discipline,TRIGRAMS
from neural_app.intent_channel import process as channel

class ConnectedStudyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.rt=Runtime(Path(self.tmp.name),start=False)
    def tearDown(self):self.rt.close();self.tmp.cleanup()
    def test_policy_blocks_harm_even_with_high_benefit(self):
        decision=decide({});self.assertEqual(decision['selected'],'offline');self.assertFalse(decision['actions'][0]['eligible']);self.assertTrue(decision['round_trip'])
        checks=dict.fromkeys(CHECKS,True);checks['reviewed']=None
        decision=decide({'candidates':[dict(id='unknown',benefit=1,need=1,confidence=1,cost=0,checks=checks)]})
        self.assertIsNone(decision['selected']);self.assertEqual(decision['actions'][0]['known_bits'][-1],'0')
        for val in [float('nan'),True,-1]:
            with self.assertRaises(ValueError):decide({'budget':val})
    def test_complete_sources_are_exact_and_chunks_reassemble(self):
        study=self.rt.four_texts();self.assertEqual(len(study.texts),6)
        for source,text in study.texts.items():
            parts=[c for c in study.chunks if c['source']==source]
            self.assertEqual(''.join(c['text'] for c in parts),text)
            self.assertTrue(all(len(c['text'].encode('utf-8'))<=480 for c in parts))
        first=study.chunks[0]
        result=study.process({'mode':'ingest','chunk':first['id'],'text':first['text']});self.assertEqual(result['source_excerpt'],first['text'])
        with self.assertRaises(ValueError):study.process({'mode':'ingest','chunk':first['id'],'text':'changed'})
    def test_64_hexagrams_and_known_changes(self):
        changes=self.rt.changes();self.assertEqual(len(changes.by_bits),64)
        for lines,primary,related in [([9]*6,1,2),([6]*6,2,1),([7]*6,1,1),([8]*6,2,2),([7,8,8,8,7,8],3,3)]:
            result=changes.process({'mode':'traditional','lines':lines,'question':'What changes?'})
            self.assertEqual(result['primary']['number'],primary);self.assertEqual(result['related']['number'],related);self.assertTrue(result['binary']['round_trip'])
        with self.assertRaises(ValueError):changes.process({'lines':[True]*6})
        result=changes.process({'lines':[7]*6,'mode':'adapted'})
        self.assertEqual(result['app_adaptation']['decision']['selected'],'offline')
        self.assertTrue(result['app_adaptation']['harm_analysis'][0]['constructive_counters'])
    def test_model_conditioned_cast_replays_and_preserves_coin_lines(self):
        sample=self.rt.changes().sample_model()
        digest=bytes.fromhex(sample['model_sha256']);entropy=bytes.fromhex(sample['entropy_hex'])
        bits=''.join(f'{a^b:08b}' for a,b in zip(entropy,digest[:3]))[:18]
        self.assertEqual(bits,sample['sampled_coin_bits']);self.assertEqual(sample['lines'],[6+sum(map(int,bits[i:i+3])) for i in range(0,18,3)])
        self.assertIn('stellar_flux_model_wm2',sample['model']);self.assertIn('biosphere_carrier_hz',sample['model'])
    def test_trigrams_channel_and_live_feedback(self):
        self.assertEqual(len(TRIGRAMS),8)
        for bits in TRIGRAMS:
            value=discipline({'trigram':bits});self.assertTrue(value['trigram']['transport']['round_trip']);self.assertEqual(sum(value['practice']['attention_vector']),1)
        value=channel({'intention':'Let care guide the next step.'});self.assertTrue(value['channel']['software_bits']['round_trip']);self.assertFalse(value['channel']['external_delivery'])
        circuit=self.rt.living_circuit();circuit.configure({'enabled':True});circuit.receive({'kind':'water','source':'test client','temperature':-10,'value':.5});circuit.drop();circuit.step()
        self.assertEqual(circuit.ticks,1);self.assertEqual(circuit.known_inputs,1);self.assertTrue(all(-1<=n<=1 for n in circuit.values));self.assertEqual(circuit.view()['water']['remote']['celsius'],-10)
        self.assertEqual(circuit.phase(-1),'ice');self.assertIn('boundary',circuit.phase(0));self.assertFalse(circuit.outbox[-1]['external_delivery'])
        self.rt.latest['pipeline']={'result':{'stages':{'gnostic_four':{'decision':{'selected':None}}}}};circuit.last=0;circuit.step();self.assertEqual(circuit.outbox[-1]['signal'],0)
        circuit.configure({'enabled':False});circuit.last=0;circuit.step();self.assertEqual(circuit.ticks,2)
    def test_watts_private_import_coverage_and_exact_chunks(self):
        watts=self.rt.watts_study();self.assertEqual(watts.view()['coverage']['full_recordings_ingested'],0)
        with self.assertRaises(ValueError):watts.ingest({'title':'Test','text':'abc','rights_confirmed':False})
        text='A local practice note. '+('Faith and care. 水 '*100)
        watts.ingest({'title':'Own study text','text':text,'rights_confirmed':True});watts.ingest({'title':'Duplicate','text':text,'rights_confirmed':True})
        self.assertEqual(len(watts.records),1);self.assertEqual(''.join(c['text'] for c in watts.chunks),text)
        self.assertTrue(all(len(c['text'].encode('utf-8'))<=480 for c in watts.chunks));self.assertEqual(watts.reading()['kind'],'User-imported transcript excerpt')
        chunk=watts.chunks[0];result=watts.process({'mode':'ingest','chunk':chunk['id'],'text':chunk['text']});self.assertFalse(result['external_delivery'])
    def test_shared_pipeline_new_sections_transport_and_learn(self):
        before=self.rt.get_model().updates
        for section,body in [('gnostic_four',{'lesson':'engine'}),('discipline',{}),('intent_channel',{}),('watts_study',{}),('iching',{'mode':'adapted','lines':[7]*6})]:
            result=self.rt.pipeline({'text':'Care and clarity','sections':[section],'section_inputs':{section:body}})
            self.assertIn(section,result['stages']);self.assertTrue(all(t['round_trip'] for t in result['transfers']))
        self.assertGreater(self.rt.get_model().updates,before)

if __name__=='__main__':unittest.main()
