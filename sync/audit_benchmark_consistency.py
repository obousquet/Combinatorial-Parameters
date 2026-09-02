#!/usr/bin/env python3
"""Check that unambiguous exact benchmark values respect direct relationships.

This intentionally verifies only literal nonnegative integer values.  Formulae,
asymptotic statements, intervals, and parameters with more than one value on a
class are skipped: parsing those safely requires their stated parameter range.
The check is therefore a regression detector, not a prover of any relationship.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from fractions import Fraction
from pathlib import Path


INTEGER_VALUE = re.compile(r"^\s*\$?\s*([0-9]+)\s*\$?\s*$")
INTEGER_CONSTANT = re.compile(r"^\s*([+-]?\d+)\s*$")
TFRAC_CONSTANT = re.compile(r"^\s*([+-]?)\\tfrac(\d+)(\d+)\s*$")


def records(directory: Path) -> list[dict[str, object]]:
    return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))
            if path.name != "schema.json"]


def integer_value(record: dict[str, object]) -> int | None:
    if record.get("status") != "established":
        return None
    value = record.get("value")
    if not isinstance(value, str):
        return None
    match = INTEGER_VALUE.fullmatch(value)
    return int(match.group(1)) if match else None


def numeric_constant(value: object) -> Fraction | None:
    """Parse the deliberately small constant syntax used in relationship JSON."""
    if not isinstance(value, str):
        return None
    integer = INTEGER_CONSTANT.fullmatch(value)
    if integer:
        return Fraction(int(integer.group(1)))
    frac = TFRAC_CONSTANT.fullmatch(value)
    if frac and frac.group(3) != "0":
        sign = -1 if frac.group(1) == "-" else 1
        return sign * Fraction(int(frac.group(2)), int(frac.group(3)))
    return None


def has_conditional_scope(relationship: dict[str, object]) -> bool:
    """Recognize the common prose marker for a non-universal bound.

    Scope is currently free text.  Conservatively skip a relationship whose
    details begin ``For ...`` unless it explicitly says ``For every`` or
    ``For all``; a benchmark value may fall outside an unstated threshold.
    """
    details = relationship.get("details")
    if not isinstance(details, str):
        return False
    normalized = details.lstrip().lower()
    return normalized.startswith("for ") and not normalized.startswith(("for every", "for all"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--fail-on-contradiction", action="store_true")
    parser.add_argument("--report-equality-gaps", action="store_true",
                        help="Report classes with a value for only one side of an equality.")
    args = parser.parse_args()

    values_by_key: dict[tuple[str, str], list[int]] = defaultdict(list)
    for value in records(args.data_dir / "values"):
        parsed = integer_value(value)
        class_id = value.get("class_id")
        parameter_id = value.get("parameter_id")
        if parsed is not None and isinstance(class_id, str) and isinstance(parameter_id, str):
            values_by_key[(class_id, parameter_id)].append(parsed)

    # A duplicate record can have a different stated range.  Do not assume the
    # ranges overlap; retain only keys with one literal exact record.
    exact = {key: entries[0] for key, entries in values_by_key.items() if len(entries) == 1}
    established_keys = {
        (value["class_id"], value["parameter_id"])
        for value in records(args.data_dir / "values")
        if value.get("status") == "established"
        and isinstance(value.get("class_id"), str)
        and isinstance(value.get("parameter_id"), str)
    }
    contradictions: list[str] = []
    comparisons = 0
    for relationship in records(args.data_dir / "relationships"):
        if relationship.get("status") != "established":
            continue
        kind = relationship.get("relationship_type")
        if kind not in {"larger", "larger_c", "equivalence"}:
            continue
        if kind == "larger_c" and has_conditional_scope(relationship):
            continue
        first = relationship.get("parameter_1_id")
        second = relationship.get("parameter_2_id")
        if not isinstance(first, str) or not isinstance(second, str):
            continue
        factor = offset = None
        if kind == "larger_c":
            factor = numeric_constant(relationship.get("multiplicative_constant"))
            offset = numeric_constant(relationship.get("additive_constant"))
            if factor is None or offset is None:
                continue
        for class_id in {class_id for class_id, _ in exact}:
            left = exact.get((class_id, first))
            right = exact.get((class_id, second))
            if left is None or right is None:
                continue
            comparisons += 1
            if kind == "equivalence":
                violates = left != right
                symbol = "="
            elif kind == "larger":
                violates = left < right
                symbol = ">="
            else:
                assert factor is not None and offset is not None
                violates = Fraction(left) < factor * right - offset
                symbol = f">= {factor}* - {offset}"
            if violates:
                name = relationship.get("short_name", relationship.get("id", "relationship"))
                contradictions.append(f"{class_id}: {name}: {left} {symbol} {right} fails")

    print(f"Exact benchmark comparisons checked: {comparisons}")
    if contradictions:
        print("Contradictions:")
        print("\n".join(contradictions))
        if args.fail_on_contradiction:
            return 1
    else:
        print("No exact benchmark contradictions found.")

    if args.report_equality_gaps:
        gaps: list[str] = []
        for relationship in records(args.data_dir / "relationships"):
            if relationship.get("status") != "established" or relationship.get("relationship_type") != "equivalence":
                continue
            first = relationship.get("parameter_1_id")
            second = relationship.get("parameter_2_id")
            if not isinstance(first, str) or not isinstance(second, str):
                continue
            name = relationship.get("short_name", relationship.get("id", "relationship"))
            classes = {class_id for class_id, parameter_id in established_keys
                       if parameter_id in {first, second}}
            for class_id in sorted(classes):
                has_first = (class_id, first) in established_keys
                has_second = (class_id, second) in established_keys
                if has_first != has_second:
                    missing = second if has_first else first
                    gaps.append(f"{class_id}: {name}: missing {missing}")
        print(f"Equality coverage gaps: {len(gaps)}")
        print("\n".join(gaps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
