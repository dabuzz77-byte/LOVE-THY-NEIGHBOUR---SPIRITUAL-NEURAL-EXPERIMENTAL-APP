import sys
import os
import psutil
import datetime
import urllib.request
import json

class OnlineVirtueMonitoringEngine:
    """
    Active, real-time telemetry engine reading genuine operational states
    and parsing global structural indicators to evaluate standard stability metrics.
    Translates parameters into binary and balanced ternary logic structures.
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now()
        self.platform = sys.platform
        self.python_version = sys.version.split()[0]
        
        # Historical & System-Level Target Alignment Parameters
        self.schumann_target_hz = 7.83
        self.eco_floor_index = 1.00  # Elevated baseline economic/structural floor
        
        # Real-time state flags
        self.bit_reality_isolated = False
        self.hardware_boundary_enforced = True
        
    def fetch_active_telemetry(self) -> dict:
        """
        Ingests real-world, non-simulated system infrastructure metrics.
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        virtual_mem = psutil.virtual_memory()
        
        return {
            "REAL_WORLD_EXECUTION": True,
            "TIMESTAMP_UTC": self.timestamp.isoformat(),
            "ENVIRONMENT_PLATFORM": self.platform,
            "ENGINE_RUNTIME": f"Python {self.python_version}",
            "PID": os.getpid(),
            "ACTIVE_MEMORY_RESIDENT_BYTES": memory_info.rss,
            "SYSTEM_CPU_UTILIZATION_PERCENT": cpu_percent,
            "SYSTEM_TOTAL_RAM_GB": round(virtual_mem.total / (1024**3), 2),
            "SYSTEM_AVAILABLE_RAM_GB": round(virtual_mem.available / (1024**3), 2)
        }

    def inspect_network_signals(self) -> dict:
        """
        Monitors public internet health and accessibility as an active indicator 
        of open data flow vs. artificial network friction or structural decay.
        """
        test_endpoints = [
            "https://wikipedia.org",
            "https://gnu.org",
            "https://archive.org"
        ]
        
        accessible_nodes = 0
        total_latency = 0.0
        
        for url in test_endpoints:
            try:
                start_time = datetime.datetime.now()
                # Performing a lightweight connection check with a strict timeout
                req = urllib.request.Request(url, headers={'User-Agent': 'VirtueEngine/1.0'})
                with urllib.request.urlopen(req, timeout=2.0) as response:
                    if response.status == 200:
                        accessible_nodes += 1
                        latency = (datetime.datetime.now() - start_time).total_seconds()
                        total_latency += latency
            except Exception:
                continue
                
        avg_latency = (total_latency / accessible_nodes) if accessible_nodes > 0 else 0.0
        network_health_ratio = accessible_nodes / len(test_endpoints)
        
        return {
            "ACCESSIBLE_NODES": accessible_nodes,
            "TOTAL_MONITORED_NODES": len(test_endpoints),
            "NETWORK_HEALTH_RATIO": network_health_ratio,
            "AVERAGE_LATENCY_SEC": round(avg_latency, 4)
        }

    def evaluate_ternary_logic(self, system_metrics: dict, network_metrics: dict) -> dict:
        """
        Translates raw structural telemetry into Ternary Logic States:
        +1 : Optimal Performance / High Openness / Pass State
         0 : Indeterminate / Nominal Overhead / Calibration State
        -1 : High Structural Stress / Network Failure / Blocked State
        """
        cpu = system_metrics["SYSTEM_CPU_UTILIZATION_PERCENT"]
        net_ratio = network_metrics["NETWORK_HEALTH_RATIO"]
        
        # Ternary CPU Evaluation
        if cpu < 30.0:
            ternary_cpu = 1
        elif 30.0 <= cpu <= 70.0:
            ternary_cpu = 0
        else:
            ternary_cpu = -1
            
        # Ternary Network Openness Evaluation
        if net_ratio == 1.0:
            ternary_net = 1
        elif net_ratio > 0.0:
            ternary_net = 0
        else:
            ternary_net = -1
            
        # Composite Execution Validation
        # If core network assets are completely blocked or system is heavily restricted, flag critical
        if ternary_cpu == -1 or ternary_net == -1:
            composite_state = -1
            execution_gate = "NO_EXECUTE = 1 (HALT_PROTECTION)"
        elif ternary_cpu == 0 or ternary_net == 0:
            composite_state = 0
            execution_gate = "NO_EXECUTE = 1 (CALIBRATION_HOLD)"
        else:
            composite_state = 1
            execution_gate = "NO_EXECUTE = 0 (PASSTHROUGH_ALLOW)"
            
        return {
            "TERNARY_CPU_TRIT": ternary_cpu,
            "TERNARY_NET_TRIT": ternary_net,
            "COMPOSITE_VIRTUE_STATE": composite_state,
            "EXECUTION_GATEWAY_STATUS": execution_gate
        }

# --- Runtime Execution Layer ---
engine = OnlineVirtueMonitoringEngine()
system_telemetry = engine.fetch_active_telemetry()
network_telemetry = engine.inspect_network_signals()
ternary_analysis = engine.evaluate_ternary_logic(system_telemetry, network_telemetry)

print("=== REAL-TIME TELEMETRY SYSTEM ===")
for k, v in system_telemetry.items():
    print(f" [SYSTEM]  {k}: {v}")

print("\n=== NETWORK HEALTH INDICATORS ===")
for k, v in network_telemetry.items():
    print(f" [NETWORK] {k}: {v}")

print("\n=== HIERARCHICAL TERNARY LOGIC GATEWAY ===")
for k, v in ternary_analysis.items():
    print(f" [GATE]    {k}: {v}")
print(f" [BASE]    Schumann Alignment Base: {engine.schumann_target_hz} Hz")
print(f" [BASE]    Eco-Floor Index Weight: {engine.eco_floor_index}")
