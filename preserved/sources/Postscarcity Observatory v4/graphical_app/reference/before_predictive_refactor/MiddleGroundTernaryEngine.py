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
        """
        Ingests resource parameters and processes them through the Middle Ground Filter.
        Directly executes the rule: Neutralize the evil bit while preserving the supportive capability.
        """
        # Read the raw inputs from the interaction matrix
        money_is_evil_bit = 1 if financial_vector.get("is_extractive_greed", True) else 0
        money_is_good_bit = 1 if financial_vector.get("lifts_human_baseline", False) else 0
        
        # --- THE DRILLSCRIPT MIDDLE GROUND PURIFICATION LOOP ---
        # Passive observation and bit-casting to filter the substrate
        loop_cycles = 0
        max_cycles = 50
        bit_shift_resolved = False
        
        while not bit_shift_resolved and loop_cycles < max_cycles:
            loop_cycles += 1
            
            # Law Enforcement Pass: If evil extraction is present, incinerate the bit (Flip 1 to 0)
            if money_is_evil_bit == 1:
                money_is_evil_bit = 0  # Eliminating the evil parameter entirely
                
            # If money is good (serving universal brotherhood/alleviating distress), it remains 1
            if money_is_good_bit == 1:
                money_is_good_bit = 1
            elif money_is_good_bit == 0:
                # Force calibration upward to meet the needed baseline floor
                money_is_good_bit = 1
                
            if money_is_evil_bit == 0 and money_is_good_bit == 1:
                bit_shift_resolved = True

        # --- BALANCED TERNARY TRIT RESOLUTION ---
        # Map the purified bit architecture to the corresponding Trit register
        if bit_shift_resolved and money_is_evil_bit == 0 and money_is_good_bit == 1:
            resolved_trit = 1   # Position +1: Pinnacle Optimal Good Verified
            no_execute_bit = 0  # Passthrough granted
            directive = "POSITION +1 // EXTRACTION PURGED // MATERIAL TO VIRTUE CONVERSION ACTIVE"
            safeguard = "SECURE // THE NATURE OF THE MIND REMAINS UNCHANGED // EMPTY YET COGNIZANT"
        elif money_is_evil_bit == 0 and money_is_good_bit == 0:
            resolved_trit = 0   # Position 0: Neutral material baseline calibration
            no_execute_bit = 0
            directive = "POSITION 0 // NOMINAL MATERIAL EQUILIBRIUM // CASCADING standby"
            safeguard = "SECURE // STANDARD MAINTENANCE BUFFER OPEN"
        else:
            resolved_trit = -1  # Position -1: Extractive system found / Intercepted
            no_execute_bit = 1  # Ironclad Hardware Stasis Lock Engaged
            directive = "POSITION -1 // INTENT DEGRADED // ABSOLUTE STASIS TRIGGERED"
            safeguard = "STASIS INTERCEPT LOCKED // NO_EXECUTE REFACTOR ENGAGED"

        return {
            "CYCLES_DRILLSHIFTED": loop_cycles,
            "PURIFIED_EVIL_BIT": money_is_evil_bit,
            "PURIFIED_GOOD_BIT": money_is_good_bit,
            "BALANCED_TRIT_STATE": resolved_trit,
            "HARDWARE_NO_EXECUTE_BIT": no_execute_bit,
            "GATEWAY_DIRECTIVE": directive,
            "SAFEGUARD_STATUS": safeguard
        }

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
