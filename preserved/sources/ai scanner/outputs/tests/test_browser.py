"""Offline browser integration fixture; never connects to the user's Google account."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_mode_scanner as scanner

FIXTURE = r'''<!doctype html><html><body><div id="history"></div>
<button id="more">Load more</button><div id="details"></div>
<script>
const transcript = '<p><strong>Your prompt:</strong><br>Question one</p>'+
  '<p><strong>Search\'s response:</strong><br>Answer one</p><pre>def example():\n    return "Your prompt:"</pre>'+
  '<h1>Your prompt:</h1><p>Question two</p>'+
  '<p><strong>Search\'s response:</strong><br>Answer two &amp; detail</p>';
function add(title, stamp, body) {
 const card=document.createElement('div');
 card.setAttribute('role','listitem');
 card.setAttribute('aria-label','Card showing an activity from AI mode');
 const del=document.createElement('button');del.setAttribute('aria-label','Delete activity item '+title);card.append(del);
 const open=document.createElement('button');open.setAttribute('aria-label',"Open details of activity 'Searched for "+title+"'");
 open.textContent='Details';card.append(open);
 open.onclick=()=>{
   document.getElementById('details').innerHTML='<div class="LmDcAe W86oB">'+
    '<button aria-label="Close this dialogue">Close</button><div class="ETHINc"><div class="jiqmSb">'+stamp+
    '</div></div><div class="w8Zere">'+body+'</div></div>';
   document.querySelector('[aria-label="Close this dialogue"]').onclick=()=>{document.getElementById('details').innerHTML='';};
 };
 document.getElementById('history').append(card);
}
const short='<p><strong>Your prompt:</strong><br>Repeated</p><p><strong>Search\'s response:</strong><br>Response</p>';
add('first','6 October 2026 at 06:56',transcript);
add('same title','5 October 2026 at 10:00',short);
document.getElementById('more').onclick=()=>{add('same title','5 October 2026 at 10:00',short);document.getElementById('more').hidden=true;};
</script></body></html>'''


@unittest.skipUnless(os.environ.get("SCANNER_BROWSER_TEST") == "1" and importlib.util.find_spec("playwright"),
                     "Optional: set SCANNER_BROWSER_TEST=1 with a test Chromium installed")
class BrowserTests(unittest.TestCase):
    def test_all_pages_all_turns_and_repeat_scan(self):
        from playwright.sync_api import sync_playwright
        test_root=Path(os.environ.get("SCANNER_TEST_TEMP", ".scanner-test-temp")).resolve()
        test_root.mkdir(parents=True,exist_ok=True)
        temporary=tempfile.TemporaryDirectory(dir=test_root)
        folder=Path(temporary.name)
        store=scanner.Store(folder/"archive.sqlite3")
        cfg={"base":folder,"data_dir":"archive","timezone":"Europe/London",
             "account_namespace":"offline-fixture","handlers":[],"max_pages":0}
        try:
            with sync_playwright() as p:
                if not Path(p.chromium.executable_path).is_file():
                    self.skipTest("Optional browser fixture needs an installed Playwright Chromium; Opera mode does not")
                browser=p.chromium.launch(headless=True)
                try:
                    page=browser.new_page()
                    page.route("**/*",lambda route: route.fulfill(status=200,content_type="text/html",body=FIXTURE))
                    scanner.scan(page,store,cfg,threading.Event())
                    self.assertEqual(store.status()["activities"],3)
                    self.assertEqual(store.status()["message_versions"],8)
                    scanner.scan(page,store,cfg,threading.Event())
                    self.assertEqual(store.status()["message_versions"],8)
                    import json
                    messages=[json.loads(r[0]) for r in store.db.execute("SELECT payload FROM events")]
                    answer=next(m for m in messages if 'def example():' in m["text"])
                    self.assertEqual(answer["role"],"assistant")
                    self.assertIn('    return "Your prompt:"',answer["text"])
                    self.assertIn('Answer two & detail',[m["text"].strip() for m in messages])
                finally:
                    browser.close()
        finally:
            store.db.close()
            assert folder.resolve().parent==test_root
            temporary.cleanup()


if __name__=="__main__":
    unittest.main()
