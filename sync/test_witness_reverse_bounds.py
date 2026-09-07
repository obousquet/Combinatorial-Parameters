"""Reverse exact domination forbids even a finite strict endpoint witness."""

import unittest
from pathlib import Path
from unittest.mock import patch

from audit_hasse_edges import load_graph_module
from audit_relationship_witnesses import audit, reverse_adjacencies, reverse_bound_path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = load_graph_module(ROOT)


def relation(identifier: int, first: str, second: str, kind: str = "larger", **extra) -> dict:
    return dict(id=identifier, short_name=f"relation_{identifier}", status="established",
                parameter_1_id=f"#parameters/{first}", parameter_2_id=f"#parameters/{second}",
                relationship_type=kind) | extra


class ReverseBoundTests(unittest.TestCase):
    def paths(self, target, records):
        affine, exact = reverse_adjacencies(records, GRAPH)
        return reverse_bound_path(target, affine), reverse_bound_path(target, exact)

    def test_exact_path_and_bidirectional_equality(self):
        records = [relation(1, "b", "c"), relation(2, "a", "c", "equivalence")]
        self.assertEqual(self.paths(relation(3, "a", "b"), records), ([1, 2], [1, 2]))

    def test_affine_factor_and_offset_signs(self):
        target = relation(1, "a", "b")
        for c, d, is_exact in (("1/2", "0", False), ("2", "1", False),
                               ("2", "-1", True), ("1", "0", True),
                               (r"\frac{3}{2}", r"-\frac{1}{2}", True),
                               ("c", "0", False), ("1", "d", False)):
            with self.subTest(c=c, d=d):
                back = relation(2, "b", "a", "larger_c",
                                multiplicative_constant=c, additive_constant=d)
                self.assertEqual(self.paths(target, [back]),
                                 ([2], [2] if is_exact else None))

    def test_nonpositive_factors_and_nonestablished_edges_are_excluded(self):
        for extra in ({"multiplicative_constant": "0"}, {"multiplicative_constant": "-1/2"},
                      {"multiplicative_constant": "2", "status": "refuted"},
                      {"multiplicative_constant": "2", "status": "needs_verification"}):
            back = relation(2, "b", "a", "larger_c", **extra)
            self.assertEqual(self.paths(relation(1, "a", "b"), [back]), (None, None))

    def test_variants_do_not_mix(self):
        target = relation(1, "a", "b", variant="projected")
        self.assertEqual(self.paths(target, [relation(2, "b", "a")]), (None, None))
        self.assertEqual(self.paths(target, [relation(2, "b", "a", variant="projected")]),
                         ([2], [2]))

    def test_upper_bound_endpoint_direction(self):
        for kind in ("log_upper", "sqrt_upper"):
            # A <= f(B) seeks B>A; its reverse exact obstruction is A>=B.
            target = relation(1, "a", "b", kind)
            self.assertEqual(self.paths(target, [relation(2, "a", "b")]), ([2], [2]))
        self.assertEqual(self.paths(relation(1, "a", "b"),
                                    [relation(2, "b", "a", "log")]), (None, None))

    def test_compensating_factors_are_deliberately_not_certified_exact(self):
        records = [relation(1, "b", "c", "larger_c", multiplicative_constant="1/2"),
                   relation(2, "c", "a", "larger_c", multiplicative_constant="2")]
        self.assertEqual(self.paths(relation(3, "a", "b"), records), ([1, 2], None))

    def test_declared_conflicts_are_reported(self):
        params = [dict(id=i, short_name=name) for i, name in enumerate(("a", "b"), 1)]
        for strength, field in (("strict", "strict_reverse_conflicts"),
                                ("unbounded", "unbounded_reverse_conflicts")):
            relations = [relation(1, "a", "b", witness="test", witness_strength=strength),
                         relation(2, "b", "a")]
            with patch("audit_relationship_witnesses.records",
                       side_effect=lambda p: {"parameters": params, "relationships": relations,
                                              "values": []}[p.name]):
                report = audit(ROOT / "data")
            self.assertEqual([r["id"] for r in report[field]], [1])

    def test_catalogue_radius_direction_and_no_new_conflicts(self):
        report = audit(ROOT / "data")
        rows = {r["id"]: r for r in report["rows"]}
        self.assertEqual(rows[124]["reverse_exact_path"], [146])
        self.assertEqual(rows[124]["witness_search_if_scopes_match"], "neither_strict_nor_unbounded")
        self.assertIsNone(rows[146]["reverse_exact_path"])
        self.assertEqual(rows[146]["witness_search_if_scopes_match"], "strict_only")
        self.assertEqual(report["strict_reverse_conflicts"], [])
        self.assertEqual(report["unbounded_reverse_conflicts"], [])


if __name__ == "__main__":
    unittest.main()
