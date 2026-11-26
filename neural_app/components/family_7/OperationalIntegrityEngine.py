import sys
import os
import psutil
import datetime
import urllib.request

class OperationalIntegrityEngine:
    """
    Core Runtime Engine evaluating live physical infrastructure, network health,
    and translating operational data into definitive Binary and Ternary states.
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.schumann_target_hz = 7.83
        self.eco_floor_index = 1.00
        
    def check_hardware_layer(self) -> dict:
        """Reads true physical boundaries and resource data from the host machine."""
        process = psutil.Process(os.getpid())
        return {
            "PID": os.getpid(),
            "RAM_USED_MB": round(process.memory_info().rss / (1024**2), 2),
            "CPU_USAGE_PCT": psutil.cpu_percent(interval=0.1),
            "RAM_AVAILABLE_GB": round(psutil.virtual_memory().available / (1024**3), 2)
        }

    def check_network_layer(self) -> dict:
        """Evaluates live data flow connectivity across foundational web repositories."""
        endpoints = ["https://wikipedia.org", "https://gnu.org"]
        accessible = 0
        
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'IntegrityEngine/1.0'})
                with urllib.request.urlopen(req, timeout=1.5) as response:
                    if response.status == 200:
                        accessible += 1
            except Exception:
                continue
                
        return {
            "NODES_ONLINE": accessible,
            "TOTAL_NODES": len(endpoints),
            "RATIO": accessible / len(endpoints) if len(endpoints) > 0 else 0.0
        }

    def resolve_logic_states(self, hw: dict, net: dict) -> dict:
        """Translates binary operational thresholds into multi-state ternary outputs."""
        # Binary Threshold Assessment
        binary_hw_pass = 1 if hw["RAM_AVAILABLE_GB"] > 0.5 else 0
        binary_net_pass = 1 if net["RATIO"] > 0.0 else 0
        
        # Ternary Logic Transformation (-1 = Restricted, 0 = Balanced, 1 = Optimal)
        ternary_cpu = 1 if hw["CPU_USAGE_PCT"] < 30.0 else (0 if hw["CPU_USAGE_PCT"] <= 70.0 else -1)
        ternary_net = 1 if net["RATIO"] == 1.0 else (0 if net["RATIO"] > 0.0 else -1)
        
        # System Gate Determination (0 = Go/Execute, 1 = Stop/No_Execute)
        no_execute = 0 if (binary_hw_pass == 1 and ternary_net != -1) else 1
        
        return {
            "BINARY_HW_PASS": binary_hw_pass,
            "BINARY_NET_PASS": binary_net_pass,
            "TERNARY_CPU_STATE": ternary_cpu,
            "TERNARY_NET_STATE": ternary_net,
            "SYSTEM_NO_EXECUTE_BIT": no_execute,
            "GATE_STATUS": "PASSTHROUGH ALLOWED" if no_execute == 0 else "HALT PROTECTION ACTIVE"
        }

# --- ACTIVE CORE RUNTIME EXECUTION ---
engine = OperationalIntegrityEngine()
hardware_metrics = engine.check_hardware_layer()
network_metrics = engine.check_network_layer()
resolved_logic = engine.resolve_logic_states(hardware_metrics, network_metrics)
