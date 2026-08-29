#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    # Public distribution manifest. Deliberately NOT the DevKit's internal doc
    # set: the handoff, source-verification and operating-rule files are working
    # documents for the team that built this, not part of the standard. Anything
    # listed here must exist or the package is not publishable.
    required=[
        "README.md", "STANDARD.md", "RESULTS.md", "TEST_0.md",
        "THREAT_MODEL.md", "RELEASE_GATES.md", "THIRD_PARTY_NOTICE.md",
        "pyproject.toml", "SHA256SUMS",
    ]
    missing=[p for p in required if not (ROOT/p).exists()]
    if missing: raise SystemExit(f"missing required files: {missing}")
    for p in sorted((ROOT/"contracts").glob("*.json")):
        json.loads(p.read_text(encoding="utf-8"))
    for p in sorted((ROOT/"configs").glob("*.json")):
        json.loads(p.read_text(encoding="utf-8"))
    corpus=ROOT/"evals"/"adversarial_corpus.jsonl"
    rows=[json.loads(x) for x in corpus.read_text(encoding="utf-8").splitlines() if x.strip()]
    ids=[r["id"] for r in rows]
    if len(ids)!=len(set(ids)): raise SystemExit("duplicate eval id")
    if len(rows)<25: raise SystemExit("adversarial corpus must contain at least 25 cases")
    print(json.dumps({"required_files":len(required),"contracts":len(list((ROOT/"contracts").glob("*.json"))),"eval_cases":len(rows),"status":"pass"},sort_keys=True))


if __name__=="__main__": main()
