"""Standard-library connector for a Python program. Only your handler executes input."""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class GenesisConnector:
    def __init__(self, name, handler, url=None, token=None):
        self.name = name
        self.handler = handler
        self.url = (url or os.getenv("GENESIS_URL", "http://127.0.0.1:7860")).rstrip("/")
        self.token = token or os.getenv("GENESIS_TOKEN") or (
            Path(__file__).resolve().parent.parent / "data" / "connector-token"
        ).read_text().strip()
        self.stop_event = threading.Event()
        self.program_id = None
        self.executor = ThreadPoolExecutor(max_workers=1)

    def _request(self, route, data=None, content_type="application/json"):
        request = urllib.request.Request(
            self.url + route,
            data=data,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": content_type},
        )
        return urllib.request.urlopen(request, timeout=10)

    def _handle(self, request_id, text, program_id):
        try:
            output = str(self.handler(text))
        except Exception as error:
            output = "Program handler error: " + str(error)
        try:
            with self._request(
                f"/api/bridge/reply?id={program_id}&request={request_id}",
                output.encode("utf-8")[:99000], "text/plain; charset=utf-8",
            ):
                pass
        except (OSError, urllib.error.URLError):
            # Replies have a 60-second lifetime; do not execute a timed-out message again.
            pass

    def serve_forever(self):
        try:
            while not self.stop_event.is_set():
                try:
                    if not self.program_id:
                        data = json.dumps({"name": self.name, "language": "python", "pid": os.getpid()}).encode()
                        with self._request("/api/bridge/register", data) as response:
                            self.program_id = json.load(response)["id"]
                        print(f"Connected to AI Genesis Node: {self.name}", flush=True)
                    with self._request("/api/bridge/next?id=" + self.program_id) as response:
                        if response.status == 200:
                            self.executor.submit(self._handle, response.headers["X-Genesis-Request-Id"], response.read().decode("utf-8"), self.program_id)
                except (OSError, urllib.error.URLError, ValueError, KeyError):
                    self.program_id = None
                self.stop_event.wait(1)
        finally:
            self.executor.shutdown(wait=False, cancel_futures=True)

    def start(self):
        """Start beside an existing app's main loop; retain the connector to stop it."""
        thread = threading.Thread(target=self.serve_forever, name="genesis-connector", daemon=True)
        thread.start()
        return self

    def stop(self):
        self.stop_event.set()
