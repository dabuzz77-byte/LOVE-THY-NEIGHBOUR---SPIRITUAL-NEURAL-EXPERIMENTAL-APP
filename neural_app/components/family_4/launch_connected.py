"""Run a Python entry point with a cooperative bus and stdout capture.

The program sees MESH_BUS and MESH_INBOX in globals. Optionally define
hydrogen_on_event(event) to handle inbound events in the bus worker thread.
GUI programs should read MESH_INBOX on their own GUI event loop instead.
"""
import io
import os
from pathlib import Path
import queue
import sys
from neural_app import section_threads as threading
import time
from .mesh_client import MeshClient

def main():
    script = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    sys.path.insert(0, str(script.parent))
    inbox = queue.Queue(maxsize=512)
    ns = {'__name__': '__main__', '__file__': str(script), '__package__': None, '__spec__': None, 'MESH_INBOX': inbox}

    def receive(event):
        callback = ns.get('hydrogen_on_event')
        if callable(callback):
            callback(event)
        else:
            inbox.put(event, timeout=5)
    client = MeshClient(script.stem + '-' + str(os.getpid()), on_event=receive)
    ns['MESH_BUS'] = client

    class Output(io.TextIOBase):

        def __init__(self, original):
            self.original = original
            self.buffered = ''
            self.omitted = 0
            self.lock = threading.RLock()
            self.done = threading.Event()
            self.relay = threading.Thread(target=self.send_loop, daemon=True)
            self.relay.start()

        def write(self, text):
            if self.original:
                self.original.write(text)
            with self.lock:
                room = max(0, 32768 - len(self.buffered))
                self.buffered += text[:room]
                self.omitted += max(0, len(text) - room)
            return len(text)

        def send_loop(self):
            for _shared_tick in range(1):
                with self.lock:
                    text = self.buffered[:8000]
                    self.buffered = self.buffered[8000:]
                    omitted = self.omitted
                    self.omitted = 0
                if text or omitted:
                    try:
                        client.publish('process.stdout', {'text': text, 'pid': os.getpid(), 'omitted_characters': omitted, 'scope': 'Rate-limited stdout preview; local logs rotate separately'})
                    except Exception:
                        pass

        def flush(self):
            if self.original:
                self.original.flush()
    old = sys.stdout
    output = Output(old)
    sys.stdout = output
    sys.argv = [str(script)] + args
    try:
        exec(compile(script.read_bytes(), str(script), 'exec'), ns)
    finally:
        sys.stdout = old
        output.done.set()
        output.relay.join(timeout=1)
        client.close()
