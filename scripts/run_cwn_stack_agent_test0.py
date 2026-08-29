#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from cwn_coordination_assurance.stack_test0 import evaluate_cwn_stack_agent_test0


def main() -> int:
    # SHA256SUMS is frozen with LF and verify.sh redirects this stdout straight
    # into a manifest-covered file, so text-mode newline translation would fail
    # the manifest check on Windows for a purely cosmetic reason.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(newline="\n")
    parser = argparse.ArgumentParser(description="Run CWN Stack/Agent Test 0 against read-only evidence")
    parser.add_argument("evidence", type=Path, help="JSON evidence exported by the CWN repository adapter")
    parser.add_argument("--output", type=Path, help="optional JSON result path")
    parser.add_argument("--now", help="test-only RFC 3339 evaluation time; omit for the current time")
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    evaluation_time = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else None
    result = evaluate_cwn_stack_agent_test0(evidence, now=evaluation_time).to_dict()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return {"PASS": 0, "UNKNOWN": 3, "FAIL": 4}[result["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
