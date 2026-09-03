#!/usr/bin/env python3
"""Audit witness coverage and structural importance of Hasse-graph edges.

The graph intentionally reduces only homogeneous compatible linear facts.
This script uses the same quotient and reduction helpers as ``make_graph``;
it never treats a transitive consequence as a new database relationship.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


Record = dict[str, Any]
BOUNDARY_PARAMETERS = {"#parameters/effective_range", "#parameters/size"}
GROWTH_RANK = {
    "omega_1": 0,
    "omega_log_n": 1,
    "omega_n": 2,
    "omega_n_log_n": 3,
    "omega_n_squared": 4,
    "omega_2^n": 5,
    "$\\Omega(2^n)$": 5,
}


def load_records(directory: Path) -> list[Record]:
    return [
        json.loads(path.read_text())
        for path in sorted(directory.glob("*.json"))
        if path.name != "schema.json"
    ]


def load_graph_module(root: Path) -> Any:
    spec = importlib.util.spec_from_file_location("make_graph", root / "data" / "make_graph.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load data/make_graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def literal_integer(value: str | None) -> int | None:
    """Return an unambiguous nonnegative displayed integer, if there is one."""
    if not value:
        return None
    stripped = value.strip()
    if stripped.startswith("$") and stripped.endswith("$"):
        stripped = stripped[1:-1].strip()
    if re.fullmatch(r"\d+", stripped):
        return int(stripped)
    return None


def reachability(adjacency: dict[str, set[str]], source: str) -> set[str]:
    seen: set[str] = set()
    pending = list(adjacency[source])
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        pending.extend(adjacency[node] - seen)
    return seen


def closure(adjacency: dict[str, set[str]], vertices: set[str]) -> set[tuple[str, str]]:
    return {
        (source, target)
        for source in vertices
        for target in reachability(adjacency, source)
    }


def strict_value_candidates(
    relationship: Record,
    values: list[Record],
    component_of: dict[str, str],
) -> list[dict[str, Any]]:
    """Find exact integer values that strictly refute the reverse inequality.

    These are research leads, not automatically attached witnesses: the class
    must still be checked against the stated relationship's scope and the two
    value proofs before it is promoted into the catalogue.
    """
    first, second = (
        relationship["parameter_1_id"],
        relationship["parameter_2_id"],
    )
    by_class: dict[str, dict[str, int]] = defaultdict(dict)
    for value in values:
        if value.get("status") != "established":
            continue
        integer = literal_integer(value.get("value"))
        if integer is None:
            continue
        component = component_of.get(value["parameter_id"], value["parameter_id"])
        by_class[value["class_id"]][component] = integer
    candidates = []
    for class_id, observed in by_class.items():
        left = observed.get(first)
        right = observed.get(second)
        if left is not None and right is not None and left > right:
            candidates.append({"class": class_id, "left": left, "right": right})
    return sorted(candidates, key=lambda item: (item["right"] - item["left"], item["class"]))


def localize_bypass_witness(
    relationship: Record,
    path: list[Record],
    values: list[Record],
    component_of: dict[str, str],
) -> dict[str, Any]:
    """Try to place a bypass witness on an edge of its witnessless proof path.

    If ``A >= B >= C`` is the reason a direct witnessed ``A >= C`` edge was
    reduced away, its witness must separate at least one path edge. Exact
    values can identify that edge mechanically; missing or symbolic cells are
    deliberately reported as an unresolved research task rather than guessed.
    """
    witness = relationship["witness"]
    observed: dict[str, int] = {}
    growth: dict[str, tuple[int, str]] = {}
    for value in values:
        if value.get("status") != "established" or value.get("class_id") != witness:
            continue
        integer = literal_integer(value.get("value"))
        if integer is not None:
            observed[component_of.get(value["parameter_id"], value["parameter_id"])] = integer
        rank = GROWTH_RANK.get(value.get("value_class"))
        if rank is not None:
            component = component_of.get(value["parameter_id"], value["parameter_id"])
            previous = growth.get(component)
            if previous is None or rank > previous[0]:
                growth[component] = (rank, value["value_class"])

    localized = []
    unknown = []
    for edge in path:
        source, target = graph_endpoints(edge)
        left, right = observed.get(source), observed.get(target)
        if relationship.get("witness_strength") == "unbounded":
            left_growth, right_growth = growth.get(source), growth.get(target)
            if left_growth is not None and right_growth is not None and left_growth[0] > right_growth[0]:
                localized.append({
                    "id": edge["id"], "source": source, "target": target,
                    "evidence": f"{left_growth[1]} > {right_growth[1]}",
                })
            elif left_growth is None or right_growth is None:
                unknown.append({"id": edge["id"], "source": source, "target": target})
        elif left is None or right is None:
            unknown.append({"id": edge["id"], "source": source, "target": target})
        elif left > right:
            localized.append({
                "id": edge["id"], "source": source, "target": target,
                "evidence": f"{left}>{right}",
            })
    return {
        "witness": witness,
        "path": [edge["id"] for edge in path],
        "localized_edges": localized,
        "unknown_edges": unknown,
        "resolved": bool(localized),
    }


def graph_endpoints(relationship: Record) -> tuple[str, str]:
    """Use quotient endpoints when auditing a graph-level relationship."""
    return relationship["parameter_1_id"], relationship["parameter_2_id"]


def audit(data_dir: Path) -> dict[str, Any]:
    root = data_dir.parent.resolve()
    graph = load_graph_module(root)
    parameters = load_records(data_dir / "parameters")
    values = load_records(data_dir / "values")
    relationships = [
        record
        for record in load_records(data_dir / "relationships")
        if record.get("status") == "established"
    ]
    _, component_of = graph.exact_equivalence_components(parameters, relationships)
    quotient = graph.quotient_relationships(relationships, component_of)
    by_variant: dict[str, list[Record]] = defaultdict(list)
    for relationship in quotient:
        by_variant[graph.variant_of(relationship)].append(relationship)
    # Match the renderer's vertical ordering: base affine bounds contribute to
    # rank closure even though only homogeneous facts are Hasse-reduced.
    ranks = graph.hierarchy_ranks(by_variant.get(graph.BASE_VARIANT, []))

    result: dict[str, Any] = {
        "direct_established_relationships": len(relationships),
        "variants": {},
        "boundary_witness_queue": [],
        "witness_queue": [],
        "witness_protected_bypasses": [],
    }
    boundary_components = {
        component_of[parameter]
        for parameter in BOUNDARY_PARAMETERS
        if parameter in component_of
    }
    for variant, variant_relationships in sorted(by_variant.items()):
        canonical = graph.canonical_linear_relations(variant_relationships)
        reduced = graph.reduced_linear_relations(variant_relationships)
        reduced_ids = {record["id"] for record in reduced}
        omitted = [record for record in canonical if record["id"] not in reduced_ids]
        adjacency: dict[str, set[str]] = defaultdict(set)
        vertices: set[str] = set()
        for record in reduced:
            source, target = graph.relation_endpoints(record)
            adjacency[source].add(target)
            vertices.update((source, target))
        complete_closure = closure(adjacency, vertices)
        edge_rows = []
        for record in reduced:
            source, target = graph.relation_endpoints(record)
            without = {node: set(neighbours) for node, neighbours in adjacency.items()}
            without[source].discard(target)
            lost_pairs = len(complete_closure - closure(without, vertices))
            row = {
                "id": record["id"],
                "short_name": record["short_name"],
                "type": record["relationship_type"],
                "variant": variant,
                "source": source,
                "target": target,
                "source_rank": ranks.get(source),
                "target_rank": ranks.get(target),
                "has_witness": bool(record.get("witness")),
                "witness_strength": record.get("witness_strength"),
                "lost_reachability_pairs": lost_pairs,
                "strict_value_candidates": strict_value_candidates(record, values, component_of),
            }
            if row["witness_strength"] == "strict":
                row["strict_witness_value_check"] = any(
                    candidate["class"] == record.get("witness")
                    for candidate in row["strict_value_candidates"]
                )
            else:
                row["strict_witness_value_check"] = None
            edge_rows.append(row)
            if not row["has_witness"]:
                result["witness_queue"].append(row)
                if source in boundary_components:
                    result["boundary_witness_queue"].append(row)
        result["variants"][variant] = {
            "canonical_linear_facts": len(canonical),
            "reduced_edges": len(reduced),
            "transitively_omitted_facts": [
                {"id": record["id"], "short_name": record["short_name"]}
                for record in omitted
            ],
            "edges": sorted(edge_rows, key=lambda row: (-row["lost_reachability_pairs"], row["id"])),
        }
        for bypass, path in graph.witness_protected_bypass_relations(variant_relationships):
            localization = localize_bypass_witness(bypass, path, values, component_of)
            result["witness_protected_bypasses"].append({
                "id": bypass["id"],
                "short_name": bypass["short_name"],
                "variant": variant,
                "strength": bypass["witness_strength"],
                **localization,
            })
    for key in ("boundary_witness_queue", "witness_queue"):
        result[key].sort(key=lambda row: (-row["lost_reachability_pairs"], row["id"]))
    result["strict_witness_value_checks"] = {
        "confirmed": sum(
            row["strict_witness_value_check"] is True
            for summary in result["variants"].values()
            for row in summary["edges"]
        ),
        "not_literal_or_not_recorded": sum(
            row["strict_witness_value_check"] is False
            for summary in result["variants"].values()
            for row in summary["edges"]
        ),
    }
    result["witness_protected_bypasses"].sort(key=lambda row: row["id"])
    return result


def print_queue(title: str, rows: list[dict[str, Any]]) -> None:
    print(f"\n{title}: {len(rows)}")
    for row in rows:
        witness = "yes" if row["has_witness"] else "no"
        candidates = ", ".join(
            f"{item['class']} ({item['left']}>{item['right']})"
            for item in row["strict_value_candidates"][:3]
        ) or "-"
        print(
            f"  #{row['id']:>3} impact={row['lost_reachability_pairs']:<3} witness={witness:<3} "
            f"rank={row['source_rank']}→{row['target_rank']} "
            f"{row['source']} >= {row['target']} | strict-value leads: {candidates}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--json", action="store_true", help="emit the full machine-readable audit")
    parser.add_argument("--all", action="store_true", help="also print every witnessless reduced edge")
    parser.add_argument(
        "--check-witness-bypasses", action="store_true",
        help="fail when a retained witnessed bypass cannot be localized to an alternate witnessless path edge",
    )
    args = parser.parse_args()
    report = audit(args.data_dir.resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"Established direct relationships: {report['direct_established_relationships']}")
    for variant, summary in report["variants"].items():
        print(
            f"{variant}: {summary['canonical_linear_facts']} canonical linear facts, "
            f"{summary['reduced_edges']} reduced edges, "
            f"{len(summary['transitively_omitted_facts'])} transitively omitted"
        )
    checks = report["strict_witness_value_checks"]
    print(
        "Strict witnesses independently confirmed by literal endpoint values: "
        f"{checks['confirmed']}; not mechanically checkable: {checks['not_literal_or_not_recorded']}"
    )
    bypasses = report["witness_protected_bypasses"]
    resolved = sum(row["resolved"] for row in bypasses)
    print(
        "Witness-protected transitive bypasses: "
        f"{len(bypasses)} ({resolved} localized to an alternate path edge; "
        f"{len(bypasses) - resolved} need value evidence)"
    )
    for row in bypasses:
        locations = ", ".join(
            f"#{edge['id']} ({edge['evidence']})"
            for edge in row["localized_edges"]
        ) or "unresolved"
        print(
            f"  #{row['id']:>3} {row['strength']} witness {row['witness']} "
            f"via {' -> '.join('#' + str(edge_id) for edge_id in row['path'])}: {locations}"
        )
    print_queue("Boundary Hasse edges needing witnesses", report["boundary_witness_queue"])
    if args.all:
        print_queue("All reduced Hasse edges needing witnesses", report["witness_queue"])
    if args.check_witness_bypasses and any(not row["resolved"] for row in bypasses):
        raise SystemExit("unlocalized witness-protected transitive bypasses")


if __name__ == "__main__":
    main()
