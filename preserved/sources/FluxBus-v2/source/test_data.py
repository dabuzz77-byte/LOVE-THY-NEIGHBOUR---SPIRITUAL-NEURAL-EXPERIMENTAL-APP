import io
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
from cloud_ai import KeyVault,generate,list_models,compose_input,request_json
from hub import LocalInferenceHubServer,database
from pipeline import DataPipeline,parse_content
from routing import run_model
from tcp_ingestion import TCPTargetIngestionAdapter,TCPPacketGrammarParser,parse_target


def wait_for(predicate,timeout=5):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate():return
        time.sleep(.02)
    raise AssertionError("Timed out waiting for worker")


class TCPTests(unittest.TestCase):
    def test_actual_large_unicode_roundtrip_and_unique_packets(self):
        with tempfile.TemporaryDirectory() as folder:
            hub=LocalInferenceHubServer(port=0,db_path=Path(folder)/"hub.db")
            self.assertTrue(hub.start_listener_bus())
            client=TCPTargetIngestionAdapter(target_port=hub.port,db_path=Path(folder)/"client.db")
            try:
                content=json.dumps({"input":"Binary → ternary "*300,"output":"preserve"},ensure_ascii=False)
                first=client.transmit_and_ingest_payload("Google AI",content,"evil","source")
                second=client.transmit_and_ingest_payload("Google AI",content,"good","source")
                self.assertTrue(first["delivery_confirmed"]);self.assertTrue(second["delivery_confirmed"])
                self.assertNotEqual(first["packet_id"],second["packet_id"])
                self.assertEqual(hub.rows()[0]["context_anchor"],content)
                self.assertEqual(client.stats()["confirmed"],2)
                self.assertIn("AUTOMATIC_NOT_GATE",TCPPacketGrammarParser(client.db_path).compile_network_grammar_signature())
            finally:hub.terminate()

    def test_failure_is_durable_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            client=TCPTargetIngestionAdapter(db_path=Path(folder)/"db")
            with patch("tcp_ingestion.socket.create_connection",side_effect=ConnectionRefusedError("offline")):
                result=client.transmit_and_ingest_payload("n","data","evil")
            self.assertEqual(result["status"],"FAILED");self.assertIsNone(result["bridge_gate"])
            self.assertEqual(client.rows()[0]["delivery_status"],"FAILED")
            self.assertEqual(client.rows()[0]["corrected_bit"],1)

    def test_fragmented_response_and_mismatched_echo(self):
        class Socket:
            def __init__(self,parts):self.parts=iter(parts)
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def settimeout(self,*args):pass
            def sendall(self,*args):pass
            def recv(self,*args):return next(self.parts,b"")
        with tempfile.TemporaryDirectory() as folder:
            client=TCPTargetIngestionAdapter(db_path=Path(folder)/"db")
            with patch("tcp_ingestion.socket.create_connection",return_value=Socket([b'{"status":',b'"ACK"}'])):
                self.assertTrue(client.transmit_and_ingest_payload("n","text","good")["delivery_confirmed"])
            reply=json.dumps({"status":"ACK","node":{"node_id":"wrong","raw_state":"good"}}).encode()
            with patch("tcp_ingestion.socket.create_connection",return_value=Socket([reply])):
                self.assertEqual(client.transmit_and_ingest_payload("n","text","good")["status"],"UNCONFIRMED")

    def test_original_schema_migration_preserves_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"db"
            with database(path) as conn:
                conn.execute("CREATE TABLE network_ingested_logs(packet_id TEXT PRIMARY KEY,raw_payload TEXT,corrected_bit INTEGER,network_address TEXT,timestamp TEXT)")
                conn.execute("INSERT INTO network_ingested_logs VALUES('original','{}',1,'127.0.0.1:9999','yesterday')")
            client=TCPTargetIngestionAdapter(db_path=path)
            self.assertEqual(client.rows()[0]["delivery_status"],"LEGACY_UNVERIFIED")
            self.assertEqual(client.stats()["confirmed"],0)

    def test_target_typo_and_invalid_port(self):
        self.assertEqual(parse_target("127:0.0.1.9999"),("127.0.0.1",9999))
        with self.assertRaises(ValueError):parse_target("localhost:99999")


class PipelineTests(unittest.TestCase):
    def test_manual_queue_deduplicates_and_runs_all_stages(self):
        with tempfile.TemporaryDirectory() as folder:
            engine=DataPipeline(Path(folder)/"db",auto=False);engine.start()
            payload={"state_reg":"good","evaluate":"evil","can":False,"cannot":True}
            identity=engine.submit("test","one",json.dumps(payload),{"route":run_model()})
            self.assertIsNone(engine.submit("test","one",json.dumps(payload)))
            time.sleep(.1);self.assertEqual(engine.detail(identity)["status"],"QUEUED")
            engine.run_pending();wait_for(lambda:engine.detail(identity)["status"]=="COMPLETE")
            result=json.loads(engine.detail(identity)["result_json"]);engine.stop()
            self.assertEqual(len(result["stages"]),7);self.assertEqual(len(result["engines"]),9)
            self.assertTrue(result["audit"]["result"]["can"]);self.assertFalse(result["audit"]["result"]["cannot"])
            for row in result["binary_ternary"]:
                self.assertEqual(sum(t*3**i for i,t in enumerate(reversed(row["trits"]))),row["decimal"])

    def test_nested_history_json_and_code_are_processed(self):
        record={"raw_input":'{"state":"evil","can":false}',"raw_output":"def keep():\n    return False"}
        parsed=parse_content(record)
        self.assertFalse(parsed["value"]["raw_input"]["can"])
        self.assertEqual(parsed["embedded_sources"][1]["functions"],["keep"])
        self.assertIsInstance(record["raw_input"],str)

    def test_source_code_retained_without_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/"marker"
            source=f"from pathlib import Path\nPath({str(target)!r}).write_text('executed')"
            parsed=parse_content(source)
            self.assertEqual(parsed["kind"],"Python source");self.assertEqual(parsed["value"],source)
            self.assertFalse(target.exists())

    def test_resume_interrupted_and_manual_rerun(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"db";first=DataPipeline(path,False)
            identity=first.submit("test","id","hello")
            with database(path) as conn:conn.execute("UPDATE pipeline_jobs SET status='RUNNING'")
            second=DataPipeline(path,False);self.assertEqual(second.detail(identity)["status"],"QUEUED")
            second.run_selected(identity);second.start()
            wait_for(lambda:second.detail(identity)["status"]=="COMPLETE");second.stop()

    def test_supplied_engine_register_input_affects_result(self):
        from engines import run_engine_suite
        data={"engine_inputs":{"UniversalKrakenReleaseEngine":{"state_registers":{"bit_array_separate":1}}}}
        result=run_engine_suite(payload=data)[1]
        self.assertEqual(result["output"]["bit_array_separate"],0)
        self.assertEqual(result["input_registers"],["state_registers"])
        self.assertEqual(data["engine_inputs"]["UniversalKrakenReleaseEngine"]["state_registers"]["bit_array_separate"],1)


class CloudTests(unittest.TestCase):
    def test_windows_keys_encrypt_persist_and_delete(self):
        with tempfile.TemporaryDirectory() as folder:
            vault=KeyVault(folder)
            for provider in ("gemini","openai"):
                secret="test-key-not-a-real-credential-"+provider
                vault.save(provider,secret)
                self.assertEqual(KeyVault(folder).load(provider),secret)
                self.assertNotIn(secret.encode(),(Path(folder)/(provider+".key.dpapi")).read_bytes())
                vault.delete(provider);self.assertEqual(vault.load(provider),"")

    def test_gemini_state_request_and_text_response(self):
        response={"candidates":[{"content":{"parts":[{"text":"thought","thought":True},{"text":"visible"}]},"finishReason":"STOP"}],"usageMetadata":{"totalTokenCount":5}}
        def opener(request,timeout):
            self.assertEqual(request.get_header("X-goog-api-key"),"test-secret")
            self.assertNotIn("test-secret",request.full_url)
            text=json.loads(request.data)["contents"][0]["parts"][0]["text"]
            self.assertIn('"can": false',text)
            return io.BytesIO(json.dumps(response).encode())
        with patch("cloud_ai.urllib.request.urlopen",side_effect=opener):
            result=generate("gemini","test-secret","gemini-test","Read engine",{"can":False})
        self.assertEqual(result["output"],"visible");self.assertTrue(result["state_included"])

    def test_openai_responses_api_and_actual_output(self):
        raw={"status":"completed","id":"resp_test","output":[{"type":"reasoning","summary":[]},{"type":"message","content":[{"type":"output_text","text":"read state"}]}],"usage":{"total_tokens":9}}
        def opener(request,timeout):
            self.assertEqual(request.full_url,"https://api.openai.com/v1/responses")
            self.assertEqual(request.get_header("Authorization"),"Bearer test-secret")
            body=json.loads(request.data);self.assertFalse(body["store"]);self.assertIn('"bit": 1',body["input"][-1]["content"])
            return io.BytesIO(json.dumps(raw).encode())
        with patch("cloud_ai.urllib.request.urlopen",side_effect=opener):
            result=generate("openai","test-secret","gpt-test","Read",{"bit":1})
        self.assertEqual(result["output"],"read state");self.assertEqual(result["request_id"],"resp_test")

    def test_http_errors_redact_key_and_do_not_report_success(self):
        error=urllib.error.HTTPError("https://example.com",401,"Unauthorized",{},io.BytesIO(b'{"error":{"message":"invalid test-secret"}}'))
        with patch("cloud_ai.urllib.request.urlopen",side_effect=error):
            with self.assertRaises(RuntimeError) as caught:request_json("https://example.com","test-secret","openai")
        self.assertNotIn("test-secret",str(caught.exception));self.assertIn("401",str(caught.exception))

    def test_models_and_no_state_option(self):
        pages=[{"models":[{"name":"models/text","supportedGenerationMethods":["generateContent"]}],"nextPageToken":"next"},
               {"models":[{"name":"models/embed","supportedGenerationMethods":["embedContent"]}]}]
        with patch("cloud_ai.request_json",side_effect=pages):self.assertEqual(list_models("gemini","test"),["text"])
        self.assertEqual(compose_input("plain",None),"plain")


class DataUITests(unittest.TestCase):
    def test_both_cloud_pages_save_key_and_ingest_worker_response(self):
        os.environ["QT_QPA_PLATFORM"]="offscreen"
        from PySide6.QtWidgets import QApplication
        import app
        from monitor import SystemBusMonitor
        application=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            monitor=SystemBusMonitor();monitor.sample_once()
            window=app.GraphicalVirtueMatrixEngine(monitor,folder,start_services=False)
            try:
                window.pipeline_auto.setChecked(False)
                for provider in ("gemini","openai"):
                    controls=window.cloud_controls[provider]
                    controls["key"].setText("dummy-not-a-live-key")
                    controls["input"].setPlainText("Read current state")
                    def reply(service,key,model,prompt,state,history=None,context_options=None):
                        self.assertEqual(service,provider);self.assertIn("latest_pipeline",state)
                        return {"provider":service,"model":model,"input":compose_input(prompt,state),
                                "output":"Verified worker result","status":"completed","usage":{},"state_included":True}
                    with patch("data_pages.generate",side_effect=reply):
                        window.send_cloud(provider)
                        deadline=time.monotonic()+3
                        while provider in window.cloud_busy and time.monotonic()<deadline:
                            application.processEvents();window.tick_data_pages();time.sleep(.02)
                    self.assertEqual(controls["output"].toPlainText(),"Verified worker result")
                    self.assertTrue(controls["send"].isEnabled())
                    self.assertEqual(KeyVault(Path(folder)/"credentials").load(provider),"dummy-not-a-live-key")
                window.tick_data_pages()
                self.assertEqual({r["source_kind"] for r in window.history_engine.rows()},{"gemini API","openai API"})
                self.assertGreaterEqual(window.pipeline.stats()["QUEUED"],4)
                self.assertNotIn("dummy-not-a-live-key",json.dumps(window.extension_export()))
            finally:window.close()

    def test_ingest_transmit_pipeline_cloud_state_and_prayer(self):
        os.environ["QT_QPA_PLATFORM"]="offscreen"
        from PySide6.QtWidgets import QApplication
        import app
        from monitor import SystemBusMonitor
        application=QApplication.instance() or QApplication([]);app.load_fonts(application)
        with tempfile.TemporaryDirectory() as folder:
            monitor=SystemBusMonitor();monitor.sample_once()
            window=app.GraphicalVirtueMatrixEngine(monitor,folder,start_services=False)
            window.hub.port=0;self.assertTrue(window.hub.start_listener_bus())
            try:
                self.assertEqual(window.pages.count(),27)
                window.pipeline_auto.setChecked(False)
                window.tcp_target.setText(f"127.0.0.1:{window.hub.port}")
                window.google_input.setPlainText('{"state_reg":"good","evaluate":"evil","can":false}')
                window.google_output.setPlainText("The original answer")
                window.ingest_google(True);window.tick_data_pages()
                deadline=time.monotonic()+4
                while not window.latest_packet and time.monotonic()<deadline:
                    application.processEvents();window.tick_data_pages();time.sleep(.02)
                self.assertTrue(window.latest_packet["delivery_confirmed"])
                record=json.loads(window.hub.rows()[0]["context_anchor"])["record"]
                self.assertEqual(record["raw_output"],"The original answer")
                window.run_pipeline_pending()
                wait_for(lambda:window.pipeline.stats().get("COMPLETE",0)>0)
                window.tick_data_pages();self.assertEqual(len(window.latest_pipeline["engines"]),9)
                for provider in ("gemini","openai"):
                    controls=window.cloud_controls[provider];controls["key"].setText("private-test-key")
                    controls["input"].setPlainText("Read the live engine")
                    window.preview_cloud(provider);preview=controls["preview"].toPlainText()
                    self.assertIn("process_telemetry",preview);self.assertIn("engines",preview)
                    self.assertNotIn("private-test-key",preview)
                    controls["include"].setChecked(False);window.preview_cloud(provider)
                    self.assertEqual(controls["preview"].toPlainText(),"Read the live engine")
                window.update_summary();summary=window.summary_view.toPlainText()
                self.assertIn("Stated goal",summary);self.assertIn("Our Father in heaven,",summary)
                self.assertIn("now and for ever.",summary)
            finally:window.close()


if __name__=="__main__":unittest.main(verbosity=2)
