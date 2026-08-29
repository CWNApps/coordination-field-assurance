from __future__ import annotations

from .models import AgentWindow, Deployment, Surface


def agents(n: int, *, stagger: bool = False) -> tuple[AgentWindow, ...]:
    out = []
    for i in range(n):
        start = float(i * 2) if stagger else 0.0
        out.append(AgentWindow(f"a{i}", f"p{i}", start, start + 1.0))
    return tuple(out)


def deployment(
    n: int = 4,
    *,
    topology: str = "clique",
    persistence: float = 0.0,
    coverage: float = 1.0,
    calibrated: bool = True,
    stagger: bool = False,
) -> Deployment:
    aa = agents(n, stagger=stagger)
    ids = [a.agent_id for a in aa]
    surfaces = []
    if topology == "clique":
        surfaces.append(Surface("s0", frozenset(ids), frozenset(ids), 10, 8, 1.0, persistence, "durable" if persistence else "ephemeral"))
    elif topology == "star":
        center = ids[0]
        for i, leaf in enumerate(ids[1:]):
            surfaces.append(Surface(f"s{i}", frozenset({center, leaf}), frozenset({center}), 10, 8, 1.0, persistence))
    elif topology == "chain":
        for i in range(n - 1):
            surfaces.append(Surface(f"s{i}", frozenset({ids[i + 1]}), frozenset({ids[i]}), 10, 8, 1.0, persistence))
    elif topology == "disconnected":
        half = max(1, n // 2)
        for j, group in enumerate((ids[:half], ids[half:])):
            if group:
                surfaces.append(Surface(f"s{j}", frozenset(group), frozenset(group), 10, 8, 1.0, persistence))
    else:
        raise ValueError(topology)
    return Deployment("d0", aa, tuple(surfaces), 1.0, "p1", coverage, "cal1" if calibrated else None)

