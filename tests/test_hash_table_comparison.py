from pathlib import Path
import tempfile
import unittest

from experiments.compare_hash_tables import measure_comparison, write_pdf


class HashTableComparisonTests(unittest.TestCase):
    def test_comparison_uses_same_items_and_reports_theory_for_both_tables(self):
        rows = measure_comparison(capacity=100, query_count=250)
        self.assertEqual(len(rows), 9)
        for step, row in enumerate(rows, start=1):
            alpha = step / 10
            with self.subTest(alpha=alpha):
                self.assertAlmostEqual(row.load_factor, alpha)
                self.assertEqual(row.item_count, round(alpha * 100))
                self.assertGreater(row.chaining_successful, 0)
                self.assertGreater(row.linear_successful, 0)
                self.assertAlmostEqual(row.chaining_successful_theory, 1 + alpha / 2)
                self.assertAlmostEqual(row.chaining_unsuccessful_theory, alpha)
                self.assertAlmostEqual(
                    row.linear_successful_theory,
                    0.5 * (1 + 1 / (1 - alpha)),
                )
                self.assertAlmostEqual(
                    row.linear_unsuccessful_theory,
                    0.5 * (1 + 1 / (1 - alpha) ** 2),
                )

    def test_pdf_report_is_two_pages_and_starts_with_repository_url(self):
        rows = measure_comparison(capacity=100, query_count=50)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.pdf"
            write_pdf(rows, path)
            report = path.read_bytes()

        self.assertTrue(report.startswith(b"%PDF-1.4"))
        self.assertIn(b"/Count 2", report)
        repository_line = b"(Repository: https://github.com/jiwon5042/algori_hw2)"
        self.assertIn(repository_line, report)
        self.assertLess(
            report.index(repository_line),
            report.index(b"(Interpretation and validation notes)"),
        )
        self.assertIn(b"(Agent errors and how they were caught)", report)


if __name__ == "__main__":
    unittest.main()
