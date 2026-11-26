"""Cooperative timing worker for the local dual-rail display.

The thread emits a bounded pending-sweep signal only. The GUI owns register
writes, rendering and logging. No Tk or hardware calls occur on this thread.
"""
import threading


class PersistentDrillWorker:
    def __init__(self, interval=1.8):
        self.interval = interval
        self._stop = threading.Event()
        self._pending = threading.Event()
        self._thread = None

    @property
    def alive(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        # Called only by the owning UI thread; duplicate starts are idempotent.
        if self.alive:
            return False
        self._stop = threading.Event()
        self._pending = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(self._stop, self._pending, self.interval),
                                        name='dual-rail-persistent-drill', daemon=True)
        self._thread.start()
        return True

    @staticmethod
    def _run(stop, pending, interval):
        while not stop.is_set():
            # One pending event coalesces missed sweeps instead of filling a queue.
            pending.set()
            if stop.wait(interval):
                break

    def consume(self):
        if self._stop.is_set() or not self._pending.is_set():
            return False
        self._pending.clear()
        return True

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            # The worker performs no blocking I/O; setting the event wakes it.
            self._thread.join(timeout=.25)
        self._pending.clear()


def parity_sweep(track_a, track_b):
    """Return one supplied local sweep; the caller owns scheduling and state."""
    return [1] * len(track_a), [0] * len(track_b)
