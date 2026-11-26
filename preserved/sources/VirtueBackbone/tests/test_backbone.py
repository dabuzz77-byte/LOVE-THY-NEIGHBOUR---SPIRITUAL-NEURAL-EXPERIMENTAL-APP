import asyncio
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backbone import Bus, Client, HZ, Knowledge, MAGIC, MAX_FRAME, encoded, read_frame, token_at


class BackboneTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_root = Path(os.environ.get("BACKBONE_TEST_TMP", Path.cwd() / "work" / "backbone-tests")).resolve()
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.test_root)
        self.root = Path(self.temp.name)
        self.token = token_at(self.root / "token.txt")
        self.knowledge = Knowledge(self.root / "test.sqlite3")
        self.bus = Bus(self.token, self.knowledge)
        self.server = await asyncio.start_server(self.bus.handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        self.pulse = asyncio.create_task(self.bus.pulse_loop())
        self.writers = []

    async def asyncTearDown(self):
        for writer in self.writers:
            writer.close()
            await writer.wait_closed()
        await self.bus.close()
        self.server.close()
        await self.server.wait_closed()
        self.pulse.cancel()
        await asyncio.gather(self.pulse, return_exceptions=True)
        await asyncio.sleep(.05)
        self.knowledge.close()
        assert self.root.resolve().parent == self.test_root
        self.temp.cleanup()

    async def connect(self, name, topics=None, token=None, fragment=False):
        r,w = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", self.port), 5)
        self.writers.append(w)
        data = encoded({"op":"hello","token":self.token if token is None else token,"service":name,"topics":topics or []})
        if fragment:
            for byte in data:
                w.write(bytes([byte]))
                await w.drain()
                await asyncio.sleep(0)
        else:
            w.write(data)
            await w.drain()
        result = await asyncio.wait_for(read_frame(r), 3)
        return r,w,result

    async def test_framing_fragmentation_unicode_and_routing(self):
        a,aw,welcome = await self.connect("sender", fragment=True)
        b,bw,_ = await self.connect("receiver", ["user.exchange"])
        self.assertEqual(welcome["op"], "welcome")
        text = "Mercy · 平和 · compassion"
        aw.write(encoded({"op":"publish","request_id":"p1","topic":"user.exchange","data":{"text":text}}))
        event = await asyncio.wait_for(read_frame(b), 2)
        self.assertEqual(event["data"]["text"], text)
        self.assertEqual(event["service"], "sender")
        self.assertIn("event_id", event)
        self.assertEqual((await read_frame(a))["data"]["accepted"], True)

    async def test_authentication_and_duplicate_identity(self):
        _,_,bad = await self.connect("wrong", token="wrong")
        self.assertEqual(bad["op"],"error")
        _,_,good = await self.connect("unique")
        _,_,duplicate = await self.connect("unique")
        self.assertEqual(good["op"],"welcome")
        self.assertEqual(duplicate["op"],"error")

    async def test_oversized_frame_and_reserved_pulse(self):
        r,w = await asyncio.wait_for(asyncio.open_connection("127.0.0.1",self.port), 5)
        self.writers.append(w)
        w.write(struct.pack("!4sI",MAGIC,MAX_FRAME+1))
        self.assertEqual((await read_frame(r))["op"],"error")
        r,w,_ = await self.connect("publisher")
        w.write(encoded({"op":"publish","request_id":"p1","topic":"pulse","data":{}}))
        self.assertEqual((await read_frame(r))["op"],"error")

    async def test_pulses_have_measured_frequency_and_no_clock_drift(self):
        r,w,_ = await self.connect("timing", ["pulse"])
        pulses = [(await asyncio.wait_for(read_frame(r),2))["data"] for _ in range(32)]
        elapsed = (pulses[-1]["sent_monotonic_ns"]-pulses[0]["sent_monotonic_ns"])/1e9
        frequency = (len(pulses)-1)/elapsed
        self.assertAlmostEqual(frequency,HZ,delta=.3)
        self.assertEqual([p["sequence"] for p in pulses],list(range(pulses[0]["sequence"],pulses[0]["sequence"]+32)))
        expected_ns = 31/HZ*1e9
        self.assertLess(abs((pulses[-1]["deadline_monotonic_ns"]-pulses[0]["deadline_monotonic_ns"])-expected_ns),2)
        print(f"TIMING: {frequency:.6f} Hz; p95 lateness {self.bus.snapshot()['lateness_p95_ms']:.3f} ms", flush=True)

    async def test_stall_records_skipped_ticks_without_catchup_burst(self):
        r,w,_ = await self.connect("stall", ["pulse"])
        first = (await read_frame(r))["data"]
        time.sleep(.55)  # Deliberately stall the event loop, as system load or suspension would.
        second = (await read_frame(r))["data"]
        third = (await read_frame(r))["data"]
        self.assertGreater(second["skipped_total"],0)
        self.assertGreater(second["sequence"]-first["sequence"],1)
        self.assertEqual(third["sequence"], second["sequence"]+1)
        self.assertGreater(third["deadline_monotonic_ns"], second["sent_monotonic_ns"])

    async def test_source_provenance_graph_and_persistence(self):
        r,w,_ = await self.connect("editor")
        passage = {"id":"sample","title":"User note","author":"Test author","reference":"Paragraph 1",
                   "source":"test-fixture","text":"Compassion and honest research.","themes":["compassion"],"kind":"user-note"}
        w.write(encoded({"op":"import","request_id":"i1","passage":passage}))
        self.assertEqual((await read_frame(r))["data"]["id"],"sample")
        w.write(encoded({"op":"graph","request_id":"g1"}))
        graph = (await read_frame(r))["data"]
        self.assertTrue(any(e["basis"]=="keyword-suggestion" and e["to"]=="theme:learning" for e in graph["edges"]))
        self.assertEqual(graph["nodes"][0]["source"],"test-fixture")
        other = Knowledge(self.root/"test.sqlite3")
        self.assertEqual(other.graph(),graph)
        other.close()

    async def test_python_client_roundtrip(self):
        def use_client():
            with Client(self.port,self.root/"token.txt","python-sdk",["user.exchange"]) as client:
                client.publish("user.exchange",{"message":"python-sdk-test"})
                return client.receive(),client.request("status")["data"]
        event,status = await asyncio.to_thread(use_client)
        self.assertEqual(event["data"]["message"],"python-sdk-test")
        self.assertTrue(any(s["id"]=="python-sdk" for s in status["services"]))

    async def test_large_corpus_pages_without_losing_texts(self):
        for i in range(12):
            self.knowledge.put({"id":f"p{i:02}","title":"Long passage","author":"Test","reference":str(i),
                                "source":"test-fixture","text":"慈悲"*9999,"themes":["compassion"],"kind":"user-note"})
        def get_graph():
            with Client(self.port,self.root/"token.txt","pagination",[]) as client:
                return client.graph()
        graph = await asyncio.to_thread(get_graph)
        self.assertEqual(sum(n["type"]=="passage" for n in graph["nodes"]),12)
        self.assertEqual(sum(n["type"]=="theme" for n in graph["nodes"]),1)
        self.assertEqual(len(graph["edges"]),12)

    async def test_java_python_interoperability(self):
        java = os.environ.get("BACKBONE_JAVA")
        if not java:
            self.skipTest("Set BACKBONE_JAVA to a Java 17+ executable")
        r,w,_ = await self.connect("python-observer",["user.exchange"])
        jar = Path(__file__).resolve().parents[1]/"java"/"backbone-client.jar"
        proc = await asyncio.create_subprocess_exec(java,"-jar",str(jar),str(self.port),str(self.root/"token.txt"),"8",
                      stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:
            event = await asyncio.wait_for(read_frame(r),10)
            self.assertEqual(event["data"]["language"],"Java")
            w.write(encoded({"op":"publish","request_id":"j1","topic":"user.exchange","data":{"text":"Python to Java: peace · 平和"}}))
            output,error = await asyncio.wait_for(proc.communicate(),15)
            self.assertEqual(proc.returncode,0,error.decode(errors="replace"))
            text = output.decode("utf-8")
            self.assertIn("Python to Java",text)
            self.assertIn("平和",text)
            self.assertEqual(sum('"topic":"pulse"' in line for line in text.splitlines()),8)
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()

    async def test_knowledge_worker_completes_a_routed_job(self):
        from knowledge_worker import summarize
        self.knowledge.put({"id":"one","title":"Sample","author":"Test","reference":"One",
                            "source":"test-fixture","text":"Mercy and compassion.","themes":[],"kind":"user-note"})
        async def worker():
            def work():
                with Client(self.port,self.root/"token.txt","summary-worker",["workflow.request"]) as client:
                    self.worker_ready = True
                    job = client.receive()
                    client.publish("workflow.result", summarize(client,job["data"]))
            await asyncio.to_thread(work)
        self.worker_ready = False
        task = asyncio.create_task(worker())
        for _ in range(100):
            if self.worker_ready: break
            await asyncio.sleep(.02)
        r,w,_ = await self.connect("requester",["workflow.result"])
        w.write(encoded({"op":"publish","request_id":"job1","topic":"workflow.request",
                         "data":{"task_id":"test-job","action":"map-summary"}}))
        result = None
        for _ in range(2):
            message = await asyncio.wait_for(read_frame(r),3)
            if message.get("topic") == "workflow.result": result = message["data"]
        self.assertEqual(result["task_id"],"test-job")
        self.assertEqual(result["state"],"completed")
        self.assertEqual(result["passage_count"],1)
        self.assertIn("compassion",result["themes"])
        await task


if __name__ == "__main__":
    unittest.main(verbosity=2)
