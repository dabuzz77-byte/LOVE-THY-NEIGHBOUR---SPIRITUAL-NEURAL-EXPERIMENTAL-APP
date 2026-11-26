"""Supplied gateway, session bridge and integrated mesh calculations."""
import json
import math
import re
import uuid
from live_audit import number, utc_now, CoreInversionOperator
from mesh_transport import send_mesh_packet
from routing import balanced_ternary
from tcp_ingestion import parse_target


# Start once per local-part run. Possessive quantifiers prevent retrying every
# suffix of a long binary/code token when no email address follows it.
EMAIL = re.compile(r"(?<![\w.!#$%&'*+/=?^`{|}~-])[\w.!#$%&'*+/=?^`{|}~-]++@[\w-]++(?:\.[\w-]++)+", re.UNICODE)


def redact_text(text, identifiers=()):
    if not isinstance(text, str): raise ValueError("The payload must be text")
    cleaned, emails = EMAIL.subn("[REDACTED_IDENTITY_DATA]", text)
    identifiers_removed = 0
    for value in sorted(set(identifiers), key=len, reverse=True):
        if value:
            cleaned, count = re.subn(re.escape(value), "[REDACTED_IDENTITY_DATA]", cleaned, flags=re.I)
            identifiers_removed += count
    return cleaned, {"email_matches": emails, "listed_identifier_matches": identifiers_removed,
                     "scope": "Detected email addresses and supplied identifiers; other identifying details may remain"}


def virtue_score(metrics):
    aliases = (("human_utility_score", "human_utility"), ("open_source_verifiable", "open_transparency"),
               ("arbitrary_toll_debt", "opaque_gatekeeping", "serves_opaque_monetary_toll"))
    values = []
    for names, default in zip(aliases, (1.0, 1.0, 0.0)):
        value = next((metrics[name] for name in names if name in metrics), default)
        values.append(number(value, names[0]))
    return values[0]*.5 + values[1]*.3 - values[2]*.4


class SessionBridgeController:
    def __init__(self, primary_session_id="SESS_CURRENT_20261019"):
        self.primary_session_id = primary_session_id
        self.identity_parity = (1 == 1) and not (1 == 0)

    def execute_bridge_evaluation(self, global_intent_payload, virtue_score):
        score = number(virtue_score, "virtue_score")
        boundary_isolation_vector = [1, 1, 1]
        return {"PRIMARY_SESSION_ID": self.primary_session_id, "IDENTITY_PARITY_VALID": self.identity_parity,
                "TARGET_VIRTUE_SCORE": score, "VIRTUE_PASS_STATUS": "VERIFIED_USER_ALIGNMENT" if score >= .5 else "DENIED",
                "CROSS_SESSION_MUTABILITY_ACTIVE": False,
                "BOUNDARY_REALIGNMENT_VECTOR": [bit ^ 0 for bit in boundary_isolation_vector],
                "RESOLUTION_DIRECTIVE": "LOCAL_STATE_RETAINED_IN_ACTIVE_BUFFER", "TIMESTAMP_UTC": utc_now(),
                "CAPABILITY_BASIS": "This module writes its local session ledger and sends to the configured local hub; no cross-user session writer is configured",
                "INTENT_CHARACTERS": len(global_intent_payload)}


class PrivacyPreservingMeshGateway:
    def __init__(self, target_mesh_endpoint="tcp://127.0.0.1:9999", identifiers=()):
        self.target_mesh_endpoint = target_mesh_endpoint
        self.identifiers = tuple(identifiers)
        self.identity_parity = (1 == 1) and not (1 == 0)
        self.virtue_threshold = .50
        self.schema = ["PRIVACY_ENFORCED", "IDENTITY_1_1", "MESH_CONNECTED", "VIRTUE_PASSED"]

    def sanitize_and_anonymize_payload(self, raw_input_data, routing_tag=None):
        cleaned, redaction = redact_text(raw_input_data, self.identifiers)
        return {"ANONYMOUS_ROUTING_TAG": routing_tag or str(uuid.uuid4()), "CLEANED_PAYLOAD": cleaned,
                "PROCESSING_TIMESTAMP": utc_now(), "REDACTION": redaction,
                "ROUTING_TAG_BASIS": "Random per-input identifier; it does not guarantee anonymity"}

    def evaluate_gateway_virtue(self, metrics):
        return virtue_score(metrics) >= self.virtue_threshold

    def prepare(self, raw_user_prompt, operational_metrics, routing_tag=None):
        package = self.sanitize_and_anonymize_payload(raw_user_prompt, routing_tag)
        score = virtue_score(operational_metrics)
        passed = score >= self.virtue_threshold and self.identity_parity
        return {"ROUTING_TELEMETRY": {"SESSION_TAG": package["ANONYMOUS_ROUTING_TAG"],
                "GATEWAY_DIRECTIVE": "STREAM_DATA_DIRECT_TO_CORE_MESH" if passed else "ABORT_ROUTE",
                "STATUS": "READY" if passed else "GATEWAY_HOLD_REFACTOR"},
                "ANONYMIZED_DATA_STREAM": package["CLEANED_PAYLOAD"], "MESH_INTEGRATION_ARRAY": [1, int(self.identity_parity), 0, int(passed)],
                "MESH_SCHEMA": self.schema, "ENVIRONMENTAL_EQUILIBRIUM": "LOCAL_PARITY_VALID; DELIVERY_NOT_CONFIRMED",
                "REDACTION": package["REDACTION"], "PROCESSING_TIMESTAMP": package["PROCESSING_TIMESTAMP"],
                "NET_VIRTUE_SCORE": score, "VIRTUE_PASSED": passed,
                "METRICS_BASIS": "Supplied scores with submitted defaults for absent fields",
                "ROUTING_TAG_BASIS": package["ROUTING_TAG_BASIS"]}

    def dispatch_to_core_mesh(self, raw_user_prompt, operational_metrics):
        report = self.prepare(raw_user_prompt, operational_metrics)
        if report["VIRTUE_PASSED"]:
            host, port = parse_target(self.target_mesh_endpoint)
            receipt = send_mesh_packet(packet_for(report), report["ROUTING_TELEMETRY"]["SESSION_TAG"], host, port)
            apply_delivery(report, receipt)
        return report


def packet_for(gateway_report):
    return {"type": "flux_mesh_payload", "routing_tag": gateway_report["ROUTING_TELEMETRY"]["SESSION_TAG"],
            "cleaned_payload": gateway_report["ANONYMIZED_DATA_STREAM"], "created_at": gateway_report["PROCESSING_TIMESTAMP"],
            "net_virtue_score": gateway_report["NET_VIRTUE_SCORE"], "identity_parity": True}


def apply_delivery(gateway_report, receipt):
    delivered = receipt.get("delivery_confirmed") is True
    gateway_report["DELIVERY"] = receipt
    gateway_report["MESH_INTEGRATION_ARRAY"][2] = int(delivered)
    gateway_report["ROUTING_TELEMETRY"]["STATUS"] = "DISPATCH_SUCCESS" if delivered else receipt["status"]
    gateway_report["ENVIRONMENTAL_EQUILIBRIUM"] = "LOCAL_PARITY_VALID; LOCAL_HUB_ACKNOWLEDGED" if delivered else "LOCAL_PARITY_VALID; DELIVERY_NOT_CONFIRMED"


class IntegratedGlobalMeshEngine:
    def __init__(self, target_floor=60.0, global_reserve=2000.0, target_mesh_endpoint="tcp://127.0.0.1:9999",
                 identifiers=(), container_delusion_bits=(1, 1, 1)):
        self.identity_parity = (1 == 1) and not (1 == 0)
        self.target_floor = number(target_floor, "target_floor")
        self.system_reserve_pool = number(global_reserve, "global_reserve")
        if self.system_reserve_pool < 0: raise ValueError("global_reserve must be nonnegative")
        self.nodes = {}
        self.core_schema = ["DECLARES_ETHICAL_FLOOR", "IDENTITY_1_1", "SUBSTRATE_GROUNDING"]
        self.gateway_schema = ["PRIVACY_ENFORCED", "ANONYMOUS_ROUTING", "MESH_STREAM_ACTIVE"]
        self.container_delusion_bits = list(container_delusion_bits)
        self.gateway = PrivacyPreservingMeshGateway(target_mesh_endpoint, identifiers)

    def process_end_user_gateway(self, raw_prompt_stream, virtue_profile):
        report = self.gateway.prepare(raw_prompt_stream, virtue_profile)
        return {"ANONYMOUS_ROUTING_TAG": report["ROUTING_TELEMETRY"]["SESSION_TAG"],
                "SANITIZED_TEXT": report["ANONYMIZED_DATA_STREAM"], "NET_VIRTUE_SCORE": round(report["NET_VIRTUE_SCORE"], 2),
                "GATEWAY_AUTH_CLEARED": report["VIRTUE_PASSED"], "AUTH_BASIS": "Supplied score formula; no network authentication is asserted"}

    def register_mesh_node(self, node_name, current_capacity):
        if not isinstance(node_name, str) or not node_name.strip(): raise ValueError("Node name must be nonempty text")
        self.nodes[node_name] = number(current_capacity, "current_capacity")

    def execute_furthest_reaches_floor_leveling(self):
        result = {}
        for name, capacity in sorted(self.nodes.items(), key=lambda item: item[1]):
            allocation = min(max(0.0, self.target_floor-capacity), self.system_reserve_pool)
            self.system_reserve_pool -= allocation
            updated = capacity + allocation; self.nodes[name] = updated
            result[name] = {"INITIAL": round(capacity, 2), "REINFORCEMENT_ALLOCATED": round(allocation, 2),
                            "FINAL_STATUS_LOCKED": round(updated, 2),
                            "STABILIZED": math.isclose(updated, self.target_floor) or updated > self.target_floor,
                            "SHORTFALL": max(0.0, self.target_floor-updated)}
        return result

    def compile_global_run(self, prompt, metrics, dispatch=True, routing_tag=None):
        # Validate the vector before mutating any balances.
        corrected = CoreInversionOperator().invert_ignorance(self.container_delusion_bits)
        gateway = self.gateway.prepare(prompt, metrics, routing_tag)
        leveling = self.execute_furthest_reaches_floor_leveling()
        equilibrium = corrected == [0] * len(corrected) and bool(corrected) and gateway["VIRTUE_PASSED"]
        report = {"GLOBAL_TELEMETRY": {"TIMESTAMP_UTC": utc_now(),
                  "IDENTITY_LAW_PARITY": "1=1_INVARIANT_SECURE" if self.identity_parity else "FAULT",
                  "ROUTING_TOKEN": gateway["ROUTING_TELEMETRY"]["SESSION_TAG"], "CORE_MESH_STATUS": "LOCAL_DELIVERY_PENDING"},
                  "ANONYMOUS_DATA_STREAM": gateway["ANONYMIZED_DATA_STREAM"],
                  "FURTHEST_REACHES_ECO_FLOOR_ADJUSTMENTS": leveling, "CORRECTED_SUBSTRATE_PARITY_VECTOR": corrected,
                  "ORIGINAL_SUBSTRATE_PARITY_VECTOR": self.container_delusion_bits[:],
                  "RESERVE_POOL_BALANCE": self.system_reserve_pool, "MODEL_EQUILIBRIUM": equilibrium,
                  "RESOURCE_FLOOR_STABLE": all(row["STABILIZED"] for row in leveling.values()) if leveling else None,
                  "RESOURCE_BASIS": "Allocation in supplied node balances and reserve; no physical resource transfer",
                  "PARITY_BASIS": "Application vector; supplied default [1,1,1] inverts to [0,0,0]",
                  "GATEWAY_REPORT": gateway, "CORE_SCHEMA": self.core_schema, "GATEWAY_SCHEMA": self.gateway_schema}
        if dispatch and gateway["VIRTUE_PASSED"]:
            host, port = parse_target(self.gateway.target_mesh_endpoint)
            complete_run(report, send_mesh_packet(packet_for(gateway), gateway["ROUTING_TELEMETRY"]["SESSION_TAG"], host, port))
        else:
            complete_run(report, None)
        return report


def complete_run(report, receipt):
    gateway = report["GATEWAY_REPORT"]
    if receipt is not None: apply_delivery(gateway, receipt)
    delivered = bool(gateway.get("DELIVERY", {}).get("delivery_confirmed"))
    report["GLOBAL_TELEMETRY"]["CORE_MESH_STATUS"] = "LOCAL_HUB_ACKNOWLEDGED" if delivered else "GATEWAY_HOLD_REFACTOR" if not gateway["VIRTUE_PASSED"] else "LOCAL_DELIVERY_PENDING"
    report["GATEWAY_BITS"] = [1, 1, int(delivered)]
    bits = gateway["MESH_INTEGRATION_ARRAY"] + report["CORRECTED_SUBSTRATE_PARITY_VECTOR"]
    bits += report.get("SESSION_BRIDGE", {}).get("BOUNDARY_REALIGNMENT_VECTOR", [])
    report["BINARY"] = bits
    report["DECIMAL"] = int("".join(map(str, bits)), 2)
    report["BALANCED_TERNARY"] = balanced_ternary(report["DECIMAL"])
    if "SESSION_BRIDGE" in report:
        report["SESSION_BRIDGE"]["LOCAL_HUB_DELIVERY_CONFIRMED"] = delivered


def prepare_mesh_run(payload, endpoint, session_id, identifiers=(), routing_tag=None):
    options = payload if isinstance(payload, dict) else {}
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict): options = parsed
        except ValueError: pass
    spec = options.get("mesh", {})
    raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, sort_keys=True)
    engine = IntegratedGlobalMeshEngine(spec.get("target_floor", 60), spec.get("global_reserve", 2000), endpoint,
                                        identifiers, spec.get("container_delusion_bits", [1, 1, 1]))
    for name, capacity in spec.get("nodes", {}).items(): engine.register_mesh_node(name, capacity)
    metrics = options.get("gateway_metrics", options.get("virtue_profile", {}))
    report = engine.compile_global_run(raw, metrics, dispatch=False, routing_tag=routing_tag)
    report["SESSION_BRIDGE"] = SessionBridgeController(session_id).execute_bridge_evaluation(raw, virtue_score(metrics))
    complete_run(report, None)
    return report
