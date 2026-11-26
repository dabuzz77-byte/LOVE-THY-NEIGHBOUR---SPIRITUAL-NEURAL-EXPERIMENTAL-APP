import threading
import json

class StructuralStateLedger:
    def __init__(self):
        self.lock = threading.Lock()
        
        # Operational Weights Register
        self.current_weights = [0.2, 0.2, 0.2, 0.2, 0.2]
        self.target_profile = [0.90, 0.95, 0.85, 0.90, 0.95]
        self.mean_system_integrity = 0.2
        
        # Material Asset Inventory (Tangible Real-World Counters)
        self.nodes = {
            "upper_floor_wealth": 1000.0,
            "lowest_floor_baseline": 250.0,
            "lowest_floor_current": 50.0
        }
        
    def get_weights(self):
        with self.lock:
            return list(self.current_weights), list(self.target_profile), self.mean_system_integrity

    def update_weights(self, new_weights, mean_integrity):
        with self.lock:
            self.current_weights = new_weights
            self.mean_system_integrity = mean_integrity

    def read_ledger(self):
        with self.lock:
            return dict(self.nodes)

    def execute_sky_elevator(self) -> str:
        """Raises the lower floor while maintaining and protecting upper floor wealth."""
        with self.lock:
            current = self.nodes["lowest_floor_current"]
            target = self.nodes["lowest_floor_baseline"]
            
            if current < target:
                shortfall = target - current
                self.nodes["lowest_floor_current"] += shortfall
                return f"Sky Elevator Logged: Uplifted lower floor by +{shortfall} units. Upper floor protected at {self.nodes['upper_floor_wealth']}."
            return "System in structural equilibrium. No adjustment required."

# Global singleton storage instantiation for cross-thread access
system_ledger = StructuralStateLedger()
print("[LAYER 1 INITIALISED] Thread-safe Material State Ledger Active.")
