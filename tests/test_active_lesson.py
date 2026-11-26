import json,tempfile,time,unittest
from pathlib import Path
from neural_app.active_lesson import ActiveLesson,LESSONS
from neural_app.runtime import Runtime
from neural_app import translation as btq

class ActiveLessonTests(unittest.TestCase):
 def test_exact_causal_mask_and_counterfactual(self):
  with tempfile.TemporaryDirectory() as folder:
   m=ActiveLesson(folder);bits='01'*128;a=m.evaluate(bits);off=m.evaluate(bits,weight_override=0)
   self.assertGreater(a['changed_bits'],0);self.assertEqual(off['working_bits'],bits)
   self.assertEqual(''.join(str(int(x)^int(y)) for x,y in zip(a['working_bits'],a['xor_mask'])),bits)
   dark=m.evaluate(bits,parameters={'loss':1,'pressure':1,'resilience':0,'repair':0})
   self.assertNotEqual(a['working_bits'],dark['working_bits']);self.assertLess(dark['signal'],0)
   m.close()
 def test_review_persistence_without_self_labels(self):
  with tempfile.TemporaryDirectory() as folder:
   m=ActiveLesson(folder);a=m.evaluate('01'*64);weights=list(m.weights)
   m.tick(False);m.observe('example','a'*64);self.assertEqual(weights,m.weights)
   result=m.review(a['features'],1);self.assertGreater(result['after'],result['before']);m.close()
   n=ActiveLesson(folder);self.assertEqual(n.reviews,1);self.assertEqual(n.weights,m.weights);n.close()
 def test_heartbeat_and_private_lossless_packet(self):
  with tempfile.TemporaryDirectory() as folder:
   seen=[];m=ActiveLesson(folder,on_packet=lambda p:seen.append(p),period=.02)
   m.set_events([{'label':'PRIVATE EVENT','severity':.8}]);m.start();time.sleep(.09)
   self.assertGreater(m.ticks,0);self.assertEqual(m.reviews,0);packet=m.transmission()
   self.assertEqual(json.loads(btq.decode(packet['transport'])),packet['payload'])
   self.assertNotIn('PRIVATE EVENT',json.dumps(packet));m.close();ticks=m.ticks;time.sleep(.04);self.assertEqual(ticks,m.ticks)
 def test_pipeline_uses_working_bits_and_receipt_review(self):
  with tempfile.TemporaryDirectory() as folder:
   r=Runtime(folder,start=False)
   try:
    bits='01'*64;v=r.pipeline({'bits':bits,'sections':[]});a=v['stages']['causal'];x=v['stages']['classifier']['features'][0]
    self.assertAlmostEqual(x,a['working_bits'].count('1')/len(bits)*2-1)
    self.assertGreater(a['changed_bits'],0);self.assertEqual(v['stages']['signals']['ones'],64)
    ident=r.record('pipeline',{'bits':bits},v,1);self.assertEqual(r.receipts(ident)['causal']['module'],'active-lesson')
    r.feedback({'receipt':ident,'target':1});self.assertEqual(r.causal.reviews,1)
    with self.assertRaises(ValueError):r.feedback({'receipt':ident,'target':1})
    self.assertEqual(r.causal.reviews,1)
   finally:r.close()
 def test_distinct_lessons_include_story_and_sermon(self):
  self.assertEqual(len({x['id'] for x in LESSONS}),len(LESSONS));self.assertTrue({'frith','sermon','ladder'} <= {x['id'] for x in LESSONS})

 def test_authenticated_network_lesson_and_live_subscription(self):
  import socket
  from neural_app.network import Bus
  with tempfile.TemporaryDirectory() as folder:
   r=Runtime(folder);bus=Bus(r,port=0,discovery_port=0)
   try:
    with socket.create_connection(('127.0.0.1',bus.port),timeout=8) as sock:
     stream=sock.makefile('rwb');stream.write((json.dumps({'op':'lesson','token':bus.key})+'\n').encode());stream.flush()
     packet=json.loads(stream.readline());self.assertEqual(json.loads(btq.decode(packet['transport'])),packet['payload'])
    with socket.create_connection(('127.0.0.1',bus.port),timeout=8) as sock:
     stream=sock.makefile('rwb');stream.write((json.dumps({'op':'subscribe','token':bus.key})+'\n').encode());stream.flush()
     self.assertEqual(json.loads(stream.readline())['type'],'subscribed')
     item=json.loads(stream.readline());self.assertEqual(item['type'],'active-lesson');self.assertTrue(item['round_trip'])
   finally:bus.close();r.close()
