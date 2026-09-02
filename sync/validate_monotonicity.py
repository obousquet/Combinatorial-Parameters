#!/usr/bin/env python3
"""Validate monotonicity metadata using only definitional implications.

This intentionally does not try to prove monotonicity from benchmark values.
Absent fields remain unknown.  It only closes implications that hold by the
definitions in the survey and transfers facts across established equalities.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FLAGS = (
    "monotonic",
    "p_monotonic",
    "c_monotonic",
    "doubly_monotonic",
    "strict_c_monotonic",
    "tight_strict_c_monotonic",
    "strictly_monotonic",
)


def records(directory: Path) -> list[tuple[Path, dict]]:
    return [(path, json.loads(path.read_text())) for path in sorted(directory.glob("[0-9]*.json"))]


def implied(flags: dict[str, bool | None]) -> bool:
    """Close the facts forced by the definitions; return whether they changed."""
    changed = False

    def set_true(name: str) -> None:
        nonlocal changed
        if flags[name] is None:
            flags[name] = True
            changed = True
        elif flags[name] is False:
            raise ValueError(f"{name}=false contradicts a definitional implication")

    if flags["monotonic"] is True and flags["p_monotonic"] is True:
        set_true("doubly_monotonic")
    if flags["doubly_monotonic"] is True:
        set_true("monotonic")
        set_true("p_monotonic")
        set_true("c_monotonic")
    if flags["strict_c_monotonic"] is True:
        set_true("c_monotonic")
    if flags["tight_strict_c_monotonic"] is True:
        set_true("strict_c_monotonic")
    if flags["strictly_monotonic"] is True:
        set_true("doubly_monotonic")
        set_true("strict_c_monotonic")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--check", action="store_true", help="fail if any forced fact is absent from JSON")
    args = parser.parse_args()

    parameter_records = records(args.data_dir / "parameters")
    parameters = {entry["short_name"]: (path, entry) for path, entry in parameter_records}
    flags = {name: {flag: entry.get(flag) for flag in FLAGS} for name, (_, entry) in parameters.items()}

    # Established exact equalities identify the same parameter, so all of their
    # monotonicity facts must agree.  Use a simple fixed point rather than
    # assuming a particular orientation of relationship records.
    equalities = []
    for _, relationship in records(args.data_dir / "relationships"):
        if relationship.get("relationship_type") != "equivalence":
            continue
        if relationship.get("status", "established") != "established":
            continue
        equalities.append((relationship["parameter_1_id"].rsplit("/", 1)[-1], relationship["parameter_2_id"].rsplit("/", 1)[-1]))

    changed = True
    try:
        while changed:
            changed = False
            for parameter_flags in flags.values():
                changed = implied(parameter_flags) or changed
            for left, right in equalities:
                for flag in FLAGS:
                    left_value, right_value = flags[left][flag], flags[right][flag]
                    if left_value is not None and right_value is not None and left_value != right_value:
                        raise ValueError(f"equality {left}={right} disagrees on {flag}")
                    if left_value is None and right_value is not None:
                        flags[left][flag] = right_value
                        changed = True
                    elif right_value is None and left_value is not None:
                        flags[right][flag] = left_value
                        changed = True
    except ValueError as error:
        print(f"Monotonicity metadata invalid: {error}")
        return 1

    inferred = []
    for name, (_, entry) in parameters.items():
        for flag in FLAGS:
            if entry.get(flag) is None and flags[name][flag] is not None:
                inferred.append(f"{name}: {flag}={str(flags[name][flag]).lower()}")

    print(f"Monotonicity metadata valid for {len(parameters)} parameters.")
    if inferred:
        print("Facts forced by definitions/equalities but missing from JSON:")
        print("\n".join(f"- {item}" for item in inferred))
        return 1 if args.check else 0
    print("No forced monotonicity facts are missing from JSON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
