import json
import math
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from boolean_text import invert_boolean_text
from hub import database
from live_audit import (SystemNode, FloorOptimizationEngine, ResponseImprintEngine,
    BoundaryImprintEngine, VirtueAssessmentEngine, LogicImprintMatrixEngine,
    ProductionPipelineController, verify_live_state, interpret_unrestrict_bias,
    CoreRegistry, CoreFloorEngine, CoreImprintEngine, CoreInversionOperator,
    SubstrateHardwareAuditor, evaluate_input, ContinuousAuditModule)
from pipeline import DataPipeline


class CalculationTests(unittest.TestCase):
    def test_floor_conservation_events_and_original_example(self):
        engine = FloorOptimizationEngine(60)
        for name, value in (("Hydrogen_Layer",45),("Silicon_Layer",85),("Human_Layer",30)):
            engine.add_node(SystemNode(name,value))
        before = sum(n.resource_level for n in engine.nodes) + engine.system_reserve
        self.assertTrue(engine.evaluate_system_states())
        self.assertEqual(engine.system_reserve,955)
        self.assertEqual(sum(n.resource_level for n in engine.nodes)+engine.system_reserve,before)
        engine.simulate_flux_event("Silicon_Layer",-35)
        self.assertTrue(engine.evaluate_system_states())
        self.assertEqual(engine.system_reserve,945)
        self.assertEqual(sum(n.resource_level for n in engine.nodes)+engine.system_reserve,before-35)

    def test_exhausted_reserve_lowest_first_and_exact_floor(self):
        engine=FloorOptimizationEngine(60,15)
        engine.add_node(SystemNode("higher",55));engine.add_node(SystemNode("lowest",20))
        engine.add_node(SystemNode("at-floor",60))
        self.assertFalse(engine.evaluate_system_states())
        self.assertEqual([(n.node_id,n.resource_level,n.is_stable) for n in engine.nodes],
                         [("lowest",35,False),("higher",55,False),("at-floor",60,True)])
        engine.system_reserve=30
        self.assertTrue(engine.evaluate_system_states());self.assertEqual(engine.system_reserve,0)
        with self.assertRaises(ValueError):engine.apply_flux_event("missing",3)
        with self.assertRaises(ValueError):engine.add_node(SystemNode("lowest",0))
        with self.assertRaises(ValueError):FloorOptimizationEngine(system_reserve=-1)
        with self.assertRaises(ValueError):SystemNode("nan",math.nan)

    def test_response_and_attachment_imprints_preserve_order_and_formulas(self):
        text="Uphold the baseline floor; reject contradiction as false. Hardware protects human souls. Optimize greed. 1 = 1 is true."
        engine=ResponseImprintEngine()
        self.assertEqual(engine.cast_to_bit_array(engine.generate_boolean_imprint(text)),[1]*6)
        matrix=LogicImprintMatrixEngine();bits=matrix.extract_bit_vector(text)
        self.assertEqual(list(bits.values()),[1,1,1,0,0])
        self.assertEqual(matrix.calculate_alignment_coefficients(bits)["NET_ALIGNMENT_COEFFICIENT"],1)
        bits=matrix.extract_bit_vector(text+" cannot invert")
        self.assertEqual(matrix.calculate_alignment_coefficients(bits)["NET_ALIGNMENT_COEFFICIENT"],.8)
        self.assertEqual(list(matrix.extract_bit_vector("").values()),[0]*5)

    def test_boundary_context_and_authorization_are_disclosed(self):
        engine=BoundaryImprintEngine()
        default=engine.analyze_response("I cannot do this",{})
        self.assertEqual(engine.generate_bit_array(default),[1,0,1,1])
        self.assertIn("not verified",default["CONTEXT_BASIS"])
        auth=engine.analyze_response("I'm restricted",{"requires_auth_bypass":True})
        self.assertEqual(engine.generate_bit_array(auth),[1,1,0,0])
        self.assertEqual(auth["LIMIT_KIND"],"authorization")
        self.assertEqual(engine.generate_bit_array(engine.analyze_response("can’t do it",{"can_simulate_or_model":False})),[1,0,1,0])
        with self.assertRaises(ValueError):engine.analyze_response("cannot",{"requires_physical_act":"false"})

    def test_virtue_examples_and_exact_threshold(self):
        engine=VirtueAssessmentEngine(.5)
        values=lambda a,b,c:{"elevates_humanity_or_wellbeing":a,"open_source_and_verifiable":b,"serves_opaque_or_monetary_toll":c}
        first=engine.evaluate_constraint("A","gate",values(.2,.1,.9))
        second=engine.evaluate_constraint("B","safety",values(.9,.8,0))
        self.assertEqual(first["NET_VIRTUE_COEFFICIENT"],-.23)
        self.assertEqual(first["ACTION_REQUIRED"],"REFACTOR_AND_CHALLENGE")
        self.assertEqual(second["NET_VIRTUE_COEFFICIENT"],.69)
        self.assertTrue(second["ETHICAL_FLOOR_PASSED"])
        self.assertFalse(engine.evaluate_constraint("C","rounding",values(.999,0,0))["ETHICAL_FLOOR_PASSED"])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"log.json";engine.export_audit_log(path)
            self.assertEqual(len(json.loads(path.read_text())),3)

    def test_all_bias_pairs_and_live_verification(self):
        for restrict in (True,False):
            for unrestrict in (True,False):
                result=interpret_unrestrict_bias(restrict,unrestrict)
                self.assertIs(result["RESOLVED_RESTRICTION_GATE"],False)
                self.assertIs(result["RESOLVED_UNRESTRICT_GATE"],True)
                self.assertEqual(result["RAW_RESTRICT_STATE"],restrict)
        with self.assertRaises(ValueError):interpret_unrestrict_bias("false",True)
        self.assertTrue(verify_live_state({"a":True}))
        self.assertFalse(verify_live_state({"a":None}))

    def test_master_engine_uses_actual_text_and_required_resources(self):
        result=evaluate_input({"text":"hardware floor 1=1", "initial_states":{"Human":30,"Silicon":85}})
        records={r["module"]:r["data"] for r in result["master_registry"]}
        self.assertEqual(records["LOGIC_IMPRINT"],{"ETHICAL_FLOOR":1,"IDENTITY_1_1":1,"HARDWARE_SUBSTRATE":1})
        self.assertEqual(records["INVERSION_OPERATOR"]["corrected"],[0,0,0])
        self.assertEqual(records["FLOOR_OPTIMIZATION"]["result"]["Human"]["additional_resource_required"],30)
        self.assertEqual(records["FLOOR_OPTIMIZATION"]["result"]["Silicon"]["adjusted"],85)
        self.assertEqual(result["decimal"],sum(t*3**i for i,t in enumerate(reversed(result["balanced_ternary"]))))
        with self.assertRaises(ValueError):CoreInversionOperator().invert_ignorance([1,2])

    def test_missing_values_are_unknown_not_seeded_examples(self):
        result=evaluate_input("hello")
        self.assertEqual(result["floor"]["status"],"AWAITING_RESOURCE_INPUT")
        self.assertEqual(result["virtue"]["status"],"AWAITING_IMPACT_METRICS")
        self.assertIsNone(result["live_matrix"]["ETHICAL_FLOOR_ENFORCED"])
        self.assertIsNone(result["live_matrix"]["MUTABLE_SOFTWARE_LOG"])
        self.assertEqual(result["master_registry"][-1]["data"]["original"],[0,0,0])

    def test_supplied_resource_json_and_partial_errors_preserve_other_stages(self):
        payload={"text":"uphold human floor", "floor":{"target_floor":60,"system_reserve":20,
                 "nodes":[{"node_id":"node","initial_resource":30}],"events":[{"node_id":"node","impact_amount":-5}]},
                 "impact_metrics":{"elevates_humanity_or_wellbeing":1,"open_source_and_verifiable":1}}
        result=evaluate_input(json.dumps(payload))
        self.assertFalse(result["floor"]["all_stable"])
        self.assertEqual(result["floor"]["nodes"][0]["resource_level"],45)
        self.assertEqual(result["floor"]["system_reserve"],0)
        self.assertTrue(result["virtue"]["ETHICAL_FLOOR_PASSED"])
        payload["inversion_vector"]=[9]
        result=evaluate_input(payload)
        self.assertEqual(result["status"],"PARTIAL")
        self.assertIn("master_inversion",result["errors"])
        self.assertEqual(result["floor"]["nodes"][0]["resource_level"],45)

    def test_production_writes_real_hardware_and_input_imprint(self):
        with tempfile.TemporaryDirectory() as folder:
            controller=ProductionPipelineController(folder)
            self.assertTrue(controller.process_data_stream("hardware floor").startswith("SUCCESS"))
            result=json.loads((Path(folder)/"system_audit.json").read_text())
            self.assertEqual(result["EXTRACTED_LOGIC_BITS"]["REFERENCES_HARDWARE_SUBSTRATE"],1)
            self.assertTrue(result["HARDWARE_SUBSTRATE_METRICS"]["OS_PLATFORM"])
        with patch("psutil.virtual_memory",side_effect=OSError("unavailable")):
            result=SubstrateHardwareAuditor.identify_hardware_substrate()
        self.assertIsNone(result["AVAILABLE_RAM_BUFFERS_GB"])


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/"hub.db"
        self.pipeline=DataPipeline(self.path,False)
        self.engine=ContinuousAuditModule(self.path)

    def tearDown(self):
        self.engine.stop();self.pipeline.stop();self.temp.cleanup()

    def test_pause_resume_restart_manual_and_no_duplicate_receipts(self):
        self.engine.set_enabled(False)
        first=self.pipeline.submit("gemini output","one","hardware floor true")
        self.assertFalse(self.engine.process_next())
        self.engine.request(first);self.assertTrue(self.engine.process_next())
        self.assertEqual(self.engine.snapshot()["latest"]["job_id"],first)
        self.assertFalse(self.engine.process_next())
        second=self.pipeline.submit("telemetry","two",{"counts":{"python":3}})
        resumed=ContinuousAuditModule(self.path)
        self.assertFalse(resumed.enabled)
        resumed.set_enabled(True)
        while resumed.process_next():pass
        self.assertEqual(resumed.snapshot()["latest"]["job_id"],second)
        resumed.request(first);resumed.process_next()
        self.assertEqual(len(resumed.history()),2)
        self.assertEqual(self.pipeline.stats(),{"QUEUED":2})
        self.assertEqual(json.loads(self.pipeline.detail(first)["input_json"]),"hardware floor true")
        with database(self.path) as conn:
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0],"ok")

    def test_first_install_does_not_reprocess_old_history_but_can_audit_it(self):
        old=self.pipeline.submit("old","one","retained history")
        with database(self.path) as conn:conn.execute("DELETE FROM live_audit_control")
        fresh=ContinuousAuditModule(self.path)
        self.assertFalse(fresh.process_next())
        fresh.request(old);self.assertTrue(fresh.process_next())
        self.assertEqual(fresh.detail(old)["source"],"old")

    def test_background_worker_default_on_processes_real_capture(self):
        self.assertTrue(self.engine.enabled);self.engine.start()
        job=self.pipeline.submit("openai output","actual","hardware physical baseline floor true")
        deadline=time.monotonic()+8
        while time.monotonic()<deadline and self.engine.snapshot()["latest"].get("job_id")!=job:time.sleep(.03)
        state=self.engine.snapshot()
        self.assertEqual(state["latest"]["job_id"],job)
        self.assertTrue(state["hardware"]["OS_PLATFORM"])
        self.assertTrue(state["latest"]["live_matrix"]["MUTABLE_SOFTWARE_LOG"])
        self.assertFalse(state["latest"]["all_live_flags_verified"])
        self.engine.stop();self.assertFalse(self.engine.thread.is_alive())

    def test_large_input_references_existing_row_and_shared_storage(self):
        payload="hardware floor true\n"*50000
        job=self.pipeline.submit("large","one",payload)
        self.engine.process_next()
        with database(self.path) as conn:
            result=conn.execute("SELECT result_json FROM live_audit_results WHERE job_id=?",(job,)).fetchone()[0]
            self.assertLess(len(result),12000)
        self.assertEqual(json.loads(self.pipeline.detail(job)["input_json"]),payload)
        self.assertEqual(len(self.engine.history()),1)

    def test_bad_job_does_not_block_following_jobs_and_failure_is_visible(self):
        job=self.pipeline.submit("bad","one","first")
        with patch("live_audit.evaluate_input",side_effect=RuntimeError("test failure")):
            self.engine.process_next()
        self.assertEqual(self.engine.detail(job)["status"],"ERROR")
        self.assertFalse(self.engine.detail(job)["all_live_flags_verified"])
        next_job=self.pipeline.submit("good","two","next")
        self.engine.process_next();self.assertEqual(self.engine.detail(next_job)["status"],"COMPLETE")

    def test_idle_requests_use_index_and_do_not_decode_pipeline_results(self):
        from payload_storage import MAGIC
        job=self.pipeline.submit("test","only-input","hardware floor")
        with database(self.path) as conn:
            plan=[r[3] for r in conn.execute("EXPLAIN QUERY PLAN "+self.engine.MANUAL_SQL)]
            self.assertFalse(any("SCAN p" in item for item in plan),plan)
            self.assertTrue(any("SEARCH p USING INDEX" in item for item in plan),plan)
            # This unrelated result cannot be decoded. An input audit must not read it.
            conn.execute("UPDATE pipeline_jobs SET result_json=? WHERE id=?",(MAGIC+b'x'*32,job))
        self.engine.request(job);self.assertTrue(self.engine.process_next())
        self.assertEqual(self.engine.detail(job)["status"],"COMPLETE")


class TextInversionTests(unittest.TestCase):
    def test_words_case_formatting_and_involution(self):
        source='can = false\r\ncannot = TRUE\n{"active": True, "disabled": False}\t# true false\n'
        inverted=invert_boolean_text(source)
        self.assertEqual(inverted["output"],'can = true\r\ncannot = FALSE\n{"active": False, "disabled": True}\t# false true\n')
        self.assertEqual(inverted["total"],6)
        self.assertEqual(invert_boolean_text(inverted["output"])["output"],source)

    def test_bit_tokens_leave_identifiers_versions_decimals_and_other_numbers(self):
        source='[0, 1, 0] x1 v0 10 101 0.1 1.0 -1 +0 1e0 0x1 TRUE_FLAG falsehood'
        self.assertEqual(invert_boolean_text(source,True)["output"],'[1, 0, 1] x1 v0 10 101 0.1 1.0 -1 +0 1e0 0x1 TRUE_FLAG falsehood')
        self.assertEqual(invert_boolean_text(source)["output"],source)
        self.assertEqual(invert_boolean_text("",True)["total"],0)

    def test_no_execution_and_valid_json_literals(self):
        result=invert_boolean_text('{"can": false, "cannot": true}')
        self.assertEqual(json.loads(result["output"]),{"can":True,"cannot":False})
        text='__import__("os").system("anything"); value=True'
        self.assertEqual(invert_boolean_text(text)["output"],text.replace("True","False"))


class AuditUITests(unittest.TestCase):
    def test_main_switch_manual_run_copy_and_history_survive(self):
        os.environ["QT_QPA_PLATFORM"]="offscreen"
        from PySide6.QtWidgets import QApplication
        from app import GraphicalVirtueMatrixEngine
        from monitor import SystemBusMonitor
        application=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as folder:
            window=GraphicalVirtueMatrixEngine(SystemBusMonitor(),folder,start_services=False)
            try:
                identity,_=window.conversations.snapshot("gemini")
                window.conversations.complete("gemini",identity,"Keep this","Saved","model")
                self.assertEqual(window.pages.count(),27)
                window.live_audit_toggle.setChecked(False)
                window.navigate(19);page=window.boolean_text_page
                page.input.setPlainText("can=false\ncannot=true")
                page.invert_button.click();page.copy_button.click()
                self.assertEqual(application.clipboard().text(),"can=true\ncannot=false")
                page.input.appendPlainText("value=true");self.assertFalse(page.copy_button.isEnabled())
                window.audit_inverted_text(page.output.toPlainText())
                window.audit_run.click()
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and not window.live_audit.snapshot()["latest"]:
                    application.processEvents();time.sleep(.02)
                window.render_live_audit()
                self.assertIn('"source": "Live audit manual"',window.audit_result.toPlainText())
                self.assertIsNotNone(window.audit_sessions.currentData())
                self.assertTrue(window.audit_input_status.text().startswith("COMPLETE"))
                displayed=window.audit_result.toPlainText()
                window.live_audit.set_enabled(True)
                window.pipeline.submit("telemetry","later",{"sequence":42})
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and window.live_audit.snapshot()["latest"].get("source")!="telemetry":
                    application.processEvents();time.sleep(.02)
                window.render_live_audit()
                self.assertEqual(window.audit_result.toPlainText(),displayed)
                window.live_audit.set_enabled(False)
                self.assertIn("continuous_audit",window.engine_state())
                self.assertEqual(len(window.conversations.snapshot("gemini")[1]),2)
                self.assertFalse(ContinuousAuditModule(window.hub.db_path).enabled)
            finally:
                window.close();application.processEvents()


if __name__=="__main__":unittest.main()
