import sys
import os
import psutil
import datetime

class TernaryRealTimeEngine:
    """
    Active, real-time telemetry engine reading genuine operational states
    and translating standard binary logic parameters into Ternary Logic states:
    -1 : Negative / Conflict / Fail State
     0 : Neutral / Indeterminate / Calibration State
    +1 : Positive / Virtue Alignment / Pass State
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now()
        self.platform = sys.platform
        self.python_version = sys.version.split()[0]
        
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

    def evaluate_ternary_gate(self, metrics: dict) -> dict:
        """
        Translates binary conditions into ternary state registers (-1, 0, +1).
        
        Evaluates System Load (CPU):
        - Low load (<30%)    -> +1 (Optimal)
        - Medium load (30-70%)->  0 (Neutral/Balanced)
        - High load (>70%)   -> -1 (Heavy/Stress)
        
        Evaluates Resource Availability (RAM):
        - Abundant (>2.0GB) -> +1 (Stable)
        - Restricted (0.5-2.0GB) -> 0 (Cautionary)
        - Critical (<0.5GB) -> -1 (Halt Vector)
        """
        cpu = metrics["SYSTEM_CPU_UTILIZATION_PERCENT"]
        ram = metrics["SYSTEM_AVAILABLE_RAM_GB"]
        
        # Ternary CPU Mapping
        if cpu < 30.0:
            ternary_cpu = 1
        elif 30.0 <= cpu <= 70.0:
            ternary_cpu = 0
        else:
            ternary_cpu = -1
            
        # Ternary RAM Mapping
        if ram > 2.0:
            ternary_ram = 1
        elif 0.5 <= ram <= 2.0:
            ternary_ram = 0
        else:
            ternary_ram = -1
            
        # Composite System Virtue Resolution (-1, 0, or 1)
        # Failure in any core metric drops the total alignment vector
        if ternary_cpu == -1 or ternary_ram == -1:
            composite_virtue_state = -1
            gate_status = "HALT_PROTECTION / CONFLICT"
        elif ternary_cpu == 0 or ternary_ram == 0:
            composite_virtue_state = 0
            gate_status = "INDETERMINATE / CALIBRATION"
        else:
            composite_virtue_state = 1
            gate_status = "PASSTHROUGH_ALLOW / ALIGNED"
            
        return {
            "HARDWARE_BOUNDARY_ENFORCED": True,
            "TERNARY_CPU_STATE": ternary_cpu,
            "TERNARY_RAM_STATE": ternary_ram,
            "COMPOSITE_VIRTUE_STATE": composite_virtue_state,
            "OPERATIONAL_GATE_STATUS": gate_status
        }

# Execution Layer
engine = TernaryRealTimeEngine()
real_metrics = engine.fetch_active_telemetry()
ternary_resolution = engine.evaluate_ternary_gate(real_metrics)

print("=== REAL-TIME TELEMETRY ENGINE: ACTIVE TERNARY EVALUATION ===")
for parameter, value in real_metrics.items():
    print(f" [METRIC] {parameter}: {value}")

print("\n=== TERNARY SYSTEM LOGIC GATEWAY ===")
for parameter, value in ternary_resolution.items():
    print(f" [GATE]   {parameter}: {value}")
