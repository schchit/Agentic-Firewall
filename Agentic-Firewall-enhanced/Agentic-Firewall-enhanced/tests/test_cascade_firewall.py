import unittest
from cascade import matrix_from_edges, analyze_cascade
from firewall import evaluate_firewall

class CascadeFirewallTests(unittest.TestCase):
    def test_stable_graph(self):
        agents = ["a", "b"]
        m = matrix_from_edges(agents, [("a", "b", 0.2)])
        r = analyze_cascade(m)
        self.assertIn(r.regime, {"convergent", "critical"})

    def test_firewall_requires_verifier_on_conflict(self):
        d = evaluate_firewall(["a", "b"], [("a", "b", 0.2)], residual_conflict_count=1)
        self.assertEqual(d.action, "REQUIRE_VERIFIER")

if __name__ == "__main__":
    unittest.main()
