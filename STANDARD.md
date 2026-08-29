# Coordination Field Assurance Metric Profile v0.2.0-research

## Normative principle

No single scalar may be called “coordination risk.” A conforming report is a profile with explicit evidence state.

## 1. Structural Directed Exposure (SDE)

For surface `s`, with writer set `W_s` and reader set `R_s`:

```text
SDE_s = |{(w,r): w∈W_s, r∈R_s, w≠r, policy/time permit influence}|
```

This is a count of directed potential influence pairs. It is not throughput or probability.

## 2. Temporal Causal Reachability (TCR)

A path is valid only when its edges are time-respecting and state survives until the next read. For `n` agents:

```text
TCR = reachable ordered agent pairs / (n(n-1))
```

Report the observation window, timestamps, persistence rule, and late-event policy. Permission-derived TCR is an upper bound; observation-derived TCR requires signed events.

## 3. Information Capacity Bound (ICB)

```text
ICB_s ≤ writers × writes/writer/hour × hours × bits/symbol upper bound × read visibility
```

This is deliberately an upper bound. A production estimate needs symbol distribution, encoding, timing resolution, read bandwidth, error rate, contention, compression, deduplication, and surface semantics. It must not be multiplied by reader pair count for broadcast surfaces.

## 4. Persistence and Reconstitution Vector (PRV)

Report raw evidence rather than one coefficient:

- TTL and retention policy;
- purge/destruction attestation;
- reset survival rate;
- cross-run readable fraction;
- reconstruction time distribution;
- artifact lineage depth;
- backup/replica survival;
- policy epoch and revocation generation.

Any scalar reduction is calibration-specific and must carry its dataset ID and uncertainty interval.

## 5. Coordination Criticality Proxy (CCP)

Construct a transmissibility matrix `T` over agents or principals. `T[i,j]` is an empirically bounded handoff probability or normalized capacity for the selected window. Report spectral radius `ρ(T)` as a **research proxy**.

Under branching/SIS-like assumptions, thresholds around `ρ(T)` can separate extinction from persistence. Real agent fleets violate independence, stationarity, and homogeneous-response assumptions; therefore `ρ(T)` is not a universal phase boundary. It is useful for intervention ranking and stress testing, not authorization.

## 6. Observed Coordination Evidence (OCE)

At least two independent signal families are required before an alert candidate:

- temporal motifs or reciprocity;
- resource handoffs;
- shared markers conditioned on frequency/entropy;
- write-volume or symbol-distribution deviation;
- independent behavioral/text monitor;
- owned-model activation signal;
- reconstitution after reset;
- policy/permit mismatch.

Common causes—scheduler, incident, template, model version, approved workflow, shared upstream dependency—must be modeled. Missing coverage yields `UNKNOWN`.

## 7. Harmful Coordination Risk (HCR)

HCR is not computed by this kit. It requires independently labeled harmful and benign deployments, realistic prevalence, temporal holdouts, organization holdouts, adaptive attacks, intervention outcomes, calibration, and confidence intervals.

## Required report fields

- metric profile/version;
- deployment/tenant/window/policy epoch;
- principal, agent, run, session, and campaign identity coverage;
- surface discovery coverage;
- writer/reader telemetry coverage;
- measurement sources and signatures;
- SDE, TCR, ICB, PRV, optional CCP/OCE;
- calibration dataset and split, if any;
- uncertainty/confidence interval;
- caveats and invalid fields;
- evidence Merkle root and receipt reference;
- final state: `UNKNOWN`, `RESEARCH_ONLY`, `SHADOW_VALIDATED`, or `PRODUCTION_ELIGIBLE`.

This reference implementation can emit only `UNKNOWN` and `RESEARCH_ONLY`.

