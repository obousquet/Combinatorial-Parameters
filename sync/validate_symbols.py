#!/usr/bin/env python3
"""Enforce the shared bare-TeX symbol convention for catalogue records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()

    invalid: list[str] = []
    checked = 0
    for table in ("parameters", "classes"):
        for path in sorted((args.data_dir / table).glob("[0-9]*.json")):
            entry = json.loads(path.read_text())
            symbol = str(entry.get("symbol", "")).strip()
            checked += 1
            if not symbol:
                invalid.append(f"{table}/{entry.get('short_name', path.stem)}: missing symbol")
            elif symbol.startswith("$") or symbol.endswith("$"):
                invalid.append(
                    f"{table}/{entry.get('short_name', path.stem)}: symbols must be bare TeX, not $...$"
                )

    print(f"Bare-TeX symbol convention checked for {checked} records.")
    if invalid:
        print("\n".join(f"- {item}" for item in invalid))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
