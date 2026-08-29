# The instruments

A standard that names quantities without saying how to measure them is a
vocabulary, not a standard. This file specifies the six instruments an
organisation needs to run Coordination Field Assurance against its own stack,
what each one measures, what it must refuse to measure, and how to tell whether
yours is working.

Every instrument here takes a **reader callable**, not a database driver. It runs
against an export produced by whatever query tool the organisation already
trusts. No live credentials are handed to a measurement tool, and the export can
be inspected before it is measured.

---

## The rule every instrument obeys

> A failure to measure must never produce a value a consumer reads as a
> measurement, and every bound must err toward **more** apparent exposure.

The asymmetry is the whole point. Overstating exposure wastes an investigation.
Understating it certifies a deployment on evidence nobody collected. Those costs
are not symmetric, so the bounds are not either.

Four measurement statuses, and they are not interchangeable:

| Status | Means |
|---|---|
| `MEASURED` | Every declared input was usable and the value is real |
| `PARTIAL` | Measured over a subset, and the report says which |
| `UPPER_BOUNDED` | Not measured; bounded in the direction that maximises apparent exposure |
| `NOT_RECORDED` | The deployment emits nothing for this, with the instrument required named |
| `DEGRADED` | The read failed. **Not** a finding about the deployment |

A fifth, `NOT_RUN`, belongs to the runner rather than the instrument: it means
the query was never exported. `DEGRADED` points at the deployment; `NOT_RUN`
points at the operator. Conflating them sends someone hunting a fault that does
not exist.

---

## 1. Surface inventory → SDE

**Measures** structural directed exposure: how many directed writer→reader pairs
exist across surfaces that more than one agent touches.

**Query** every (resource, agent, action, tenant, timestamp) tuple in the live
decision population.

**The three decisions that determine whether it is honest**

- **An unrecognised action counts as a WRITE.** Writers create influence,
  readers receive it. Classifying an unknown action as a read understates
  exposure, which is the direction that flatters the deployment.
- **A solo resource is not a coordination surface.** One agent cannot coordinate
  with itself. Counting solo resources inflates the surface count with things
  carrying no coordination risk, which is how a measure stops meaning anything.
- **Self-pairs are excluded.** An agent reading its own write is not
  coordination.

**How to tell yours is broken:** it returns an empty inventory on a failed read.
"No surfaces found" and "could not look" must not render the same.

---

## 2. Substrate coverage → Test 0 gates

**Measures** what fraction of the decision population carries a signature and a
usable ordering key.

**The denominator is the entire problem.** Two mistakes are easy and both inflate
the result in opposite directions:

- Counting lifecycle or feature records as runtime decisions inflates the
  denominator and depresses coverage.
- Counting deliberately-superseded duplicates counts retired evidence twice.

Define the live population explicitly, in the query, and state it in the report.
A denominator nobody can see is a denominator nobody can check.

**One gate must return null permanently.** Signature *verification* coverage
requires key material the measuring layer must not hold — an instrument that
held it could mint what it audits. Reporting signature **presence** in its place
answers a different question and quietly counts as the same one.

---

## 3. Temporal permission graph → TCR

**Measures** temporal causal reachability: what remains reachable once activity
windows are respected. Two agents that never overlap cannot influence each
other, however much surface they share.

**Emits an upper bound, not a measurement.** Persistence is bounded to the
observation window, which maximises reachability on purpose, so TCR is a ceiling
and cannot understate.

**Two unit traps, both of which we hit**

- Hours added to epoch milliseconds. A 4,005-hour bound behaved like four
  seconds and nothing complained.
- A failed window read producing `0.0` hours. That zero propagates into every
  surface's persistence and drives reachability toward nothing — an unmeasured
  deployment reading as one where no written state survives. An unestablished
  window must be `None`.

---

## 4. Capacity meter → ICB

**Measures** a floor on channel capacity. **Refuses** the ceiling.

The safety-relevant ICB quantity is the ceiling: the most that could flow. It
requires payload size at the write site. If your deployment does not record
that, an unobserved channel has no finite bound and any ceiling you emit is a
number chosen for its availability.

**A floor is still worth having.** Content is not the only channel: an agent also
encodes information in *which* action it takes, and that is recorded. An agent
observed using k distinct write actions proves its channel carries at least k
symbols, so that channel's capacity is at least log₂(k) bits per write.

**Be exact about what that bounds.** log₂(k) is a floor on **capacity** and an
*upper* bound on traffic. Actual information conveyed is the entropy of the
agent's action distribution, and H ≤ log₂(k) always — an agent using five
actions but sending one of them 99% of the time transmits far less than log₂(5).
Reading the floor as traffic inverts the inequality. Name the emitted fields for
capacity so a consumer cannot make that mistake from the JSON alone.

**A floor must never satisfy a requirement for a ceiling.** Emit it under its own
key, and do not let it change the status of the `write_sizes` input — a profile
requiring ICB must still refuse.

**Two counting traps**

- Counting reads in a per-**write** figure. On our stack one channel logged 12
  reads, 19 more reads and 5 writes; multiplying the per-write floor by 36 rather
  than 5 overstated it 7.2×.
- Not reporting attribution coverage. Decisions missing an agent or a resource
  cannot be placed on any channel. Three of 247 is a small error; reporting
  `MEASURED` over a silently shrunk population is not.

---

## 5. Persistence prober → PRV

**Measures** each persistence component separately and reports the vector as
evidence.

**Never reduce it to a coefficient.** Any scalar reduction is
calibration-specific and must carry its dataset and uncertainty interval. If you
have no calibration set bound to the deployment, emit `scalar_reduction: null`.

**Every component the standard names must appear**, measured or explicitly absent
with the instrument required. A vector reporting four of eight components and
omitting the rest looks complete.

**The zero-TTL ambiguity.** A TTL of `0` means either "expires immediately" or
"nobody set one". Those are opposite facts — the safest possible surface and an
unbounded one — and folding them into a distribution picks one silently. Count
them separately and flag them.

**Distinguish "no nodes" from "no property".** A label holding zero nodes and a
label whose nodes carry none of the properties both return zero for every
property. Return the population alongside the counts, or "checked, nothing
found" and "nothing was there to check" print identically.

---

## 6. Reproduction harness → the behavioural gates

**Measures** what the system *does*. Some gates are claims about behaviour, not
about stored state, and no query answers them. Asserting one from a code reading
credits the claim to a field rather than to a verified leg.

**Two scopes, and only one of them may set a gate**

| Scope | What it proves |
|---|---|
| `LOGIC` | The control's real code runs in-process with unreachable dependencies injected. Proves the algorithm. |
| `DEPLOYMENT` | The control runs against the deployment's own wiring, nothing injected. Proves this deployment enforces it. |

"The algorithm is correct" and "this deployment enforces it" are different
claims, and a gate asserts the second. A `LOGIC` result must be reported in full
and must not populate the evidence document.

**Every check carries its own negative control.** A verifier hard-wired to return
False passes every refusal test. Never report a control as holding without also
demonstrating it *accepting* a case it should accept. Where the accepting half
cannot run, report `PARTIAL` and name the missing half.

**Exercise the whole reachable input space, not chosen cases.** We got this
wrong and it is worth stating plainly. Our first advisory-cannot-loosen check ran
four cases and reported the control holding. None of them reached the guard: the
composer returned the base action because nothing had tried to change it. Four
cases chosen to exercise today's branches cannot catch a future branch that
loosens. Enumerating all 60 reachable inputs can — and it surfaced the true
finding, which is that the invariant holds *by construction* and the guard
written to enforce it is never exercised at all.

**Do not substitute a double for a constraint.** Where a control depends on a
database constraint, exercising it against an in-memory stand-in tests the
stand-in. Use a non-production target, or report `NOT_EXERCISED` with the
procedure.

**An instrument must not mutate what it measures.** If reaching deployment scope
requires writes, it requires a non-production target — not an exception.

---

## What "we could not measure it" has to include

An unknown is only honest when it comes with what would make it known. For every
gate an instrument cannot answer, state three things:

1. **What it needs** — the specific evidence or environment.
2. **Why not here** — the actual obstacle, not a category.
3. **What must not be done** — the shortcut that would produce a confident wrong
   answer. This is the one most reports omit, and it is the one that stops
   somebody closing the gap by weakening the check.
