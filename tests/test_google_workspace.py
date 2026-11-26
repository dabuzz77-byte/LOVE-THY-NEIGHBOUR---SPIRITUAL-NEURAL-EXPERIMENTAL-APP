import json
import queue
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from neural_app.google_index import GoogleIndex,chunks
from neural_app.opera_workspace import OperaWorkspace
from neural_app.model_intersect import ModelIntersect

class FakeRuntime:
    def __init__(self,path):
        import threading
        self.data=Path(path);self.queue=queue.Queue();self.halt=threading.Event();self.sent=[]
    def submit(self,section,body):self.sent.append(body);return {'id':str(len(self.sent))}
    def result(self,ident):return {'status':'complete','receipt':int(ident)}

class FakeChat:
    def __init__(self):self.calls=[]
    def settings(self):return {p:{'model':p+'-test'} for p in ('llama','qwen','gemma','gemini','chatgpt')}
    def request(self,p,model,messages,system):self.calls.append(p);return p+' contribution with source limits'

class GoogleWorkspaceTests(unittest.TestCase):
    def test_full_text_unicode_index_deduplication_and_learning_queue(self):
        with tempfile.TemporaryDirectory() as d:
            runtime=FakeRuntime(d);index=GoogleIndex(runtime)
            content='Animal spheres across the globe 🌍 '+('三'*600)
            record={'source':'ai_mode','title':'Animal study','content':content,'capture':'full_text'}
            self.assertEqual(index.ingest({'records':[record]})['new'],1)
            self.assertEqual(index.ingest({'records':[record]})['new'],0)
            self.assertEqual(len(index.search('animal spheres')),1)
            self.assertEqual(''.join(chunks(content)),content)
            self.assertTrue(all(len(c.encode())<=480 for c in chunks(content)))
            index.pulse();self.assertNotIn('research',runtime.sent[0]);self.assertIn('private_google_index',runtime.sent[0])
            index.pulse();self.assertEqual(index.view()['chunks']['complete'],1)
            with self.assertRaises(ValueError):index.ingest({'records':[{**record,'url':'https://evil.example/'}]})

    def test_opera_autostart_is_local_setting_and_uses_existing_profile(self):
        with tempfile.TemporaryDirectory() as d:
            opera=OperaWorkspace(d);self.assertFalse(opera.config['enabled']);opera.configure(True)
            with patch.object(opera,'executable',return_value='opera.exe'),patch('neural_app.opera_workspace.subprocess.Popen') as launch:
                self.assertEqual(opera.on_start('http://127.0.0.1:8797')['state'],'opened')
                args=launch.call_args.args[0];self.assertIn('http://127.0.0.1:8797/#googleworkspace',args)
                self.assertFalse(any('remote-debug' in a or 'user-data-dir' in a for a in args))
            with self.assertRaises(ValueError):opera.open('https://external.example/')

    def test_both_coordinators_collect_review_and_learn_without_cloud_leakage(self):
        for coordinator,peer in [('qwen','llama'),('llama','qwen')]:
            with self.subTest(coordinator=coordinator),tempfile.TemporaryDirectory() as d:
                runtime=FakeRuntime(d);runtime.google_index=GoogleIndex(runtime);chat=FakeChat();mesh=ModelIntersect(runtime,chat)
                mesh.busy.acquire();job={'id':'test','providers':[coordinator,peer],'coordinator':coordinator,'responses':[]}
                mesh.run(job,{'prompt':'Compare care planning','bidirectional':True},[])
                self.assertEqual(job['status'],'complete')
                self.assertEqual(chat.calls,[peer,coordinator,peer,coordinator])
                self.assertIn('private_model_intersect',runtime.sent[0]);self.assertNotIn('research',runtime.sent[0])
                with self.assertRaises(ValueError):mesh.start({'prompt':'Private material','providers':['gemini'],'allow_cloud':False})
