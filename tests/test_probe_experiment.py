import unittest

from experiments.probe_experiment import measure_load_factors


class ProbeExperimentTests(unittest.TestCase):
    def test_measurement_covers_requested_load_factors_and_balanced_misses(self):
        rows = measure_load_factors(capacity=100)
        self.assertEqual(len(rows), 16)
        for quarter, row in enumerate(rows, start=1):
            alpha, count, success, success_theory, miss, miss_theory = row
            with self.subTest(alpha=alpha):
                self.assertAlmostEqual(alpha, quarter / 4)
                self.assertEqual(count, round(alpha * 100))
                self.assertGreater(success, 0)
                self.assertAlmostEqual(success_theory, 1 + alpha / 2)
                self.assertAlmostEqual(miss, miss_theory)


if __name__ == "__main__":
    unittest.main()
