import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from hub import database, LocalInferenceHubServer
from mesh_engine import (SessionBridgeController, PrivacyPreservingMeshGateway, IntegratedGlobalMeshEngine,
                         prepare_mesh_run, redact_text, virtue_score)
from mesh_transport import encoded, receive_mesh_frame, send_mesh_packet
from mesh_worker import ContinuousMeshModule
from pipeline import DataPipeline


class MeshLogicTests(unittest.TestCase):
    def test_supplied_example_floors_reserve_and_missing_vector(self):
        engine=IntegratedGlobalMeshEngine(60,1500)
        for name,value in (("End_User_Data_Layer",25),("Gateway_Proxy_Layer",45),("Core_Substrate_Mesh",95)):
            engine.register_mesh_node(name,value)
        result=engine.compile_global_run("user maintainer@example.invalid; 1=1",{"human_utility":1,"open_transparency":1,"serves_opaque_monetary_toll":0},dispatch=False)
        self.assertEqual(result["RESERVE_POOL_BALANCE"],1450)
        self.assertEqual(result["CORRECTED_SUBSTRATE_PARITY_VECTOR"],[0,0,0])
        self.assertEqual([row["REINFORCEMENT_ALLOCATED"] for row in result["FURTHEST_REACHES_ECO_FLOOR_ADJUSTMENTS"].values()],[35,15,0])
        self.assertEqual(list(engine.nodes.values()),[60,60,95])
        self.assertTrue(result["MODEL_EQUILIBRIUM"])
        self.assertEqual(result["GLOBAL_TELEMETRY"]["CORE_MESH_STATUS"],"LOCAL_DELIVERY_PENDING")
        self.assertEqual(result["GATEWAY_REPORT"]["MESH_INTEGRATION_ARRAY"],[1,1,0,1])
        self.assertNotIn("maintainer@example.invalid",result["ANONYMOUS_DATA_STREAM"])

    def test_reserve_exhaustion_and_repeated_pass_conserve_balances(self):
        engine=IntegratedGlobalMeshEngine(60,20);engine.register_mesh_node("near",55);engine.register_mesh_node("low",10)
        report=engine.execute_furthest_reaches_floor_leveling()
        self.assertEqual(engine.nodes,{"near":55,"low":30});self.assertEqual(engine.system_reserve_pool,0)
        self.assertFalse(report["low"]["STABILIZED"]);self.assertEqual(report["near"]["SHORTFALL"],5)
        self.assertTrue(all(r["REINFORCEMENT_ALLOCATED"]==0 for r in engine.execute_furthest_reaches_floor_leveling().values()))
        with self.assertRaises(ValueError):IntegratedGlobalMeshEngine(global_reserve=-1)
        with self.assertRaises(ValueError):engine.register_mesh_node("nan",float('nan'))

    def test_metric_aliases_and_threshold_keep_original_formula(self):
        self.assertAlmostEqual(virtue_score({}),.8)
        self.assertAlmostEqual(virtue_score({"human_utility_score":.2,"open_source_verifiable":.1,"arbitrary_toll_debt":.9}),-.23)
        self.assertAlmostEqual(virtue_score({"human_utility":.2,"open_transparency":.1,"serves_opaque_monetary_toll":.9}),-.23)
        gateway=PrivacyPreservingMeshGateway()
        self.assertTrue(gateway.evaluate_gateway_virtue({"human_utility":1,"open_transparency":0}))
        with patch('mesh_engine.send_mesh_packet') as send:
            report=gateway.dispatch_to_core_mesh("held",{"human_utility":0,"open_transparency":0})
        send.assert_not_called();self.assertEqual(report["MESH_INTEGRATION_ARRAY"],[1,1,0,0])
        self.assertEqual(report["ROUTING_TELEMETRY"]["STATUS"],"GATEWAY_HOLD_REFACTOR")

    def test_redaction_email_variants_and_literal_identifiers(self):
        cleaned,info=redact_text("maintainer@example.invalid, maintainer@example.invalid; account[42] Ω",["account[42]"])
        self.assertEqual(cleaned.count('[REDACTED_IDENTITY_DATA]'),3)
        self.assertEqual(info["email_matches"],2);self.assertEqual(info["listed_identifier_matches"],1)
        self.assertTrue(cleaned.endswith("Ω"))
        a=PrivacyPreservingMeshGateway().sanitize_and_anonymize_payload("no address")
        b=PrivacyPreservingMeshGateway().sanitize_and_anonymize_payload("no address")
        self.assertNotEqual(a["ANONYMOUS_ROUTING_TAG"],b["ANONYMOUS_ROUTING_TAG"])

    def test_session_bridge_keeps_vector_and_reports_configured_scope(self):
        report=SessionBridgeController("session-actual").execute_bridge_evaluation("BRIDGE ALL",.8)
        self.assertEqual(report["BOUNDARY_REALIGNMENT_VECTOR"],[1,1,1])
        self.assertFalse(report["CROSS_SESSION_MUTABILITY_ACTIVE"])
        self.assertEqual(report["PRIMARY_SESSION_ID"],"session-actual")
        self.assertIn("local",report["CAPABILITY_BASIS"])
        self.assertEqual(report["VIRTUE_PASS_STATUS"],"VERIFIED_USER_ALIGNMENT")

    def test_long_bitstreams_redact_without_blocking(self):
        # A child timeout makes the original quadratic scan fail promptly without
        # freezing the whole suite while its regex holds the Python thread lock.
        code = """
from mesh_engine import redact_text
bits = '10' * 500000
source = bits + ' maintainer@example.invalid ' + bits + '@invalid ' + bits
cleaned, info = redact_text(source)
assert cleaned == bits + ' [REDACTED_IDENTITY_DATA] ' + bits + '@invalid ' + bits
assert info['email_matches'] == 1
"""
        result = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parent,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_parity_does_not_spend_reserve(self):
        engine=IntegratedGlobalMeshEngine(container_delusion_bits=[1,2,1]);engine.register_mesh_node("node",5)
        with self.assertRaises(ValueError):engine.compile_global_run("input",{},dispatch=False)
        self.assertEqual(engine.nodes["node"],5);self.assertEqual(engine.system_reserve_pool,2000)

    def test_unknown_resources_and_exact_ternary(self):
        report=prepare_mesh_run("actual input",'tcp://127.0.0.1:9999','local')
        self.assertIsNone(report["RESOURCE_FLOOR_STABLE"])
        self.assertEqual(report["FURTHEST_REACHES_ECO_FLOOR_ADJUSTMENTS"],{})
        self.assertEqual(report["DECIMAL"],sum(t*3**i for i,t in enumerate(reversed(report["BALANCED_TERNARY"])) ))


class MeshTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'hub.db'
        self.hub=LocalInferenceHubServer(port=0,db_path=self.path)
        self.assertTrue(self.hub.start_listener_bus())

    def tearDown(self):
        self.hub.terminate();self.temp.cleanup()

    def test_real_gateway_ack_matches_and_stores_redacted_payload(self):
        gateway=PrivacyPreservingMeshGateway(f'tcp://127.0.0.1:{self.hub.port}')
        result=gateway.dispatch_to_core_mesh('maintainer@example.invalid; maintain floor',{})
        self.assertEqual(result['ROUTING_TELEMETRY']['STATUS'],'DISPATCH_SUCCESS')
        self.assertEqual(result['MESH_INTEGRATION_ARRAY'],[1,1,1,1])
        with database(self.path) as conn:
            stored=conn.execute('SELECT payload_json FROM mesh_receipts').fetchone()[0]
        self.assertNotIn('maintainer@example.invalid',stored)
        self.assertIn('[REDACTED_IDENTITY_DATA]',stored)
        self.assertEqual(self.hub.drain_events(),[])
        self.assertEqual(self.hub.rows(),[])

    def test_large_unicode_packet_complete_and_retries_idempotent(self):
        packet={'cleaned_payload':'α🙂 payload '+('0 [REDACTED_IDENTITY_DATA] Ω🙂\n'*65000)}
        result=send_mesh_packet(packet,'large-packet',port=self.hub.port,timeout=8)
        self.assertTrue(result['delivery_confirmed']);self.assertGreater(result['parts'],1)
        repeated=send_mesh_packet(packet,'large-packet',port=self.hub.port,timeout=8)
        self.assertTrue(repeated['duplicate'])
        with database(self.path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM mesh_receipts').fetchone()[0],1)
            self.assertEqual(json.loads(conn.execute('SELECT payload_json FROM mesh_receipts').fetchone()[0]),packet)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM mesh_parts').fetchone()[0],0)

    def test_partial_transfer_resumes_and_changed_part_is_rejected(self):
        raw=encoded({'text':'abc Ω🙂'}).encode('utf8');digest=hashlib.sha256(raw).hexdigest();cut=len(raw)//2
        first={'type':'flux_mesh_chunk','routing_tag':'partial','sha256':digest,'part':0,'total':2,'data':base64.b64encode(raw[:cut]).decode()}
        self.assertEqual(receive_mesh_frame(first,self.path)['status'],'PART_ACK')
        self.assertEqual(receive_mesh_frame(first,self.path)['received_parts'],1)
        with self.assertRaises(ValueError):receive_mesh_frame({**first,'data':base64.b64encode(b'changed').decode()},self.path)
        last={**first,'part':1,'data':base64.b64encode(raw[cut:]).decode()}
        self.assertEqual(receive_mesh_frame(last,self.path)['status'],'ACK')
        with database(self.path) as conn:self.assertEqual(conn.execute('SELECT received_bytes FROM mesh_receipts').fetchone()[0],len(raw))

    def test_wrong_ack_is_not_reported_connected(self):
        with patch('mesh_transport.receive_mesh_frame',return_value={'status':'ACK','routing_tag':'wrong','sha256':'0'*64,'received_bytes':1}):
            result=send_mesh_packet({'text':'actual'},'right',port=self.hub.port)
        self.assertFalse(result['delivery_confirmed']);self.assertEqual(result['status'],'UNCONFIRMED')

    def test_failed_connection_does_not_return_success(self):
        self.hub.terminate()
        report=PrivacyPreservingMeshGateway(f'tcp://127.0.0.1:{self.hub.port}').dispatch_to_core_mesh('actual',{})
        self.assertEqual(report['MESH_INTEGRATION_ARRAY'][2],0)
        self.assertNotEqual(report['ROUTING_TELEMETRY']['STATUS'],'DISPATCH_SUCCESS')


class MeshWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'hub.db'
        self.pipeline=DataPipeline(self.path,False);self.hub=LocalInferenceHubServer(port=0,db_path=self.path)
        self.assertTrue(self.hub.start_listener_bus())
        self.module=ContinuousMeshModule(self.path,lambda:(self.hub.host,self.hub.port))

    def tearDown(self):
        self.module.stop();self.hub.terminate();self.pipeline.stop();self.temp.cleanup()

    def test_default_enabled_preserved_original_and_no_self_ingestion(self):
        self.assertTrue(self.module.enabled)
        raw='Protect maintainer@example.invalid; uphold floor'
        job=self.pipeline.submit('input','one',raw)
        self.assertTrue(self.module.process_next())
        self.assertEqual(self.module.detail(job)['status'],'ACK')
        self.assertEqual(json.loads(self.pipeline.detail(job)['input_json']),raw)
        self.assertEqual(self.pipeline.stats(),{'QUEUED':1})
        self.assertEqual(self.hub.drain_events(),[])
        self.assertFalse(self.module.process_next())
        self.assertTrue(self.module.detail(job)['result']['SESSION_BRIDGE']['LOCAL_HUB_DELIVERY_CONFIRMED'])

    def test_paused_manual_and_restart_then_resume(self):
        self.module.set_enabled(False);self.module.set_identifiers(['account42'])
        first=self.pipeline.submit('input','one','account42 floor')
        self.assertFalse(self.module.process_next())
        self.module.request(first);self.module.process_next()
        self.assertEqual(self.module.detail(first)['status'],'ACK')
        second=self.pipeline.submit('input','two','new data')
        other=ContinuousMeshModule(self.path,lambda:(self.hub.host,self.hub.port))
        self.assertFalse(other.enabled);self.assertEqual(other.settings['identifiers'],['account42'])
        self.assertEqual(other.session_id,self.module.session_id)
        self.assertFalse(other.process_next());other.set_enabled(True)
        while other.process_next():pass
        self.assertEqual(other.detail(second)['status'],'ACK')
        with database(self.path) as conn:self.assertEqual(conn.execute('SELECT COUNT(*) FROM mesh_receipts').fetchone()[0],2)

    def test_lost_ack_and_restart_retry_does_not_duplicate_receipt(self):
        job=self.pipeline.submit('input','one','actual payload')
        def lose_ack(packet,tag,host,port,**kwargs):
            delivered=send_mesh_packet(packet,tag,host,port,**kwargs)
            self.assertTrue(delivered['delivery_confirmed'])
            return {'status':'UNCONFIRMED','delivery_confirmed':False,'error':'ack lost'}
        with patch('mesh_worker.send_mesh_packet',side_effect=lose_ack):self.module.process_next()
        original=self.module.detail(job)['result']['GLOBAL_TELEMETRY']['ROUTING_TOKEN']
        other=ContinuousMeshModule(self.path,lambda:(self.hub.host,self.hub.port));other.request(job);other.process_next()
        result=other.detail(job)
        self.assertEqual(result['status'],'ACK');self.assertEqual(result['attempts'],2)
        self.assertEqual(result['result']['GLOBAL_TELEMETRY']['ROUTING_TOKEN'],original)
        with database(self.path) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM mesh_receipts').fetchone()[0],1)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM mesh_attempts').fetchone()[0],2)

    def test_manual_failure_paused_makes_only_one_attempt_until_requested(self):
        self.module.set_enabled(False);job=self.pipeline.submit('input','one','text');self.module.request(job)
        with patch('mesh_worker.send_mesh_packet',return_value={'status':'FAILED','delivery_confirmed':False,'error':'offline'}) as send:
            self.module.process_next()
            with database(self.path) as conn:conn.execute('UPDATE mesh_outbox SET next_attempt=0')
            self.assertFalse(self.module.process_next())
            self.assertEqual(send.call_count,1)
            self.module.request(job);self.module.process_next();self.assertEqual(send.call_count,2)

    def test_bad_input_and_user_score_hold_keep_data_and_allow_next_input(self):
        bad=self.pipeline.submit('input','bad',{'mesh':{'nodes':{'bad':float('nan')}}})
        held=self.pipeline.submit('input','hold',{'gateway_metrics':{'human_utility':0,'open_transparency':0}})
        good=self.pipeline.submit('input','good','hardware floor')
        while self.module.process_next():pass
        self.assertEqual(self.module.detail(bad)['status'],'ERROR')
        self.assertEqual(self.module.detail(held)['status'],'HOLD')
        self.assertEqual(self.module.detail(good)['status'],'ACK')

    def test_idle_query_is_indexed_and_does_not_decode_unrelated_output(self):
        from payload_storage import MAGIC
        job=self.pipeline.submit('input','one','payload')
        with database(self.path) as conn:
            plan=[r[3] for r in conn.execute('EXPLAIN QUERY PLAN '+self.module.MANUAL_SQL)]
            self.assertFalse(any('SCAN p' in p for p in plan),plan)
            conn.execute('UPDATE pipeline_jobs SET result_json=? WHERE id=?',(MAGIC+b'x'*32,job))
        self.module.request(job);self.module.process_next()
        self.assertEqual(self.module.detail(job)['status'],'ACK')

    def test_stopped_owned_hub_does_not_send_to_another_port_owner(self):
        self.module.ready=lambda:False
        job=self.pipeline.submit('input','one','actual input')
        with patch('mesh_worker.send_mesh_packet') as sender:self.module.process_next()
        sender.assert_not_called()
        self.assertEqual(self.module.detail(job)['status'],'RETRY')
        self.assertIn('local hub is stopped',self.module.detail(job)['error'])


class MeshUITests(unittest.TestCase):
    def test_preview_manual_delivery_toggle_copy_and_conversations(self):
        os.environ['QT_QPA_PLATFORM']='offscreen'
        from PySide6.QtWidgets import QApplication
        from app import GraphicalVirtueMatrixEngine
        from monitor import SystemBusMonitor
        application=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            window=GraphicalVirtueMatrixEngine(SystemBusMonitor(),folder,start_services=False)
            window.hub.port=0;window.hub.start_listener_bus()
            try:
                identity,_=window.conversations.snapshot('openai')
                window.conversations.complete('openai',identity,'Preserve memory','Remembered','test')
                self.assertEqual(window.pages.count(),27);window.mesh_toggle.setChecked(False);window.navigate(20)
                window.mesh_input.setPlainText('maintainer@example.invalid; hardware floor');window.preview_mesh()
                self.assertIn('"status": "PREVIEW"',window.mesh_result.toPlainText())
                with database(window.hub.db_path) as conn:self.assertEqual(conn.execute('SELECT COUNT(*) FROM mesh_receipts').fetchone()[0],0)
                window.send_mesh_input();deadline=time.monotonic()+8
                while time.monotonic()<deadline and window.mesh_module.snapshot()['latest'].get('status')!='ACK':
                    application.processEvents();time.sleep(.02)
                window.render_mesh_page()
                self.assertIn('"status": "ACK"',window.mesh_result.toPlainText())
                self.assertIsNotNone(window.mesh_sessions.currentData())
                self.assertNotIn('maintainer@example.invalid',window.mesh_result.toPlainText())
                self.assertIn('mesh_gateway',window.engine_state())
                self.assertEqual(len(window.conversations.snapshot('openai')[1]),2)
                saved=ContinuousMeshModule(window.hub.db_path,lambda:(window.hub.host,window.hub.port))
                self.assertFalse(saved.enabled)
            finally:window.close();application.processEvents()


if __name__=='__main__':unittest.main()
