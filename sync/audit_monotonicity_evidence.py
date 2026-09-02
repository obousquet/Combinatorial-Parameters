#!/usr/bin/env python3
"""Report declared monotonicity flags that lack a proof or provenance record."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--check", action="store_true", help="fail if declared properties lack evidence")
    args = parser.parse_args()

    missing: list[str] = []
    declared = 0
    for path in sorted((args.data_dir / "parameters").glob("[0-9]*.json")):
        entry = json.loads(path.read_text())
        evidence = entry.get("monotonicity_evidence", {})
        for flag in FLAGS:
            if entry.get(flag) is None:
                continue
            declared += 1
            item = evidence.get(flag)
            if not isinstance(item, dict) or not any(item.get(key) for key in ("proof", "latex_proof_label", "references")):
                missing.append(f"{entry['short_name']}: {flag}={str(entry[flag]).lower()}")

    print(f"Declared monotonicity facts: {declared}")
    print(f"Facts lacking per-property evidence: {len(missing)}")
    if missing:
        print("\n".join(f"- {item}" for item in missing))
    return 1 if args.check and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
