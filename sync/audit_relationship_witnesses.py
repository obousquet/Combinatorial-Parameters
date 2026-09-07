#!/usr/bin/env python3
"""Screen all established relationships for missing or stronger witnesses.

The output is a research queue, never an automatic fact migration. Growth
classes can be one-sided bounds, and scoped reverse paths need human review.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from fractions import Fraction
from pathlib import Path

from audit_witness_strength import GROWTH_RANK, literal_rational, records
from audit_hasse_edges import load_graph_module


def implies_exact_domination(relation: dict, coefficients: tuple[Fraction, Fraction] | None) -> bool:
    """Sufficient, not exhaustive, for A >= B on nonnegative parameters.

    Affine records use A >= c B - d. Symbolic constants and paths whose
    weak factors compensate are deliberately left for manual review.
    """
    kind = relation["relationship_type"]
    if kind in {"larger", "equivalence"}:
        return True
    if kind != "larger_c":
        return False
    return coefficients is not None and coefficients[0] >= 1 and coefficients[1] <= 0


def reverse_bound_path(relation: dict, adjacency: dict) -> list[int] | None:
    first, second = relation["parameter_1_id"], relation["parameter_2_id"]
    if relation["relationship_type"] in {"log_upper", "sqrt_upper", "functional_upper"}:
        first, second = second, first
    pending = deque([(second, [])])
    seen = {second}
    while pending:
        node, path = pending.popleft()
        if node == first:
            return path
        for neighbor, identifier in adjacency.get(relation.get("variant", "base"), {}).get(node, []):
            if neighbor not in seen:
                seen.add(neighbor)
                pending.append((neighbor, path + [identifier]))
    return None


def reverse_adjacencies(relations: list[dict], graph) -> tuple[dict, dict]:
    affine = defaultdict(lambda: defaultdict(list))
    exact = defaultdict(lambda: defaultdict(list))
    for relation in relations:
        if relation.get("status") != "established":
            continue
        kind = relation["relationship_type"]
        if kind not in {"larger", "larger_c", "equivalence"}:
            continue
        coefficient = graph.rational_constant(relation.get("multiplicative_constant"))
        if kind == "larger_c" and coefficient is not None and coefficient <= 0:
            continue
        variant = relation.get("variant", "base")
        first, second = relation["parameter_1_id"], relation["parameter_2_id"]
        coefficients = graph.affine_coefficients(relation)
        for adjacency in (affine, exact) if implies_exact_domination(relation, coefficients) else (affine,):
            adjacency[variant][first].append((second, relation["id"]))
            if kind == "equivalence":
                adjacency[variant][second].append((first, relation["id"]))
    return affine, exact


def audit(data_dir: Path) -> dict:
    relations = records(data_dir / "relationships")
    parameters = records(data_dir / "parameters")
    values = records(data_dir / "values")
    graph = load_graph_module(data_dir.parent)
    established = [r for r in relations if r.get("status") == "established"]
    _, component_of = graph.exact_equivalence_components(parameters, established)
    by_class = defaultdict(lambda: defaultdict(list))
    for value in values:
        if value.get("status") == "established":
            by_class[value["class_id"]][component_of[value["parameter_id"]]].append(value)

    # Each path retains IDs so its constants and extra scope assumptions can
    # be reviewed. Nonlinear statements cannot certify an affine reverse.
    adjacency, exact_adjacency = reverse_adjacencies(established, graph)

    rows = []
    conflicts = []
    strict_conflicts = []
    counts = Counter()
    for relation in established:
        kind = relation["relationship_type"]
        if kind in {"equivalence", "incomparable"}:
            counts[kind] += 1
            continue
        if relation.get("witness_strength") == "unbounded":
            counts["unbounded"] += 1
            path = reverse_bound_path(relation, adjacency)
            if path is not None:
                conflicts.append({
                    "id": relation["id"],
                    "short_name": relation["short_name"],
                    "reverse_affine_path": path,
                    "review": "An unbounded witness conflicts with this reverse affine path if their scopes match.",
                })
            continue
        category = (
            "strict" if relation.get("witness_strength") == "strict"
            else "unclassified" if relation.get("witness")
            else "missing"
        )
        counts[category] += 1
        a, b = (component_of[p] for p in graph.relation_endpoints(relation))
        if kind in {"log_upper", "sqrt_upper", "functional_upper"}:
            a, b = b, a
        growth_leads, strict_leads = [], []
        for class_id, observed in sorted(by_class.items()):
            for left in observed.get(a, []):
                for right in observed.get(b, []):
                    record = {
                        "class": class_id,
                        "larger_value": left["value"],
                        "smaller_value": right["value"],
                        "value_ids": [left["id"], right["id"]],
                    }
                    large_growth = GROWTH_RANK.get(left.get("value_class"))
                    small_growth = GROWTH_RANK.get(right.get("value_class"))
                    if large_growth is not None and small_growth is not None and large_growth > small_growth:
                        growth_leads.append(record)
                    large_exact, small_exact = literal_rational(left.get("value")), literal_rational(right.get("value"))
                    if large_exact is not None and small_exact is not None and large_exact > small_exact:
                        strict_leads.append(record)
        path = reverse_bound_path(relation, adjacency)
        exact_path = reverse_bound_path(relation, exact_adjacency)
        if category == "strict" and exact_path is not None:
            strict_conflicts.append({
                "id": relation["id"],
                "short_name": relation["short_name"],
                "reverse_exact_path": exact_path,
                "review": "A strict endpoint witness conflicts with this exact reverse if their scopes match.",
            })
        rows.append({
            "id": relation["id"],
            "short_name": relation["short_name"],
            "category": category,
            "witness": relation.get("witness"),
            "reverse_affine_path": path,
            "reverse_exact_path": exact_path,
            "witness_search_if_scopes_match": (
                "neither_strict_nor_unbounded" if exact_path is not None
                else "strict_only" if path is not None
                else "no_reverse_bound_found"
            ),
            "unbounded_candidates": growth_leads,
            "strict_candidates": strict_leads,
            "review": (
                "Check reverse-path scope; if compatible, even a strict endpoint gap is impossible. "
                "Coefficient sharpness is a separate question, not an endpoint-separation witness."
                if exact_path is not None else
                "Check scope of reverse affine path; if compatible, only a finite strict gap is possible."
                if path is not None
                else "Check endpoint proofs and scope before promoting any candidate."
            ),
        })
    return {
        "counts": dict(counts),
        "scope": "Every established direct record. Equalities and incomparabilities counted separately.",
        "caution": "Candidate growth ranks are leads, not certificates. Reverse paths require matching scope and positive affine coefficients. Exact paths use individually sufficient bounds on nonnegative parameters; compensating affine factors are not searched. Coefficient sharpness is not endpoint separation.",
        "unbounded_reverse_conflicts": conflicts,
        "strict_reverse_conflicts": strict_conflicts,
        "rows": sorted(rows, key=lambda row: row["id"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, help="Write the complete JSON research queue.")
    parser.add_argument("--check", action="store_true",
                        help="Fail when an unbounded/strict witness has a reverse affine/exact path requiring review.")
    args = parser.parse_args()
    report = audit(args.data_dir.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("Established relationship coverage:", json.dumps(report["counts"], sort_keys=True))
    print("Unbounded witness / reverse-affine conflicts:",
          len(report["unbounded_reverse_conflicts"]))
    print("Strict witness / reverse-exact conflicts:", len(report["strict_reverse_conflicts"]))
    for category in ("missing", "strict", "unclassified"):
        rows = [row for row in report["rows"] if row["category"] == category]
        print(f"{category}: {len(rows)}; reverse-affine paths: "
              f"{sum(row['reverse_affine_path'] is not None for row in rows)}; "
              f"reverse-exact paths: {sum(row['reverse_exact_path'] is not None for row in rows)}; "
              f"growth leads: {sum(bool(row['unbounded_candidates']) for row in rows)}; "
              f"strict integer leads: {sum(bool(row['strict_candidates']) for row in rows)}")
    for row in report["rows"]:
        if row["reverse_affine_path"] is not None:
            print(f"  #{row['id']} {row['short_name']}: reverse path {row['reverse_affine_path']}")
    if args.check and (report["unbounded_reverse_conflicts"] or report["strict_reverse_conflicts"]):
        raise SystemExit("Declared witnesses have incompatible reverse bounds: review scope and endpoint proofs.")


if __name__ == "__main__":
    main()
