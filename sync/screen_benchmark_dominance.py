#!/usr/bin/env python3
"""Rank unrecorded dominance candidates using exact benchmark values.

This is a *research queue*, not a verifier and not a source of mathematical
facts.  It only screens out candidate directions already contradicted by an
established literal-integer value.  Any reported pair still needs a direct
proof or primary source before it can become a relationship record.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def records(directory: Path) -> list[dict]:
    return [
        json.loads(path.read_text())
        for path in sorted(directory.glob("[0-9]*.json"))
    ]


def literal_nonnegative_integer(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.startswith("$") and value.endswith("$"):
        value = value[1:-1].strip()
    return int(value) if value.isdigit() else None


def short(reference: str) -> str:
    return reference.rsplit("/", 1)[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--min-coobservations",
        type=int,
        default=8,
        help="minimum number of shared exact benchmark values to report",
    )
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    values_by_class: dict[str, dict[str, int]] = defaultdict(dict)
    for value in records(args.data_dir / "values"):
        if value.get("status", "established") != "established":
            continue
        integer = literal_nonnegative_integer(value.get("value"))
        if integer is not None:
            values_by_class[value["class_id"]][value["parameter_id"]] = integer

    parameters = {
        f"#parameters/{parameter['short_name']}": parameter["name"]
        for parameter in records(args.data_dir / "parameters")
        if parameter.get("short_name")
    }
    relationships = records(args.data_dir / "relationships")
    stated_pairs = {
        (relationship["parameter_1_id"], relationship["parameter_2_id"])
        for relationship in relationships
        # A refuted proposal is also no longer an unrecorded research lead.
        # Incomparability records are deliberately excluded: their witnesses
        # concern asymptotic affine bounds, whereas this screen only compares
        # exact finite benchmark cells.
        if relationship.get("relationship_type") != "incomparable"
    }

    candidates = []
    parameter_ids = sorted(parameters)
    for upper in parameter_ids:
        for lower in parameter_ids:
            if upper == lower or (upper, lower) in stated_pairs:
                continue
            shared = [
                (class_id, entries[upper], entries[lower])
                for class_id, entries in values_by_class.items()
                if upper in entries and lower in entries
            ]
            if len(shared) < args.min_coobservations:
                continue
            if any(upper_value < lower_value for _, upper_value, lower_value in shared):
                continue
            strict_count = sum(
                upper_value > lower_value
                for _, upper_value, lower_value in shared
            )
            if strict_count:
                candidates.append((
                    len(shared), strict_count, upper, lower,
                ))

    candidates.sort(reverse=True)
    print(
        "Diagnostic candidates with no exact-integer benchmark counterexample "
        f"(at least {args.min_coobservations} co-observations): {len(candidates)}"
    )
    for shared, strict, upper, lower in candidates[:args.limit]:
        print(
            f"{shared:3} shared; {strict:3} strict  "
            f"{short(upper)} >= {short(lower)}"
        )
    print(
        "These are not established relationships. Inspect definitions and a "
        "primary source before recording any of them."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
