# First run against a production stack

**Subject:** Cyber Warrior Network — Trust Gate, production graph
**Date:** 2026-08-28
**Method:** read-only, reader-role credential, no writes, no migrations, no deploys
**State:** `RESEARCH_ONLY`

We ran this standard against our own system first. Not as a demonstration that we pass — we do not
fully pass — but because a standard whose author has not run it on themselves is a proposal, not a
measurement.

---

## Test 0 — the substrate gate

**Result: `UNKNOWN` (exit 3) — 6 pass · 10 unknown · 0 fail**

| | |
|---|---|
| Snapshot freshness | PASS — evidence collected live, not from a stored snapshot |
| Read-only shadow mode | PASS |
| Agent identity uniqueness | PASS — 125 agents, no duplicate identities |
| Research plane has no authority | PASS — the measuring layer holds no keys and cannot allow or deny |
| Signed-event coverage | PASS — 100.0% (247/247) |
| Event-sequence coverage | PASS — 100.0% (247/247) |
| **Ten remaining checks** | **UNKNOWN** — see below |

Zero failures does **not** mean the system is proven. It means nothing we could measure fell below
the line. The ten unknowns are what stand between this and a real claim.

---

## Surface inventory

| | |
|---|---|
| Resources observed | 24 |
| **Shared coordination surfaces** | **4**, across 28 agents |
| **Structural Directed Exposure (SDE)** | **4** directed influence pairs |
| Largest single surface | **14 agents** |
| **Cross-tenant surfaces** | **2** |
| Surface classes unrecognised by the classifier | 18 of 24 |

### The caveat that matters more than the number

**SDE = 4 is a floor, not a finding.**

The 14-agent surface resolves to 14 writers and **zero readers**, so it contributes nothing to the
count — despite being structurally capable of 182 directed pairs. Fourteen agents writing somewhere
nobody reads is far more likely to be *unobserved reads* than a genuinely write-only surface.

Read events are under-represented in our decision log. Reader sets come out empty. Exposure reads
near zero — which is the flattering direction, and therefore the direction that deserves the least
trust.

Closing that gap is the next instrument, and **it will make our own number worse**. That is the
correct direction of travel for an assurance measure.

---

## The ten unknowns, by what actually blocks them

Not ten separate problems. Five kinds of blocker.

### 1 — Behaviour cannot be read from a database
*Gates: unsigned-permit rejection, advisory-overwrite prevention, replay protection*

These are claims about what a system does *under attack*. No query answers them. Both controls exist
in our code and have passing tests — but a test passing in CI is not evidence collected from the
running deployment.

**Instrument needed:** a reproduction harness that attempts each violation against a live shadow
deployment and records the refusal as signed evidence.

### 2 — Verification needs a key the measuring layer must not hold
*Gate: receipt signature-verification coverage*

We can prove a signature is *present*. Proving it *validates* requires the public key and the exact
canonical payload — and this standard forbids the research plane from holding key material, because
a measuring layer that can verify can also forge.

Reporting signature *presence* as *verification* would have scored 100% and meant nothing.

**Instrument needed:** a verification leg in a separate trust domain that re-checks signatures and
publishes only the coverage ratio, never the keys.

### 3 — The system does not record it yet
*Gates: run-to-principal bindings, policy-epoch binding, runtime record coverage*

Five expected record types have **zero rows in production**. Nothing is broken; nothing writes them.

**Instrument needed:** emit those records at the point of the event, and bind the policy epoch into
the receipt at signing time rather than inferring it afterwards.

### 4 — The measurement itself does not exist
*Gates: migration-ledger reconciliation, tenant-binding completeness*

Migration state cannot be inferred from filenames, and our live registry is known to misreport
long-applied migrations as pending. Tenant-binding completeness has no instrument at all.

**Instrument needed:** a live registry reconciler, and a tenant-coverage meter that reports UNKNOWN
rather than assuming completeness.

### 5 — It needs a human, not a program
*Gate: restricted payload exclusion*

Whether restricted payload classes are excluded from the evidence graph is a privacy and retention
judgement. A script can check field names; it cannot decide what should never have been recorded.

**Instrument needed:** a documented privacy review, re-run when the schema changes.

---

## What we got wrong on the way here

Recorded because a measurement you can show is one whose mistakes you can also show. Every one of
these was caught by adversarial review against production data, corrected, and left in the commit
history.

**We read the wrong identifier field.** Decision nodes key on `id`; we queried `decision_id`, which
those writers set on the *linked* receipt instead. A wrong property name in a graph query returns
null rather than raising, so it produced a fully coherent false story: a coverage figure, a growth
curve, a suspect writer. All of it retracted. The supposedly-missing identifiers were present the
whole time.

**We counted the wrong population, twice.** First by including every labelled row — 359 of which
were the product's own release-lifecycle records, inflating both halves of the fraction and making
coverage read about twice as good as reality. Then by counting deliberately-retired duplicate
records as live decisions.

**We built the prerequisite and mistook it for the product.** Test 0 asks whether a stack can be
observed. That is necessary and it is not the measurement. The surface inventory is the first
instrument that actually feeds a metric.

Each error ran in the direction that flattered the system. That is the direction nobody catches by
accident, which is why the standard requires missing evidence to yield `UNKNOWN` rather than a
default pass.

---

## What this report does not claim

- Not an incident probability
- Not evidence of malicious intent or actual collusion
- Not a security, compliance or certification claim
- Not a validated calibration — the coefficients in this standard are unvalidated and the standard
  says so in its own text

It is one deployment, on one day, under a stated method, with its gaps named.
