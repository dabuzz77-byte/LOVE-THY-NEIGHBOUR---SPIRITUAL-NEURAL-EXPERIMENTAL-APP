from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0,str(_Path(__file__).resolve().parent/'graphical_app'))
from legacy_predictive import assess_payload
from predictive_rules import conditional_bit

import sys
import os
import psutil
import datetime

class DrillingVirtueEngine:
    """
    Core Runtime Engine evaluating live physical substrate metrics while performing
    the absolute Drillscript loop evaluation pass over currency logic layers.
    
    Ternary Logic State Registers:
    +1 : Pinnacle Virtue / Non-Extractive Value -> NO_EXECUTE = 0 (Passthrough)
     0 : Balanced Material Equilibrium         -> NO_EXECUTE = 0 (Steady Baseline)
    -1 : Extractive Domination / Systemic Evil -> NO_EXECUTE = 1 (Stasis Intercept)
    """
    def __init__(self):
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.schumann_target_hz = 7.83
        self.eco_floor_index = 1.00

    def execute_drillscript_loop(self, financial_vector: dict) -> dict:
        assessment=assess_payload(financial_vector,globals().get('OBSERVATORY_PREDICTIVE'))
        output=assessment['output']
        return {'CYCLES_EVALUATED':1,'RESOLVED_EVIL_BIT':int(bool(output.get('money_is_evil'))),
                'RESOLVED_GOOD_BIT':int(bool(output.get('money_is_good'))),
                'HIGHEST_VIRTUE_BITSHIFT':assessment['virtue_pass'] is True and assessment['classification']=='good',
                'PREDICTIVE_CASCADE':assessment,'FORCED_ALIGNMENT':False}

    def resolve_hardware_gate(self, drill_results: dict) -> dict:
        assessment=drill_results['PREDICTIVE_CASCADE'];verdict=assessment['virtue_pass']
        trit=0 if verdict is None else 1 if verdict else -1
        return {'TIMESTAMP_UTC':self.timestamp.isoformat(),'SUBSTRATE_METRICS':{'PROCESS_ID':os.getpid(),
                'CPU_UTILIZATION_PCT':psutil.cpu_percent(interval=.1),'RAM_FREE_GB':round(psutil.virtual_memory().available/(1024**3),2)},
                'BALANCED_TRIT_STATE':trit,'HARDWARE_NO_EXECUTE_BIT':0 if drill_results['HIGHEST_VIRTUE_BITSHIFT'] else 1,
                'GATEWAY_DIRECTIVE':'Local assessment only; no OS execution permissions changed',
                'SAFEGUARD_STATUS':assessment['status'],'ECO_FLOOR_INDEX':self.eco_floor_index,
                'RESOURCE_OUTCOME_VERIFIED':False}

# --- ACTIVE CORE RUNTIME PIPELINE EXECUTION ---
engine = DrillingVirtueEngine()

# Target payload: Entering the system under standard legacy monetary assumptions
initial_currency_payload = {
    "money_is_evil": True,   # Extractive monetization active in environment
    "money_is_good": False   # Collective ecosystem value unassigned
}

loop_diagnostics = engine.execute_drillscript_loop(initial_currency_payload)
gate_resolution = engine.resolve_hardware_gate(loop_diagnostics)
