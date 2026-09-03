#!/usr/bin/env python3
"""Report unresolved comparisons among the first non-source graph layer.

The Hasse audit prioritizes reduced dominance edges.  This companion report
instead supports the catalogue-completion campaign: it identifies parameters
that have rank one after the established affine-dominance closure, then lists
their pairs which have no direct stated relationship.  Existing asymptotic
benchmark values are used only as leads; the script never proposes a database
fact from transitivity or numerical coincidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


ASYMPTOTIC_RANK = {
    "omega_1": 0,
    "constant": 0,
    "omega_log_n": 1,
    "omega_n": 2,
    "omega_n_log_n": 3,
    "omega_n_squared": 4,
}


def records(directory: Path) -> list[dict]:
    return [
        json.loads(path.read_text())
        for path in sorted(directory.glob("[0-9]*.json"))
    ]


def parameter_ref(record: dict) -> str:
    return f"#parameters/{record['short_name']}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()

    # The graph hook owns the precise rank semantics, including equality
    # contraction and affine relationships.  Import it from the data source
    # rather than duplicating those choices here.
    sys.path.insert(0, str(data_dir))
    import make_graph  # pylint: disable=import-error,import-outside-toplevel

    parameters = records(data_dir / "parameters")
    relationships = records(data_dir / "relationships")
    established_linear = [
        relationship
        for relationship in relationships
        if relationship.get("status", "established") == "established"
        and relationship.get("relationship_type") != "incomparable"
    ]
    components, component_of = make_graph.exact_equivalence_components(
        parameters, established_linear
    )
    ranks = make_graph.hierarchy_ranks(
        make_graph.quotient_relationships(established_linear, component_of),
        set(components),
    )
    parameters_by_ref = {parameter_ref(parameter): parameter for parameter in parameters}
    roots = sorted(
        (
            reference
            for reference in parameters_by_ref
            if ranks.get(component_of[reference]) == 1
        ),
        key=lambda reference: parameters_by_ref[reference]["name"],
    )

    established_pairs = {
        frozenset((relationship["parameter_1_id"], relationship["parameter_2_id"]))
        for relationship in relationships
        if relationship.get("status", "established") == "established"
    }
    value_ranks: dict[tuple[str, str], int] = {}
    for value in records(data_dir / "values"):
        value_class = value.get("value_class")
        if value_class in ASYMPTOTIC_RANK:
            value_ranks[(value["parameter_id"], value["class_id"])] = ASYMPTOTIC_RANK[value_class]

    print(f"Root-layer parameters ({len(roots)}):")
    for reference in roots:
        print(f"  {parameters_by_ref[reference]['name']}")
    print("\nUnresolved root-layer pairs:")
    unresolved = 0
    for first, second in combinations(roots, 2):
        if frozenset((first, second)) in established_pairs:
            continue
        unresolved += 1
        first_larger = []
        second_larger = []
        classes = {class_ref for _, class_ref in value_ranks}
        for class_ref in classes:
            first_rank = value_ranks.get((first, class_ref))
            second_rank = value_ranks.get((second, class_ref))
            if first_rank is None or second_rank is None:
                continue
            if first_rank >= second_rank + 2:
                first_larger.append(class_ref.removeprefix("#classes/"))
            elif second_rank >= first_rank + 2:
                second_larger.append(class_ref.removeprefix("#classes/"))
        first_name = parameters_by_ref[first]["short_name"]
        second_name = parameters_by_ref[second]["short_name"]
        if first_larger and second_larger:
            lead = f"two-sided benchmark lead: {first_name}>{first_larger}; {second_name}>{second_larger}"
        elif first_larger or second_larger:
            lead = f"one-sided benchmark lead: {first_name}>{first_larger}; {second_name}>{second_larger}"
        else:
            lead = "no paired asymptotic benchmark gap"
        print(f"  {first_name} / {second_name}: {lead}")
    print(f"\nUnresolved pairs: {unresolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
