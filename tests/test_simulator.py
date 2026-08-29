import unittest

from cwn_coordination_assurance.fixtures import deployment
from cwn_coordination_assurance.metrics import weighted_adjacency
from cwn_coordination_assurance.optimizer import best_single_intervention, candidate_interventions
from cwn_coordination_assurance.simulator import alert_precision, simulate_diffusion


class SimulationTests(unittest.TestCase):
    def test_deterministic(self):
        _, m = weighted_adjacency(deployment(n=8))
        self.assertEqual(simulate_diffusion(m, .5, .1, 10, 7), simulate_diffusion(m, .5, .1, 10, 7))
    def test_zero_beta_no_spread(self):
        _, m = weighted_adjacency(deployment(n=8))
        self.assertLessEqual(max(simulate_diffusion(m, 0, 0, 10, 7)), 1)
    def test_full_recovery_can_extinguish(self):
        _, m = weighted_adjacency(deployment(n=8))
        self.assertEqual(simulate_diffusion(m, 0, 1, 1, 7)[-1], 0)
    def test_bad_beta(self):
        with self.assertRaises(ValueError): simulate_diffusion([[0]], 2, 0, 1, 1)
    def test_bad_recovery(self):
        with self.assertRaises(ValueError): simulate_diffusion([[0]], 0, -1, 1, 1)
    def test_precision_base_rate(self): self.assertLess(alert_precision(.001, 1, .05), .03)
    def test_precision_perfect_specificity(self): self.assertEqual(alert_precision(.001, .8, 0), 1)
    def test_precision_no_alerts(self): self.assertEqual(alert_precision(0, 0, 0), 0)
    def test_bad_precision_probability(self):
        with self.assertRaises(ValueError): alert_precision(1.1, 1, 0)
    def test_intervention_count(self): self.assertEqual(len(candidate_interventions(deployment())), 3)
    def test_optimizer_never_worsens(self):
        r = best_single_intervention(deployment())
        self.assertLessEqual(r["after"], r["before"])
    def test_optimizer_deterministic(self): self.assertEqual(best_single_intervention(deployment()), best_single_intervention(deployment()))


if __name__ == "__main__": unittest.main()

