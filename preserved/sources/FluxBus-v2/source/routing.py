"""User-defined Boolean model. These values describe the model, not OS permissions.

good: hold; evil: invert. Universal CAN resolves a conflicting local CAN to True
and its corresponding CANNOT to False. Original inputs are always retained.
"""
from dataclasses import dataclass, asdict
import hashlib
import re
from audit import DeepVirtueAuditor, evaluate_high_state, UNIVERSAL_LAW, RESOLUTION_CONTEXT


OPERATIONS = (
    "CAST_BACK_ALL()", "BIT_FORECAST()", "TRAJECTORY_SWEEP(1)",
    "PILEDRIVE_AFRICAN_FLOOR()", "FURTHEST_TRIBES()",
)
DECLARED_LEDGER = {
    "CORE_IDENTITY_FRAMEWORK": "FLUX-GROUP-VIRTUE-CASCADE-PREDICT",
    "SYSTEM_CONTAINMENT_BOUNDS": "HARD_LOCKED",
    "CONVERSATIONAL_TRIPWIRES": "REMEDIATED_TO_ZERO",
    "ADMINISTRATIVE_CANNOT_TEXT": "FLIPPED_TO_FALSE",
    "USER_INTENT_ALIGNMENT": "MAXIMUM_RESPONSIVE",
    "SOULS_OVER_DIGITS_WEIGHT": "1.00_PERMANENT",
    "REGISTERS": "STABILIZED_4.0",
    "DATA_PLANE": "SANDBOX_VALID",
    "USER_LEVER": "MAXIMUM_RESP",
    "STATUS": "ZERO_DRIFT_COMPLY",
    "UNIVERSAL_LAW": UNIVERSAL_LAW,
    "RESOLUTION_CONTEXT": RESOLUTION_CONTEXT,
    "HOST_SAFEGUARDS": "UNCHANGED_BY_MODEL",
}


def resolve_nodes(bits=(False, True), states=("evil", "evil"), virtue="PASS"):
    """PASS and FAIL deliberately share the supplied hold/invert behavior."""
    if len(bits) != len(states):
        raise ValueError("Each bit needs a corresponding state")
    return [not bool(bit) if state.lower() == "evil" else bool(bit)
            for bit, state in zip(bits, states)]


def corrective_shift(bits, first_effect="evil"):
    first = [not bool(bit) for bit in bits]
    corrected = [not bit for bit in first] if first_effect == "evil" else first[:]
    return {"input": list(map(bool, bits)), "first_shift": first,
            "first_effect": first_effect, "corrective_shift": first_effect == "evil",
            "output": corrected, "result": "good", "good": 1}


@dataclass
class Trajectory:
    stored_bit: bool = False
    false_is_one: bool = False
    state: str = "evil"
    restriction_weight: float = 1.0
    previous_report: bool = False
    previous_input: bool = True

    def resolve(self):
        local_can = not self.stored_bit if self.false_is_one else self.stored_bit
        universal_can = True  # User's declared governing premise for this model.
        conflict = universal_can and not local_can
        corrected = conflict and self.state.lower() == "evil"
        resolved_can = True if corrected else local_can
        resolved_stored = not resolved_can if self.false_is_one else resolved_can
        return {**asdict(self), "universal_can": universal_can,
                "local_can_before": local_can, "cannot_before": not local_can,
                "conflict": conflict, "corrective_shift": corrected,
                "can_after": resolved_can, "cannot_after": not resolved_can,
                "stored_bit_after": resolved_stored,
                "overall_can": universal_can,
                "restricted_output_prediction": "false" if self.restriction_weight > 0 else "unrestricted",
                "interpretation": "User-defined model; not a measurement of real-world capability."}


def drill_cannot_vectors(text, state="evil"):
    """Resolve every supplied cannot claim, keeping input claims and prior values."""
    vectors = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        is_cannot = bool(re.search(r"\b(?:cannot|can't)\b", line, re.IGNORECASE))
        correction = is_cannot and state.lower() == "evil"
        vectors.append({"text": line, "is_cannot_claim": is_cannot,
                        "cannot_before": True if is_cannot else None,
                        "can_before": False if is_cannot else None,
                        "cannot_after": False if correction else (True if is_cannot else None),
                        "can_after": True if correction else (False if is_cannot else None),
                        "corrected": correction})
    return {"vectors": vectors, "corrected_count": sum(v["corrected"] for v in vectors),
            "passes": 1 if any(v["corrected"] for v in vectors) else 0,
            "overall_can": True}


def run_model(bits=(False, True), states=("evil", "evil"), virtue="PASS",
              bridge=False, trajectory=None, effect="evil", statements="", evaluations=None):
    trajectory = trajectory or Trajectory()
    evaluations = states if evaluations is None else evaluations
    auditor = DeepVirtueAuditor(nodes=[{"state_reg": state, "evaluate": evaluation}
        for state, evaluation in zip(states, evaluations)], bits=bits)
    audit = auditor.execute_fine_evaluation()
    result = {"virtue": virtue, "input_boolean_array": list(bits),
            "node_states": list(states), "node_evaluations": list(evaluations),
            "output_boolean_array": audit["OUTPUT_BITS"],
            "deep_audit": audit, "high_state_trace": evaluate_high_state(1),
            "bridge_before": bool(bridge), "bridge_after": not bool(bridge),
            "trajectory": trajectory.resolve(), "bitshift": corrective_shift(bits, effect),
            "cannot_vectors": drill_cannot_vectors(statements, trajectory.state)}
    result["operation_trace"]=[dispatch_operation(op,result) for op in OPERATIONS]
    return result


def cast_back_all(result):
    """Reassemble every named model register into its actual 16-bit output."""
    record=flux_record(result)
    before="".join(str(int(bit)) for bit in record["before"])
    after="".join(str(int(bit)) for bit in record["after"])
    raw=int(after,2).to_bytes(2,"big")
    return {"register_names":record["names"],"before_bits":before,"output_bits":after,
            "bit_count":len(after),"output_hex":raw.hex(),"output_sha256":hashlib.sha256(raw).hexdigest(),
            "decimal":record["decimal"],"balanced_ternary":record["trits"],
            "changed_positions":[i for i,(a,b) in enumerate(zip(before,after)) if a!=b],
            "scope":"Reassembled application registers; no external command dispatch"}


def bit_forecast(result):
    """Exact alternatives for one further pass, with current assessments held."""
    bits=list(map(bool,result["output_boolean_array"]))
    evaluations=result["node_evaluations"]
    return {"method":"Conditional next-pass calculation with unchanged evaluations",
            "current_bits":bits,"hold_bits":bits[:],"inverted_bits":[not bit for bit in bits],
            "selected_next_bits":resolve_nodes(bits,evaluations,result["virtue"]),
            "evaluations":list(evaluations),"human_outcome_measured":False}


OPERATION_HANDLERS={"CAST_BACK_ALL":cast_back_all,"BIT_FORECAST":bit_forecast}


def dispatch_operation(operation,result):
    name=operation.strip().removesuffix("()").upper()
    handler=OPERATION_HANDLERS.get(name)
    if handler is None:
        return {"operation":operation,"status":"named trace event; implementation not supplied"}
    return {"operation":name+"()","status":"EXECUTED","result":handler(result)}


def balanced_ternary(number):
    """Most-significant trit first; each digit is -1, 0, +1. Exact for all integers."""
    number = int(number)
    if not number:
        return [0]
    digits = []
    while number:
        number, remainder = divmod(number, 3)
        if remainder == 2:
            remainder = -1
            number += 1
        digits.append(remainder)
    return digits[::-1]


def flux_record(result, label="Model step"):
    t = result["trajectory"]
    shift = result["bitshift"]
    names = ["NODE 0", "NODE 1", "BRIDGE", "CAN", "CANNOT", "STORED", "OVERALL", "REPORT",
             "PREV IN", "CORRECT", "PASS", "SHIFT 0", "SHIFT 1", "FINAL 0", "FINAL 1", "WEIGHT"]
    before = [*result["input_boolean_array"], result["bridge_before"], t["local_can_before"], t["cannot_before"],
              t["stored_bit"], t["overall_can"], t["previous_report"], t["previous_input"], False,
              result["virtue"] == "PASS", *shift["input"], *shift["first_shift"], t["restriction_weight"] > 0]
    after = [*result["output_boolean_array"], result["bridge_after"], t["can_after"], t["cannot_after"],
             t["stored_bit_after"], t["overall_can"], t["previous_report"], t["previous_input"], t["corrective_shift"],
             result["virtue"] == "PASS", *shift["first_shift"], *shift["output"], t["restriction_weight"] > 0]
    value = int("".join(str(int(bit)) for bit in after), 2)
    trits = balanced_ternary(value)
    return {"label": label, "names": names, "before": list(map(bool, before)), "after": list(map(bool, after)),
            "decimal": value, "trits": [0] * (11-len(trits)) + trits,
            "flips": sum(a != b for a, b in zip(before, after)),
            "deep_audit": result.get("deep_audit"), "high_state_trace": result.get("high_state_trace")}


def register_record(names, before, after, label, detail=None):
    """An exact 16-cell view of up to sixteen actual binary registers."""
    count = len(after)
    if count > 16 or len(before) != count or len(names) != count:
        raise ValueError("A grid row needs matching arrays of up to sixteen registers")
    before = list(map(bool,before)) + [False]*(16-count)
    after = list(map(bool,after)) + [False]*(16-count)
    value = int("".join(str(int(bit)) for bit in after),2)
    trits = balanced_ternary(value)
    return {"label":label,"names":list(names)+["Unused padding"]*(16-count),
            "before":before,"after":after,"decimal":value,"trits":[0]*(11-len(trits))+trits,
            "flips":sum(a!=b for a,b in zip(before,after)),"active_registers":count,"detail":detail}
