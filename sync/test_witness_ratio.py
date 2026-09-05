"""Regression: an unbounded difference need not refute a reverse linear bound."""
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from audit_witness_strength import audit, bounded_ratio_contradiction, elementary_growth_degree


class WitnessRatioTests(unittest.TestCase):
    def test_full_cube_ratio_is_bounded(self):
        self.assertTrue(bounded_ratio_contradiction(
            {"relationship_type": "larger"}, {"value": "$n$"},
            {"value": r"$\lceil n/2\rceil$"}))

    def test_unbounded_ratio_is_not_rejected(self):
        self.assertFalse(bounded_ratio_contradiction(
            {"relationship_type": "larger"}, {"value": "$n-1$"}, {"value": "$2$"}))

    def test_upper_and_refuted_directions(self):
        for relation in ({"relationship_type": "log_upper"},
                         {"relationship_type": "larger", "status": "refuted"}):
            self.assertFalse(bounded_ratio_contradiction(
                relation, {"value": "$2$"}, {"value": "$n$"}))
            self.assertTrue(bounded_ratio_contradiction(
                relation, {"value": "$n$"}, {"value": "$2$"}))

    def test_lower_bounds_and_piecewise_formulas_are_unknown(self):
        for value in (r"$\Omega(n)$", "$n$ for odd n", "$n/0$", None):
            self.assertIsNone(elementary_growth_degree(value))

    def test_prose_does_not_override_a_ratio_contradiction(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "values").mkdir()
            (root / "relationships").mkdir()
            relationship = {"id": 1, "short_name": "test", "status": "established",
                            "parameter_1_id": "a", "parameter_2_id": "b", "witness": "cube",
                            "relationship_type": "larger", "witness_strength": "unbounded",
                            "witness_verification": "The difference grows without bound."}
            (root / "relationships" / "test.json").write_text(json.dumps(relationship))
            for name, value in (("a", "$n$"), ("b", r"$\lceil n/2\rceil$")):
                (root / "values" / f"{name}.json").write_text(json.dumps({
                    "parameter_id": name, "class_id": "cube", "status": "established",
                    "value": value, "value_class": "omega_n"}))
            self.assertFalse(audit(root)["unbounded"][0]["verified"])


if __name__ == "__main__":
    unittest.main()
