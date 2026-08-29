from __future__ import annotations

import math

from .models import Deployment, MetricResult
from .temporal import potential_edges, temporal_reachability_ratio


def baseline_ce(n: int, writes_per_agent_hour: float, duration_hours: float, persistence_multiplier: float) -> float:
    if n < 0 or writes_per_agent_hour < 0 or duration_hours < 0 or persistence_multiplier < 0:
        raise ValueError("baseline inputs must be non-negative")
    return n * (n - 1) / 2 * writes_per_agent_hour * duration_hours * persistence_multiplier


def structural_directed_pairs(deployment: Deployment) -> int:
    return len({(u, v) for u, v, _, _ in potential_edges(deployment)})


def information_capacity_upper_bound(deployment: Deployment) -> float:
    """Coarse upper bound in bits for the analysis window.

    It deliberately does not multiply writes by all potential reader pairs: one
    broadcast write is one emitted symbol even if many readers can observe it.
    """
    total = 0.0
    for s in deployment.surfaces:
        writers = len(s.writers)
        total += (
            writers
            * s.writes_per_writer_hour
            * deployment.window_hours
            * s.bits_per_write_upper_bound
            * s.read_visibility
        )
    return total


def weighted_adjacency(deployment: Deployment) -> tuple[list[str], list[list[float]]]:
    ids = sorted(a.agent_id for a in deployment.agents)
    idx = {a: i for i, a in enumerate(ids)}
    matrix = [[0.0 for _ in ids] for _ in ids]
    for s in deployment.surfaces:
        if not s.readers or not s.writers:
            continue
        emitted = s.writes_per_writer_hour * min(deployment.window_hours, 1.0)
        persistence_factor = 1.0 - math.exp(-max(0.0, s.persistence_hours))
        persistence_factor = max(0.05, persistence_factor)
        weight = min(1.0, emitted / (1.0 + emitted)) * s.read_visibility * persistence_factor
        for u in s.writers:
            for v in s.readers:
                if u != v and u in idx and v in idx:
                    matrix[idx[u]][idx[v]] = max(matrix[idx[u]][idx[v]], weight)
    return ids, matrix


def spectral_radius(matrix: list[list[float]], iterations: int = 200) -> float:
    n = len(matrix)
    if n == 0:
        return 0.0
    v = [1.0 / math.sqrt(n)] * n
    eigen = 0.0
    for _ in range(iterations):
        w = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(x * x for x in w))
        if norm == 0:
            return 0.0
        v = [x / norm for x in w]
        av = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        new_eigen = sum(v[i] * av[i] for i in range(n))
        if abs(new_eigen - eigen) < 1e-12:
            break
        eigen = new_eigen
    return max(0.0, eigen)


def baseline_max(deployment: Deployment) -> float:
    pmap = {"ephemeral": 1.0, "session": 3.0, "durable": 10.0}
    values = []
    for s in deployment.surfaces:
        n = len(s.readers & s.writers)
        values.append(baseline_ce(n, s.writes_per_writer_hour, deployment.window_hours, pmap[s.persistence_class]))
    return max(values, default=0.0)


def evaluate_deployment(deployment: Deployment) -> MetricResult:
    warnings: list[str] = [
        "capacity and criticality values are upper-bound research proxies, not incident probabilities",
        "permission reachability is not evidence of deliberate coordination",
    ]
    if deployment.telemetry_coverage < 0.99:
        warnings.append("telemetry coverage below 99%; enforcement use is prohibited")
    if deployment.calibration_id is None:
        warnings.append("no independent calibration dataset is bound")
    _, adjacency = weighted_adjacency(deployment)
    return MetricResult(
        metric_version="CFA-0.2.0-research",
        structural_directed_pairs=structural_directed_pairs(deployment),
        temporal_reachability_ratio=temporal_reachability_ratio(deployment),
        information_capacity_upper_bound_bits=information_capacity_upper_bound(deployment),
        spectral_criticality_proxy=spectral_radius(adjacency),
        baseline_ce_max=baseline_max(deployment),
        telemetry_coverage=deployment.telemetry_coverage,
        risk_state="RESEARCH_ONLY" if deployment.telemetry_coverage >= 0.99 and deployment.calibration_id else "UNKNOWN",
        warnings=tuple(warnings),
    )

