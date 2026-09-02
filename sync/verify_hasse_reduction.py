#!/usr/bin/env python3
"""Regression checks for the homogeneous Hasse-edge transitive reduction."""

from __future__ import annotations

import importlib.util
from pathlib import Path


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
    print("Hasse transitive-reduction checks passed.")


if __name__ == "__main__":
    main()
