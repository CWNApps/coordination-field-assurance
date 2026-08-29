from __future__ import annotations

from collections import defaultdict

from .models import Deployment, Surface


def _surface_edges(deployment: Deployment, surface: Surface) -> list[tuple[str, str, float]]:
    """Return potential time-respecting influence edges (writer, reader, earliest arrival).

    This is a permission-and-window upper bound, not proof that information flowed.
    """
    agents = {a.agent_id: a for a in deployment.agents}
    edges: list[tuple[str, str, float]] = []
    for writer_id in sorted(surface.writers):
        if writer_id not in agents:
            continue
        writer = agents[writer_id]
        for reader_id in sorted(surface.readers):
            if reader_id == writer_id or reader_id not in agents:
                continue
            reader = agents[reader_id]
            write_at = writer.start
            read_at = max(reader.start, write_at)
            survives_until = writer.end + surface.persistence_hours
            if read_at <= reader.end and read_at <= survives_until:
                edges.append((writer_id, reader_id, read_at))
    return edges


def potential_edges(deployment: Deployment) -> list[tuple[str, str, float, str]]:
    out: list[tuple[str, str, float, str]] = []
    for surface in deployment.surfaces:
        for u, v, t in _surface_edges(deployment, surface):
            out.append((u, v, t, surface.surface_id))
    return sorted(out, key=lambda e: (e[2], e[0], e[1], e[3]))


def temporal_reachability(deployment: Deployment) -> dict[str, set[str]]:
    """Compute upper-bound reachability via nondecreasing event times."""
    events = potential_edges(deployment)
    ids = sorted(a.agent_id for a in deployment.agents)
    reachable: dict[str, set[str]] = {i: set() for i in ids}
    earliest: dict[str, dict[str, float]] = defaultdict(dict)
    for source in ids:
        earliest[source][source] = float("-inf")
    changed = True
    while changed:
        changed = False
        for u, v, t, _ in events:
            for source in ids:
                if u in earliest[source] and earliest[source][u] <= t:
                    prev = earliest[source].get(v)
                    if prev is None or t < prev:
                        earliest[source][v] = t
                        changed = True
    for source in ids:
        reachable[source] = set(earliest[source]) - {source}
    return reachable


def temporal_reachability_ratio(deployment: Deployment) -> float:
    n = len(deployment.agents)
    if n < 2:
        return 0.0
    reachable = temporal_reachability(deployment)
    return sum(len(v) for v in reachable.values()) / (n * (n - 1))

