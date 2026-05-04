import unittest
from determinability import check_determinability

class DeterminabilityTests(unittest.TestCase):
    def test_detects_conflict(self):
        configs = [{"o": 1, "d": "A"}, {"o": 1, "d": "B"}]
        r = check_determinability(configs, lambda c: c["o"], lambda c: c["d"])
        self.assertFalse(r.determinable)
        self.assertEqual(r.residual_conflict_count, 1)
        self.assertEqual(len(r.conflicts), 1)

    def test_decision_table_when_determinable(self):
        configs = [{"o": 1, "d": "A"}, {"o": 2, "d": "B"}]
        r = check_determinability(configs, lambda c: c["o"], lambda c: c["d"])
        self.assertTrue(r.determinable)
        self.assertEqual(r.residual_conflict_count, 0)

if __name__ == "__main__":
    unittest.main()
