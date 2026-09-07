#!/usr/bin/env python3
"""Regression checks for homogeneous and exact-affine Hasse-edge pruning."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from fractions import Fraction
import json


def relationship(identifier: int, source: str, target: str, kind: str = "larger") -> dict[str, object]:
    return {
        "id": identifier,
        "parameter_1_id": source,
        "parameter_2_id": target,
        "relationship_type": kind,
        "status": "established",
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("make_graph", root / "data" / "make_graph.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load data/make_graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    first, second, third = "#parameters/A", "#parameters/B", "#parameters/C"
    chain = [
        relationship(1, first, second),
        relationship(2, second, third),
        relationship(3, first, third),
    ]
    reduced = module.reduced_linear_relations(chain)
    assert {entry["id"] for entry in reduced} == {1, 2}

    # A constant-factor conclusion may use a constant-factor intermediate;
    # plain dominance alone must not erase it.
    affine_chain = [
        relationship(4, first, second, "larger_c"),
        relationship(5, second, third, "larger_c"),
        relationship(6, first, third, "larger_c"),
    ]
    reduced_affine = module.reduced_linear_relations(affine_chain)
    assert {entry["id"] for entry in reduced_affine} == {4, 5}

    # Exact dominance composes into a constant-factor conclusion (with
    # constant one), so it also removes that redundant conclusion.
    mixed = [
        relationship(7, first, second),
        relationship(8, second, third),
        relationship(9, first, third, "larger_c"),
    ]
    reduced_mixed = module.reduced_linear_relations(mixed)
    assert {entry["id"] for entry in reduced_mixed} == {7, 8}

    # A universal stated equivalence that has been explicitly admitted to the
    # graph policy must quotient the two parameter nodes before ranks and
    # transitive reduction are computed.
    selfdirected_dimension = "#parameters/selfdirected_dimension"
    selfdirected_complexity = "#parameters/selfdirected_queries_complexity"
    components, component_of = module.exact_equivalence_components(
        [
            {"short_name": "selfdirected_dimension"},
            {"short_name": "selfdirected_queries_complexity"},
        ],
        [relationship(318, selfdirected_dimension, selfdirected_complexity, "equivalence")],
    )
    assert component_of[selfdirected_dimension] == component_of[selfdirected_complexity]
    assert len(components) == 1

    # The proved positive projection closures form one node. Every external
    # relationship of every member survives the quotient automatically.
    positive = ["projected_positive_recursive_teaching_dimension",
                "projected_positive_noclashing_teaching_dimension",
                "projected_maximum_positive_degree"]
    refs = [f"#parameters/{name}" for name in positive]
    external = ["upper", "lower_a", "lower_b"]
    identities = [relationship(457, refs[0], refs[1], "equivalence"),
                  relationship(461, refs[1], refs[2], "equivalence")]
    incident = [relationship(9001, "#parameters/upper", refs[0]),
                relationship(9002, refs[1], "#parameters/lower_a"),
                relationship(9003, refs[2], "#parameters/lower_b")]
    _, component_of = module.exact_equivalence_components(
        [{"short_name": name} for name in positive + external], identities + incident)
    assert len({component_of[ref] for ref in refs}) == 1
    quotient = module.quotient_relationships(identities + incident, component_of)
    assert {row["id"] for row in quotient} == {9001, 9002, 9003}
    merged = component_of[refs[0]]
    assert {(row["parameter_1_id"], row["parameter_2_id"]) for row in quotient} == {
        ("#parameters/upper", merged), (merged, "#parameters/lower_a"),
        (merged, "#parameters/lower_b")}

    # Once different direct facts collapse to the same displayed endpoint
    # pair, only one witness card may remain.  An unbounded family separation
    # takes precedence over a strict finite example; otherwise the larger
    # literal gap wins.
    exact_values = {
        ("#classes/C", first): 7,
        ("#classes/C", second): 2,
        ("#classes/D", first): 3,
        ("#classes/D", second): 1,
    }
    strict_large = relationship(10, first, second)
    strict_large.update({"witness": "#classes/C", "witness_strength": "strict"})
    unbounded = relationship(11, first, second, "larger_c")
    unbounded.update({"witness": "#classes/D", "witness_strength": "unbounded"})
    chosen = module.strongest_displayed_relationships(
        [(strict_large, "base", True), (unbounded, "nonlinear", False)], exact_values
    )
    assert len(chosen) == 1
    assert chosen[0][0]["id"] == 11
    assert chosen[0][1] == "nonlinear"
    assert chosen[0][2] is True
    def affine(identifier, source, target, a, b="0", strength=None):
        edge = relationship(identifier, source, target, "larger_c")
        edge.update(multiplicative_constant=a, additive_constant=b)
        if strength:
            edge.update(witness="#classes/C", witness_strength=strength)
        return edge

    # Exact example: E >= 2 pNCTD - 1 >= 2 NCTD - 1, including evidence.
    target = affine(449, first, third, "2", "1", "unbounded")
    upper = affine(450, first, second, "2", "1", "unbounded")
    lower = relationship(439, second, third)
    path = module.exact_affine_alternate_path(target, [target, upper, lower])
    assert [edge["id"] for edge in path] == [450, 439]
    # Mere domination does not prove the coefficient-two inequality.
    weak_upper = relationship(450, first, second)
    weak_upper.update(witness="#classes/C", witness_strength="unbounded")
    assert module.exact_affine_alternate_path(target, [target, weak_upper, lower]) is None
    # Composition is (a*c, b+a*d), including negative additive constants.
    numeric = affine(20, first, third, "6", "7")
    chain = [affine(21, first, second, "2", "1"), affine(22, second, third, "3", "3")]
    assert module.exact_affine_alternate_path(numeric, chain)
    assert module.exact_affine_alternate_path({**numeric, "additive_constant": "6"}, chain) is None
    assert module.affine_coefficients(affine(23, first, second, r"\tfrac12", r"-\frac{3}{2}")) == (Fraction(1, 2), Fraction(-3, 2))
    assert module.affine_coefficients(affine(23, first, second, r"\frac{2}{k}")) is None
    for a in ("0", "-1", "nan", "1/0"):
        assert module.affine_coefficients(affine(23, first, second, a)) is None
    # A witnessless/strict path cannot discard an unbounded witness.
    assert module.exact_affine_alternate_path(target, [{**upper, "witness_strength": "strict"}, lower]) is None
    assert module.exact_affine_alternate_path(target, [{**upper, "variant": "k=2"}, lower]) is None
    assert module.exact_affine_alternate_path(target, [{**upper, "status": "refuted"}, lower]) is None
    assert module.exact_affine_alternate_path(target, [upper, lower], max_states=0) is None
    # Finite strict evidence cannot be transported through a scaled edge.
    strict_target = affine(24, first, third, "1/2", "0", "strict")
    scaled = affine(25, first, second, "1/2", "0", "strict")
    assert module.exact_affine_alternate_path(strict_target, [scaled, lower]) is None
    # Sequential removal preserves proof paths, even in a cyclic block.
    cycle = [affine(30, first, second, "1", "1"),
             affine(31, first, third, "1", "1"),
             relationship(32, second, third), relationship(33, third, second)]
    kept, certificates = module.prune_exact_affine_edges([(e, "base", False) for e in cycle])
    retained_ids = {entry[0]["id"] for entry in kept}
    assert not {30, 31} <= certificates.keys()
    assert all(set(path) <= retained_ids for path in certificates.values())
    # Replay the real catalogue after equality collapse and display selection.
    def records(table):
        return [json.loads(p.read_text()) for p in (root / "data" / table).glob("*.json") if p.name != "schema.json"]
    real = [e for e in records("relationships") if e.get("status") == "established"]
    _, components = module.exact_equivalence_components(records("parameters"), real)
    quotient = module.quotient_relationships(real, components)
    kept, certificates = module.select_displayed_relationships(quotient, {})
    retained_ids = {entry[0]["id"] for entry in kept}
    assert 449 not in retained_ids and 449 in certificates
    assert 450 in retained_ids
    assert all(set(path) <= retained_ids for path in certificates.values())
    # Independently replay every returned path on the final quotient graph.
    by_id = {e["id"]: e for e in quotient}
    for identifier, path in certificates.items():
        direct = by_id[identifier]
        node = direct["parameter_1_id"]
        a, b = Fraction(1), Fraction(0)
        strength, domination = 0, True
        for step in path:
            edge = by_id[step]
            assert module.variant_of(edge) == module.variant_of(direct)
            if node == edge["parameter_1_id"]:
                node = edge["parameter_2_id"]
            else:
                assert edge["relationship_type"] == "equivalence" and node == edge["parameter_2_id"]
                node = edge["parameter_1_id"]
            c, d = module.affine_coefficients(edge)
            b += a*d
            a *= c
            domination &= c >= 1 and d <= 0
            strength = max(strength, module.witness_strength_level(edge) if edge.get("witness") else 0)
        assert node == direct["parameter_2_id"]
        c, d = module.affine_coefficients(direct)
        assert a >= c and b <= d
        assert (strength if strength == 2 or domination else 0) >= module.witness_strength_level(direct)
    print(f"Hasse/affine transitive-reduction checks passed; #449 replaced by {certificates[449]}.")


if __name__ == "__main__":
    main()
