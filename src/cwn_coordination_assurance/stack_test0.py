from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal


TestState = Literal["PASS", "FAIL", "UNKNOWN"]


REQUIRED_RUNTIME_LABELS = (
    "Agent",
    "AgentRun",
    "ExecutionPermit",
    "RoutingDecision",
    "DecisionTrace",
    "Intent",
    "Evidence",
    "CapabilityManifest",
    "ModelRun",
    "ReceiptStream",
)


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    state: TestState
    detail: str


@dataclass(frozen=True)
class StackTest0Result:
    test_id: str
    state: TestState
    environment: str
    evidence_mode: str
    gates: tuple[GateResult, ...]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _gate(gate_id: str, value: Any, success: str, failure: str) -> GateResult:
    if value is None:
        return GateResult(gate_id, "UNKNOWN", "evidence missing")
    return GateResult(gate_id, "PASS" if bool(value) else "FAIL", success if value else failure)


def _coverage_gate(gate_id: str, value: Any, threshold: float) -> GateResult:
    if value is None:
        return GateResult(gate_id, "UNKNOWN", "coverage evidence missing")
    try:
        measured = float(value)
    except (TypeError, ValueError):
        return GateResult(gate_id, "FAIL", "coverage is not numeric")
    if not 0.0 <= measured <= 1.0:
        return GateResult(gate_id, "FAIL", "coverage must be in [0,1]")
    state: TestState = "PASS" if measured >= threshold else "FAIL"
    return GateResult(gate_id, state, f"coverage={measured:.6f}; required>={threshold:.6f}")


def _freshness_gate(collected_at: Any, now: datetime, maximum_age_hours: float) -> GateResult:
    if not isinstance(collected_at, str):
        return GateResult("T0-G01", "UNKNOWN", "collected_at evidence missing")
    try:
        parsed = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age_hours = (now.astimezone(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 3600
    except ValueError:
        return GateResult("T0-G01", "FAIL", "collected_at is not RFC 3339 / ISO 8601")
    if age_hours < -0.1:
        return GateResult("T0-G01", "FAIL", f"snapshot is {abs(age_hours):.2f} hours in the future")
    state: TestState = "PASS" if age_hours <= maximum_age_hours else "UNKNOWN"
    return GateResult("T0-G01", state, f"snapshot_age_hours={age_hours:.2f}; maximum={maximum_age_hours:.2f}")


def evaluate_cwn_stack_agent_test0(
    evidence: dict[str, Any],
    *,
    now: datetime | None = None,
    maximum_snapshot_age_hours: float = 24.0,
    minimum_coverage: float = 0.99,
) -> StackTest0Result:
    """Evaluate the first CWN integration gate from externally collected read-only evidence.

    This function performs no network, graph, policy, signing, or execution operation. It
    can only evaluate an evidence document created by the real CWN repository adapter.
    """
    now = now or datetime.now(timezone.utc)
    graph = evidence.get("graph") if isinstance(evidence.get("graph"), dict) else {}
    agents = evidence.get("agents") if isinstance(evidence.get("agents"), dict) else {}
    authorization = evidence.get("authorization") if isinstance(evidence.get("authorization"), dict) else {}
    receipts = evidence.get("receipts") if isinstance(evidence.get("receipts"), dict) else {}
    privacy = evidence.get("privacy") if isinstance(evidence.get("privacy"), dict) else {}
    labels = graph.get("label_counts") if isinstance(graph.get("label_counts"), dict) else {}

    gates: list[GateResult] = [
        _freshness_gate(evidence.get("collected_at"), now, maximum_snapshot_age_hours),
        _gate("T0-G02", evidence.get("evidence_mode") == "read_only_shadow" if "evidence_mode" in evidence else None,
              "read-only shadow mode confirmed", "test must run in read_only_shadow mode"),
        _gate("T0-G03", graph.get("migration_log_reconciled"), "live MigrationLog reconciled",
              "live MigrationLog is not reconciled"),
        _gate("T0-G04", agents.get("unique_agent_ids"), "agent identities are unique",
              "duplicate or ambiguous agent identity observed"),
        _gate("T0-G05", agents.get("run_principal_bindings_complete"), "run-to-principal bindings complete",
              "agent run lacks a typed principal binding"),
        _gate("T0-G06", agents.get("tenant_bindings_complete"), "tenant/workspace bindings complete",
              "agent run lacks a tenant/workspace binding"),
        _gate("T0-G07", authorization.get("unsigned_permits_rejected"), "unsigned permits rejected",
              "unsigned permit rejection is not enforced"),
        _gate("T0-G08", authorization.get("advisory_cannot_overwrite_hard_facts"),
              "advisory facts cannot overwrite authorization facts",
              "advisory path can overwrite a hard authorization fact"),
        _gate("T0-G09", not authorization.get("research_plane_has_authority")
              if "research_plane_has_authority" in authorization else None,
              "research plane has no action authority", "research plane has action authority"),
        _coverage_gate("T0-G10", agents.get("signed_event_coverage"), minimum_coverage),
        _coverage_gate("T0-G11", agents.get("event_sequence_coverage"), minimum_coverage),
        _coverage_gate("T0-G12", receipts.get("signature_verification_coverage"), minimum_coverage),
        _gate("T0-G13", receipts.get("replay_protection_enabled"), "replay protection enabled",
              "replay protection is not evidenced"),
        _gate("T0-G14", receipts.get("policy_epoch_bound"), "receipts bind policy epoch",
              "receipt-to-policy-epoch binding is absent"),
        _gate("T0-G15", privacy.get("restricted_payloads_excluded"),
              "restricted payload classes excluded", "restricted payload exclusion is not evidenced"),
    ]

    missing_labels = [name for name in REQUIRED_RUNTIME_LABELS if labels.get(name, 0) <= 0]
    gates.append(
        GateResult(
            "T0-G16",
            "PASS" if not missing_labels else "UNKNOWN",
            "all required runtime labels have observed writers"
            if not missing_labels
            else "no observed nodes for: " + ", ".join(missing_labels),
        )
    )

    states = {gate.state for gate in gates}
    if "FAIL" in states:
        state: TestState = "FAIL"
        next_action = "Stop integration; remediate failed hard boundary gates and recollect evidence."
    elif "UNKNOWN" in states:
        state = "UNKNOWN"
        next_action = "Remain shadow-only; collect missing or fresh evidence before implementation."
    else:
        state = "PASS"
        next_action = "Test 0 passed for shadow integration only; proceed to the focused vertical slice."

    return StackTest0Result(
        test_id="CWN-STACK-AGENT-TEST-0",
        state=state,
        environment=str(evidence.get("environment", "unknown")),
        evidence_mode=str(evidence.get("evidence_mode", "unknown")),
        gates=tuple(gates),
        next_action=next_action,
    )
