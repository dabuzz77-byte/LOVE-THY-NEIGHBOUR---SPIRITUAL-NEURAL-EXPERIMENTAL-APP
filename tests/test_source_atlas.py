import hashlib,json,tempfile,unittest
from pathlib import Path
from neural_app.runtime import Runtime,model_groups

class SourceAtlasTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.runtime=Runtime(self.folder.name,start=False)
    def tearDown(self):self.runtime.close();self.folder.cleanup()

    def test_catalogue_deduplicates_and_preserves_every_source_digest(self):
        atlas=self.runtime.source_atlas();catalogue=atlas.catalogue()
        self.assertEqual(len(atlas.records),catalogue['summary']['unique_code'])
        for ident,row in atlas.records.items():
            self.assertEqual(hashlib.sha256((atlas.root/row['object']).read_bytes()).hexdigest(),ident)
        with self.assertRaises(ValueError):atlas.source('../outside')

    def test_source_analysis_changes_shared_learning_and_retains_full_identity(self):
        atlas=self.runtime.source_atlas();ident=next(iter(atlas.records));body=atlas.input(ident)
        value=self.runtime.pipeline(body)
        self.assertEqual(value['stages']['source_atlas']['source_id'],ident)
        self.assertGreater(value['learning']['updates'],0)
        self.assertIn('inference',value['stages'])
        self.assertIn('rss_mb',value['stages']['source_atlas']['actual_runtime'])
        self.assertTrue(all(t['round_trip'] for t in value['transfers']))

    def test_imported_native_sections_have_shared_feature_groups(self):
        atlas=self.runtime.source_atlas();groups=dict(model_groups())
        self.assertEqual(len(atlas.panels),38)
        self.assertTrue(all('section/'+p['id'] in groups for p in atlas.panels))
        self.assertEqual(self.runtime.engine('source_atlas',{})['status'],'AWAITING_INPUT')

    def test_continuous_observations_rotate_and_train_shared_section_features(self):
        class Host:
            def __init__(self):self.opened=[]
            def pause(self,ident,value):pass
            def open(self,ident):self.opened.append(ident);return {'engine_fields':{'cycle':len(self.opened),'signal':.5}}
        atlas=self.runtime.source_atlas();atlas.continuous['enabled']=True;host=Host()
        atlas.background_step(host);atlas.background_step(host)
        self.assertNotEqual(host.opened[0],host.opened[1])
        self.assertEqual(atlas.continuous['loaded'],2)
        self.assertEqual(atlas.continuous['observations'],2)
        self.assertEqual(atlas.continuous['errors'],[])
        self.assertGreaterEqual(self.runtime.learning_view()['updates'],2)
