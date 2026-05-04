import unittest
from semantic_loss import check_semantic_compression

class SemanticLossTests(unittest.TestCase):
    def test_compression_loss(self):
        histories = [
            {"z": "same", "ctx": "c", "q": "allow", "raw": "allow because verified"},
            {"z": "same", "ctx": "c", "q": "block", "raw": "block because unsafe"},
        ]
        r = check_semantic_compression(histories, lambda h: h["z"], lambda h: h["q"], lambda h: h["ctx"], lambda h: h["raw"])
        self.assertFalse(r.exact)
        self.assertGreater(len(r.semantic_loss_certificates), 0)

if __name__ == "__main__":
    unittest.main()
