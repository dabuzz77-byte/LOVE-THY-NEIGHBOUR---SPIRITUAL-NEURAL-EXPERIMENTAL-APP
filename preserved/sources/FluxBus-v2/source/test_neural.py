import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from souls_ingress import SoulsOverDigitsCore,ContinuousSoulsModule,execute_ingress,INPUT_TEMPLATE
from resource_governor import CentralBankResourceGovernor,INPUT_TEMPLATE as GOV
from central_bank_mesh import CentralBankMeshController,INPUT_TEMPLATE as MESH
from world_banking import WorldGridCentralBankingCore,INPUT_TEMPLATE as WORLD
from neural_model import NeuralModel,build_features,GROUPS
from neural_learning import NeuralLearning,packed
from web_research import WebResearch,discover_topics
from library import LibraryStore
from pipeline import DataPipeline
from hub import database


class LedgerTests(unittest.TestCase):
    def core(self,reserve=1000):
        core=SoulsOverDigitsCore(b'test-key',reserve)
        for name,layer,money in [('root','ROOTS',1),('top','TOP',10000),('target','ROOTS',0)]:
            core.register_mesh_node(name,layer,64,10,0,money);core.assign_capability_privilege(name,'move')
        return core

    def test_all_four_supplied_examples(self):
        report=execute_ingress({**INPUT_TEMPLATE,'resource_governor':GOV,'central_bank_mesh':MESH,'world_banking':WORLD})
        self.assertEqual(report['status'],'COMPLETE');self.assertEqual(len(report['engines']),4)
        for result in report['engines'].values():self.assertTrue(result['resource_conserved'])
        souls=report['engines']['SoulsOverDigitsCore']
        transfer=souls['actions'][2]['output'];self.assertAlmostEqual(transfer['root_stabilizer_dividend'],553.5)
        self.assertAlmostEqual(transfer['net_transfer_units'],14446.5)
        self.assertAlmostEqual(transfer['receiver_balance_ru'],14946.5)
        gov=report['engines']['CentralBankResourceGovernor']['receipts'][0]
        self.assertEqual(gov['eco_floor_stabilizer_yield'],92250)
        self.assertEqual(report['engines']['CentralBankMeshController']['receipts'][0]['status'],'EVICTED_AND_REBALANCED')
        self.assertEqual(report['engines']['WorldGridCentralBankingCore']['receipts'][1]['eco_floor_dividend_yield'],36900)

    def test_token_sender_capability_and_replay(self):
        core=self.core();token=core.issue_capability_token('top','move',.9)
        before=core.snapshot()
        for sender,cap in [('root','move'),('top','wrong')]:
            self.assertEqual(core.route_christmas_tree_stream(sender,'target',10,token,cap)['status'],'CRITICAL_ERROR')
        self.assertEqual(before,core.snapshot())
        self.assertEqual(core.route_christmas_tree_stream('top','target',10,token,'move')['status'],'STREAM_SUCCESSFULLY_SANCTIFIED')
        self.assertEqual(core.route_christmas_tree_stream('top','target',10,token)['status'],'CRITICAL_ERROR')

    def test_expiry_revocation_tampering(self):
        core=self.core()
        with patch('souls_ingress.time.time',return_value=100):token=core.issue_capability_token('top','move',1)
        with patch('souls_ingress.time.time',return_value=400):self.assertEqual(core.route_christmas_tree_stream('top','target',1,token)['status'],'CRITICAL_ERROR')
        token=core.issue_capability_token('top','move',1);core.revoke_capability_token(token)
        self.assertEqual(core.route_christmas_tree_stream('top','target',1,token)['status'],'CRITICAL_ERROR')
        token=core.issue_capability_token('top','move',1)
        self.assertEqual(core.route_christmas_tree_stream('top','target',1,token[:-1]+'x')['status'],'CRITICAL_ERROR')

    def test_negative_nan_and_unknown_endpoints_do_not_mutate(self):
        core=self.core();before=core.snapshot();token=core.issue_capability_token('top','move',1)
        for value in (-1,0,float('nan'),float('inf'),True):
            self.assertEqual(core.route_christmas_tree_stream('top','target',value,token)['status'],'CRITICAL_ERROR')
        self.assertEqual(core.route_christmas_tree_stream('missing','target',1,token)['status'],'CRITICAL_ERROR')
        self.assertEqual(before,core.snapshot())

    def test_root_shortfall_and_dividend_conserve(self):
        core=self.core();before=core.snapshot()['total_ru']
        token=core.issue_capability_token('root','move',1)
        result=core.route_christmas_tree_stream('root','target',501,token)
        self.assertEqual(result['root_stabilizer_dividend'],0);self.assertEqual(core.global_root_reserve_ru,500)
        self.assertEqual(core.snapshot()['total_ru'],before)
        token=core.issue_capability_token('root','move',1);state=core.snapshot()
        self.assertEqual(core.route_christmas_tree_stream('root','target',1000,token)['status'],'INSUFFICIENT_LIQUIDITY')
        self.assertEqual(state,core.snapshot())

    def test_quarantine_idempotent_redemption_and_reassessment(self):
        core=self.core(0);core.node_registry['top']['deception_ratio']=8
        self.assertFalse(core._evaluate_node_purity('top'));self.assertEqual(core.global_root_reserve_ru,10000)
        self.assertFalse(core._evaluate_node_purity('top'));self.assertEqual(core.global_root_reserve_ru,10000)
        self.assertFalse(core.execute_redemption_handshake('top','no'))
        self.assertTrue(core.execute_redemption_handshake('top','sorry'))
        self.assertFalse(core._evaluate_node_purity('top'))
        core.node_registry['top']['deception_ratio']=0
        self.assertTrue(core.execute_redemption_handshake('top','sorry'));self.assertTrue(core._evaluate_node_purity('top'))

    def test_redemption_insufficient_reserve(self):
        core=self.core(0);core._trigger_quarantine_eviction('root','test');before=core.snapshot()
        self.assertFalse(core.execute_redemption_handshake('root','sorry'));self.assertEqual(before,core.snapshot())

    def test_token_serializes_colon_names_and_signature_verifies(self):
        core=self.core();core.register_mesh_node('node:one','TOP',64,10,0,10);core.assign_capability_privilege('node:one','cap:a')
        token=core.issue_capability_token('node:one','cap:a',1)
        result=core.route_christmas_tree_stream('node:one','target',1,token)
        expected=hmac.new(core.secret,result['seal_payload'].encode(),hashlib.sha256).hexdigest()
        self.assertEqual(result['cryptographic_seal'],'369-TREE-SIG:'+expected)

    def test_governor_rejects_invalid_and_preserves_total(self):
        core=CentralBankResourceGovernor(b'key',10)
        core.register_economic_sector('a','CANOPY',100);core.register_economic_sector('b','ROOTS',0)
        for value in (0,-1,float('nan')):self.assertEqual(core.execute_sovereign_settlement('a','b',value)['status'],'REJECTED')
        result=core.execute_sovereign_settlement('a','b',50)
        self.assertAlmostEqual(result['net_transfer_ru'],48.155)
        self.assertAlmostEqual(core.commons_reserve_ru+sum(n['liquidity_pool_ru'] for n in core.banking_sectors.values()),110)

    def test_mesh_checks_signature_scope_and_hardware(self):
        core=CentralBankMeshController(b'key')
        core.onboard_central_bank_node('a','CANOPY',64,10,0,1000)
        core.onboard_central_bank_node('b','ROOTS',20,10,0,0)
        self.assertEqual(core.process_mesh_settlement('a','b',10,'MOCK_SIG')['status'],'BLOCKED')
        token=core.sign_settlement('a','b',10)
        self.assertEqual(core.process_mesh_settlement('a','b',11,token)['status'],'BLOCKED')
        self.assertEqual(core.process_mesh_settlement('a','b',10,token)['status'],'ROUTING_REJECTED')
        core.mesh_nodes['b']['vram_gb']=32
        self.assertEqual(core.process_mesh_settlement('a','b',10,token)['status'],'SETTLEMENT_MESH_SANCTIFIED')
        self.assertEqual(core.process_mesh_settlement('a','b',10,token)['status'],'BLOCKED')

    def test_no_config_does_not_create_fake_nodes(self):
        self.assertEqual(execute_ingress('ordinary text')['status'],'AWAITING_INPUT')


class ModelTests(unittest.TestCase):
    def test_reconstruction_and_feedback_are_real_gradient_updates(self):
        model=NeuralModel([('engine',3)],hidden=3);x=[.2,-.5,.8];mask=[True]*3
        initial=model.forward(x,mask);g=model.g[:]
        for _ in range(100):model.train(x,mask)
        self.assertLess(model.forward(x,mask)['loss'],initial['loss']/3)
        self.assertNotEqual(model.g,g)
        before=model.forward(x,mask)['score']
        for _ in range(60):model.train(x,mask,1)
        self.assertGreater(model.forward(x,mask)['score'],before+.15)

    def test_backprop_gain_matches_numerical_derivative(self):
        model=NeuralModel([('a',2),('b',1)],hidden=2);x=[.2,-.8,.5];mask=[True]*3
        state=model.state();epsilon=1e-5
        def loss(delta):
            m=NeuralModel.from_state(state);m.g[0]+=delta;out=m.forward(x,mask)
            return out['loss']-math.log(out['score'])
        derivative=(loss(epsilon)-loss(-epsilon))/(2*epsilon)
        model.train(x,mask,1,rate=.001)
        self.assertAlmostEqual((state['g'][0]-model.g[0])/.001,derivative,places=7)

    def test_mask_prevents_missing_group_weight_update(self):
        model=NeuralModel([('present',2),('absent',2)])
        for _ in range(10):model.train([.2,.4,1,1],[True,True,False,False],.9)
        self.assertNotEqual(model.g[0],0);self.assertEqual(model.g[1],0)

    def test_save_restore_is_exact(self):
        model=NeuralModel([('x',2)]);model.train([.2,.8],[True,True],.9)
        restored=NeuralModel.from_state(json.loads(json.dumps(model.state())))
        self.assertEqual(restored.forward([.2,.8],[True,True]),model.forward([.2,.8],[True,True]))

    def test_invalid_target(self):
        for target in (True,float('nan'),-1,2):
            with self.assertRaises(ValueError):NeuralModel([('x',1)]).train([1],[True],target)

    def test_features_mask_missing_and_exclude_secret_numbers(self):
        report={'engines':{'SoulsOverDigitsCore':{'good':True,'secret':999,'resource':100}},'stages':[{'engine':'SoulsOverDigitsCore','status':'COMPLETE'}]}
        a=build_features({'text':'Learning binary'}, {'souls_ingress':report})
        report['engines']['SoulsOverDigitsCore']['secret']=1
        b=build_features({'text':'Learning binary'}, {'souls_ingress':report})
        self.assertEqual(a,b);self.assertIn('souls_ingress.SoulsOverDigitsCore',a[2]);self.assertNotIn('suite.UniversalKarmicEngine',a[2])


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.pipeline=DataPipeline(self.root/'hub.db');self.worker=NeuralLearning(self.pipeline.db_path)
    def tearDown(self):self.worker.stop();self.pipeline.stop();self.tmp.cleanup()
    def submit(self,payload,source='Neural manual'):
        job=self.pipeline.submit(source,str(time.time_ns()),payload)
        claimed=self.pipeline._claim();self.pipeline.process(claimed)
        return job

    def test_supplied_target_persists_and_duplicate_does_not_retrain(self):
        job=self.submit({'text':'ethical floor','neural':{'target':.9}})
        self.assertTrue(self.worker.process_next());first=self.worker.snapshot()
        self.assertEqual(first['targets'],1);self.assertGreater(first['latest']['prediction_after'],first['latest']['prediction_before'])
        self.worker.request(job);self.worker.process_next();self.assertEqual(self.worker.snapshot()['updates'],first['updates'])
        reopened=NeuralLearning(self.pipeline.db_path);self.assertEqual(reopened.model.state(),self.worker.model.state())
        self.assertEqual(reopened.detail(job)['target'],.9)

    def test_feedback_queue_and_snapshot_restore_preserve_history(self):
        job=self.submit({'text':'test'});self.worker.process_next();identity=self.worker.save_snapshot('before')
        state=self.worker.model.state();self.worker.add_feedback(job,0,'Prefer lower');self.worker.process_next()
        self.assertNotEqual(state,self.worker.model.state())
        self.worker.restore_snapshot(identity);self.assertEqual(state,self.worker.model.state())
        self.assertEqual(len(self.worker.detail(job)['feedback']),1);self.assertEqual(len(self.worker.snapshots()),2)

    def test_learning_switch_and_manual_run(self):
        self.worker.set_enabled(False);job=self.submit('binary values')
        self.assertFalse(self.worker.process_next());self.worker.request(job)
        self.assertTrue(self.worker.process_next());self.assertEqual(self.worker.snapshot()['observations'],1)

    def test_web_switch_and_provenance(self):
        self.worker.configure(web=False)
        self.submit([{'title':'Ethics','summary':'human ethics','url':'https://en.wikipedia.org/wiki/Ethics','revision':'12'}],'definitions')
        self.worker.process_next();self.assertEqual(self.worker.snapshot()['observations'],0)
        self.worker.configure(web=True)
        job=self.submit({'article':{'title':'Ethics','summary':'human ethics','url':'https://en.wikipedia.org/wiki/Ethics','revision':'13'},'neural':{'target':1}},'web research')
        self.worker.process_next();detail=self.worker.detail(job)
        self.assertIsNone(detail['target']);self.assertEqual(detail['web_sources'][0]['revision'],'13')

    def test_activity_switch_and_demo_exclusion(self):
        self.worker.configure(activity=False);self.submit({'host_memory':20,'mode':'LIVE'},'telemetry');self.worker.process_next()
        self.assertEqual(self.worker.snapshot()['observations'],0)
        self.worker.configure(activity=True);self.submit({'host_memory':20,'mode':'DEMO'},'telemetry');self.worker.process_next()
        self.assertEqual(self.worker.snapshot()['observations'],0)
        job=self.submit({'host_memory':20,'host_cpu':10,'mode':'LIVE'},'telemetry');self.worker.process_next()
        self.assertIn('activity.HostTelemetry',self.worker.detail(job)['observed_engines'])

    def test_model_output_cannot_supply_a_user_target(self):
        job=self.submit({'text':'model reply','neural':{'target':1}},'gemini output');self.worker.process_next()
        self.assertIsNone(self.worker.detail(job)['target'])

    def test_failed_commit_does_not_mutate_model(self):
        self.submit({'text':'new target','neural':{'target':1}})
        before=self.worker.model.state()
        with self.worker.connect() as conn:conn.execute("CREATE TRIGGER fail_learning BEFORE INSERT ON observations BEGIN SELECT RAISE(ABORT,'test failure'); END")
        with self.assertRaises(Exception):self.worker.process_next()
        self.assertEqual(before,self.worker.model.state())
        self.assertEqual(NeuralLearning(self.pipeline.db_path).model.state(),before)

    def test_cancellation_leaves_pending_for_resume(self):
        self.submit('pending');self.worker.stop_event.set();self.assertFalse(self.worker.process_next())
        self.assertEqual(self.worker.snapshot()['observations'],0)
        self.worker.stop_event.clear();self.assertTrue(self.worker.process_next())

    def test_ingress_receipt_is_persisted_and_becomes_four_weights(self):
        service=ContinuousSoulsModule(self.pipeline.db_path)
        job=self.submit({**INPUT_TEMPLATE,'resource_governor':GOV,'central_bank_mesh':MESH,'world_banking':WORLD})
        self.assertTrue(service.process_next());self.worker.process_next()
        self.assertEqual(len(service.detail(job)['engines']),4)
        self.assertEqual(sum(name.startswith('souls_ingress.') for name in self.worker.detail(job)['observed_engines']),4)

    def test_missing_enabled_result_waits_then_masks(self):
        service=ContinuousSoulsModule(self.pipeline.db_path);job=self.submit('waiting')
        self.assertFalse(self.worker.process_next())
        with self.worker.connect() as conn:conn.execute('UPDATE pending SET added=?',(time.time()-31,))
        self.assertTrue(self.worker.process_next());self.assertIn('souls_ingress',self.worker.detail(job)['unavailable'])


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name)
        self.pipeline=DataPipeline(root/'hub.db');self.store=LibraryStore(root/'library.db');self.calls=[]
        def fetch(topic):
            self.calls.append(topic)
            return dict(title=topic,summary='Definition of '+topic,url='https://en.wikipedia.org/wiki/'+topic.replace(' ','_'),revision='123',revised_at='2026-10-21',fetched_at=time.time())
        self.worker=WebResearch(self.store,self.pipeline,fetch)
    def tearDown(self):self.worker.stop();self.pipeline.stop();self.tmp.cleanup()

    def test_discovery_uses_public_concepts_without_full_prompt(self):
        topics=discover_topics({'text':'My email maintainer@example.invalid; neural hardware resource floor privacy','secret':'secret only'})
        self.assertIn('Artificial neural network',topics);self.assertIn('Resource allocation',topics)
        self.assertFalse(any('@' in topic or 'person' in topic for topic in topics))

    def test_automatic_research_ingests_real_fetcher_result(self):
        self.pipeline.submit('manual','a',{'text':'Geothermal energy research'})
        self.worker.process_next()
        self.assertIn('Geothermal energy',[r['topic'] for r in self.worker.topics()])
        receipt=self.worker.history()[0];self.assertEqual(receipt['status'],'FETCHED');self.assertTrue(receipt['job_id'])
        with database(self.pipeline.db_path) as conn:
            payload=json.loads(conn.execute('SELECT input_json FROM pipeline_jobs WHERE id=?',(receipt['job_id'],)).fetchone()[0])
        self.assertEqual(payload['article']['revision'],'123');self.assertIn('creativecommons',payload['license'])

    def test_pause_manual_and_pacing(self):
        self.worker.set_enabled(False);self.assertFalse(self.worker.process_next());self.assertEqual(self.calls,[])
        self.worker.request('Ethics');self.assertTrue(self.worker.process_next());self.assertEqual(self.calls,['Ethics'])
        self.worker.set_enabled(True);self.assertFalse(self.worker.process_next())

    def test_unchanged_reference_is_not_duplicated(self):
        self.worker.set_enabled(False)
        for _ in range(2):self.worker.request('Ethics');self.worker.process_next()
        self.assertEqual(len(self.worker.history()),2);self.assertIsNone(self.worker.history()[0]['job_id'])

    def test_network_failure_is_recorded_and_scheduled(self):
        self.worker.fetcher=lambda title:(_ for _ in ()).throw(OSError('Offline'))
        self.worker.process_next();row=self.worker.history()[0]
        self.assertEqual(row['status'],'ERROR');self.assertIsNone(row['job_id']);self.assertEqual(row['error'],'Offline')


class LearningUITests(unittest.TestCase):
    def test_page_manual_learning_feedback_context_and_old_pages(self):
        os.environ['QT_QPA_PLATFORM']='offscreen'
        from PySide6.QtWidgets import QApplication
        from app import GraphicalVirtueMatrixEngine
        from monitor import SystemBusMonitor
        from ai_context import context_choices
        application=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            w=GraphicalVirtueMatrixEngine(SystemBusMonitor(),folder,start_services=False)
            try:
                w.timer.stop();w.neural_toggle.setChecked(False)
                self.assertTrue(w.virtue_text.enabled);self.assertTrue(w.unified_core.enabled)
                w.navigate(25);self.assertEqual(w.pages.count(),27)
                w.neural_input.setPlainText('Learn this binary floor');w.neural_target_on.setChecked(True);w.run_neural_input()
                job=w.neural_pending;deadline=time.monotonic()+8
                while time.monotonic()<deadline and w.neural.detail(job) is None:application.processEvents();time.sleep(.02)
                self.assertIsNotNone(w.neural.detail(job));w.neural_last_render=0;w.render_neural()
                self.assertEqual(w.neural_selected,job);self.assertIn('Learned and saved',w.neural_input_status.text())
                self.assertIn('observed_engines',w.neural_detail.toPlainText())
                w.feedback_score.setValue(.2);w.teach_neural();deadline=time.monotonic()+5
                while time.monotonic()<deadline and w.neural.snapshot()['feedback']<1:application.processEvents();time.sleep(.02)
                self.assertEqual(w.neural.snapshot()['feedback'],1)
                choices=dict(context_choices(w.engine_state()))
                for key in ('neural_learning','web_research','souls_ingress'):self.assertIn(key,choices)
                self.assertIn('virtue_text',choices);self.assertIn('neural_learning',w.extension_export())
                w.learn_web.setChecked(False);w.learn_activity.setChecked(False)
                self.assertFalse(w.neural.web);self.assertFalse(w.neural.activity)
                self.assertTrue(w.web_research.enabled)
                w.save_neural_snapshot();self.assertEqual(w.neural_snapshots.count(),1)
                for i in range(27):w.navigate(i)
            finally:w.close()

    def test_research_manual_ui_fetch_and_copyable_ledger_examples(self):
        os.environ['QT_QPA_PLATFORM']='offscreen'
        from PySide6.QtWidgets import QApplication
        from app import GraphicalVirtueMatrixEngine
        from monitor import SystemBusMonitor
        from neural_page import examples
        application=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            w=GraphicalVirtueMatrixEngine(SystemBusMonitor(),folder,start_services=False)
            try:
                w.timer.stop();w.web_research.set_enabled(False);w.navigate(25);w.learning_tabs.setCurrentIndex(2)
                w.web_research.fetcher=lambda topic:dict(title=topic,summary='Complete definition',url='https://en.wikipedia.org/wiki/Ethics',revision='1',revised_at='',fetched_at=time.time())
                w.research_topic.setText('Ethics');w.request_research();deadline=time.monotonic()+5
                while time.monotonic()<deadline and not w.web_research.history():application.processEvents();time.sleep(.02)
                w.neural_last_render=0;w.render_neural();self.assertIn('Complete definition',w.research_output.toPlainText())
                w.souls_input.setPlainText(json.dumps(examples()));w.run_souls_input();job=w.neural_pending;deadline=time.monotonic()+8
                while time.monotonic()<deadline and not w.souls_ingress.ready(job):application.processEvents();time.sleep(.02)
                w.show_souls_result();self.assertIn('CentralBankResourceGovernor',w.souls_result.toPlainText())
                self.assertEqual(len(w.souls_ingress.snapshot()['last_ledger']['engines']),4)
            finally:w.close()


if __name__=='__main__':unittest.main()
