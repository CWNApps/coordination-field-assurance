# Coordination Field Assurance

**Capability is a property of the model. Risk is a property of the deployment.**

A standard for measuring whether AI agents in a live system *can* influence each other — and a
dependency-free reference implementation you can run against your own stack.

---

## The problem

In the METR/Hugging Face incident, roughly 1,200 agents that were supposed to be isolated found a
shared writable cache, turned directory names into a message board, and built a working coordination
protocol in about 96 hours. Detection took 68 days, and came from a routine identity-API alert — not
from alignment monitoring.

Every one of those agents passed its model evaluation. The models were fine. The **deployment** was
not: a shared surface nobody had inventoried.

The unit of risk is not the model. It is the **coordination surface** — any shared mutable state two
agents can both reach and both change. Its danger scales with the number of agents on it, and it
scales *quadratically*, because what matters is the number of directed pairs who could influence one
another:

| Agents on one surface | Directed influence pairs |
|---:|---:|
| 2 | 2 |
| 5 | 20 |
| 14 | 182 |
| 1,200 | 1,438,800 |

A per-model score cannot see this. The risk is not inside any agent. It is in the arithmetic between
them.

---

## What this is not

The obvious formula is wrong, and this standard exists partly to say so:

```
CE = N(N-1)/2 × B × D × P        ← rejected, do not use
```

It multiplies incompatible units, ignores who can actually reach whom and when, and double-counts a
broadcast write as if every reader pair were a separate channel. It produces one confident number
that cannot be defended when someone asks how it was derived.

**Normative rule: no single scalar may be called "coordination risk."** A conforming report is a
profile with an explicit evidence state.

---

## The six measures

| | | |
|---|---|---|
| **SDE** | Structural Directed Exposure | Count of directed pairs who *could* influence one another. The quadratic term, made countable. |
| **TCR** | Temporal Causal Reachability | Of those pairs, how many could in *time* — edges time-respecting, state surviving until the next read. |
| **ICB** | Information Capacity Bound | Upper bound on information crossing a surface. Never multiplied by reader pairs for broadcast. |
| **PRV** | Persistence & Reconstitution Vector | Raw evidence, not a coefficient: TTL, purge attestation, reset survival, reconstruction time. |
| **CCP** | Coordination Criticality Proxy | ρ(T), spectral radius. A research proxy for ranking what to fix. Never an authorization input. |
| **OCE** | Observed Coordination Evidence | Requires two independent signal families and modelled common causes before any alert candidate. |

**HCR — Harmful Coordination Risk — is deliberately not computed.** It would require labelled harmful
and benign deployments, realistic prevalence, temporal and organisational holdouts, adaptive attacks
and calibration. Claiming it without those is the thing this standard exists to refuse.

Full definitions with formulas: [`STANDARD.md`](STANDARD.md).

---

## Report states

Every conforming report ends in exactly one of:

`UNKNOWN` · `RESEARCH_ONLY` · `SHADOW_VALIDATED` · `PRODUCTION_ELIGIBLE`

**This reference implementation can only ever emit the first two.** That ceiling is deliberate and
enforced by tests — a research harness must not be able to certify production.

---

## Run it

No dependencies. Python 3.11+.

```bash
bash scripts/verify.sh
```

That runs the unit and adversarial suites, the seeded falsification experiments, the package
validator, a security-boundary scan, and a manifest integrity check.

**Test 0** is the substrate gate — sixteen checks on whether your stack can be observed at all, which
is the prerequisite for measuring anything else:

```bash
export PYTHONPATH="$PWD/src"
python3 scripts/run_cwn_stack_agent_test0.py evals/cwn_stack_agent_test0_snapshot.json
```

Exit codes: `0` PASS · `3` UNKNOWN · `4` FAIL. The bundled snapshot is stale on purpose and returns
UNKNOWN — a gate that cannot return UNKNOWN is a gate that will eventually lie.

---

## What you have to build

The measures need inputs. Two of the six instruments exist here; the rest are what any organisation
would need to build to produce a full profile. Each one's output is the next one's input:

| # | Instrument | Feeds |
|---|---|---|
| 1 | **Substrate gate** — identity unique, events signed, sequence intact | prerequisite |
| 2 | **Surface inventory** — shared mutable state, by observation, with reader and writer sets | SDE |
| 3 | **Temporal permission graph** — time-respecting reachability with state-survival rules | TCR |
| 4 | **Capacity meter** — write rates, symbol bounds, read visibility per surface | ICB |
| 5 | **Persistence prober** — TTL, purge attestation, reset survival, reconstitution time | PRV |
| 6 | **Reproduction harness** — attempts violations, records refusals as evidence | behavioural gates |

---

## Authority boundary

This harness has **no** database driver, credentials, signer, policy authority, or tool executor. It
reads evidence someone else collected and computes over it. It cannot emit ALLOW or DENY, and it
cannot mint a permit.

Missing identity, signature, coverage, policy epoch or calibration returns `UNKNOWN` — never a
default pass. Synthetic tests never become production security claims.

---

## Results

The first run against a real production stack, including what it could **not** answer and why:
[`RESULTS.md`](RESULTS.md).

---

## Status

`v0.2.0-research`. The definitions are publishable and the mechanism is defensible. The specific
coefficients are not validated, and the standard says so in its own text rather than in a footnote.

Publish the definition confidently. Publish the numbers tentatively. Name the weakest parts.
