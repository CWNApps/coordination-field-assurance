# CWN Stack/Agent Test 0

This is the first integration test. It is a read-only, shadow-mode prerequisite check against evidence collected by the real CWN repository. It does not connect to Neo4j, mint permits, call agents, alter policy, or execute tools.

## Why it comes first

Coordination metrics are not meaningful if agent/run/principal/tenant identity is ambiguous, runtime writers are absent, receipt coverage is unknown, or the research plane can affect authorization. Test 0 therefore blocks metric integration until the substrate is trustworthy enough to observe.

## Required real-stack evidence

- current graph snapshot no older than 24 hours;
- live `MigrationLog` reconciliation, never filename inference;
- unique typed agent, run, principal, tenant/workspace identity;
- observed writers for every required runtime label;
- at least 99% signed-event, sequence, and receipt-verification coverage;
- reproduced rejection of unsigned permits;
- reproduced prevention of advisory overwrite of hard authorization facts;
- proof that the research plane has no action authority;
- replay protection and policy-epoch binding;
- evidence that restricted payloads are excluded.

The supplied 2026-08-02 snapshot is included as `evals/cwn_stack_agent_test0_snapshot.json`. It intentionally returns `UNKNOWN`: it is stale, lacks live migration evidence, has no measured event coverage, and shows no nodes for five required runtime labels.

## Run

```bash
export PYTHONPATH="$PWD/src"
python3 scripts/run_cwn_stack_agent_test0.py evals/cwn_stack_agent_test0_snapshot.json
```

Exit codes are `0=PASS`, `3=UNKNOWN`, and `4=FAIL`. `PASS` authorizes only the next shadow integration slice; it never authorizes production enforcement.

Claude must add a target-repository adapter that exports the schema in `contracts/cwn_stack_agent_test0.schema.json` without placing secrets or unrestricted content in the evidence file. The adapter and its data-source permissions require repository-specific review.
