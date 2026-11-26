"""The supplied 7.83 Hz gradient update with controllable, clean thread lifecycle."""
from collections import deque
import math
import threading

from .StructuralStateLedger import finite_number


class BackgroundWeightOptimizer(threading.Thread):
    def __init__(self, ledger_reference, clock_speed_hz=7.83):
        super().__init__(name="profile-weight-optimizer", daemon=True)
        self.ledger = ledger_reference
        self.step_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._enabled = threading.Event()
        self.learning_rate = 0.05
        self.interval = 1 / finite_number(clock_speed_hz, "Clock speed", 0.1, 60)
        self.steps = 0
        self.last_error = None
        self.history = deque(maxlen=300)
        self._record()

    @property
    def running(self):
        return self._enabled.is_set() and not self._stop_event.is_set()

    def configure(self, learning_rate, clock_speed_hz):
        rate = finite_number(learning_rate, "Profile learning rate", 0.0001, 1)
        clock = finite_number(clock_speed_hz, "Clock speed", 0.1, 60)
        with self.step_lock:
            self.learning_rate, self.interval = rate, 1 / clock

    def _record(self):
        current, target, mean = self.ledger.get_weights()
        record = {"step": self.steps, "rmse": math.sqrt(sum((a-b)**2 for a,b in zip(current,target))/5),
                  "mean": mean}
        if self.history and self.history[-1]["step"] == self.steps:
            self.history[-1] = record
        else:
            self.history.append(record)
        return record

    def step_once(self):
        with self.step_lock, self.ledger.lock:
            current, target, _ = self.ledger.get_weights()
            updated = [weight + self.learning_rate * (goal - weight) for weight,goal in zip(current,target)]
            self.ledger.update_weights(updated, sum(updated)/len(updated))
            self.steps += 1
            return self._record()

    def run(self):
        while not self._stop_event.wait(self.interval):
            with self.step_lock:
                if self.running:
                    try:
                        self.step_once()
                    except Exception as error:
                        self.last_error = str(error)
                        self._enabled.clear()

    def resume_engine(self):
        if self._stop_event.is_set():
            raise RuntimeError("This optimizer has been shut down.")
        self.last_error = None
        self._enabled.set()

    def pause_engine(self):
        self._enabled.clear()
        with self.step_lock:
            pass  # Wait for any in-flight update before returning.

    def stop_engine(self):
        self._enabled.clear()
        self._stop_event.set()
        if self.is_alive() and threading.current_thread() is not self:
            self.join(timeout=3)

    def snapshot(self):
        with self.step_lock:
            latest = self._record()
            return {"running": self.running, "steps": self.steps, "learning_rate": self.learning_rate,
                    "clock_speed_hz": 1/self.interval, "rmse": latest["rmse"],
                    "last_error": self.last_error, "history": list(self.history)}

    @staticmethod
    def validate_state(data):
        if not isinstance(data, dict):
            raise ValueError("Invalid optimizer checkpoint.")
        rate = finite_number(data.get("learning_rate"), "Profile learning rate", 0.0001, 1)
        clock = finite_number(data.get("clock_speed_hz"), "Clock speed", 0.1, 60)
        steps = data.get("steps")
        if type(steps) is not int or not 0 <= steps <= 10**12:
            raise ValueError("Invalid optimizer step count.")
        history = data.get("history", [])
        if not isinstance(history, list) or len(history) > 300:
            raise ValueError("Invalid optimizer history.")
        previous = -1
        clean = []
        for row in history:
            if not isinstance(row, dict) or type(row.get("step")) is not int or not previous <= row["step"] <= steps:
                raise ValueError("Invalid optimizer history step.")
            previous = row["step"]
            clean.append({"step": previous, "rmse": finite_number(row.get("rmse"), "RMSE", 0, 1),
                          "mean": finite_number(row.get("mean"), "Mean", 0, 1)})
        return rate, clock, steps, clean

    def restore(self, data):
        rate, clock, steps, history = self.validate_state(data)
        self.pause_engine()
        with self.step_lock:
            self.learning_rate, self.interval, self.steps = rate, 1/clock, steps
            self.history = deque(history, maxlen=300)
            self.last_error = None
            self._record()
