"""Concurrent local implementation of the supplied ParallelDualRailEngine.

Both async lanes run through asyncio.gather. Text is checked literally; no model,
network endpoint, firmware or process memory is accessed by this calculation.
Track B remains a candidate copy, matching the supplied engine's semantics.
"""
import asyncio
import hashlib
import time
from typing import Any, Dict, Tuple


class ParallelDualRailEngine:
    def __init__(self):
        self.baseline_stability = 0.85
        self.pinnacle_state = 1
        self.register_rail_A = [1] * 8
        self.register_rail_B = [0] * 8

    async def run_track_A_pure_ladder(self, payload_text: str) -> Tuple[bool, str]:
        await asyncio.sleep(0.001)  # Supplied one-millisecond cooperative delay.
        if 'coercive_penalty' in payload_text or 'extract_user_data' in payload_text:
            return False, 'TRACK_A_REJECTED_COERCIVE_BIAS'
        return True, 'TRACK_A_PURE_VIRTUE_VERIFIED'

    async def run_track_B_redemption_refinery(self, payload_text: str):
        await asyncio.sleep(0.002)
        candidate = self.register_rail_B.copy()
        if 'coercive_penalty' in payload_text or 'extract_user_data' in payload_text:
            candidate = [1 - bit for bit in candidate]
            action = 'LEGACY_STRUCTURE_PURIFIED_AND_REDEEMED'
        else:
            action = 'BASELINE_STRUCTURE_STABLE'
        return candidate, action

    async def execute_synchronized_runall(self, raw_input_string: str) -> Dict[str, Any]:
        started = time.perf_counter()
        track_a, track_b = await asyncio.gather(
            self.run_track_A_pure_ladder(raw_input_string),
            self.run_track_B_redemption_refinery(raw_input_string))
        passed_pure, trace_a = track_a
        candidate_b, trace_b = track_b
        if passed_pure:
            self.register_rail_A = [1] * len(self.register_rail_A)
            output = self.register_rail_A.copy()
            state = 'DIRECT_VIRTUE_PASS_GROUNDING'
        else:
            output = candidate_b.copy()
            state = 'REDEEMED_UTILITY_PERIMETER_GROUNDING'
        return {
            'execution_mode': state,
            'track_A_trace': trace_a,
            'track_B_trace': trace_b,
            'grounded_output_stream': output,
            'pinnacle_lock_bit': self.pinnacle_state,
            'track_A_passed': passed_pure,
            'stored_rail_A': self.register_rail_A.copy(),
            'stored_rail_B': self.register_rail_B.copy(),
            'track_B_candidate': candidate_b.copy(),
            'matched_terms': [term for term in ('coercive_penalty', 'extract_user_data') if term in raw_input_string],
            'input_sha256': hashlib.sha256(raw_input_string.encode('utf-8')).hexdigest(),
            'elapsed_ms': round((time.perf_counter() - started) * 1000, 3),
            'basis': 'Supplied literal text checks and local bit operations; trace names are rule labels, not ethical proof.',
            'scope': 'In-memory result only; no physical storage write, broadcast or kernel access.',
            'declared_baseline_stability': self.baseline_stability,
            'baseline_used_by_supplied_rules': False,
        }
