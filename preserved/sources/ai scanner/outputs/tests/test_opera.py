import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ai_mode_scanner as scanner
from opera_tab import OperaTab

VERSION={"Browser":"Chrome/122.0", "User-Agent":"Mozilla/5.0 Chrome/122.0 OPR/108.0",
         "webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/browser/example"}


class OperaTests(unittest.TestCase):
    def test_endpoint_rejects_remote_hosts_paths_and_credentials(self):
        for value in ["http://example.com:9222", "http://127.0.0.1:9222/path",
                      "http://127.0.0.1:9222?x=1", "http://user:pass@127.0.0.1:9222",
                      "https://127.0.0.1:9222", "http://127.0.0.1"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                scanner.opera_endpoint({"opera_cdp_url":value})
        self.assertEqual(scanner.opera_endpoint({}),"http://127.0.0.1:9222")

    def test_endpoint_checks_browser_identity(self):
        opener=MagicMock()
        reply=opener.open.return_value.__enter__.return_value
        with patch.object(scanner,"build_opener",return_value=opener):
            reply.read.return_value=json.dumps(VERSION).encode()
            self.assertEqual(scanner.opera_metadata({}),VERSION)
            reply.read.return_value=json.dumps({"Browser":"Chrome/150","User-Agent":"Chrome/150"}).encode()
            with self.assertRaisesRegex(ValueError,"different browser"):
                scanner.opera_metadata({})

    def test_reuses_session_and_closes_only_new_tab(self):
        playwright=MagicMock()
        with patch.object(scanner,"opera_metadata",return_value=VERSION), \
             patch.object(OperaTab,"open") as open_tab:
            page=open_tab.return_value.__enter__.return_value
            with scanner.scanner_page(playwright,{},"run") as selected:
                self.assertIs(selected,page)
        open_tab.assert_called_once_with("http://127.0.0.1:9222")
        open_tab.return_value.__exit__.assert_called_once()
        playwright.chromium.connect_over_cdp.assert_not_called()
        playwright.chromium.launch_persistent_context.assert_not_called()

    def test_failed_scan_still_leaves_opera_open(self):
        playwright=MagicMock()
        with patch.object(scanner,"opera_metadata",return_value=VERSION), \
             patch.object(OperaTab,"open") as open_tab:
            open_tab.return_value.__exit__.return_value=False
            with self.assertRaisesRegex(RuntimeError,"fixture failure"):
                with scanner.scanner_page(playwright,{},"run"):
                    raise RuntimeError("fixture failure")
        open_tab.return_value.__exit__.assert_called_once()
        playwright.chromium.connect_over_cdp.assert_not_called()

    def test_opera_login_does_not_start_playwright_driver(self):
        import threading
        with patch("playwright.sync_api.sync_playwright") as driver, \
             patch.object(scanner,"scanner_page") as session, \
             patch.object(scanner,"wait_for_history") as ready:
            scanner.browser_run({"browser_mode":"opera"},None,"login",threading.Event())
        driver.assert_not_called()
        ready.assert_called_once_with(session.return_value.__enter__.return_value)

    def test_running_opera_is_not_terminated_or_relaunched(self):
        with patch.object(scanner,"opera_metadata",side_effect=OSError("closed port")), \
             patch.object(scanner,"opera_running",return_value=True), \
             patch.object(scanner.subprocess,"Popen") as launch:
            with self.assertRaisesRegex(RuntimeError,"Opera menu > Exit"):
                scanner.open_opera({})
            launch.assert_not_called()

    def test_ready_opera_is_not_relaunched(self):
        with patch.object(scanner,"opera_metadata",return_value=VERSION), \
             patch.object(scanner.subprocess,"Popen") as launch:
            scanner.open_opera({})
            launch.assert_not_called()

    def test_launcher_uses_normal_profile_without_protection_overrides(self):
        with patch.object(scanner,"opera_metadata",side_effect=[OSError("closed port"),VERSION]), \
             patch.object(scanner,"opera_running",return_value=False), \
             patch.object(scanner.Path,"is_file",return_value=True), \
             patch.object(scanner.subprocess,"Popen") as launch:
            scanner.open_opera({"opera_executable":"C:/Opera/opera.exe"})
        arguments=launch.call_args.args[0]
        self.assertEqual(Path(arguments[0]),Path("C:/Opera/opera.exe"))
        self.assertIn("--remote-debugging-address=127.0.0.1",arguments)
        self.assertIn("--remote-debugging-port=9222",arguments)
        for forbidden in ["--user-data-dir", "--no-sandbox", "--disable-web-security", "--remote-allow-origins"]:
            self.assertFalse(any(arg.startswith(forbidden) for arg in arguments))


if __name__=="__main__":
    unittest.main()
