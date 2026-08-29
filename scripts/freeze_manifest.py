#!/usr/bin/env python3
"""Freeze the sha256 of every kit file into SHA256SUMS.

`--out` writes elsewhere so the writer can be tested without mutating the
tracked manifest. Exclusions must stay identical to verify_manifest.py's.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=ROOT/"SHA256SUMS"


def freeze(out: Path) -> int:
    # Resolve before comparing: a relative --out inside the tree would otherwise
    # miss the `p==out` exclusion, hash its own stale bytes, then overwrite them.
    out=out.resolve()
    rows=[]
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p==DEFAULT_OUT or p==out or "__pycache__" in p.parts or p.suffix==".pyc": continue
        rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}")
    # newline="\n": SHA256SUMS is compared byte for byte across platforms.
    out.write_text("\n".join(rows)+"\n",encoding="utf-8",newline="\n")
    return len(rows)


def main() -> None:
    parser=argparse.ArgumentParser(description="Freeze kit file hashes")
    parser.add_argument("--out",type=Path,default=DEFAULT_OUT,help="manifest path (default: SHA256SUMS)")
    args=parser.parse_args()
    print(f"frozen {freeze(args.out)} files")


if __name__=="__main__": main()
