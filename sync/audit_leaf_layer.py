#!/usr/bin/env python3
"""Report unclassified comparisons among bottom-layer graph parameters.

This is the leaf counterpart of :mod:`audit_root_layer`.  It imports the
graph hook so that equality contraction and rank semantics agree exactly with
the published Hasse-like graph.  Benchmark values are leads for research, not
inferred database facts.
"""

from __future__ import annotations

import argparse
import json
import sys
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
    return [json.loads(path.read_text()) for path in sorted(directory.glob("[0-9]*.json"))]


def parameter_ref(record: dict) -> str:
    return f"#parameters/{record['short_name']}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--all",
        action="store_true",
        help="also report pairs that already have a refuted or open direct statement",
    )
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()

    sys.path.insert(0, str(data_dir))
    import make_graph  # pylint: disable=import-error,import-outside-toplevel

    parameters = records(data_dir / "parameters")
    relationships = records(data_dir / "relationships")
    established_linear = [
        relation
        for relation in relationships
        if relation.get("status", "established") == "established"
        and relation.get("relationship_type") != "incomparable"
    ]
    components, component_of = make_graph.exact_equivalence_components(
        parameters, established_linear
    )
    ranks = make_graph.hierarchy_ranks(
        make_graph.quotient_relationships(established_linear, component_of),
        set(components),
    )
    by_ref = {parameter_ref(parameter): parameter for parameter in parameters}
    leaf_rank = max(ranks.values())
    leaves = sorted(
        {
            component_of[reference]
            for reference in by_ref
            if ranks.get(component_of[reference]) == leaf_rank
        },
        key=lambda component: [by_ref[reference]["name"] for reference in components[component]],
    )
    component_members = {component: set(components[component]) for component in leaves}

    direct_statuses: dict[frozenset[str], set[str]] = {}
    for relation in relationships:
        pair = frozenset((relation["parameter_1_id"], relation["parameter_2_id"]))
        direct_statuses.setdefault(pair, set()).add(relation.get("status", "established"))

    value_ranks = {
        (value["parameter_id"], value["class_id"]): ASYMPTOTIC_RANK[value["value_class"]]
        for value in records(data_dir / "values")
        if value.get("value_class") in ASYMPTOTIC_RANK
    }
    classes = {class_ref for _, class_ref in value_ranks}

    print(f"Leaf-layer components at rank {leaf_rank} ({len(leaves)}):")
    for component in leaves:
        print("  " + " / ".join(by_ref[reference]["name"] for reference in components[component]))

    print("\nLeaf-pair research queue:")
    unresolved = 0
    for first, second in combinations(leaves, 2):
        member_pairs = [
            frozenset((left, right))
            for left in component_members[first]
            for right in component_members[second]
        ]
        statuses = set().union(*(direct_statuses.get(pair, set()) for pair in member_pairs))
        if statuses and not args.all:
            continue
        unresolved += 1
        first_larger: list[str] = []
        second_larger: list[str] = []
        for class_ref in classes:
            first_rank = max(
                (value_ranks.get((reference, class_ref), -99) for reference in component_members[first]),
                default=-99,
            )
            second_rank = max(
                (value_ranks.get((reference, class_ref), -99) for reference in component_members[second]),
                default=-99,
            )
            if first_rank >= second_rank + 2:
                first_larger.append(class_ref.removeprefix("#classes/"))
            elif second_rank >= first_rank + 2:
                second_larger.append(class_ref.removeprefix("#classes/"))
        first_name = "/".join(by_ref[reference]["short_name"] for reference in components[first])
        second_name = "/".join(by_ref[reference]["short_name"] for reference in components[second])
        status_note = f" (existing: {', '.join(sorted(statuses))})" if statuses else ""
        if first_larger and second_larger:
            lead = f"two-sided lead: {first_name}>{first_larger}; {second_name}>{second_larger}"
        elif first_larger or second_larger:
            lead = f"one-sided lead: {first_name}>{first_larger}; {second_name}>{second_larger}"
        else:
            lead = "no paired asymptotic benchmark gap"
        print(f"  {first_name} / {second_name}{status_note}: {lead}")

    print(f"\nPairs in this queue: {unresolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
