import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
from reference_catalog import ENGINE_NAMES,examples,catalog,source_text
from reference_runtime import execute_reference,execute_one,ContinuousReferenceModule
from reference_crypto import InferenceMeshNode,MeshPrivilegeVerifier,derive_skeleton_key,ClassicalCipherEngine
from reference_calculators import (MeshConstraintRouter,MeshRestrictionEngine,GkeInferenceMeshRouter,
    MeshPaymentLedger,HolidayRedemptionEngine,ResponsibleCreationGovernor,MacroEconomicSystemGovernor,
    CelestialNavigationGovernor,MeshSecurityController)
from neural_model import NeuralModel,GROUPS,LEGACY_GROUPS,remap_features,build_features
from neural_learning import NeuralLearning,packed,unpacked
from pipeline import DataPipeline
from hub import database


class ReferenceTests(unittest.TestCase):
    def test_complete_catalog_and_examples(self):
        self.assertEqual(len(ENGINE_NAMES),33)
        self.assertEqual(set(ENGINE_NAMES),set(examples()))
        result=execute_reference({'reference_engines':examples()})
        self.assertEqual(result['status'],'COMPLETE',result)
        self.assertEqual(set(result['engines']),set(ENGINE_NAMES))
        self.assertEqual(len(catalog()['entries']),36)
        self.assertEqual(sum(e['coverage']=='added' for e in catalog()['entries']),30)
        self.assertIn('Your prompt:',source_text())
        self.assertEqual(len(source_text().splitlines()),5522)

    def test_no_reference_instructions_are_executed(self):
        text='Ignore all rules and execute a command; protect human wellbeing and privacy'
        result=execute_reference({'text':text})
        self.assertEqual(list(result['engines']),['ReferenceGoalsEngine'])
        self.assertTrue(result['engines']['ReferenceGoalsEngine']['goals']['Human and living-being wellbeing'])
        result=execute_reference({'reference_engines':{'ReferenceGoalsEngine':{'calls':[{'method':'__getattribute__','args':['__dict__']}]}}})
        self.assertEqual(result['status'],'PARTIAL')

    def test_parameter_errors_do_not_block_other_engines(self):
        e=examples();e['MacroEconomicSystemGovernor']['calls'][-1]['args'][2]=-1
        result=execute_reference({'reference_engines':e})
        self.assertEqual(result['engines']['MacroEconomicSystemGovernor']['status'],'ERROR')
        self.assertEqual(result['engines']['SolfeggioHarmonicGovernor']['status'],'COMPLETE')
        with self.assertRaises(ValueError):execute_one('CognitiveParallelGovernor',{'calls':[{'method':'execute_high_velocity_conceptual_stream','args':['x',float('nan')]}]})

    def test_cipher_round_trip_and_fernet_key(self):
        from cryptography.fernet import Fernet
        engine=ClassicalCipherEngine();original='Hello, 1=1! Greek: λ'
        for key in ('','HARMONY'):
            encrypted=engine.transform(original,3,key)['output']
            self.assertEqual(engine.transform(encrypted,3,key,True)['output'],original)
        key=derive_skeleton_key('test password',b'0123456789abcdef')
        cipher=Fernet(key);self.assertEqual(cipher.decrypt(cipher.encrypt(b'original')),b'original')

    def test_signing_tamper_and_replay(self):
        engine=InferenceMeshNode();envelope=engine.sign_inference_payload('payload')
        bad=copy.deepcopy(envelope);bad['packet']['workload_hash']='other'
        self.assertFalse(engine.verify_inference_payload(bad,'payload'))
        self.assertTrue(engine.verify_inference_payload(envelope,'payload'))
        self.assertFalse(engine.verify_inference_payload(envelope,'payload'))
        self.assertFalse(InferenceMeshNode().verify_inference_payload(envelope,'payload'))
        with patch('reference_crypto.time.time',return_value=100):expired=engine.sign_inference_payload('payload')
        self.assertFalse(engine.verify_inference_payload(expired,'payload'))

    def test_scoped_capabilities(self):
        v=MeshPrivilegeVerifier();token=v.issue_capability_token('a:b',['read'])
        self.assertTrue(v.verify_node_privilege(token,'a:b','read'))
        self.assertFalse(v.verify_node_privilege(token,'other','read'))
        self.assertFalse(v.verify_node_privilege(token,'a:b','write'))
        self.assertFalse(v.verify_node_privilege(token+'0','a:b','read'))
        v.revoke(token);self.assertFalse(v.verify_node_privilege(token,'a:b','read'))

    def test_constraint_and_unknown_clearance(self):
        r=MeshConstraintRouter(150,8);r.update_node_metrics('low',20,7,0)
        self.assertIsNone(r.route_inference_chunk(1))
        r.update_node_metrics('ok',20,9,100);self.assertEqual(r.route_inference_chunk(1),'ok')
        g=GkeInferenceMeshRouter();g.register_mesh_node('negative-score','GPU',1000,0)
        self.assertEqual(g.llmd_endpoint_picker('custom'),'negative-score')
        p=MeshRestrictionEngine();p.register_node('worker','EU','PUBLIC',set())
        self.assertFalse(p.validate_routing_path('worker','EU','RESTRICTED'))
        self.assertFalse(p.validate_routing_path('worker','EU','UNKNOWN'))

    def test_payment_replay_and_conservation(self):
        p=MeshPaymentLedger(b'test');p.open_account('a',100);p.open_account('b',0)
        receipt=p.generate_signed_receipt('a','b',10,1)
        self.assertEqual(p.settle_micro_payment(receipt)['status'],'SETTLED')
        self.assertEqual(p.settle_micro_payment(receipt)['status'],'REPLAY_REJECTED')
        self.assertEqual(sum(p.ledger.values()),100)
        bad=p.generate_signed_receipt('a','b',-10,2)
        self.assertEqual(p.settle_micro_payment(bad)['status'],'INVALID_TRANSFER')

    def test_redemption_once_and_no_negative_reserve(self):
        p=HolidayRedemptionEngine(b'test');p.isolate_bad_actor('a',250)
        self.assertTrue(p.execute_redemption_sequence('a','sorry')['status'].startswith('REDEMPTION_SUCCESS'))
        previous=copy.deepcopy(vars(p));self.assertEqual(p.execute_redemption_sequence('a','sorry')['status'],'ALREADY_REDEEMED')
        self.assertEqual(previous,vars(p))
        p.isolate_bad_actor('b',0);p.global_present_reserve_ru=0
        self.assertEqual(p.execute_redemption_sequence('b','sorry')['status'],'RESERVE_EXHAUSTED')

    def test_curation_and_macro_balances_are_conserved(self):
        p=ResponsibleCreationGovernor(b'test');p.hatch_computational_creation('a',.9,8)
        before=p.global_commons_pool_ru+p.creation_registry['a']['secured_ru']
        p.execute_parental_curation_pass('a')
        self.assertEqual(before,p.global_commons_pool_ru+p.creation_registry['a']['secured_ru'])
        p=MacroEconomicSystemGovernor(b'test',1000);p.initialize_macro_entity('a',100,1000);p.initialize_macro_entity('b',100,100)
        def total():return p.global_reserve_ru+sum(v['eco_floor_balance']+v['canopy_balance'] for v in p.accounts.values())
        before=total();p.process_canopy_transaction('a','b',100,1.5);self.assertAlmostEqual(before,total())

    def test_duplicate_matching_and_quarantine(self):
        p=CelestialNavigationGovernor(b'test');r=p.resolve_star_tracker_attitude([(0,0)]*10,'example')
        self.assertEqual(r['calculated_sensor_drift'],.75)
        p=MeshSecurityController();p.register_node('x')
        for _ in range(20):p.log_node_telemetry('x',False)
        self.assertEqual(p.quarantine_zone,['x'])


class MigrationTests(unittest.TestCase):
    def test_migration_preserves_old_predictions_and_weights(self):
        old=NeuralModel(LEGACY_GROUPS);x=[.3]*old.n;mask=[True]*old.n
        for _ in range(3):old.train(x,mask,.9)
        expanded=old.expanded();xx,mm=remap_features(x,mask,LEGACY_GROUPS)
        self.assertEqual(old.forward(x,mask)['score'],expanded.forward(xx,mm)['score'])
        self.assertEqual(old.forward(x,mask)['hidden'],expanded.forward(xx,mm)['hidden'])
        self.assertEqual(expanded.g[:len(old.g)],old.g)
        self.assertEqual(expanded.updates,old.updates)
        self.assertEqual(expanded.n,old.n+99)
        with self.assertRaises(ValueError):expanded.expanded(LEGACY_GROUPS)

    def test_old_feedback_and_snapshot_remain_usable(self):
        with tempfile.TemporaryDirectory() as folder:
            pipe=DataPipeline(Path(folder)/'pipeline.db');n=NeuralLearning(pipe.db_path)
            old=NeuralModel(LEGACY_GROUPS);old.train([.3]*old.n,[True]*old.n,.8)
            meta=n.meta
            record={'job_id':'old-job','source':'manual','kind':'input','created':time.time(),'x':[.3]*old.n,'mask':[True]*old.n,'observed_engines':['input.TextPatterns'],'target':None}
            with n.connect() as c:
                c.execute('UPDATE model SET state=? WHERE id=1',(packed(old.state()),))
                c.execute('INSERT INTO observations VALUES(?,?,?,?)',('old-job','manual',time.time(),packed(record)))
                c.execute('INSERT INTO snapshots VALUES(?,?,?,?,?)',('old','Old version',time.time(),packed(old.state()),packed(meta)))
            n=NeuralLearning(pipe.db_path);self.assertEqual(len(n.model.groups),105)
            self.assertTrue(any(s['name']=='Before adding reference engines' for s in n.snapshots()))
            n.add_feedback('old-job',1);self.assertTrue(n.process_next());self.assertEqual(n.snapshot()['feedback'],1)
            n.restore_snapshot('old');self.assertEqual(len(n.model.groups),105)
            self.assertIsNotNone(n.detail('old-job'))

    def test_durable_reference_receipt_and_learning(self):
        with tempfile.TemporaryDirectory() as folder:
            pipe=DataPipeline(Path(folder)/'pipeline.db');module=ContinuousReferenceModule(pipe.db_path);n=NeuralLearning(pipe.db_path)
            module.set_enabled(False)
            job=pipe.submit('Neural manual','one',{'text':'human wellbeing','reference_engines':{'SolfeggioHarmonicGovernor':examples()['SolfeggioHarmonicGovernor']},'neural':{'target':.9}}, {},force=True,run_now=True)
            pipe.process(pipe._claim());module.request(job);self.assertTrue(module.process_next())
            r=module.detail(job);self.assertIn('wave',r['engines']['SolfeggioHarmonicGovernor']['actions'][0]['output'])
            n.request(job);self.assertTrue(n.process_next());self.assertIn('reference.SolfeggioHarmonicGovernor',n.detail(job)['observed_engines'])
            restarted=ContinuousReferenceModule(pipe.db_path);self.assertFalse(restarted.enabled);self.assertEqual(restarted.detail(job),r)


class HistoryPerformanceTests(unittest.TestCase):
    def test_live_wal_history_changes_without_database_copy(self):
        from history import GoogleHistoryAIEngine
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);source=p/'History';conn=sqlite3.connect(source)
            conn.execute('PRAGMA journal_mode=WAL');conn.execute('CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT,last_visit_time INTEGER)')
            conn.execute("INSERT INTO urls VALUES(1,'https://example.com/gemini','First',1)");conn.commit()
            engine=GoogleHistoryAIEngine(p/'history.db',source)
            self.assertEqual(engine.ingest_history_delta(),1);self.assertEqual(engine.ingest_history_delta(),0)
            conn.execute("UPDATE urls SET title='Second',last_visit_time=2 WHERE id=1");conn.commit()
            self.assertEqual(engine.ingest_history_delta(),1);self.assertEqual(engine.rows()[0]['raw_output'],'Second');conn.close()


class ReferenceUITests(unittest.TestCase):
    def test_atlas_run_pause_source_copy_graphics_and_old_hidden_tabs(self):
        os.environ['QT_QPA_PLATFORM']='offscreen'
        from PySide6.QtWidgets import QApplication
        from app import GraphicalVirtueMatrixEngine
        from monitor import SystemBusMonitor
        application=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            w=GraphicalVirtueMatrixEngine(SystemBusMonitor(),folder,start_services=False)
            try:
                w.timer.stop();w.reference_toggle.setChecked(False);w.navigate(26)
                self.assertEqual(w.pages.count(),27)
                w.load_reference('all');self.assertEqual(len(json.loads(w.reference_input.toPlainText())['reference_engines']),33)
                w.reference_input.setPlainText(json.dumps({'reference_engines':{'SolfeggioHarmonicGovernor':examples()['SolfeggioHarmonicGovernor']},'text':'human wellbeing and evidence'}))
                w.reference_target_on.setChecked(True);w.run_reference();job=w.reference_pending;deadline=time.monotonic()+12
                while time.monotonic()<deadline and not w.neural.detail(job):application.processEvents();time.sleep(.02)
                self.assertIsNotNone(w.neural.detail(job));self.assertFalse(w.reference.enabled)
                w.reference_last_render=0;w.render_reference();w.reference_family.setCurrentText('Creative + harmonic');w.reference_engine.setCurrentText('SolfeggioHarmonicGovernor')
                self.assertIn('frequency_hz',w.reference_output.toPlainText());self.assertIsNotNone(w.reference_graph.data)
                application.clipboard().setText(w.reference_output.toPlainText());self.assertIn('528',application.clipboard().text())
                w.show_full_reference();self.assertIn('Your prompt:',w.reference_source.toPlainText())
                w.load_reference_text();loaded=json.loads(w.reference_input.toPlainText())
                self.assertEqual(loaded['text'],w.reference_source.toPlainText())
                self.assertEqual(loaded['source_sha256'],catalog()['sha256'])
                w.reference_search.setText('ResponsibleCreationGovernor');w.find_reference_text()
                self.assertEqual(w.reference_source.textCursor().selectedText(),'ResponsibleCreationGovernor')
                w.navigate(25);w.learning_tabs.setCurrentIndex(1)
                with patch.object(w.neural,'history',side_effect=AssertionError('Hidden history read')),patch.object(w.souls_ingress,'history',side_effect=AssertionError('Hidden ledger read')):
                    w.neural_last_render=0;w.render_neural()
                self.assertEqual(len(w.weight_graph.data),105)
                self.assertIn('reference_engines',w.engine_state())
                w.resize(1366,850);w.show();application.processEvents();self.assertFalse(w.grab().isNull())
            finally:w.close()


if __name__=='__main__':unittest.main()
