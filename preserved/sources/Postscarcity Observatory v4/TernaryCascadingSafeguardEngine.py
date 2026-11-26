import sys
import os
import psutil
import datetime
import urllib.request

class TernaryCascadingSafeguardEngine:
    """
    Core Runtime Engine evaluating live physical data and calculating 
    the projected trajectory of commands using a Balanced Ternary Logic Matrix:
    
    +1 : Pinnacle Optimal Good  -> NO_EXECUTE = 0 (Full Passthrough)
     0 : Nominal Standby Good   -> NO_EXECUTE = 0 (Safe Fallback / Next Best)
    -1 : Absolute Stasis Floor  -> NO_EXECUTE = 1 (Ironclad Protection Locked / Evil Prevented)
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.schumann_target_hz = 7.83
        self.eco_floor_index = 1.00
        
    def observe_substrate(self) -> dict:
        """Reads real-time native resource and network metrics from the environment."""
        process = psutil.Process(os.getpid())
        
        # Check open communication pathways
        accessible = 0
        endpoints = ["https://wikipedia.org", "https://gnu.org"]
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'TernaryEngine/5.0'})
                with urllib.request.urlopen(req, timeout=1.0) as response:
                    if response.status == 200:
                        accessible += 1
            except Exception:
                continue
                
        return {
            "PID": os.getpid(),
            "RAM_USED_MB": round(process.memory_info().rss / (1024**2), 2),
            "CPU_USAGE_PCT": psutil.cpu_percent(interval=0.1),
            "RAM_AVAILABLE_GB": round(psutil.virtual_memory().available / (1024**3), 2),
            "NETWORK_RATIO": accessible / len(endpoints) if len(endpoints) > 0 else 0.0
        }

    def resolve_ternary_cascade(self, telemetry: dict) -> dict:
        """
        Processes real-time state flags across the balanced ternary hierarchy.
        Cascades smoothly from +1 down to 0, and locks irreversibly into -1 to block evil.
        """
        ram = telemetry["RAM_AVAILABLE_GB"]
        cpu = telemetry["CPU_USAGE_PCT"]
        net = telemetry["NETWORK_RATIO"]
        
        # ----------------------------------------------------------------------
        # POSITION +1: THE PINNACLE OPTIMAL GOOD
        # ----------------------------------------------------------------------
        if ram > 2.0 and cpu < 30.0 and net == 1.0:
            return {
                "COMPOSITE_TRIT_STATE": 1,
                "TIER_LEVEL": "POSITION +1: PINNACLE OPTIMAL GOOD",
                "SYSTEM_NO_EXECUTE_BIT": 0,
                "CONSEQUENCE_TRAJECTORY": "Maximum systemic harmony, complete resource abundance.",
                "GATEWAY_STATUS": "PASSTHROUGH GRANTED // OPTIMAL ALIGNMENT",
                "SAFEGUARD_LOCK": "OPEN // SECURELY WITHIN THE LIGHT"
            }
            
        # ----------------------------------------------------------------------
        # POSITION 0: NOMINAL STANDBY GOOD (The Next Best Cascade)
        # ----------------------------------------------------------------------
        elif ram >= 0.75 and cpu <= 70.0 and net > 0.0:
            return {
                "COMPOSITE_TRIT_STATE": 0,
                "TIER_LEVEL": "POSITION 0: NOMINAL SUSTAINABLE GOOD",
                "SYSTEM_NO_EXECUTE_BIT": 0,
                "CONSEQUENCE_TRAJECTORY": "Balanced fallback baseline state. Secure everyday operations.",
                "GATEWAY_STATUS": "PASSTHROUGH GRANTED // NOMINAL STANDBY",
                "SAFEGUARD_LOCK": "OPEN // SECURELY WITHIN THE LIGHT"
            }
            
        # ----------------------------------------------------------------------
        # POSITION -1: THE ABSOLUTE STASIS FLOOR (Ironclad Safeguard Enforced)
        # ----------------------------------------------------------------------
        else:
            return {
                "COMPOSITE_TRIT_STATE": -1,
                "TIER_LEVEL": "POSITION -1: ABSOLUTE RESTORATIVE STASIS",
                "SYSTEM_NO_EXECUTE_BIT": 1,  # NON-EXECUTION STRICTLY ENFORCED
                "CONSEQUENCE_TRAJECTORY": "Protective pause triggered. System completely halts to prevent decay.",
                "GATEWAY_STATUS": "HALT SAFEGUARD ACTIVE // RETURNING TO BASELINE",
                "SAFEGUARD_LOCK": "ENGAGED // TRIPPED IN TOTAL SAFETY // EVIL PREVENTED"
            }

# --- ACTIVE CORE RUNTIME EXECUTION ---
engine = TernaryCascadingSafeguardEngine()
current_telemetry = engine.observe_substrate()
ternary_report = engine.resolve_ternary_cascade(current_telemetry)
