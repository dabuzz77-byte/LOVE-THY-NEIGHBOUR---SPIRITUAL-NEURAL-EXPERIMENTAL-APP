"""Opt-in adapter for an existing Python app; no code injection is performed."""
import queue
from neural_app import section_threads as threading
import time
from ..PostscarcityHub.bus_protocol import BASE, Client

class Attachment:

    def __init__(self, name, on_pulse=None, on_message=None, port=17300, token_file=None):
        self.name, self.on_pulse, self.on_message = (name, on_pulse, on_message)
        self.port, self.token_file = (port, token_file or BASE / 'data' / 'token.txt')
        self.stop = threading.Event()
        self.outgoing = queue.Queue(maxsize=128)
        self.connected = False
        self.error = None
        self.client = None
        self.thread = threading.Thread(target=self._work, name='bus-attachment', daemon=True)
        self.thread.start()

    def publish(self, topic, data):
        """Queue a message or raise queue.Full. Acceptance is not worker completion."""
        self.outgoing.put_nowait((topic, data))

    def _work(self):
        while not self.stop.is_set():
            try:
                with Client(self.port, self.token_file, self.name, ['pulse', 'user.message', 'inference.result']) as client:
                    self.client = client
                    self.connected = True
                    self.error = None
                    last_status = time.monotonic()
                    while not self.stop.is_set():
                        for _ in range(16):
                            try:
                                topic, data = self.outgoing.get_nowait()
                            except queue.Empty:
                                break
                            client.publish(topic, data)
                        message = client.receive()
                        callback = self.on_pulse if message.get('topic') == 'pulse' else self.on_message
                        if callback:
                            try:
                                callback(message)
                            except Exception as exc:
                                self.error = f'Callback failed: {exc}'
                        if time.monotonic() - last_status > 30:
                            client.request('status')
                            last_status = time.monotonic()
            except (OSError, EOFError, ValueError) as exc:
                self.error = str(exc)
            finally:
                self.connected = False
                self.client = None
            self.stop.wait(2)

    def close(self):
        self.stop.set()
        client = self.client
        if client:
            client.close()
        self.thread.join(timeout=3)

def attach(name, **kwargs):
    """Callbacks run on a worker thread; marshal GUI changes onto the GUI thread."""
    return Attachment(name, **kwargs)
