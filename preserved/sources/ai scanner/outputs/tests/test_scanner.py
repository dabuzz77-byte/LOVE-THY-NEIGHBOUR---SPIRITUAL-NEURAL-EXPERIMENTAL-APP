import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ai_mode_scanner as scanner


def activity(messages=None):
    return {"id":"activity-one", "timestamp":"2026-10-10T16:43:00", "timezone":"Europe/London",
            "messages":messages or [{"role":"user","text":"Question","html":"<p>Question</p>"},
                                     {"role":"assistant","text":"Answer","html":"<p>Answer</p>"}]}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.test_root=Path(os.environ.get("SCANNER_TEST_TEMP", ".scanner-test-temp")).resolve()
        self.test_root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=self.test_root)
        self.folder=Path(self.temp.name)
        self.store=scanner.Store(self.folder/"test.sqlite3")
        self.handler={"name":"test-handler","type":"http","url":"http://127.0.0.1:8765/activity","chunk_chars":6000}

    def tearDown(self):
        self.store.db.close()
        assert self.folder.resolve().parent == self.test_root
        self.temp.cleanup()

    def test_repeated_scan_and_restart_deduplicate(self):
        self.assertEqual(self.store.ingest(activity(),[self.handler]),2)
        self.assertEqual(self.store.ingest(activity(),[self.handler]),0)
        self.store.db.close()
        self.store=scanner.Store(self.folder/"test.sqlite3")
        self.assertEqual(self.store.ingest(activity(),[self.handler]),0)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM jobs").fetchone()[0],2)

    def test_added_turns_and_edited_answer_are_versioned(self):
        first=activity()
        self.store.ingest(first,[self.handler])
        first["messages"] += [{"role":"user","text":"Follow up","html":""}]
        self.assertEqual(self.store.ingest(first,[self.handler]),1)
        first["messages"][1]["text"]="Corrected answer"
        self.assertEqual(self.store.ingest(first,[self.handler]),1)
        self.assertEqual(self.store.status()["message_versions"],4)

    def test_late_handler_receives_archive_and_chunks_without_loss(self):
        original="α🙂\n"*5001
        self.store.ingest(activity([{"role":"assistant","text":original,"html":""}]),[])
        self.store.backfill_handlers([self.handler])
        chunks=[json.loads(row[0]) for row in self.store.db.execute("SELECT payload FROM jobs ORDER BY rowid")]
        self.assertEqual("".join(c["text"] for c in chunks),original)
        self.assertTrue(all(len(c["text"])<=6000 for c in chunks))
        self.assertEqual([c["part_index"] for c in chunks],list(range(len(chunks))))
        self.store.backfill_handlers([self.handler])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM jobs").fetchone()[0],len(chunks))

    def test_failed_delivery_retries_and_success_is_not_replayed(self):
        self.store.ingest(activity(),[self.handler])
        with patch.object(scanner,"deliver",side_effect=OSError("offline")) as sender:
            scanner.delivery_pass(self.store,self.handler,self.folder)
            self.assertEqual(sender.call_count,1)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM jobs WHERE state='pending'").fetchone()[0],2)
        with self.store.db:
            self.store.db.execute("UPDATE jobs SET retry_at=0")
        with patch.object(scanner,"deliver",return_value={"accepted":True}) as sender:
            scanner.delivery_pass(self.store,self.handler,self.folder)
            scanner.delivery_pass(self.store,self.handler,self.folder)
            self.assertEqual(sender.call_count,2)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM jobs WHERE state='done'").fetchone()[0],2)

    def test_export_retains_all_messages_and_original_html(self):
        self.store.ingest(activity(),[])
        self.store.export(self.folder)
        records=[json.loads(x) for x in (self.folder/"messages.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([x["role"] for x in records],["user","assistant"])
        saved=json.loads((self.folder/"conversations.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(saved["messages"][1]["html"],"<p>Answer</p>")

    def test_command_receives_text_as_data(self):
        handler={"type":"command","argv":["{python}","-c","import json,sys; print(json.dumps(json.load(sys.stdin)))"]}
        event={"text":"$(do-not-run) ; Your prompt: \n  print('hello')"}
        self.assertEqual(scanner.deliver(handler,event,self.folder),event)


class ParserTests(unittest.TestCase):
    def test_code_indentation_and_entities(self):
        value=scanner.html_text('<p>Explanation &amp; detail</p><pre>def f():\n    return "🙂"\n</pre>')
        self.assertIn('def f():\n    return "🙂"',value)
        self.assertIn("Explanation & detail",value)

    def test_relative_dates_stay_stable_next_day(self):
        first=scanner.normalise_timestamp("Today at 16:43",datetime(2026,10,10))
        second=scanner.normalise_timestamp("Yesterday at 16:43",datetime(2026,10,11))
        third=scanner.normalise_timestamp("10 October at 16:43",datetime(2026,10,12))
        self.assertEqual(first,second)
        self.assertEqual(first,third)

    def test_previous_year_and_explicit_year(self):
        self.assertEqual(scanner.normalise_timestamp("31 December at 23:59",datetime(2026,1,1)),"2025-12-31T23:59:00")
        self.assertEqual(scanner.normalise_timestamp("5 Oct 2024 at 1:05 PM",datetime(2026,10,10)),"2024-10-05T13:05:00")
        with self.assertRaises(ValueError):
            scanner.normalise_timestamp("unrecognised date",datetime(2026,10,10))

    def test_only_loopback_destinations(self):
        for url in ["https://example.com/", "file:///private", "http://127.0.0.1.attacker.example/", "http://user:pass@localhost/"]:
            with self.assertRaises(ValueError): scanner.local_url(url)
        self.assertEqual(scanner.local_url("http://127.0.0.1:9999"),"http://127.0.0.1:9999")
        with self.assertRaises(ValueError): scanner.NoRedirect().redirect_request(None)


class ActualGatewayTests(unittest.TestCase):
    def test_isolated_existing_gateway_protocol(self):
        root=Path("C:/Users/USER/Desktop/CHAT GPT APPS/Godmind Mesh Desktop/neural_weight")
        if not root.exists(): self.skipTest("User's existing Godmind source is not on this machine")
        def load(name):
            spec=importlib.util.spec_from_file_location("scanner_test_"+name,root/(name+".py"))
            module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        ledger=load("StructuralStateLedger").StructuralStateLedger()
        gateway=load("ProductionNetworkGateway").ProductionNetworkGateway(ledger,port=0)
        port=gateway.start_gateway()
        try:
            handler={"type":"godmind_tcp","host":"127.0.0.1","port":port,"timeout_seconds":5}
            event={"text":"cooperation efficiency protect floor", "delivery_id":"test-one", "role":"user"}
            result=scanner.deliver(handler,event,Path.cwd())
            self.assertEqual(result["server_status"],"ONLINE")
            self.assertEqual(result["virtue_count"],4)
            self.assertEqual(result["output_bits"],[])
            # Maximum configured Unicode chunk must fit the real gateway's byte limit.
            event["text"]="🙂"*6000
            self.assertEqual(scanner.deliver(handler,event,Path.cwd())["server_status"],"ONLINE")
        finally:
            gateway.stop_gateway()


if __name__=="__main__":
    unittest.main()
