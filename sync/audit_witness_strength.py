#!/usr/bin/env python3
"""Audit whether relationship witnesses are strict or asymptotically unbounded.

For a declared strict witness, exact literal endpoint values are checked when
available.  For a declared unbounded witness, the two endpoint value classes
must certify different growth scales on the named parameterized class.  The
script deliberately leaves legacy witnesses without a declared strength in a
queue: a witness can establish sharpness without separating the reverse bound.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any


Record = dict[str, Any]
GROWTH_RANK = {
    "omega_1": 0,
    "omega_log_n": 1,
    "omega_n": 2,
    "omega_n_log_n": 3,
    "omega_n_squared": 4,
    "omega_2^n": 5,
    "$\\Omega(2^n)$": 5,
}


def records(directory: Path) -> list[Record]:
    return [
        json.loads(path.read_text())
        for path in sorted(directory.glob("*.json"))
        if path.name != "schema.json"
    ]


def literal_rational(value: str | None) -> Fraction | None:
    if not value:
        return None
    value = value.strip()
    if value.startswith("$") and value.endswith("$"):
        value = value[1:-1].strip()
    if re.fullmatch(r"\d+", value):
        return Fraction(int(value))
    fraction = re.fullmatch(r"\\frac\{(\d+)\}\{(\d+)\}", value)
    if fraction:
        return Fraction(int(fraction.group(1)), int(fraction.group(2)))
    return None


def endpoint_values(relationship: Record, values: list[Record]) -> tuple[Record | None, Record | None]:
    matches = {
        value["parameter_id"]: value
        for value in values
        if value.get("status") == "established"
        and value.get("class_id") == relationship.get("witness")
        and value.get("parameter_id") in {
            relationship["parameter_1_id"], relationship["parameter_2_id"]
        }
    }
    return matches.get(relationship["parameter_1_id"]), matches.get(relationship["parameter_2_id"])


def strict_verified(relationship: Record, left: Record | None, right: Record | None) -> bool | None:
    if not left or not right:
        return None
    a, b = literal_rational(left.get("value")), literal_rational(right.get("value"))
    if a is None or b is None:
        return None
    if relationship.get("relationship_type") == "equivalence":
        return a != b
    if (relationship.get("status") == "refuted") != (
        relationship.get("relationship_type") in {"log_upper", "sqrt_upper"}
    ):
        return a < b
    return a > b


def unbounded_verified(
    relationship: Record, left: Record | None, right: Record | None
) -> bool | None:
    if not left or not right:
        return None
    a, b = GROWTH_RANK.get(left.get("value_class")), GROWTH_RANK.get(right.get("value_class"))
    if a is None or b is None:
        return None
    reverse = (relationship.get("status") == "refuted") != (
        relationship.get("relationship_type") in {"log_upper", "sqrt_upper"}
    )
    return a < b if reverse else a > b


def audit(data_dir: Path) -> dict[str, list[dict[str, Any]]]:
    values = records(data_dir / "values")
    report: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relationship in records(data_dir / "relationships"):
        if relationship.get("relationship_type") == "incomparable":
            first_witness = relationship.get("parameter_1_larger_witness")
            second_witness = relationship.get("parameter_2_larger_witness")
            report["incomparable"].append(
                {
                    "id": relationship["id"],
                    "short_name": relationship["short_name"],
                    "status": relationship.get("status"),
                    "parameter_1_larger_witness": first_witness,
                    "parameter_2_larger_witness": second_witness,
                    # These witnesses are generally literature families rather
                    # than a single finite benchmark row. Their explicit
                    # descriptions plus a citation or self-contained proof are
                    # the certificate.
                    # A two-sided family certificate can be self-contained:
                    # elementary comparisons are often proved by the canonical
                    # value records rather than a separate literature source.
                    "verified": bool(
                        first_witness
                        and second_witness
                        and (relationship.get("references") or relationship.get("proof"))
                    ),
                }
            )
            continue
        if not relationship.get("witness"):
            continue
        left, right = endpoint_values(relationship, values)
        strength = relationship.get("witness_strength")
        row = {
            "id": relationship["id"],
            "short_name": relationship["short_name"],
            "status": relationship.get("status"),
            "witness": relationship["witness"],
            "strength": strength or "unspecified",
            "left_value": left.get("value") if left else None,
            "left_value_class": left.get("value_class") if left else None,
            "right_value": right.get("value") if right else None,
            "right_value_class": right.get("value_class") if right else None,
        }
        if strength == "strict":
            row["verified"] = strict_verified(relationship, left, right)
            if relationship.get("witness_verification"):
                row["verified"] = True
                row["verification_method"] = "explicit symbolic certificate"
            report["strict"].append(row)
        elif strength == "unbounded":
            row["verified"] = unbounded_verified(relationship, left, right)
            if relationship.get("witness_verification"):
                row["verified"] = True
                row["verification_method"] = "explicit symbolic certificate"
            report["unbounded"].append(row)
        else:
            row["strict_candidate"] = strict_verified(relationship, left, right)
            row["unbounded_candidate"] = unbounded_verified(relationship, left, right)
            report["unclassified"].append(row)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--check", action="store_true", help="fail on a declared strength that cannot be verified")
    parser.add_argument("--require-classification", action="store_true", help="also fail if a witness has no strength")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.data_dir.resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for category in ("strict", "unbounded", "incomparable", "unclassified"):
            rows = report[category]
            confirmed = sum(row.get("verified") is True for row in rows)
            unresolved = sum(row.get("verified") is not True for row in rows)
            if category == "unclassified":
                candidates = sum(
                    row.get("strict_candidate") is True or row.get("unbounded_candidate") is True
                    for row in rows
                )
                print(f"Unclassified witnesses: {len(rows)} ({candidates} mechanically classifiable candidates)")
            elif category == "incomparable":
                print(f"Declared incomparable pairs: {len(rows)} ({confirmed} with both directional witnesses recorded; {unresolved} incomplete)")
            else:
                print(f"Declared {category} witnesses: {len(rows)} ({confirmed} verified; {unresolved} need manual evidence)")
    failures = [
        row for category in ("strict", "unbounded", "incomparable") for row in report[category]
        if row.get("verified") is not True
    ]
    if args.check and failures:
        raise SystemExit(f"{len(failures)} declared witness strengths need manual evidence")
    if args.require_classification and report["unclassified"]:
        raise SystemExit(f"{len(report['unclassified'])} witnesses have no declared strength")


if __name__ == "__main__":
    main()
