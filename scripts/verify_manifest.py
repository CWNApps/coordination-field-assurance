#!/usr/bin/env python3
"""Verify every kit file against SHA256SUMS.

Checks BOTH directions. Walking only the listed entries left anything added
after the freeze completely outside the gate, so verification printed
"manifest verified" and exited 0 while an uncovered file sat in the tree.
Exclusions below must stay identical to freeze_manifest.py's, or the two
scripts will disagree about what the manifest is supposed to contain;
tests/test_manifest_coverage.py asserts the two enumerations agree.

Deliberately NOT covered, so this docstring does not claim more than the code
delivers: empty directories (the manifest enumerates files only); anything
reachable only through a directory symlink; broken symlinks, which `is_file()`
reports as absent; and anything under a directory named `__pycache__` or with a
`.pyc` suffix, which is excluded by name at any depth rather than by content.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"SHA256SUMS"


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def covered(p: Path) -> bool:
    """Same exclusion rule as freeze_manifest.py.

    `.git/` matters here: this package is the repository root in its public
    distribution, so without excluding it a fresh clone reports git's own
    metadata as unlisted files and fails the integrity check.
    """
    if not p.is_file() or p == MANIFEST:
        return False
    parts = p.parts
    return not (
        "__pycache__" in parts
        or p.suffix == ".pyc"
        or ".git" in parts
        or ".pytest_cache" in parts
    )


def main():
    if not MANIFEST.exists():
        print("manifest absent during development; skipped")
        return
    listed={}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        expected, rel=line.split("  ",1)
        listed[rel]=expected

    bad=[rel for rel, expected in listed.items()
         if not (ROOT/rel).exists() or digest(ROOT/rel)!=expected]
    present={p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if covered(p)}
    unlisted=sorted(present-listed.keys())

    if bad: raise SystemExit(f"manifest mismatch: {sorted(bad)}")
    if unlisted: raise SystemExit(f"unlisted files not covered by manifest: {unlisted}")
    print(f"manifest verified: {len(listed)} files")


if __name__=="__main__": main()
