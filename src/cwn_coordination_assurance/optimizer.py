from __future__ import annotations

from dataclasses import replace

from .metrics import evaluate_deployment
from .models import Deployment, Surface


def candidate_interventions(deployment: Deployment) -> list[tuple[str, Deployment]]:
    out: list[tuple[str, Deployment]] = []
    for i, surface in enumerate(deployment.surfaces):
        variants: list[tuple[str, Surface]] = [
            (f"{surface.surface_id}:ttl_zero", replace(surface, persistence_hours=0.0, persistence_class="ephemeral")),
            (f"{surface.surface_id}:rate_10pct", replace(surface, writes_per_writer_hour=surface.writes_per_writer_hour * 0.1)),
            (f"{surface.surface_id}:read_visibility_10pct", replace(surface, read_visibility=surface.read_visibility * 0.1)),
        ]
        for name, variant in variants:
            surfaces = list(deployment.surfaces)
            surfaces[i] = variant
            out.append((name, replace(deployment, surfaces=tuple(surfaces))))
    return out


def best_single_intervention(deployment: Deployment) -> dict[str, float | str]:
    base = evaluate_deployment(deployment).spectral_criticality_proxy
    best_name = "none"
    best_value = base
    for name, candidate in candidate_interventions(deployment):
        value = evaluate_deployment(candidate).spectral_criticality_proxy
        if value < best_value:
            best_name, best_value = name, value
    return {"intervention": best_name, "before": base, "after": best_value, "reduction": base - best_value}

