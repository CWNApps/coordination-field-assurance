from __future__ import annotations

import random


def simulate_diffusion(
    matrix: list[list[float]],
    beta: float,
    recovery: float,
    steps: int,
    seed: int,
    initially_active: tuple[int, ...] = (0,),
) -> list[int]:
    if not 0 <= beta <= 1 or not 0 <= recovery <= 1:
        raise ValueError("beta and recovery must be probabilities")
    rng = random.Random(seed)
    active = set(initially_active)
    counts = [len(active)]
    n = len(matrix)
    for _ in range(steps):
        nxt = {i for i in active if rng.random() >= recovery}
        for target in range(n):
            if target in active:
                continue
            escape = 1.0
            for source in active:
                escape *= 1.0 - min(1.0, beta * matrix[source][target])
            if rng.random() < 1.0 - escape:
                nxt.add(target)
        active = nxt
        counts.append(len(active))
    return counts


def alert_precision(prevalence: float, true_positive_rate: float, false_positive_rate: float) -> float:
    for value in (prevalence, true_positive_rate, false_positive_rate):
        if not 0 <= value <= 1:
            raise ValueError("probabilities must be in [0,1]")
    tp = prevalence * true_positive_rate
    fp = (1.0 - prevalence) * false_positive_rate
    return tp / (tp + fp) if tp + fp else 0.0

