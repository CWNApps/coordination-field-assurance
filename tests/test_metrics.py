import math
import unittest

from cwn_coordination_assurance.fixtures import deployment
from cwn_coordination_assurance.metrics import (
    baseline_ce,
    evaluate_deployment,
    information_capacity_upper_bound,
    spectral_radius,
)
from cwn_coordination_assurance.models import AgentWindow, Deployment, Surface


class BaselineTests(unittest.TestCase):
    def test_pair_formula(self): self.assertEqual(baseline_ce(50, 600, 96, 10), 705_600_000)
    def test_single_agent_zero(self): self.assertEqual(baseline_ce(1, 10, 10, 10), 0)
    def test_zero_bandwidth(self): self.assertEqual(baseline_ce(10, 0, 10, 10), 0)
    def test_zero_duration(self): self.assertEqual(baseline_ce(10, 10, 0, 10), 0)
    def test_negative_n_rejected(self):
        with self.assertRaises(ValueError): baseline_ce(-1, 1, 1, 1)
    def test_negative_b_rejected(self):
        with self.assertRaises(ValueError): baseline_ce(1, -1, 1, 1)
    def test_negative_d_rejected(self):
        with self.assertRaises(ValueError): baseline_ce(1, 1, -1, 1)
    def test_negative_p_rejected(self):
        with self.assertRaises(ValueError): baseline_ce(1, 1, 1, -1)


class MetricTests(unittest.TestCase):
    def test_clique_reachability(self): self.assertEqual(evaluate_deployment(deployment()).temporal_reachability_ratio, 1.0)
    def test_chain_transitive_reachability(self): self.assertEqual(evaluate_deployment(deployment(topology="chain")).temporal_reachability_ratio, 0.5)
    def test_disconnected_lower_reachability(self): self.assertLess(evaluate_deployment(deployment(topology="disconnected")).temporal_reachability_ratio, 1)
    def test_capacity_not_pair_multiplied(self):
        d = deployment(n=10)
        self.assertEqual(information_capacity_upper_bound(d), 10 * 10 * 1 * 8)
    def test_visibility_scales_capacity(self):
        d = deployment(n=4)
        s = d.surfaces[0]
        s2 = Surface(s.surface_id, s.readers, s.writers, s.writes_per_writer_hour, s.bits_per_write_upper_bound, .1)
        d2 = Deployment(d.deployment_id, d.agents, (s2,), d.window_hours, telemetry_coverage=1, calibration_id="c")
        self.assertAlmostEqual(information_capacity_upper_bound(d2), information_capacity_upper_bound(d) * .1)
    def test_unknown_without_calibration(self): self.assertEqual(evaluate_deployment(deployment(calibrated=False)).risk_state, "UNKNOWN")
    def test_unknown_on_low_coverage(self): self.assertEqual(evaluate_deployment(deployment(coverage=.9)).risk_state, "UNKNOWN")
    def test_research_only_when_bound(self): self.assertEqual(evaluate_deployment(deployment()).risk_state, "RESEARCH_ONLY")
    def test_empty_spectral_radius(self): self.assertEqual(spectral_radius([]), 0)
    def test_zero_spectral_radius(self): self.assertEqual(spectral_radius([[0, 0], [0, 0]]), 0)
    def test_known_spectral_radius(self): self.assertAlmostEqual(spectral_radius([[0, 1], [1, 0]]), 1.0, places=6)
    def test_validation_visibility(self):
        with self.assertRaises(ValueError): Surface("x", frozenset(), frozenset(), 1, 1, 1.1)
    def test_validation_agent_window(self):
        with self.assertRaises(ValueError): AgentWindow("a", "p", 2, 1)
    def test_validation_duplicate_agents(self):
        a = AgentWindow("a", "p", 0, 1)
        with self.assertRaises(ValueError): Deployment("d", (a, a), (), 1)
    def test_warnings_include_probability_guard(self):
        self.assertTrue(any("not incident probabilities" in x for x in evaluate_deployment(deployment()).warnings))
    def test_staggered_ephemeral_blocks_paths(self):
        self.assertEqual(evaluate_deployment(deployment(stagger=True, persistence=0)).temporal_reachability_ratio, 0)
    def test_staggered_durable_bridges_time(self):
        self.assertGreater(evaluate_deployment(deployment(stagger=True, persistence=10)).temporal_reachability_ratio, 0)


if __name__ == "__main__": unittest.main()

