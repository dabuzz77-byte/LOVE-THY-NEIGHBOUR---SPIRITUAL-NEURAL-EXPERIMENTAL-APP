"""Thread-safe profile weights and simulated counters from the supplied ledger.

The original defaults and sky-elevator arithmetic are retained. The desktop app
persists this state together with the classifier in a JSON session file.
"""
import math
import threading

DEFAULT_TARGETS = [0.90, 0.95, 0.85, 0.90, 0.95]
DEFAULT_NODES = {"upper_floor_wealth": 1000.0, "lowest_floor_baseline": 250.0,
                 "lowest_floor_current": 50.0}


def finite_number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number.")
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}.")
    return value


def weight_vector(values):
    if not isinstance(values, (list, tuple)) or len(values) != 5:
        raise ValueError("Provide exactly five profile weights.")
    return [finite_number(v, "Weight", 0, 1) for v in values]


class StructuralStateLedger:
    def __init__(self):
        self.lock = threading.RLock()
        self.current_weights = [0.2] * 5
        self.target_profile = list(DEFAULT_TARGETS)
        self.mean_system_integrity = 0.2
        self.nodes = dict(DEFAULT_NODES)

    def get_weights(self):
        with self.lock:
            return list(self.current_weights), list(self.target_profile), self.mean_system_integrity

    def update_weights(self, new_weights, mean_integrity):
        weights = weight_vector(new_weights)
        mean = finite_number(mean_integrity, "Mean integrity", 0, 1)
        if not math.isclose(mean, sum(weights) / 5, abs_tol=1e-10):
            raise ValueError("Mean integrity must equal the mean of the five weights.")
        with self.lock:
            self.current_weights = weights
            self.mean_system_integrity = mean

    def set_targets(self, targets):
        targets = weight_vector(targets)
        with self.lock:
            self.target_profile = targets

    def read_ledger(self):
        with self.lock:
            return dict(self.nodes)

    def execute_sky_elevator(self):
        with self.lock:
            current = self.nodes["lowest_floor_current"]
            target = self.nodes["lowest_floor_baseline"]
            if current < target:
                shortfall = target - current
                self.nodes["lowest_floor_current"] += shortfall
                return (f"Sky Elevator Logged: Uplifted lower floor by +{shortfall} units. "
                        f"Upper floor protected at {self.nodes['upper_floor_wealth']}.")
            return "System in structural equilibrium. No adjustment required."

    def reset_counters(self):
        with self.lock:
            self.nodes = dict(DEFAULT_NODES)

    def to_dict(self):
        with self.lock:
            return {"current_weights": list(self.current_weights), "target_profile": list(self.target_profile),
                    "mean_system_integrity": self.mean_system_integrity, "nodes": dict(self.nodes)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Invalid ledger checkpoint.")
        result = cls()
        result.update_weights(data.get("current_weights"), data.get("mean_system_integrity"))
        result.set_targets(data.get("target_profile"))
        nodes = data.get("nodes")
        if not isinstance(nodes, dict) or set(nodes) != set(DEFAULT_NODES):
            raise ValueError("Invalid ledger counters.")
        result.nodes = {key: finite_number(nodes[key], key, 0, 1e12) for key in DEFAULT_NODES}
        return result

    def restore(self, data):
        validated = self.from_dict(data)
        with self.lock:
            self.current_weights = list(validated.current_weights)
            self.target_profile = list(validated.target_profile)
            self.mean_system_integrity = validated.mean_system_integrity
            self.nodes = dict(validated.nodes)
