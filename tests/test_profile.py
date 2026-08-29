"""Tests for the coordination profile computer.

The load-bearing tests, in order of what they protect:

  test_unrecorded_write_sizes_refuse_the_profile
      The whole reason this module exists. `metrics.evaluate_deployment`
      cannot distinguish "zero bits per write" from "nobody records write
      sizes" -- both arrive as 0.0. Emitting ICB = 0 from an unrecorded input
      certifies a deployment as having no information capacity at all.

  test_refusal_names_the_instrument
      A refusal that does not say what to build is just a failure. The point
      of refusing is to hand the operator the next task.

  test_a_metric_is_never_computed_from_an_unusable_input
      Each metric declares its inputs. If any is NOT_RECORDED or DEGRADED the
      metric must be absent, not defaulted.
"""
from __future__ import annotations

import unittest

from cwn_coordination_assurance.profile import (
    METRIC_INPUTS,
    PROFILE_REQUIRED_METRICS,
    compute_profile,
    to_deployment,
)

ALL_MEASURED = {
    name: {"status": "MEASURED"}
    for name in ("agent_windows", "reader_writer_sets", "write_rates",
                 "write_sizes", "read_visibility", "surface_persistence",
                 "telemetry_coverage")
}


def snapshot(**over):
    base = {
        "schema_version": "1.0.0",
        "deployment_id": "d1",
        "tenant_id": "t1",
        "window_id": "w1",
        "policy_epoch": "e1",
        "observed_at": "2026-08-28T00:00:00Z",
        "window_hours": 10.0,
        "agents": [
            {"agent_id": "a", "principal_id": "p1", "start_ms": 0, "end_ms": 36_000_000},
            {"agent_id": "b", "principal_id": "p2", "start_ms": 0, "end_ms": 36_000_000},
        ],
        "surfaces": [{
            "surface_id": "s1", "surface_class": "cache", "shared": True,
            "readers": ["b"], "writers": ["a"],
            "writes_per_writer_hour": 2.0, "bits_per_write_upper_bound": 8.0,
            "read_visibility": 1.0, "persistence_hours": 10.0,
            "persistence_class": "durable", "persistence_measured": True,
            "tenants": ["t1"],
        }],
        "inputs": dict(ALL_MEASURED),
        "telemetry_coverage": 1.0,
        "calibration_id": None,
        "warnings": [],
        "evidence_root": "0" * 64,
    }
    base.update(over)
    return base


class ProfileTests(unittest.TestCase):

    # ---------------------------------------------------------- the refusal

    def test_unrecorded_write_sizes_refuse_the_profile(self):
        inputs = dict(ALL_MEASURED)
        inputs["write_sizes"] = {
            "status": "NOT_RECORDED",
            "detail": "no size field on any event",
            "instrument_needed": "record payload size on every surface write",
        }
        result = compute_profile(snapshot(inputs=inputs))
        self.assertFalse(result.emitted, "ICB inputs unrecorded must refuse, not emit 0")
        self.assertIsNone(result.profile)
        self.assertIn("icb_bits_upper_bound", result.refusal["unmet_metrics"])

    def test_refusal_names_the_instrument(self):
        inputs = dict(ALL_MEASURED)
        inputs["write_sizes"] = {
            "status": "NOT_RECORDED",
            "instrument_needed": "record payload size on every surface write",
        }
        result = compute_profile(snapshot(inputs=inputs))
        needed = result.refusal["instruments_needed"]
        self.assertIn("write_sizes", needed)
        self.assertEqual(needed["write_sizes"]["instrument_needed"],
                         "record payload size on every surface write")

    def test_refusal_still_reports_what_was_measurable(self):
        """A refusal is not a blank. SDE and TCR survive an ICB failure."""
        inputs = dict(ALL_MEASURED)
        inputs["write_sizes"] = {"status": "NOT_RECORDED"}
        result = compute_profile(snapshot(inputs=inputs))
        self.assertIn("sde", result.partials)
        self.assertIn("tcr", result.partials)
        self.assertEqual(result.refusal["computed_anyway"]["sde"], result.partials["sde"])

    def test_every_required_metric_can_block_the_profile(self):
        """Each required metric must be individually capable of refusing."""
        for metric in PROFILE_REQUIRED_METRICS:
            blocking = METRIC_INPUTS[metric][0]
            inputs = dict(ALL_MEASURED)
            inputs[blocking] = {"status": "NOT_RECORDED"}
            result = compute_profile(snapshot(inputs=inputs))
            self.assertFalse(result.emitted, f"{metric} via {blocking} should have refused")

    # ---------------------------------------------------------- no silent defaults

    def test_a_metric_is_never_computed_from_an_unusable_input(self):
        for status in ("NOT_RECORDED", "DEGRADED"):
            inputs = dict(ALL_MEASURED)
            inputs["read_visibility"] = {"status": status}
            result = compute_profile(snapshot(inputs=inputs))
            self.assertNotIn("ccp", result.partials,
                             f"CCP depends on read_visibility; {status} must block it")
            self.assertNotIn("icb_bits_upper_bound", result.partials)

    def test_missing_inputs_block_rather_than_default(self):
        result = compute_profile(snapshot(inputs={}))
        self.assertFalse(result.emitted)
        self.assertEqual(result.partials, {}, "no inputs means no metrics, not zeros")

    def test_upper_bounded_is_usable_but_measured_is_not_required(self):
        """An honest bound that cannot understate exposure is allowed through."""
        inputs = dict(ALL_MEASURED)
        inputs["surface_persistence"] = {
            "status": "UPPER_BOUNDED",
            "detail": "bounded to window length; maximises reachability",
        }
        result = compute_profile(snapshot(inputs=inputs))
        self.assertTrue(result.emitted)
        self.assertIn("tcr", result.profile)

    # ---------------------------------------------------------- emitted profile

    def test_conforming_profile_has_every_required_field(self):
        result = compute_profile(snapshot())
        self.assertTrue(result.emitted)
        for key in ("schema_version", "metric_version", "tenant_id", "deployment_id",
                    "window_id", "policy_epoch", "sde", "tcr", "icb_bits_upper_bound",
                    "prv", "coverage", "state", "evidence_root"):
            self.assertIn(key, result.profile)
        self.assertEqual(len(result.profile["evidence_root"]), 64)

    def test_state_cannot_exceed_research_only(self):
        """This implementation must never certify production."""
        result = compute_profile(snapshot(telemetry_coverage=1.0, calibration_id="cal-1"))
        self.assertEqual(result.profile["state"], "RESEARCH_ONLY")

    def test_state_is_unknown_without_calibration(self):
        result = compute_profile(snapshot(telemetry_coverage=1.0, calibration_id=None))
        self.assertEqual(result.profile["state"], "UNKNOWN")

    def test_state_is_unknown_below_full_coverage(self):
        result = compute_profile(snapshot(telemetry_coverage=0.5, calibration_id="cal-1"))
        self.assertEqual(result.profile["state"], "UNKNOWN")

    def test_evidence_root_changes_with_content(self):
        a = compute_profile(snapshot()).profile["evidence_root"]
        b = compute_profile(snapshot(window_id="w2")).profile["evidence_root"]
        self.assertNotEqual(a, b)

    # ---------------------------------------------------------- identity ambiguity

    def test_multi_principal_agent_is_warned_not_silently_collapsed(self):
        """The model carries one principal per agent. More than one cannot be represented."""
        snap = snapshot()
        snap["agents"][0]["principal_count"] = 5
        result = compute_profile(snap)
        self.assertTrue(any("5 distinct principals" in w for w in result.warnings),
                        f"identity ambiguity must be surfaced. warnings={result.warnings}")

    # ---------------------------------------------------------- the metric itself

    def test_sde_counts_directed_pairs(self):
        result = compute_profile(snapshot())
        self.assertEqual(result.profile["sde"], 1, "one writer, one reader, one direction")

    def test_tcr_is_a_ratio_in_range(self):
        result = compute_profile(snapshot())
        self.assertGreaterEqual(result.profile["tcr"], 0.0)
        self.assertLessEqual(result.profile["tcr"], 1.0)

    def test_prv_is_evidence_not_a_coefficient(self):
        prv = compute_profile(snapshot()).profile["prv"]
        self.assertIsInstance(prv, dict)
        self.assertIn("persistence_measured", prv)
        self.assertNotIsInstance(prv, (int, float))

    def test_to_deployment_preserves_reader_and_writer_sets(self):
        d = to_deployment(snapshot())
        self.assertEqual(d.surfaces[0].writers, frozenset({"a"}))
        self.assertEqual(d.surfaces[0].readers, frozenset({"b"}))
        self.assertEqual({a.agent_id for a in d.agents}, {"a", "b"})


if __name__ == "__main__":
    unittest.main()
