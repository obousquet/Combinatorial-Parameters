#!/usr/bin/env python3
"""Reject duplicate direct relationship statements in the catalogue."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def signature(relationship: dict) -> tuple[str | None, str | None, str | None, str]:
    """Identify the mathematical statement, independently of its prose."""
    return (
        relationship.get("parameter_1_id"),
        relationship.get("relationship_type"),
        relationship.get("parameter_2_id"),
        relationship.get("variant") or "",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    grouped: dict[tuple[str | None, str | None, str | None, str], list[dict]] = defaultdict(list)
    for path in sorted((args.data_dir / "relationships").glob("[0-9][0-9][0-9]_*.json")):
        relationship = json.loads(path.read_text())
        relationship["_path"] = path
        grouped[signature(relationship)].append(relationship)

    duplicates = [rows for rows in grouped.values() if len(rows) > 1]
    print(f"Direct relationship statements checked: {sum(map(len, grouped.values()))}")
    print(f"Duplicate statements: {len(duplicates)}")
    for rows in duplicates:
        ids = ", ".join(
            f"{row['id']} ({row['_path'].name}, {row.get('status', 'unknown')})"
            for row in rows
        )
        first = rows[0]
        variant = f" [{first.get('variant')}]" if first.get("variant") else ""
        print(
            f"- {first['parameter_1_id']} {first['relationship_type']} "
            f"{first['parameter_2_id']}{variant}: {ids}"
        )
    if args.check and duplicates:
        raise SystemExit("Duplicate direct relationship statements found")


if __name__ == "__main__":
    main()
