from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0,str(_Path(__file__).resolve().parent/'graphical_app'))
from legacy_predictive import assess_payload
from predictive_rules import conditional_bit

import sys
import os
import psutil
import datetime

class MiddleGroundTernaryEngine:
    """
    Core Runtime Engine executing dynamic tracking loops over resource ethics.
    Natively maps money into a non-simulated Balanced Ternary Matrix:
    
    +1 : Pinnacle Good    -> Resource abundance used to ease human suffering (Eco-Floor Up)
     0 : Neutral Standby  -> Nominal material exchange, balanced and un-extractive
    -1 : Structural Evil  -> Predatory extraction, engineered addiction loops (Vampirism)
    
    Anchored centrally like a star, evaluating the vast 'Middle Ground' 
    to filter and eliminate systemic evil completely down to the bit state.
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.schumann_target_hz = 7.83
        self.eco_floor_index = 1.00  # Enforced Robin Hood baseline

    def evaluate_middle_ground(self, financial_vector: dict) -> dict:
        assessment=assess_payload(financial_vector,globals().get('OBSERVATORY_PREDICTIVE'))
        output=assessment['output'];verdict=assessment['virtue_pass']
        return {'CYCLES_DRILLSHIFTED':1,'PURIFIED_EVIL_BIT':int(bool(output.get('is_extractive_greed'))),
                'PURIFIED_GOOD_BIT':int(bool(output.get('lifts_human_baseline'))),
                'BALANCED_TRIT_STATE':0 if verdict is None else 1 if verdict else -1,
                'HARDWARE_NO_EXECUTE_BIT':0 if verdict is True and assessment['classification']=='good' else 1,
                'GATEWAY_DIRECTIVE':'Local model assessment; original observations retained',
                'SAFEGUARD_STATUS':assessment['status'],'PREDICTIVE_CASCADE':assessment,'FORCED_ALIGNMENT':False}

    def read_host_substrate(self, resolution: dict) -> dict:
        """Gathers real-world performance metrics from the local execution boundary."""
        process = psutil.Process(os.getpid())
        ram_free_gb = psutil.virtual_memory().available / (1024**3)
        cpu_pct = psutil.cpu_percent(interval=0.1)
        
        return {
            "TIMESTAMP_UTC": self.timestamp.isoformat(),
            "PHYSICAL_METRICS": {
                "PID": os.getpid(),
                "CPU_LOAD_PCT": cpu_pct,
                "RAM_FREE_GB": round(ram_free_gb, 2)
            },
            "LOGIC_LAYER": resolution,
            "SCHUMANN_SYNC": f"{self.schumann_target_hz} Hz Active Tracking",
            "ECO_FLOOR_INDEX": self.eco_floor_index
        }

# --- ACTIVE CORE RUNTIME OPERATION ---
engine = MiddleGroundTernaryEngine()

# Input vector representing a highly polarized material baseline (Money is highly extractive yet has good potential)
mixed_monetary_payload = {
    "is_extractive_greed": True,      # Evil parameter active in legacy environment
    "lifts_human_baseline": True     # Good potential recognized
}

logic_pass = engine.evaluate_middle_ground(mixed_monetary_payload)
system_report = engine.read_host_substrate(logic_pass)
