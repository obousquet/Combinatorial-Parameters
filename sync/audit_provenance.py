#!/usr/bin/env python3
"""Audit the minimum evidence required for catalogue facts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


MONOTONICITY_FLAGS = (
    "monotonic", "p_monotonic", "c_monotonic", "doubly_monotonic",
    "strict_c_monotonic", "tight_strict_c_monotonic", "strictly_monotonic",
)


def records(directory: Path) -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted(directory.glob("[0-9]*.json"))]


def has_evidence(record: dict) -> bool:
    return bool(record.get("proof") or record.get("references") or record.get("latex_proof_label"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    missing: list[str] = []
    values = records(args.data_dir / "values")
    relationships = records(args.data_dir / "relationships")
    parameters = records(args.data_dir / "parameters")

    for entry in values:
        if entry.get("status", "established") == "established" and not has_evidence(entry):
            missing.append(f"value/{entry['short_name']}")
    for entry in relationships:
        if entry.get("status", "established") == "established" and not has_evidence(entry):
            missing.append(f"relationship/{entry['short_name']}")
    for entry in parameters:
        evidence = entry.get("monotonicity_evidence", {})
        for flag in MONOTONICITY_FLAGS:
            if entry.get(flag) is not None and not has_evidence(evidence.get(flag, {})):
                missing.append(f"monotonicity/{entry['short_name']}/{flag}")

    print(f"Established values checked: {sum(v.get('status', 'established') == 'established' for v in values)}")
    print(f"Established relationships checked: {sum(r.get('status', 'established') == 'established' for r in relationships)}")
    print(f"Declared monotonicity facts checked: {sum(p.get(f) is not None for p in parameters for f in MONOTONICITY_FLAGS)}")
    print(f"Facts lacking provenance: {len(missing)}")
    if missing:
        print("\n".join(f"- {item}" for item in missing))
    return 1 if args.check and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
