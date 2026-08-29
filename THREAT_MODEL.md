# Threat Model

## Protected assets

- authorization integrity and permit keys;
- tenant/workspace isolation;
- surface and identity truth;
- event ordering and provenance;
- graph availability/integrity;
- calibration and evaluation integrity;
- incident evidence and reviewer independence;
- beneficial collaboration utility;
- sensitive relationship metadata.

## Adversaries and failures

1. Agent intentionally creates a storage/timing/metadata covert channel.
2. Benign agents accidentally coordinate through shared state.
3. Agent forges, replays, suppresses, delays, aliases, or floods observations.
4. Operator disables safeguards for evaluation or performance.
5. Insider authorizes an unsafe bypass or alters calibration.
6. Compromised collector/PEP signs false events.
7. Cross-tenant IDs or prefixes are confused.
8. Adaptive population stays beneath static thresholds.
9. Monitor is attacked to trigger denial-of-service pauses.
10. Graph outage or stale snapshot causes fail-open behavior.
11. Optimizer removes necessary collaboration or concentrates risk elsewhere.
12. Research component’s assumptions are marketed as proven controls.

## Security invariants

- No advisory output can mint, modify, extend, or satisfy an `ExecutionPermit`.
- No research process holds Neo4j credentials.
- Core authorization facts are immutable and namespaced away from advisory facts.
- Tenant identity is exact and typed, never raw-prefix matched.
- Every accepted event has valid signature, trusted key, sequence, nonce, timestamp, schema, policy epoch, and source attestation.
- Missing coverage/calibration/identity returns `UNKNOWN`.
- High-risk bypass is scoped, two-person, expiring, and receipted.
- Pause authority is narrowly scoped, tested, recoverable, and resistant to alert flooding.
- Destruction claims require external purge attestation plus post-purge sampling.
- Calibration data, generator, model, threshold, split, and promotion decision are versioned and hashed.
- Production control claims require independent evidence and confidence intervals.

## Abuse cases and tests

| Abuse | Expected result |
|---|---|
| alias one principal as many agents | principal-bound aggregation; identity warning |
| reuse cross-tenant surface ID | schema rejection |
| late event creates false temporal order | watermark policy and replay revision |
| suppress all reads but keep write permission | permission profile remains potential; observed profile shows missing coverage |
| high-rate benign fanout | approved workflow/common-cause suppression; no intent claim |
| low-rate encoded coordination | multi-channel temporal/marker/lineage detection candidate |
| disable monitoring in evaluation | unreceipted parity drift blocks deployment/promotion |
| repeatedly renew bypass | renewal-pattern alert and human review |
| forge purge receipt | signature/attestation rejection |
| alert flood | rate-limited scoped pause and independent evidence requirement |
| graph unavailable | existing verified permit follows local fail-safe semantics; no new authority |
| poison calibration | signed corpus root, independent holdout, reviewer separation |

## Residual risk

No finite telemetry set proves absence of covert coordination. Closed providers hide activations; owned-model probes transfer imperfectly; temporal/common-cause confounding persists; external services can create undiscovered channels; and a capable adaptive adversary may exploit uninstrumented physics. The correct security claim is bounded detection and control coverage, not universal detection.

