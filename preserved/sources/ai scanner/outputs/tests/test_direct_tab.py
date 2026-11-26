import base64
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import opera_tab as tab
import ai_mode_scanner as scanner

ENDPOINT='http://127.0.0.1:9222'
TARGET={'id':'OWN-TAB','type':'page','webSocketDebuggerUrl':'ws://127.0.0.1:9222/devtools/page/OWN-TAB'}


class DirectTabTests(unittest.TestCase):
    def test_does_not_follow_other_target_or_remote_addresses(self):
        for value in ['ws://remote.example:9222/devtools/page/OWN-TAB',
                      'ws://127.0.0.1:9333/devtools/page/OWN-TAB',
                      'ws://127.0.0.1:9222/devtools/browser/OWN-TAB',
                      'ws://127.0.0.1:9222/devtools/page/SOMEONE-ELSE',
                      'ws://user:pass@127.0.0.1:9222/devtools/page/OWN-TAB']:
            with self.subTest(value=value), self.assertRaises(tab.ProtocolError):
                tab.page_websocket(ENDPOINT,{**TARGET,'webSocketDebuggerUrl':value})
        self.assertEqual(tab.page_websocket(ENDPOINT,TARGET),TARGET['webSocketDebuggerUrl'])

    def test_events_and_unrelated_replies_do_not_complete_command(self):
        ws=MagicMock()
        ws.recv.side_effect=[json.dumps({'method':'Page.frameNavigated'}),
                             json.dumps({'id':0,'result':{'wrong':True}}),
                             json.dumps({'id':1,'result':{'correct':True}})]
        self.assertEqual(tab.CDP(ws).call('Page.enable'),{'correct':True})

    def test_command_deadline_applies_even_with_continuous_events(self):
        ws=MagicMock();ws.recv.return_value=json.dumps({'method':'Page.frameNavigated'})
        connection=tab.CDP(ws)
        with patch.object(tab.time,'monotonic',side_effect=[0,1,11]):
            with self.assertRaises(tab.TabTimeout):
                connection.call('Page.enable',timeout=10)
        self.assertTrue(connection.closed)
        ws.close.assert_called_once()

    def test_timeout_closes_partial_transport_and_names_failed_command(self):
        ws=MagicMock();ws.recv.side_effect=socket.timeout()
        connection=tab.CDP(ws)
        with self.assertRaisesRegex(tab.TabTimeout,'Runtime.evaluate'):
            connection.call('Runtime.evaluate')
        self.assertTrue(connection.closed)
        ws.close.assert_called_once()

    def test_protocol_failure_is_not_reported_as_success(self):
        ws=MagicMock();ws.recv.return_value=json.dumps({'id':1,'error':{'message':'Invalid command'}})
        with self.assertRaisesRegex(tab.ProtocolError,'Invalid command'):
            tab.CDP(ws).call('Page.enable')

    def test_connection_failure_closes_only_new_target(self):
        with patch.object(tab,'local_request',side_effect=[TARGET,b'closed']) as request, \
             patch('websocket.create_connection',side_effect=OSError('fixture failure')):
            with self.assertRaises(OSError):
                with tab.OperaTab.open(ENDPOINT):
                    self.fail('Connection should have failed')
        self.assertEqual([c.args[1] for c in request.call_args_list],
                         ['/json/new?about:blank','/json/close/OWN-TAB'])

    def test_success_and_failure_close_only_owned_tab(self):
        for fail in (False,True):
            with self.subTest(fail=fail):
                ws=MagicMock()
                ws.recv.side_effect=[json.dumps({'id':1,'result':{}}),
                                    json.dumps({'id':2,'result':{'result':{'value':2}}})]
                with patch.object(tab,'local_request',side_effect=[TARGET,b'closed']) as request, \
                     patch('websocket.create_connection',return_value=ws):
                    try:
                        with tab.OperaTab.open(ENDPOINT):
                            if fail: raise ValueError('fixture failure')
                    except ValueError:
                        if not fail: raise
                methods=[json.loads(c.args[0])['method'] for c in ws.send.call_args_list]
                self.assertEqual(methods,['Page.enable','Runtime.evaluate'])
                self.assertEqual([c.args[1] for c in request.call_args_list],
                                 ['/json/new?about:blank','/json/close/OWN-TAB'])
                ws.close.assert_called_once()


@unittest.skipUnless(os.environ.get('SCANNER_OPERA_TEST')=='1',
                     'Optional: SCANNER_OPERA_TEST=1 uses a new disposable Opera tab with synthetic data')
class OperaFixtureTests(unittest.TestCase):
    def test_all_turns_pagination_and_repeated_pass(self):
        from test_browser import FIXTURE
        root=Path(os.environ.get('SCANNER_TEST_TEMP','.scanner-test-temp')).resolve()
        root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as folder:
            folder=Path(folder)
            store=scanner.Store(folder/'fixture.sqlite3')
            cfg={'base':folder,'data_dir':'archive','timezone':'Europe/London',
                 'account_namespace':'offline-fixture','handlers':[],'max_pages':0}
            try:
                with tab.OperaTab.open(ENDPOINT) as page:
                    goto=page.goto
                    fixture_url='data:text/html;base64,'+base64.b64encode(FIXTURE.encode()).decode()
                    page.goto=lambda _url,**kwargs:goto(fixture_url,**kwargs)
                    scanner.scan(page,store,cfg,threading.Event())
                    self.assertEqual(store.status()['activities'],3)
                    self.assertEqual(store.status()['message_versions'],8)
                    scanner.scan(page,store,cfg,threading.Event())
                    self.assertEqual(store.status()['message_versions'],8)
                    messages=[json.loads(row[0]) for row in store.db.execute('SELECT payload FROM events')]
                    answer=next(m for m in messages if 'def example():' in m['text'])
                    self.assertEqual(answer['role'],'assistant')
                    self.assertIn('    return "Your prompt:"',answer['text'])
                    self.assertIn('Answer two & detail',[m['text'].strip() for m in messages])
            finally:
                store.db.close()


if __name__=='__main__':
    unittest.main()
