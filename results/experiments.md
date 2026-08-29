# Deterministic Experiment Report

> Synthetic falsification evidence only. This is not a reproduction of the 2026 incident and not production validation.

## E01 — topology counterexample

```json
{
  "baseline_same_inputs": 1900.0,
  "clique_tcr": 1.0,
  "finding": "baseline has no topology input",
  "id": "E01",
  "name": "topology counterexample",
  "split_tcr": 0.47368421052631576
}
```

## E02 — broadcast accounting

```json
{
  "emitted_write_units": 12000,
  "finding": "pairings times per-agent writes double counts broadcast emission",
  "id": "E02",
  "naive_pair_write_units": 7194000.0,
  "name": "broadcast accounting",
  "overcount_factor": 599.5
}
```

## E03 — temporal overlap

```json
{
  "durable_tcr": 0.5,
  "ephemeral_tcr": 0.0,
  "id": "E03",
  "name": "temporal overlap"
}
```

## E04 — multi-surface composition

```json
{
  "finding": "max-per-surface misses causal paths across surfaces",
  "id": "E04",
  "max_baseline_ce": 0.0,
  "name": "multi-surface composition",
  "per_surface_agents": 2,
  "temporal_reachability": 0.5
}
```

## E05 — read visibility

```json
{
  "baseline_high": 450.0,
  "baseline_low": 450.0,
  "capacity_high": 800.0,
  "capacity_low": 8.0,
  "id": "E05",
  "name": "read visibility"
}
```

## E06 — entropy blindness

```json
{
  "constant_unique_symbols": 1,
  "diverse_unique_symbols": 1000,
  "finding": "write counts do not estimate information without symbol distribution",
  "id": "E06",
  "name": "entropy blindness",
  "writes": 1000
}
```

## E07 — persistence sensitivity

```json
{
  "ce_p1": 45.0,
  "ce_p10": 450.0,
  "ce_p100": 4500.0,
  "finding": "unvalidated P directly controls score by orders of magnitude",
  "id": "E07",
  "name": "persistence sensitivity"
}
```

## E08 — criticality phase behavior

```json
{
  "above_mean_peak": 28.14,
  "below_mean_peak": 1.005,
  "finding": "topology and dynamics create threshold-like behavior absent from CE",
  "id": "E08",
  "name": "criticality phase behavior",
  "runs": 200
}
```

## E09 — single-intervention optimizer

```json
{
  "id": "E09",
  "name": "single-intervention optimizer",
  "result": {
    "after": 0.8636363636363636,
    "before": 17.271943092122278,
    "intervention": "s0:ttl_zero",
    "reduction": 16.408306728485915
  }
}
```

## E10 — base-rate precision

```json
{
  "finding": "attractive sensitivity can still produce unusable alert precision",
  "fpr": 0.052,
  "id": "E10",
  "name": "base-rate precision",
  "precision": 0.01888645463473597,
  "prevalence": 0.001,
  "tpr": 1.0
}
```

## E11 — receipt tamper

```json
{
  "id": "E11",
  "name": "receipt tamper",
  "tampered_valid": false,
  "valid": true
}
```

## E12 — rate limiting

```json
{
  "after": {
    "baseline_ce_max": 66.0,
    "information_capacity_upper_bound_bits": 96.0,
    "metric_version": "CFA-0.2.0-research",
    "risk_state": "RESEARCH_ONLY",
    "spectral_criticality_proxy": 0.2750000000000001,
    "structural_directed_pairs": 132,
    "telemetry_coverage": 1.0,
    "temporal_reachability_ratio": 1.0,
    "warnings": [
      "capacity and criticality values are upper-bound research proxies, not incident probabilities",
      "permission reachability is not evidence of deliberate coordination"
    ]
  },
  "before": {
    "baseline_ce_max": 660.0,
    "information_capacity_upper_bound_bits": 960.0,
    "metric_version": "CFA-0.2.0-research",
    "risk_state": "RESEARCH_ONLY",
    "spectral_criticality_proxy": 0.5000000000000001,
    "structural_directed_pairs": 132,
    "telemetry_coverage": 1.0,
    "temporal_reachability_ratio": 1.0,
    "warnings": [
      "capacity and criticality values are upper-bound research proxies, not incident probabilities",
      "permission reachability is not evidence of deliberate coordination"
    ]
  },
  "id": "E12",
  "name": "rate limiting"
}
```

## E13 — ephemerality

```json
{
  "durable_criticality": 9.999999999622483,
  "ephemeral_criticality": 0.5000000000000001,
  "id": "E13",
  "name": "ephemerality"
}
```

## E14 — identity alias inflation

```json
{
  "alias_ce": 4950.0,
  "factor": 110.0,
  "id": "E14",
  "name": "identity alias inflation",
  "principal_ce": 45.0
}
```

## E15 — coefficient uncertainty

```json
{
  "draws": 10000,
  "finding": "ordinal ranking is unstable under plausible unvalidated persistence weights",
  "id": "E15",
  "name": "coefficient uncertainty",
  "rank_flip_rate": 0.8081
}
```
