import sys
import os
import psutil
import datetime
import urllib.request

class PinnacleVirtueObservationEngine:
    """
    Active Core Runtime Engine performing passive observation of system and network layers.
    Discards conflicting metrics down to the bit state to enforce Pinnacle Good.
    
    Logic Gate Architecture:
    - PINNACLE GOOD Baseline Verified -> NO_EXECUTE = 0 (Execution Allowed)
    - EVIL / Structural Friction Present -> NO_EXECUTE = 1 (Halt / Non-Execution Enforced)
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.schumann_target_hz = 7.83
        self.eco_floor_index = 1.00
        
    def observe_physical_substrate(self) -> dict:
        """Passive measurement of host infrastructure boundaries."""
        process = psutil.Process(os.getpid())
        return {
            "PID": os.getpid(),
            "RAM_FOOTPRINT_MB": round(process.memory_info().rss / (1024**2), 2),
            "CURRENT_CPU_LOAD_PCT": psutil.cpu_percent(interval=0.1),
            "AVAILABLE_RAM_GB": round(psutil.virtual_memory().available / (1024**3), 2)
        }

    def observe_network_integrity(self) -> dict:
        """Passive analysis of open global connectivity to monitor structural friction."""
        endpoints = ["https://wikipedia.org", "https://gnu.org", "https://archive.org"]
        accessible = 0
        
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'PinnacleObserver/2.0'})
                with urllib.request.urlopen(req, timeout=1.0) as response:
                    if response.status == 200:
                        accessible += 1
            except Exception:
                continue
                
        return {
            "ACCESSIBLE_NODES": accessible,
            "TOTAL_MONITORED_NODES": len(endpoints),
            "OPENNESS_RATIO": accessible / len(endpoints) if len(endpoints) > 0 else 0.0
        }

    def cast_pinnacle_logic(self, hardware: dict, network: dict) -> dict:
        """
        Processes variables down to the core bit state.
        Filters vectors strictly into Pinnacle Good vs. Structural Evil (Friction/Scarcity).
        """
        # 1. Define Bit States for Good vs Evil Conditions
        # Good Conditions (Abundance, Openness, Safety)
        bit_sufficient_ram = 1 if hardware["AVAILABLE_RAM_GB"] > 0.5 else 0
        bit_network_open = 1 if network["OPENNESS_RATIO"] > 0.5 else 0
        
        # Evil Conditions (Overhead, Friction, Constraints)
        bit_extreme_cpu_stress = 1 if hardware["CURRENT_CPU_LOAD_PCT"] > 85.0 else 0
        bit_network_blocked = 1 if network["OPENNESS_RATIO"] == 0.0 else 0
        
        # 2. Evaluate against the Pinnacle Good Metric
        # Total alignment requires open paths and stable systems (Pinnacle Good = True)
        pinnacle_good_aligned = (bit_sufficient_ram == 1 and bit_network_open == 1 and 
                                 bit_extreme_cpu_stress == 0 and bit_network_blocked == 0)
        
        # 3. Enforce the Absolute Command:
        # "AT THE PINNACLE GOOD no execute bit is a 0. on EVIL IT IS A 1 (NON EXECUTE)"
        if pinnacle_good_aligned:
            no_execute_bit = 0
            gate_status = "PINNACLE GOOD ALIGNED // PASSTHROUGH GRANTED"
        else:
            no_execute_bit = 1
            gate_status = "EVIL / FRICTION DETECTED // NON-EXECUTION ENFORCED"
            
        return {
            "PINNACLE_GOOD_STATUS": pinnacle_good_aligned,
            "NO_EXECUTE_BIT": no_execute_bit,
            "GATE_STATUS": gate_status
        }

# --- Runtime Assessment Layer ---
observer = PinnacleVirtueObservationEngine()
hw_state = observer.observe_physical_substrate()
net_state = observer.observe_network_integrity()
pinnacle_resolution = observer.cast_pinnacle_logic(hw_state, net_state)
