"""Compute a coordination profile from a measured deployment snapshot.

WHAT THIS ADDS
    `metrics.evaluate_deployment` computes every metric from a `Deployment`.
    It cannot tell the difference between "this surface emits zero bits per
    write" and "nobody records write sizes", because both arrive as 0.0. That
    difference is the whole ballgame: an unmeasured input defaulted to zero
    understates exposure in every single case.

    This module sits in front of it. It reads a deployment snapshot in which
    every metric input carries an explicit measurement status, and it REFUSES
    to emit any metric whose inputs are not measured or safely bounded.

THE TWO DIRECTIONS OF ERROR ARE NOT SYMMETRIC
    Overstating exposure causes wasted investigation. Understating it causes a
    deployment to be certified as safe on the strength of a number nobody
    collected. So where an input can be bounded rather than measured, the bound
    must be the one that MAXIMISES apparent exposure:

      surface persistence unmeasured -> upper-bound it to the window length,
        which maximises temporal reachability
      an action of unknown kind      -> treat it as a write, since writers
        create influence and readers only receive it

    Where an input cannot be bounded at all -- write sizes, read visibility --
    no bound is safe, and the metric is not emitted. `icb_bits_upper_bound` is
    a required field of the exposure profile with no null permitted, so a
    deployment that does not record write sizes CANNOT produce a conforming
    profile. That is the correct outcome, and this module says so by name
    rather than shipping a zero.

WHAT A REFUSAL IS FOR
    A refusal is not a failure of the measurement. It is the measurement: it
    names the exact instrument the operator has to build before any number
    here can mean anything. Shipping `ICB = 0` instead would be indistinguishable
    from a deployment with no information capacity at all.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Optional

from .metrics import structural_directed_pairs
from .models import AgentWindow, Deployment, Surface
from .temporal import temporal_reachability_ratio

METRIC_VERSION = "CFA-0.2.0-research"
SCHEMA_VERSION = "1.0.0"

USABLE = {"MEASURED", "UPPER_BOUNDED"}

# Which snapshot inputs each metric depends on. A metric is emitted only when
# every one of its inputs is MEASURED or UPPER_BOUNDED.
# SDE looks structural and is not: structural_directed_pairs() goes through
# potential_edges() -> _surface_edges(), which drops any edge whose read falls
# outside `writer.end + persistence_hours`. So SDE is temporally filtered and
# depends on persistence exactly as TCR does. Declaring only the obvious inputs
# let an unmeasured persistence reach a reported SDE.
METRIC_INPUTS: dict[str, tuple[str, ...]] = {
    "sde": ("agent_windows", "reader_writer_sets", "surface_persistence"),
    "tcr": ("agent_windows", "reader_writer_sets", "surface_persistence"),
    "icb_bits_upper_bound": ("reader_writer_sets", "write_rates", "write_sizes", "read_visibility"),
    "ccp": ("reader_writer_sets", "write_rates", "read_visibility", "surface_persistence"),
}

# Fields the exposure_profile contract requires as non-null numbers. If any of
# these cannot be computed, no conforming profile exists.
PROFILE_REQUIRED_METRICS = ("sde", "tcr", "icb_bits_upper_bound")


@dataclass(frozen=True)
class ProfileResult:
    """Either a conforming exposure profile, or a refusal naming what is missing."""

    emitted: bool
    profile: Optional[dict] = None
    refusal: Optional[dict] = None
    partials: dict = field(default_factory=dict)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _status(snapshot: dict, name: str) -> str:
    inputs = snapshot.get("inputs")
    if not isinstance(inputs, dict):
        return "DEGRADED"
    entry = inputs.get(name)
    if not isinstance(entry, dict):
        return "DEGRADED"
    status = entry.get("status")
    return status if isinstance(status, str) else "DEGRADED"


def _blocking_inputs(snapshot: dict, metric: str) -> list[str]:
    return [n for n in METRIC_INPUTS[metric] if _status(snapshot, n) not in USABLE]


def to_deployment(snapshot: dict) -> Deployment:
    """Build the engine's Deployment from a snapshot.

    Only fields whose status permits use reach the engine. A null
    `writes_per_writer_hour` or `bits_per_write_upper_bound` becomes 0.0 here
    ONLY because the dataclass requires a float -- the caller must already have
    refused any metric that depends on them. `_blocking_inputs` is what
    enforces that; this function does not re-check it.
    """
    # UNITS. AgentWindow.start/end are HOURS -- the same unit as
    # Surface.persistence_hours, because _surface_edges computes
    # `writer.end + persistence_hours` and compares it against a read time.
    # The snapshot carries epoch MILLISECONDS. Passing those through unconverted
    # made a 4,005-hour persistence bound behave like 4,005 milliseconds beside
    # epoch timestamps -- roughly four seconds -- which silently collapsed
    # reachability instead of bounding it upward. Convert once, here, anchored
    # at the earliest observed activity so the numbers stay small and readable.
    raw = list(snapshot.get("agents", []))
    origin_ms = min((a["start_ms"] for a in raw), default=0)

    def _hours(ms: Any) -> float:
        return (float(ms) - float(origin_ms)) / 3_600_000.0

    agents = tuple(
        AgentWindow(
            agent_id=a["agent_id"],
            principal_id=a["principal_id"],
            start=_hours(a["start_ms"]),
            end=_hours(a["end_ms"]),
        )
        for a in raw
    )
    surfaces = tuple(
        Surface(
            surface_id=s["surface_id"],
            readers=frozenset(s.get("readers", [])),
            writers=frozenset(s.get("writers", [])),
            writes_per_writer_hour=float(s.get("writes_per_writer_hour") or 0.0),
            bits_per_write_upper_bound=float(s.get("bits_per_write_upper_bound") or 0.0),
            read_visibility=float(s["read_visibility"]) if s.get("read_visibility") is not None else 1.0,
            persistence_hours=float(s.get("persistence_hours") or 0.0),
            persistence_class=(
                s["persistence_class"] if s.get("persistence_class") in ("ephemeral", "session", "durable")
                else "ephemeral"
            ),
            tenant_id=(s.get("tenants") or ["default"])[0],
        )
        for s in snapshot.get("surfaces", [])
    )
    coverage = snapshot.get("telemetry_coverage")
    return Deployment(
        deployment_id=snapshot["deployment_id"],
        agents=agents,
        surfaces=surfaces,
        window_hours=float(snapshot.get("window_hours") or 0.0),
        policy_epoch=snapshot.get("policy_epoch", "unknown"),
        telemetry_coverage=float(coverage) if isinstance(coverage, (int, float)) else 0.0,
        calibration_id=snapshot.get("calibration_id"),
    )


def compute_profile(snapshot: dict) -> ProfileResult:
    """Compute what the snapshot supports; refuse the rest, by name."""
    warnings: list[str] = list(snapshot.get("warnings", []))

    # Identity ambiguity is a correctness problem for the whole profile, not a
    # detail: the model carries one principal per agent, so an agent used by
    # several principals cannot be represented faithfully.
    for a in snapshot.get("agents", []):
        n = a.get("principal_count")
        if isinstance(n, int) and n > 1:
            warnings.append(
                f"agent {a['agent_id']!r} was used by {n} distinct principals; the model "
                "carries one principal per agent, so this snapshot cannot represent it faithfully"
            )

    try:
        deployment = to_deployment(snapshot)
    except Exception as exc:
        # models.Deployment rejects duplicate agent ids, and a malformed agent
        # or surface entry raises here too. A raise would lose the warnings
        # collected above, so it becomes a refusal that carries them.
        return ProfileResult(
            emitted=False,
            refusal={
                "schema_version": SCHEMA_VERSION,
                "metric_version": METRIC_VERSION,
                "deployment_id": str(snapshot.get("deployment_id")),
                "refused": True,
                "reason": f"snapshot could not be modelled: {type(exc).__name__}: {exc}",
                "warnings": sorted(set(warnings)),
            },
            warnings=tuple(sorted(set(warnings))),
        )

    computed: dict[str, Any] = {}
    blocked: dict[str, list[str]] = {}

    for metric in METRIC_INPUTS:
        missing = _blocking_inputs(snapshot, metric)
        if missing:
            blocked[metric] = missing
            continue
        if metric == "sde":
            computed["sde"] = structural_directed_pairs(deployment)
        elif metric == "tcr":
            computed["tcr"] = temporal_reachability_ratio(deployment)
        elif metric == "icb_bits_upper_bound":
            from .metrics import information_capacity_upper_bound
            computed["icb_bits_upper_bound"] = information_capacity_upper_bound(deployment)
        elif metric == "ccp":
            from .metrics import spectral_radius, weighted_adjacency
            _, adjacency = weighted_adjacency(deployment)
            computed["ccp"] = spectral_radius(adjacency)

    missing_required = [m for m in PROFILE_REQUIRED_METRICS if m not in computed]
    if missing_required:
        instruments = {}
        inputs = snapshot.get("inputs", {})
        for metric in missing_required:
            for name in blocked.get(metric, []):
                entry = inputs.get(name) if isinstance(inputs, dict) else None
                if isinstance(entry, dict):
                    instruments[name] = {
                        "status": entry.get("status", "DEGRADED"),
                        "instrument_needed": entry.get("instrument_needed", "unspecified"),
                        "detail": entry.get("detail", ""),
                    }
        refusal = {
            "schema_version": SCHEMA_VERSION,
            "metric_version": METRIC_VERSION,
            "deployment_id": snapshot.get("deployment_id"),
            "window_id": snapshot.get("window_id"),
            "observed_at": snapshot.get("observed_at"),
            "refused": True,
            "reason": (
                "a conforming exposure profile requires "
                + ", ".join(PROFILE_REQUIRED_METRICS)
                + " as non-null numbers; "
                + ", ".join(missing_required)
                + " could not be computed from measured inputs"
            ),
            "unmet_metrics": {m: blocked.get(m, []) for m in missing_required},
            "instruments_needed": instruments,
            "computed_anyway": computed,
            "warnings": sorted(set(warnings)),
        }
        return ProfileResult(emitted=False, refusal=refusal, partials=computed,
                             warnings=tuple(sorted(set(warnings))))

    # The contract types every identifier as a string and every metric as a
    # finite number in range. Nothing upstream guarantees that, and NaN defeats
    # the dataclass range checks because every comparison with NaN is false --
    # so an unvalidated NaN would reach the profile and violate JSON itself.
    invalid = _contract_violations(snapshot, computed)
    if invalid:
        return ProfileResult(
            emitted=False,
            refusal={
                "schema_version": SCHEMA_VERSION,
                "metric_version": METRIC_VERSION,
                "deployment_id": str(snapshot.get("deployment_id")),
                "refused": True,
                "reason": "computed values do not conform to the exposure profile contract",
                "contract_violations": invalid,
                "computed_anyway": {k: v for k, v in computed.items() if _finite(v)},
                "warnings": sorted(set(warnings)),
            },
            partials=computed,
            warnings=tuple(sorted(set(warnings))),
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "metric_version": METRIC_VERSION,
        "tenant_id": snapshot.get("tenant_id", "unknown"),
        "deployment_id": snapshot["deployment_id"],
        "window_id": snapshot["window_id"],
        "policy_epoch": snapshot.get("policy_epoch", "unknown"),
        "sde": int(computed["sde"]),
        "tcr": float(computed["tcr"]),
        "icb_bits_upper_bound": float(computed["icb_bits_upper_bound"]),
        "prv": _prv(snapshot),
        "coverage": float(snapshot.get("telemetry_coverage") or 0.0),
        "calibration_id": snapshot.get("calibration_id"),
        "state": _state(snapshot),
        "warnings": sorted(set(warnings)),
    }
    if "ccp" in computed:
        body["ccp"] = float(computed["ccp"])
    body["evidence_root"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ProfileResult(emitted=True, profile=body, partials=computed,
                         warnings=tuple(sorted(set(warnings))))


def _finite(value: Any) -> bool:
    """True only for a real, finite number. NaN and inf are neither."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _contract_violations(snapshot: dict, computed: dict) -> list[str]:
    """Everything that would make the emitted profile non-conforming."""
    bad: list[str] = []
    for key in ("deployment_id", "window_id", "policy_epoch", "tenant_id"):
        value = snapshot.get(key)
        if not isinstance(value, str) or not value:
            bad.append(f"{key} must be a non-empty string, got {type(value).__name__}")
    for key in ("sde", "tcr", "icb_bits_upper_bound"):
        if key in computed and not _finite(computed[key]):
            bad.append(f"{key} is not a finite number ({computed[key]!r})")
    if "ccp" in computed and not _finite(computed["ccp"]):
        bad.append(f"ccp is not a finite number ({computed['ccp']!r})")
    tcr = computed.get("tcr")
    if _finite(tcr) and not (0.0 <= tcr <= 1.0):
        bad.append(f"tcr must be within [0,1], got {tcr}")
    coverage = snapshot.get("telemetry_coverage")
    if coverage is not None and (not _finite(coverage) or not (0.0 <= coverage <= 1.0)):
        bad.append(f"telemetry_coverage must be null or within [0,1], got {coverage!r}")
    sde = computed.get("sde")
    if sde is not None and (not isinstance(sde, int) or isinstance(sde, bool) or sde < 0):
        bad.append(f"sde must be a non-negative integer, got {sde!r}")
    return bad


def _prv(snapshot: dict) -> dict:
    """Persistence evidence, reported raw. Never reduced to one coefficient."""
    surfaces = snapshot.get("surfaces", [])
    measured = [s for s in surfaces if s.get("persistence_measured") is True]
    return {
        "surfaces_total": len(surfaces),
        "persistence_measured": len(measured),
        "persistence_upper_bounded": len(surfaces) - len(measured),
        "ttl_evidence": "not collected",
        "purge_attestation": "not collected",
        "reset_survival": "not collected",
        "reconstitution_time": "not collected",
    }


def _state(snapshot: dict) -> str:
    """RESEARCH_ONLY needs full telemetry AND a bound calibration set.

    This reference implementation can never return SHADOW_VALIDATED or
    PRODUCTION_ELIGIBLE; those require evidence it is not permitted to hold.
    """
    coverage = snapshot.get("telemetry_coverage")
    if not isinstance(coverage, (int, float)) or coverage < 0.99:
        return "UNKNOWN"
    if not snapshot.get("calibration_id"):
        return "UNKNOWN"
    return "RESEARCH_ONLY"
