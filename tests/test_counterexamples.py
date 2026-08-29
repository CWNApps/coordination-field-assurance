import unittest

from cwn_coordination_assurance.fixtures import deployment
from cwn_coordination_assurance.metrics import baseline_ce, evaluate_deployment
from cwn_coordination_assurance.models import Deployment, Surface


class CounterexampleTests(unittest.TestCase):
    def test_same_baseline_different_topology(self):
        # Baseline has no topology input; the new reachability metric does.
        self.assertEqual(baseline_ce(6, 10, 1, 1), baseline_ce(6, 10, 1, 1))
        self.assertNotEqual(
            evaluate_deployment(deployment(6, topology="clique")).temporal_reachability_ratio,
            evaluate_deployment(deployment(6, topology="disconnected")).temporal_reachability_ratio,
        )

    def test_max_rollup_misses_cross_surface_chain(self):
        d = deployment(5, topology="chain")
        r = evaluate_deployment(d)
        self.assertGreater(r.temporal_reachability_ratio, 0)
        self.assertTrue(all(len(s.readers | s.writers) == 2 for s in d.surfaces))

    def test_broadcast_overcount_grows_with_n(self):
        n = 100
        naive_pair_writes = n * (n - 1) / 2 * 10
        emitted_writes = n * 10
        self.assertAlmostEqual(naive_pair_writes / emitted_writes, (n - 1) / 2)

    def test_read_only_surface_zero_edges(self):
        d = deployment()
        s = d.surfaces[0]
        ro = Surface("ro", s.readers, frozenset(), 10, 8)
        d2 = Deployment("ro", d.agents, (ro,), 1, telemetry_coverage=1, calibration_id="c")
        self.assertEqual(evaluate_deployment(d2).structural_directed_pairs, 0)

    def test_alias_count_can_inflate_baseline(self):
        true_principals = 2
        aliases = 10
        self.assertGreater(baseline_ce(aliases, 1, 1, 1), baseline_ce(true_principals, 1, 1, 1))

    def test_persistence_ranking_sensitive_to_unvalidated_multiplier(self):
        low_weight_a = baseline_ce(10, 1, 1, 3)
        ephemeral_b = baseline_ce(20, 1, 1, 1)
        self.assertLess(low_weight_a, ephemeral_b)
        self.assertGreater(baseline_ce(10, 1, 1, 10), ephemeral_b)

    def test_write_count_cannot_measure_entropy(self):
        same_symbol = ["x"] * 100
        diverse = [f"x{i}" for i in range(100)]
        self.assertEqual(len(same_symbol), len(diverse))
        self.assertNotEqual(len(set(same_symbol)), len(set(diverse)))

    def test_permission_is_not_observation(self):
        r = evaluate_deployment(deployment())
        self.assertTrue(any("permission reachability" in w for w in r.warnings))


if __name__ == "__main__": unittest.main()
