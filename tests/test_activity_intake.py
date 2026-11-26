from pathlib import Path
import tempfile
import unittest
from neural_app.activity_intake import ActivityIntake


class FakeRuntime:
    def __init__(self,path):self.data=Path(path);self.sent=[];self.errors=[]
    def submit(self,section,body):self.sent.append((section,body));return {'id':str(len(self.sent))}
    def result(self,ident):return {'status':'complete','receipt':int(ident)}


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.runtime=FakeRuntime(self.temp.name)
        self.a=ActivityIntake(self.runtime);self.extension='a'*32;self.origin='chrome-extension://'+self.extension
        self.key=self.a.pair('maintainer@example.invalid',self.extension)['key']
        self.body={'account':'maintainer@example.invalid','source':'https://myactivity.google.com/myactivity?product=83','records':[{'text':'A private learning question','date_label':'2026-11-11 12:30'}]}
    def tearDown(self):self.a.close();self.temp.cleanup()

    def ingest(self,key=None,origin=None,body=None):return self.a.ingest(self.key if key is None else key,self.origin if origin is None else origin,self.extension,self.body if body is None else body)

    def test_scoped_private_intake_deduplicates_and_enters_local_pipeline(self):
        self.assertEqual(self.ingest()['new'],1);self.a.last_ingest=0;self.assertEqual(self.ingest()['new'],0)
        self.a.pulse();self.a.pulse();self.assertEqual(len(self.runtime.sent),1)
        section,body=self.runtime.sent[0];self.assertEqual(section,'pipeline');self.assertEqual(body['sections'],[])
        self.assertEqual(self.a.view()['counts']['complete'],1)
        self.assertNotIn('text',self.a.view())

    def test_wrong_account_origin_key_and_revocation_block(self):
        for kwargs in [{'key':'wrong'},{'origin':'https://unrelated.example'},{'body':{**self.body,'account':'maintainer@example.invalid'}}]:
            with self.assertRaises(PermissionError):self.ingest(**kwargs)
        self.a.revoke()
        with self.assertRaises(PermissionError):self.ingest()

    def test_pause_stops_processing(self):
        self.ingest();self.a.configure(False);self.a.pulse();self.assertEqual(self.runtime.sent,[])
        with self.assertRaises(PermissionError):self.ingest()
