"""The manifest gate must fail on files it does not cover.

`freeze_manifest.py` enumerates every file that exists at freeze time, but
`verify_manifest.py` only ever walked the entries already listed in SHA256SUMS.
Anything added afterwards therefore sat completely outside the integrity gate
and verification still printed "manifest verified" and exited 0 -- a gate
certifying coverage it did not have.

These tests pin both directions: an uncovered file must FAIL, and the
exclusions the freezer already applies must stay excluded so the new check
cannot fire on its own build artifacts.
"""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

# Probing the tree-scan REQUIRES a real file in the tree, so this cannot be moved to
# a temp dir the way the experiment test was. Names are made unique per process so
# concurrent runs cannot unlink each other's probe; cleanup is in `finally`, which
# still cannot survive a hard process kill.
TAG = f"probe_{os.getpid()}"

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "verify_manifest.py"


def _env_for_run() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(VERIFY)], cwd=ROOT,
                          env=_env_for_run(), capture_output=True, text=True)


class ManifestCoverageTests(unittest.TestCase):
    def test_clean_tree_verifies(self):
        proc = _run()
        self.assertEqual(proc.returncode, 0, f"clean tree should verify: {proc.stdout}{proc.stderr}")
        self.assertIn("manifest verified", proc.stdout)

    def test_unlisted_file_fails_verification(self):
        intruder = ROOT / f"unlisted_intruder_{TAG}.txt"
        self.assertFalse(intruder.exists(), "probe path must not already exist")
        intruder.write_text("not in the manifest\n", encoding="utf-8", newline="\n")
        try:
            proc = _run()
            self.assertNotEqual(proc.returncode, 0, "an unlisted file must fail the gate, not pass it")
            self.assertIn(intruder.name, proc.stdout + proc.stderr)
        finally:
            intruder.unlink()

    def test_unlisted_file_in_subdirectory_fails(self):
        intruder = ROOT / "src" / "cwn_coordination_assurance" / f"unlisted_module_{TAG}.py"
        self.assertFalse(intruder.exists(), "probe path must not already exist")
        intruder.write_text("# not in the manifest\n", encoding="utf-8", newline="\n")
        try:
            proc = _run()
            self.assertNotEqual(proc.returncode, 0, "nested unlisted files must fail too")
        finally:
            intruder.unlink()

    def test_pycache_and_pyc_stay_excluded(self):
        """Negative control: the freezer skips these, so the gate must not fire on them."""
        cache = ROOT / "src" / "cwn_coordination_assurance" / "__pycache__"
        cache.mkdir(exist_ok=True)
        probe = cache / f"coverage_{TAG}.cpython-312.pyc"
        probe.write_bytes(b"\x00compiled\x00")
        try:
            proc = _run()
            self.assertEqual(proc.returncode, 0,
                             f"__pycache__/*.pyc must stay excluded: {proc.stdout}{proc.stderr}")
        finally:
            probe.unlink()

    def test_manifest_itself_stays_excluded(self):
        """SHA256SUMS cannot list its own hash; it must not be reported as unlisted."""
        proc = _run()
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("SHA256SUMS", proc.stdout + proc.stderr)


    def test_freezer_and_verifier_enumerate_the_same_files(self):
        """Exclusion drift between the two scripts would silently shrink coverage.

        The rule is duplicated in freeze_manifest.py and verify_manifest.py. If
        they ever disagree, the manifest stops meaning what the gate checks.
        """
        import tempfile

        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import verify_manifest
        finally:
            sys.path.pop(0)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "SHA256SUMS"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "freeze_manifest.py"), "--out", str(out)],
                cwd=ROOT, env=_env_for_run(), check=True, capture_output=True,
            )
            frozen = {line.split("  ", 1)[1]
                      for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}

        covered = {p.relative_to(ROOT).as_posix()
                   for p in ROOT.rglob("*") if verify_manifest.covered(p)}
        self.assertEqual(frozen, covered,
                         "freeze_manifest.py and verify_manifest.py disagree on which files count")


if __name__ == "__main__":
    unittest.main()
