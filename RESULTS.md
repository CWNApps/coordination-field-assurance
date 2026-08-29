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

## Second pass — three more instruments, 28 Aug 2026

The first publication had two instruments. It now has six. See
[INSTRUMENTS.md](INSTRUMENTS.md) for what each measures and what it must refuse
to measure.

### Information Capacity Bound

| | |
|---|---|
| Write channels observed | 26 |
| **Capacity floor** | **2.32 bits per write**, max and median |
| Channels with a *measured* floor of 0 bits | 11 |
| **Ceiling** | **`NOT_RECORDED`** — permanently |
| Attribution coverage | `PARTIAL` — 244 of 247 runtime decisions |

The ceiling is the safety-relevant quantity and we cannot produce one: nothing
records payload size at the write, and an unobserved channel has no finite
bound. The floor is reported anyway, because it settles the question the
original single-score approach assumed away — capacity between agents sharing a
surface is not negligible.

**The floor bounds capacity, never traffic.** log₂(k) upper-bounds what was
transmitted and lower-bounds what the channel can carry. Reading it the other
way inverts the inequality.

**Three decisions carry no resource** and cannot be placed on any channel, so
the floor covers 244 of 247. Three of 247 is a small error. Reporting
`MEASURED` over a population the instrument had silently shrunk is not, and it
took an invariant rather than a review to catch it.

### Persistence and Reconstitution Vector

Nine components: **2 measured, 2 partial, 5 not recorded, `scalar_reduction:
null`.** Reducing PRV to one coefficient needs a calibration dataset and an
uncertainty interval, and none is bound to this deployment.

| Finding | Measurement |
|---|---|
| **Expired permits still marked live** | **156 of 156** past expiry, still status `ISSUED` |
| **Destruction attestation** | **0 across 4,817 nodes**, five labels, six property conventions |
| Ambiguous expiry | 16 receipts carry `ttl=0` — either "expires immediately" or "never set" |
| Retention coverage | 5.4% — 201 of 3,716 receipts carry a TTL at all |
| Lineage coverage | 5.4% — the same 201 name a parent decision |

Every permit being past expiry while still reading `ISSUED` is the record and
the clock disagreeing about whether a capability is live. No destruction
evidence anywhere means a purge claim is currently an assertion by the same
system that held the data — which is the thing receipts exist to replace.

### Reproduction harness

Two of three behavioural controls now run and hold. **Neither sets a gate**, and
that is the design: both ran at `LOGIC` scope, and proving an algorithm is not
proving this deployment is wired to it.

| Control | Result | Basis |
|---|---|---|
| Unsigned requests refused | `HELD` (logic) | Empty signature refused; a freshly signed request accepted; the same signature refused when replayed onto another resource |
| Advisory cannot loosen | `HELD` (logic) | All 60 reachable inputs composed; 0 less restrictive than their base; 3 still tightened |
| Replay protection | `NOT_EXERCISED` | Needs a write-capable non-production graph |

**A finding we would rather not have published.** The advisory check originally
ran four hand-picked cases and reported the control holding. None of them
reached the guard — with enforcement off the composer returns the base
immediately, and with it on only an `ALLOW` base has an action-changing branch,
so every `DENY` case fell through to an unconditional return. The base came back
because nothing tried to change it.

Enumerating the whole input space fixed it and surfaced the true finding: the
invariant holds **because no branch can produce a looser decision**, not because
the guard written to prevent one refuses. Across all 60 inputs that guard never
fires. It is unreachable defence-in-depth, and saying otherwise would credit the
result to code nothing runs.

That defect was in the instrument built to detect exactly that defect. We are
publishing it because a standard whose author hides their own instance of the
failure it names is not a standard.

### Correction, 2026-08-29: a denominator we published and had not measured

An earlier version of this document reported **zero destruction attestation across
5,271 nodes**. That denominator was wrong. Four of its five components were
measured. The fifth — a decision population of 1,163 — was never queried. It was
typed into a source literal beside the four real figures, inherited their
credibility, and travelled into this document, a wiki entry, a report and three
commit messages.

The live value is **637**. The true scope is **4,817 nodes**.

**The finding did not change.** Every destruction property was zero on every
label, and remains zero on re-measurement. What was false was the claim about how
much had been inspected — a denominator nobody could check, which is the exact
defect this standard was written to name, committed by its author in the document
announcing it.

**What now makes it catchable.** The graph is append-only, so for any label a
committed population that *exceeds* the live one cannot be drift; it can only mean
the number was never measured against that database. 1,163 against 637 fails that
test immediately. Growth in the other direction is ordinary and is reported as
drift rather than error — one receipt count moved from 3,716 to 3,790 during a
single session, and a check that failed on ordinary growth would be switched off
within a week, taking the fabrication case with it.

Equality is reported as consistent, and the output says in words that equality
proves nothing on its own: two numbers agreeing is equally consistent with both
being copied from the same mistake. Only the impossible direction is evidence. A
label that could not be read is not a pass — "could not compare" and "agrees" must
not share an outcome.

The check was negative-controlled against live production, not only in tests: the
corrected file passes, and the file exactly as it had been committed fails on the
one fabricated label.

### Reads are not a snapshot

A receipt count moved from 3,716 to 3,722 between two consecutive queries. The
graph is live, every figure comes from an independent read, and any metric
combining two of them inherits that skew. The export now declares
`read_consistency: NON_ATOMIC` rather than implying a consistent cut.

---

## How the instruments were checked

Eleven defects across three adversarial review rounds, every one verified
against the code before any fix — one by enumerating an entire input space to
confirm the claim was genuinely unsupported. A review that came back blocked was
recorded as a non-pass and rerun rather than counted as clean.

The four that mattered most, all of which understated exposure:

- A per-write figure multiplied by a read-plus-write total — 7.2× too high on
  one channel.
- Write rates reported as `MEASURED` when the surface read had returned nothing.
- A failed window read producing zero hours of persistence, driving reachability
  toward nothing.
- A published query plan that could not detect its own drift and omitted four of
  its six queries. It is now generated by recording what the instruments
  actually issue, and caught its own regression on the first run.

Every fix carries a regression test that was negative-controlled: the defect
reintroduced to confirm the test fails, then removed to confirm it passes. One
existing test was found asserting the very defect it was meant to prevent.

---

## What this report does not claim

- Not an incident probability
- Not evidence of malicious intent or actual collusion
- Not a security, compliance or certification claim
- Not a validated calibration — the coefficients in this standard are unvalidated and the standard
  says so in its own text

It is one deployment, on one day, under a stated method, with its gaps named.
