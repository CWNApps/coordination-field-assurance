"""Generated artifacts must be byte-identical on every platform.

SHA256SUMS freezes the sha256 of the working-tree bytes of every kit file,
including the regenerated files under results/. scripts/verify.sh regenerates
those files and then verifies them against that frozen manifest, so any
platform-dependent byte in the output turns verify.sh into a guaranteed
failure that has nothing to do with correctness.

Python's text mode translates "\n" to os.linesep on write, so on Windows every
writer here emitted CRLF and mismatched an LF-frozen manifest.

Coverage note, so this module does not overstate itself: the writer tests below
drive the real writers through a subprocess and assert on the bytes those
writers produce. `test_committed_results_are_lf_only` is different in kind --
it asserts the bytes of the CHECKOUT, which the parent .gitattributes (`* -text`)
is what actually guarantees. It guards that separate property and is not
evidence about any writer.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
EVIDENCE = ROOT / "evals" / "cwn_stack_agent_test0_snapshot.json"
FIXED_NOW = "2026-08-28T12:00:00Z"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _manifest() -> dict[str, str]:
    out = {}
    for line in (ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            out[rel] = digest
    return out


class ArtifactLineEndingTests(unittest.TestCase):
    def assert_lf_only(self, data: bytes, label: str) -> None:
        self.assertNotIn(b"\r", data, f"{label} contains CR; manifest is frozen with LF")

    def test_committed_results_are_lf_only(self):
        """Checkout assertion, not a writer assertion -- see the module docstring."""
        for name in ("experiments.json", "experiments.md", "cwn_stack_agent_test0_snapshot.json"):
            self.assert_lf_only((RESULTS / name).read_bytes(), f"results/{name}")

    def test_experiment_writers_match_frozen_manifest(self):
        """Regenerate into a temp dir: never mutates the tracked working tree.

        Compared against SHA256SUMS rather than against whatever is on disk, so
        neither a previous bad run nor a concurrent test can affect the result.
        """
        expected = {rel: d for rel, d in _manifest().items() if rel.startswith("results/experiments.")}
        self.assertEqual(len(expected), 2, "expected both experiment artifacts in the manifest")

        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(ROOT / "experiments" / "run_experiments.py"), "--out-dir", tmp],
                cwd=ROOT, env=_env(), check=True, capture_output=True,
            )
            for rel, digest in expected.items():
                produced = Path(tmp) / Path(rel).name
                self.assertTrue(produced.exists(), f"{rel} was not written to the temp dir")
                data = produced.read_bytes()
                self.assert_lf_only(data, f"regenerated {rel}")
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest,
                                 f"{rel} does not match the frozen manifest after regeneration")

    def test_freeze_manifest_writes_lf(self):
        """The manifest writer itself was missed by the first pass and emitted CRLF."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "SHA256SUMS"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "freeze_manifest.py"), "--out", str(out)],
                cwd=ROOT, env=_env(), check=True, capture_output=True,
            )
            self.assert_lf_only(out.read_bytes(), "freeze_manifest.py output")

    def test_cli_stdout_is_lf_only(self):
        """The package CLI emits machine-readable JSON; its bytes must be stable."""
        proc = subprocess.run(
            [sys.executable, "-m", "cwn_coordination_assurance.cli", "--agents", "3"],
            cwd=ROOT, env=_env(), capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr.decode(errors="replace"))
        self.assert_lf_only(proc.stdout, "cli stdout")
        json.loads(proc.stdout.decode("utf-8"))

    def test_test0_runner_output_file_is_lf_only(self):
        """The --output path is public API and is not exercised by verify.sh."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "result.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "run_cwn_stack_agent_test0.py"),
                 str(EVIDENCE), "--now", FIXED_NOW, "--output", str(out)],
                cwd=ROOT, env=_env(), capture_output=True,
            )
            self.assertEqual(proc.returncode, 3, "stale evidence must return UNKNOWN")
            self.assert_lf_only(out.read_bytes(), "--output file")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["state"], "UNKNOWN")

    def test_test0_runner_stdout_is_lf_only(self):
        """verify.sh redirects this stdout straight into a manifest-frozen file."""
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_cwn_stack_agent_test0.py"),
             str(EVIDENCE), "--now", FIXED_NOW],
            cwd=ROOT, env=_env(), capture_output=True,
        )
        self.assertEqual(proc.returncode, 3, "stale evidence must return UNKNOWN")
        self.assert_lf_only(proc.stdout, "Test 0 runner stdout")
        self.assertEqual(
            proc.stdout, (RESULTS / "cwn_stack_agent_test0_snapshot.json").read_bytes(),
            "stdout must match the manifest-frozen snapshot byte for byte",
        )


if __name__ == "__main__":
    unittest.main()
