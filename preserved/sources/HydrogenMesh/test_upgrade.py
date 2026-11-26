"""Storage-growth regressions and bounded-renderer checks."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest
from mesh_bus import Ledger,COMPRESSED
from bounded_io import cap_directory,RotatingSink

ROOT=Path(__file__).resolve().parents[2]/'work'/'upgrade-tests';ROOT.mkdir(parents=True,exist_ok=True)

class StorageTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=ROOT);self.path=Path(self.temp.name)/'mesh.sqlite3'
    def tearDown(self):self.temp.cleanup()
    def test_sustained_incompressible_traffic_is_bounded(self):
        ledger=Ledger(self.path,max_storage_mb=1,max_messages=80)
        for i in range(650):
            ledger.publish(dict(id=str(i),topic='load',data=os.urandom(6500).hex()))
        ledger.maintenance(force=True)
        stats=ledger.stats()
        self.assertEqual(ledger.latest(),650);self.assertLessEqual(stats['retained'],80)
        self.assertGreater(stats['storage']['pruned_messages'],500)
        self.assertLessEqual(self.path.stat().st_size,1048576)
        self.assertIsNotNone(ledger.find('649'));self.assertIsNone(ledger.find('0'))
        self.assertLessEqual(stats['storage']['payload_bytes'],ledger.payload_budget)
    def test_compression_preserves_original_and_idempotency(self):
        ledger=Ledger(self.path);value=dict(id='zeroes',topic='bits',data='00000001'*20000)
        original=ledger.publish(value);duplicate=ledger.publish(value)
        self.assertEqual(original['seq'],duplicate['seq']);self.assertEqual(ledger.find('zeroes')['data'],value['data'])
        with closing(sqlite3.connect(self.path)) as db:body=db.execute('SELECT body FROM messages').fetchone()[0]
        self.assertTrue(body.startswith(COMPRESSED));self.assertLess(len(body),4000)
    def test_old_unbounded_database_is_shrunk(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,id TEXT UNIQUE,body TEXT,created REAL)')
            with db:
                for i in range(750):
                    raw=json.dumps(dict(id=str(i),topic='legacy',data=os.urandom(4096).hex(),source='legacy',target='*',route=[],time=time.time()))
                    db.execute('INSERT INTO messages(id,body,created) VALUES(?,?,?)',(str(i),raw,time.time()))
        self.assertGreater(self.path.stat().st_size,5*1048576)
        ledger=Ledger(self.path,max_storage_mb=1,max_messages=500)
        self.assertLessEqual(self.path.stat().st_size,1048576)
        self.assertIsNotNone(ledger.find('749'));self.assertIsNone(ledger.find('0'))
        new=ledger.publish(dict(topic='after migration',data=1));self.assertEqual(new['seq'],751)
    def test_expiry_preserves_sequence_and_allows_new_messages(self):
        ledger=Ledger(self.path);ledger.publish(dict(topic='old',data='old'))
        with ledger.db() as db:db.execute('UPDATE messages SET created=?',(time.time()-100000,))
        ledger.maintenance(force=True)
        self.assertEqual(ledger.stats()['retained'],0);self.assertEqual(ledger.latest(),1)
        self.assertEqual(ledger.publish(dict(topic='new',data='new'))['seq'],2)
    def test_auxiliary_logs_and_retry_files_have_limits(self):
        root=Path(self.temp.name)/'logs';sink=RotatingSink(root/'app.log',limit=1024,backups=2)
        sink.write(os.urandom(100000))
        self.assertLessEqual(sum(p.stat().st_size for p in root.iterdir()),3072)
        for i in range(30):(root/f'{i}.json').write_bytes(b'x'*2048)
        cap_directory(root,max_bytes=8192,max_files=5)
        self.assertLessEqual(sum(p.stat().st_size for p in root.iterdir()),8192)
        self.assertLessEqual(len(list(root.iterdir())),5)
    def test_large_telemetry_uses_summary_not_recursive_bit_expansion(self):
        from hydrogen_mesh import Runtime
        data={'bits':'01'*60000,'nested':{'previous':{'bits':'10'*50000}}}
        result=Runtime.processing_text(dict(source='observatory',topic='observatory.module',data=data))
        self.assertLess(len(result),2048);self.assertEqual(json.loads(result)['processing_scope'],'Summary only; full original is in the rolling event ledger')
        self.assertEqual(Runtime.processing_text(dict(source='app',topic='compute.request',data={'text':'actual request'})),'actual request')
    def test_instance_lock_is_released_and_rejects_duplicates(self):
        from data_lock import DataLock
        first=DataLock(Path(self.temp.name)/'runtime.lock')
        try:
            with self.assertRaises(OSError):DataLock(Path(self.temp.name)/'runtime.lock')
        finally:first.close()
        second=DataLock(Path(self.temp.name)/'runtime.lock');second.close()

class RendererTests(unittest.TestCase):
    def test_all_scenes_render_and_stochastic_pulses_are_visible(self):
        from scene_renderer import SceneRenderer
        for preset in ('Cosmos','Hydrogen','Stellar','Earth','Matrix','Dyson'):
            renderer=SceneRenderer();first=renderer.render(800,480,preset,'01011010'*128,now=renderer.epoch)
            for i in range(1,55):last=renderer.render(800,480,preset,'01011010'*128,now=renderer.epoch+i*.09)
            self.assertEqual(last.size,(800,480));self.assertGreater(renderer.pulse_count,0)
            self.assertNotEqual(hashlib.sha256(first.tobytes()).digest(),hashlib.sha256(last.tobytes()).digest())
            self.assertLessEqual(len(renderer.assets),25);self.assertLessEqual(len(renderer.glyphs),201)
    def test_stochastic_toggle_and_data_matrix_sample(self):
        from scene_renderer import SceneRenderer
        renderer=SceneRenderer();renderer.simulated=False
        for i in range(30):image=renderer.render(640,400,'Matrix','000001',now=renderer.epoch+i*.1)
        self.assertEqual(renderer.pulse_count,0);self.assertGreater(renderer.last_geometry['cols'],10)
        self.assertEqual(image.size,(640,400))

if __name__=='__main__':unittest.main(verbosity=2)
