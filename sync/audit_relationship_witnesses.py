#!/usr/bin/env python3
"""Screen all established relationships for missing or stronger witnesses.

The output is a research queue, never an automatic fact migration. Growth
classes can be one-sided bounds, and scoped reverse paths need human review.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

from audit_witness_strength import GROWTH_RANK, literal_rational, records
from audit_hasse_edges import load_graph_module


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
    adjacency = defaultdict(lambda: defaultdict(list))
    for relation in established:
        if relation["relationship_type"] not in graph.LINEAR_TYPES:
            continue
        variant = relation.get("variant", "base")
        first, second = graph.relation_endpoints(relation)
        adjacency[variant][first].append((second, relation["id"]))
        if relation["relationship_type"] == "equivalence":
            adjacency[variant][second].append((first, relation["id"]))

    def reverse_path(relation: dict) -> list[int] | None:
        first, second = graph.relation_endpoints(relation)
        if relation["relationship_type"] in {"log_upper", "sqrt_upper"}:
            first, second = second, first
        pending = deque([(second, [])])
        seen = {second}
        while pending:
            node, path = pending.popleft()
            if node == first:
                return path
            for neighbor, identifier in adjacency[relation.get("variant", "base")][node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append((neighbor, path + [identifier]))
        return None

    rows = []
    conflicts = []
    counts = Counter()
    for relation in established:
        kind = relation["relationship_type"]
        if kind in {"equivalence", "incomparable"}:
            counts[kind] += 1
            continue
        if relation.get("witness_strength") == "unbounded":
            counts["unbounded"] += 1
            path = reverse_path(relation)
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
        if kind in {"log_upper", "sqrt_upper"}:
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
        path = reverse_path(relation)
        rows.append({
            "id": relation["id"],
            "short_name": relation["short_name"],
            "category": category,
            "witness": relation.get("witness"),
            "reverse_affine_path": path,
            "unbounded_candidates": growth_leads,
            "strict_candidates": strict_leads,
            "review": (
                "Check scope of reverse path; if compatible, unbounded gap is impossible."
                if path is not None
                else "Check endpoint proofs and scope before promoting any candidate."
            ),
        })
    return {
        "counts": dict(counts),
        "scope": "Every established direct record. Equalities and incomparabilities counted separately.",
        "caution": "Candidate growth ranks are leads, not certificates. Reverse paths require matching scope and positive affine coefficients.",
        "unbounded_reverse_conflicts": conflicts,
        "rows": sorted(rows, key=lambda row: row["id"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, help="Write the complete JSON research queue.")
    parser.add_argument("--check", action="store_true",
                        help="Fail when an unbounded witness has a reverse affine path requiring review.")
    args = parser.parse_args()
    report = audit(args.data_dir.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("Established relationship coverage:", json.dumps(report["counts"], sort_keys=True))
    print("Unbounded witness / reverse-affine conflicts:",
          len(report["unbounded_reverse_conflicts"]))
    for category in ("missing", "strict", "unclassified"):
        rows = [row for row in report["rows"] if row["category"] == category]
        print(f"{category}: {len(rows)}; reverse-affine paths: "
              f"{sum(row['reverse_affine_path'] is not None for row in rows)}; "
              f"growth leads: {sum(bool(row['unbounded_candidates']) for row in rows)}; "
              f"strict integer leads: {sum(bool(row['strict_candidates']) for row in rows)}")
    for row in report["rows"]:
        if row["reverse_affine_path"] is not None:
            print(f"  #{row['id']} {row['short_name']}: reverse path {row['reverse_affine_path']}")
    if args.check and report["unbounded_reverse_conflicts"]:
        raise SystemExit("Unbounded witnesses have reverse affine paths: review scope and endpoint proofs.")


if __name__ == "__main__":
    main()
