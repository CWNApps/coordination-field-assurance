from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .fixtures import deployment
from .metrics import evaluate_deployment


def main() -> None:
    # This CLI emits machine-readable JSON; its bytes must not vary by platform.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(newline="\n")
    parser = argparse.ArgumentParser(description="CWN coordination assurance research harness")
    parser.add_argument("--agents", type=int, default=4)
    parser.add_argument("--topology", choices=["clique", "star", "chain", "disconnected"], default="clique")
    parser.add_argument("--persistence-hours", type=float, default=0.0)
    args = parser.parse_args()
    result = evaluate_deployment(deployment(args.agents, topology=args.topology, persistence=args.persistence_hours))
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

