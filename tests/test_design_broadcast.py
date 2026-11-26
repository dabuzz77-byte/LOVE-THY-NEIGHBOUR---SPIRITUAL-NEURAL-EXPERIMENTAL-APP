import json
import socket
import tempfile
import unittest
from neural_app.runtime import Runtime
from neural_app.network import Bus


class DesignBroadcastTests(unittest.TestCase):
    def test_shared_learning_and_context_reaches_authenticated_subscriber(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime=Runtime(folder,start=False)
            bus=Bus(runtime,port=0,discovery_port=0)
            try:
                body={'text':'Tesla motors, Fuller shelter, Fresco humane resources.',
                      'sections':['suite','unified','platform_alignment','karmic_welfare','virtue_text','reference','inference'],
                      'research':{'topic':'design_tesla'}}
                result=runtime.pipeline(body)
                receipt=runtime.record('pipeline',body,result,1)
                runtime.checkpoint()
                restored=Runtime(folder,start=False)
                try:self.assertEqual(restored.research_public,runtime.research_public)
                finally:restored.close()
                self.assertGreater(result['learning']['updates'],0)
                self.assertGreater(result['learning']['original_flux_learner']['new_updates'],0)
                self.assertIn('inference',result['stages'])
                with socket.create_connection(('127.0.0.1',bus.port),timeout=5) as peer:
                    peer.sendall((json.dumps({'token':bus.key,'op':'subscribe'})+'\n').encode())
                    reader=peer.makefile('rb')
                    self.assertEqual(json.loads(reader.readline())['type'],'subscribed')
                    bus.broadcast({'type':'result','section':'care','receipt':receipt+1})
                    message=json.loads(reader.readline())
                    context=message['inference_context']['design_research']['design_tesla']
                    self.assertEqual(context['receipt'],receipt)
                    self.assertNotIn('text',context)
                    self.assertEqual(runtime.delivery['peer_writes'],1)
                    self.assertGreater(runtime.delivery['bytes_written'],0)
                    reader.close()
            finally:bus.close();runtime.close()
