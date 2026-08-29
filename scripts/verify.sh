#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m compileall -q "$ROOT/src" "$ROOT/tests" "$ROOT/experiments"
python3 -m unittest discover -s "$ROOT/tests" -v
set +e
python3 "$ROOT/scripts/run_cwn_stack_agent_test0.py" "$ROOT/evals/cwn_stack_agent_test0_snapshot.json" \
  --now "2026-08-28T12:00:00Z" > "$ROOT/results/cwn_stack_agent_test0_snapshot.json"
TEST0_STATUS=$?
set -e
if [[ "$TEST0_STATUS" -ne 3 ]]; then
  echo "supplied stale Test 0 evidence must return UNKNOWN (3), got $TEST0_STATUS" >&2
  exit 1
fi
python3 "$ROOT/experiments/run_experiments.py"
python3 "$ROOT/scripts/validate_package.py"
python3 "$ROOT/scripts/security_scan.py"
python3 "$ROOT/scripts/verify_manifest.py"
