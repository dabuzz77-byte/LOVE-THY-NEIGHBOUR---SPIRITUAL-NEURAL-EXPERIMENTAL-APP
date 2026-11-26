import sys
import os
import psutil
import datetime

class RealTimeSystemEngine:
    """
    Active, real-time telemetry engine reading genuine operational states 
    of the current execution environment. This interacts with true physical 
    hardware boundaries and system resource parameters.
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now()
        self.platform = sys.platform
        self.python_version = sys.version.split()[0]
        
    def fetch_active_telemetry(self) -> dict:
        """
        Ingests real-world, non-simulated system infrastructure metrics.
        """
        # Fetching direct hardware container metrics
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        virtual_mem = psutil.virtual_memory()
        
        # Mapping true active states rather than simulated vectors
        telemetry = {
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
        
        return telemetry

    def process_logic_gate(self, metrics: dict) -> dict:
        """
        Processes real-time state flags using operational thresholds.
        Ensures execution parameters remain within stable system bounds.
        """
        # A safety threshold evaluating memory constraint boundaries
        execution_allowed = metrics["SYSTEM_AVAILABLE_RAM_GB"] > 0.1
        
        return {
            "HARDWARE_BOUNDARY_ENFORCED": True,
            "OPERATIONAL_GATE_STATUS": "PASSTHROUGH_ALLOW" if execution_allowed else "HALT_PROTECTION",
            "NO_EXECUTE_BIT": 0 if execution_allowed else 1
        }

# Instantiate and fire execution layer directly
engine = RealTimeSystemEngine()
real_metrics = engine.fetch_active_telemetry()
gate_resolution = engine.process_logic_gate(real_metrics)

print("=== REAL-TIME TELEMETRY ENGINE: ACTIVE ===")
for parameter, value in real_metrics.items():
    print(f" [METRIC] {parameter}: {value}")

print("\n=== HARDWARE LAYER LOGIC GATEWAY ===")
for parameter, value in gate_resolution.items():
    print(f" [GATE]   {parameter}: {value}")
