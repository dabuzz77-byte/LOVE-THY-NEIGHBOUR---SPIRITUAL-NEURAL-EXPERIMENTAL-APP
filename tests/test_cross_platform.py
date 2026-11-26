import json
import ssl
import tempfile
import threading
import time
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from neural_app.runtime import Runtime
from neural_app.server import create_server


class CrossPlatformTests(unittest.TestCase):
    def test_intent_permission_ownership_and_pwa_assets_over_tls(self):
        with tempfile.TemporaryDirectory() as d:
            r=Runtime(d);h=r.device_hub
            try:
                h.start(0,False);base='https://127.0.0.1:'+str(h.port)
                context=ssl.create_default_context(cafile=str(h.folder/'gateway-cert.pem'));context.check_hostname=False
                for path in ['/companion.html','/manifest.webmanifest','/sw.js','/icon-192.png']:
                    self.assertEqual(urlopen(base+path,context=context,timeout=10).status,200)
                recv=h.invite('Receive');sender=h.invite('Sender',True)
                with self.assertRaises(PermissionError):h.submit_intent(recv['id'],'Care for life')
                job=h.submit_intent(sender['id'],'  Care\n for life 🌍  ')
                deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    value=h.result(sender['id'],job['id'])
                    if value['status']=='complete':break
                    time.sleep(.1)
                self.assertEqual(value['status'],'complete');self.assertIn('classifier_probability',value)
                with self.assertRaises(PermissionError):h.result(recv['id'],job['id'])
                receipt=r.receipts(value['receipt']);self.assertEqual(receipt['input']['text'],'Care for life 🌍')
            finally:r.close()

    def test_extension_write_only_scope_and_cors(self):
        with tempfile.TemporaryDirectory() as d:
            r=Runtime(d);server=create_server(r,port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                ext='b'*32;origin='chrome-extension://'+ext;pair=r.activity.pair('maintainer@example.invalid',ext)
                base='http://127.0.0.1:'+str(server.server_address[1])
                body={'account':'maintainer@example.invalid','source':'https://myactivity.google.com/myactivity?product=83','records':[{'text':'A private question','date_label':'2026-11-11 12:30'}]}
                headers={'Origin':origin,'X-Neural-Extension-Id':ext,'X-Neural-Activity-Key':pair['key'],'Content-Type':'application/json'}
                req=Request(base+'/api/activity/ingest',data=json.dumps(body).encode(),headers=headers)
                with urlopen(req,timeout=10) as response:
                    self.assertEqual(response.headers['Access-Control-Allow-Origin'],origin)
                    self.assertEqual(json.load(response)['new'],1)
                with self.assertRaises(HTTPError):urlopen(Request(base+'/api/state',headers=headers),timeout=10)
                r.activity.pulse();deadline=time.monotonic()+10
                while time.monotonic()<deadline:
                    r.activity.pulse()
                    if r.activity.view()['counts'].get('complete'):break
                    time.sleep(.1)
                self.assertEqual(r.activity.view()['counts'].get('complete'),1)
                self.assertGreater(r.learning_view()['updates'],0)
            finally:server.shutdown();server.server_close();thread.join(2);r.close()
