#!/usr/bin/env python3
"""Compute a coordination profile from a measured deployment snapshot.

    export PYTHONPATH="$PWD/src"
    python3 scripts/run_profile.py deployment.json

Exit codes describe the PROFILE, not the run:

    0   a conforming exposure profile was emitted
    3   REFUSED -- one or more required metrics could not be computed from
        measured inputs. The output names each missing input and the instrument
        you would have to build. This is a result, not an error.
    2   the snapshot could not be read or is malformed

A refusal is the honest outcome for most deployments today. `icb_bits_upper_bound`
is a required field of the profile with no null permitted, so a system that does
not record the size of its surface writes cannot produce a conforming profile at
all. Emitting zero instead would certify that deployment as having no information
capacity, which is a stronger claim than any evidence supports.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from cwn_coordination_assurance.profile import compute_profile  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("snapshot", type=Path, help="deployment snapshot JSON")
    parser.add_argument("-o", "--output", type=Path, help="write here instead of stdout")
    args = parser.parse_args()

    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"cannot read snapshot: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(snapshot, dict) or "deployment_id" not in snapshot:
        print("snapshot is not a deployment snapshot object", file=sys.stderr)
        return 2

    result = compute_profile(snapshot)
    body = result.profile if result.emitted else result.refusal
    rendered = json.dumps(body, indent=2, sort_keys=True) + "\n"

    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(newline="\n")
        print(rendered, end="")

    if result.emitted:
        p = result.profile
        print(f"profile emitted: SDE={p['sde']} TCR={p['tcr']:.4f} "
              f"ICB={p['icb_bits_upper_bound']:.1f} bits  state={p['state']}",
              file=sys.stderr)
        for w in p.get("warnings", []):
            print(f"  warning: {w}", file=sys.stderr)
        return 0

    print("REFUSED to emit a coordination profile.", file=sys.stderr)
    for metric, missing in result.refusal["unmet_metrics"].items():
        print(f"  {metric}: blocked by {', '.join(missing)}", file=sys.stderr)
    print("instruments you need to build:", file=sys.stderr)
    for name, info in result.refusal["instruments_needed"].items():
        print(f"  {name} [{info['status']}] -> {info['instrument_needed']}", file=sys.stderr)
    if result.partials:
        parts = ", ".join(
            f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}"
            for k, v in sorted(result.partials.items())
        )
        print(f"measured anyway: {parts}", file=sys.stderr)
    for w in result.warnings:
        print(f"  warning: {w}", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
