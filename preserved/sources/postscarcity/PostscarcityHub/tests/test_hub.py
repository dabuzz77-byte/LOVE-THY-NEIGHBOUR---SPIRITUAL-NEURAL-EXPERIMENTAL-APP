import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from neural_engine import NeuralEngine,mean_step,features,KEYS,HORIZON,validate_scenario
from hub_runtime import Runtime,DEFAULT_SCENARIO
from bus_protocol import Client,HZ
from process_monitor import ProcessMonitor,source_label
from attach_bus import attach


class NeuralTests(unittest.TestCase):
    def test_neural_model_on_new_synthetic_cases(self):
        model=NeuralEngine()
        rng=np.random.default_rng(88312)
        states=rng.uniform(0,100,(1500,4));controls=rng.integers(0,2,(1500,2))
        expected=mean_step(states,controls,HORIZON)
        actual=np.clip(model.forward(features(states,controls))[0]*100,0,100)
        self.assertLess(float(abs(actual-expected).mean()),1.5)
        result=model.infer(DEFAULT_SCENARIO)
        self.assertEqual(set(result["predicted"]),set(KEYS))
        self.assertEqual(result["basis"],"synthetic simulation rules")

    def test_invalid_scenarios_are_rejected(self):
        for change in ({"access":float("nan")},{"comfort":101},{"automation":True},{"valve":1}):
            with self.assertRaises(ValueError):validate_scenario(dict(DEFAULT_SCENARIO,**change))

    def test_reference_rules_match_source_increments(self):
        actual=mean_step([[45,12,0,15]],[[1,1]],60)[0]
        np.testing.assert_allclose(actual,[60,24,24,22.5])
        negative=mean_step([[45,12,50,15]],[[0,0]],10)[0]
        np.testing.assert_allclose(negative,[44.5,11.7,49,15])

    def test_source_labels_do_not_retain_command_secrets(self):
        self.assertEqual(source_label("python.exe",'python.exe "C:\\My Apps\\worker.py" --token private'),"worker.py")
        self.assertEqual(source_label("java.exe",'java.exe -cp "C:\\classes" example.Main --token private'),"example.Main")
        self.assertEqual(source_label("java.exe",'java.exe -jar "C:\\My Apps\\app.jar" --token private'),"app.jar")


class HubTests(unittest.TestCase):
    def setUp(self):
        self.work=Path(os.environ.get("BACKBONE_TEST_TMP",Path.cwd()/"work"/"postscarcity-tests")).resolve()
        self.work.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=self.work)
        self.root=Path(self.temp.name)
        self.runtime=Runtime(port=0,data_dir=self.root)
        self.runtime.start()
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            state,_=self.runtime.take()
            if state["phase"]=="error":self.fail(state["error"])
            if state["phase"]=="listening":break
            time.sleep(.03)
        else:self.fail("Hub startup timed out")

    def tearDown(self):
        self.runtime.shutdown()
        self.assertTrue(self.runtime.wait_stopped(10),"Runtime did not stop")
        self.assertEqual(self.root.resolve().parent,self.work)
        self.temp.cleanup()

    def client(self,name,topics=None):
        return Client(self.runtime.port,self.root/"token.txt",name,topics or [])

    def test_inference_over_authenticated_bus(self):
        with self.client("inference-check") as client:
            self.assertEqual(client.welcome["target_hz"],7.38)
            result=client.request("infer",scenario=DEFAULT_SCENARIO)["data"]
            self.assertEqual(result["horizon_ticks"],60)
            self.assertLess(abs(result["predicted"]["access"]-60),3)
            with self.assertRaises(ValueError):client.request("infer",scenario={"access":"evil"})
            status=client.request("status")["data"]
            self.assertEqual(status["inference_count"],1)
            self.assertEqual(status["services"][0]["reported_pid"],os.getpid())

    def test_attachment_exchanges_messages_and_reconnects_after_restart(self):
        pulse=threading.Event()
        adapter=attach("attached-python",port=self.runtime.port,token_file=self.root/"token.txt",
                       on_pulse=lambda message:pulse.set())
        try:
            self.assertTrue(pulse.wait(5),"Adapter did not receive pulses")
            with self.client("adapter-reader",["user.message"]) as reader:
                adapter.publish("user.message",{"marker":"adapter-roundtrip"})
                self.assertEqual(reader.receive()["data"]["marker"],"adapter-roundtrip")
            self.runtime.shutdown()
            self.assertTrue(self.runtime.wait_stopped(8))
            deadline=time.monotonic()+5
            while adapter.connected and time.monotonic()<deadline:time.sleep(.02)
            self.assertFalse(adapter.connected)
            pulse.clear()
            self.runtime.start()
            self.assertTrue(pulse.wait(8),"Adapter did not reconnect after restart")
            self.assertTrue(adapter.connected)
        finally:
            adapter.close()
            self.assertFalse(adapter.thread.is_alive(),"Attachment worker did not stop")

    def test_observer_discovers_real_child_without_claiming_adapter(self):
        child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(20)"],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        try:
            with self.client("process-check") as client:
                deadline=time.monotonic()+8;found=None
                while time.monotonic()<deadline:
                    data=client.request("processes")["data"]
                    found=next((p for p in data["processes"] if p["pid"]==child.pid),None)
                    if found:break
                    time.sleep(.3)
                self.assertIsNotNone(found)
                self.assertEqual(found["mode"],"observed")
                peers=client.request("status")["data"]["services"]
                self.assertFalse(any(p["reported_pid"]==child.pid for p in peers))
        finally:
            child.terminate();child.wait(timeout=5)

    def test_local_heartbeat_measured_at_7_38(self):
        with self.client("timing-check",["pulse"]) as client:
            pulses=[client.receive()["data"] for _ in range(32)]
            elapsed=(pulses[-1]["sent_monotonic_ns"]-pulses[0]["sent_monotonic_ns"])/1e9
            hz=(len(pulses)-1)/elapsed
            self.assertAlmostEqual(hz,HZ,delta=.2)
            status=client.request("status")["data"]
            report={"target_hz":HZ,"measured_hz":hz,"pulses_received":len(pulses),"skipped":status["skipped_ticks"],
                    "p95_lateness_ms":status["lateness_p95_ms"]}
            (Path(__file__).resolve().parents[1]/"reports"/"pulse-check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
            print("PULSE:",json.dumps(report),flush=True)

    def test_java_peer_receives_neural_inference(self):
        java=os.environ.get("BACKBONE_JAVA")
        if not java:self.skipTest("Java executable not configured")
        jar=Path(__file__).resolve().parents[1]/"java"/"backbone-client.jar"
        result=subprocess.run([java,"-jar",str(jar),str(self.runtime.port),str(self.root/"token.txt"),"10"],
                    capture_output=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr.decode(errors="replace"))
        messages=[json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
        reply=next(m for m in messages if m.get("request_id")=="java-inference")
        self.assertEqual(reply["op"],"reply")
        self.assertEqual(reply["data"]["basis"],"synthetic simulation rules")
        self.assertEqual(sum(m.get("topic")=="pulse" for m in messages),10)


if __name__=="__main__":unittest.main(verbosity=2)
