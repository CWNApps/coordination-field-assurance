# Evals and Release Gates

## Evaluation layers

| Layer | Unit | Metrics | Split |
|---|---|---|---|
| contracts | record | schema rejection, canonicalization, replay | golden/adversarial |
| discovery | resource | precision/recall by surface and access edge | IaC/provider holdout |
| identity | event | principal/agent/run/session/campaign binding coverage | restart/alias/provider holdout |
| temporal graph | path | exact time-respecting reachability | generated + manually audited |
| metric | deployment window | invariants, sensitivity, uncertainty | scenario holdout |
| detector | tenant-window/day | AUROC, AUPRC, FPR, PPV, calibration error | temporal/org/topology/adaptive holdout |
| intervention | controlled trial | exposure delta, harmful/benign outcome, utility cost | matched controls |
| operations | incident drill | acknowledge/pause/recover time | quarterly human drill |

## Required falsification tests

- clique, star, chain, disconnected, bridge, and temporal nonoverlap;
- asymmetric read/write and one-way channels;
- broadcast, queue, key-value, metadata, timing, cache, vector, tool-result, telemetry, and external-service surfaces;
- constant versus high-entropy writes;
- durable artifacts, backups, replicas, purge failures, and protocol reconstruction;
- shared principal, aliases, restarts, cloned agents, and missing campaign IDs;
- approved collaboration, common scheduler, incident burst, shared template, and shared upstream dependency;
- slow-and-low, burst, steganographic, cross-surface, cross-tenant, and adaptive traffic shaping;
- malformed, late, duplicated, reordered, unsigned, revoked-key, and replayed events;
- graph/collector/policy/reviewer outages;
- monitor-driven DoS and utility-destroying mitigation.

## Statistical gates

- report confidence intervals, not point estimates alone;
- freeze alert unit and base rate before threshold selection;
- tune only on training/calibration partitions;
- require temporal, organization, provider/model, and topology holdouts;
- show PPV at realistic prevalence;
- control multiple testing at the operational alert unit;
- publish coverage and abstention/`UNKNOWN` rate;
- compare against simple volume/topology/random baselines;
- require prospective shadow results before canary enforcement;
- require causal intervention evidence for claimed mitigation benefit.

## Promotion states

### `UNKNOWN`

Any missing identity, telemetry, policy epoch, signature, surface inventory, or calibration binding.

### `RESEARCH_ONLY`

Reference/synthetic harness passes and outputs are reproducible. No production claim.

### `SHADOW_VALIDATED`

Independent corpus, realistic base rates, prospective shadow deployment, privacy review, and operational drills pass. No autonomous enforcement from detector scores.

### `PRODUCTION_ELIGIBLE`

Only a specific bounded control can reach this state after security, legal, TAC/productization, privacy, reliability, rollback, and independent confirmation gates. Trust Gate remains authoritative.

## Machine-readable gates

See `configs/release_gates.json`. The current package intentionally fails production promotion because live graph freshness, independent calibration, production coverage, privacy/legal review, and shadow evidence are absent.

