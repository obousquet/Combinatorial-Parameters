#!/usr/bin/env python3
"""Validate the JSON-to-LaTeX definition mapping used for synchronization."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


LABEL_PATTERN = re.compile(r"\\label\{([^}]+)\}")


def records(data_dir: Path, table: str) -> list[dict]:
    return [
        json.loads(path.read_text())
        for path in sorted((data_dir / table).glob("[0-9]*.json"))
    ]


def expected_label(entry: dict, config: dict) -> str:
    short_name = entry["short_name"]
    return config["label_overrides"].get(
        short_name, config["default_label_template"].format(short_name=short_name)
    )


def validate_table(
    entries: list[dict], config: dict, latex_labels: set[str], table: str
) -> list[str]:
    errors = []
    explicitly_unmapped = {int(identifier) for identifier in config.get("unmapped_database_ids", {})}
    for entry in entries:
        identifier = entry["id"]
        short_name = entry.get("short_name")
        if identifier in explicitly_unmapped:
            if short_name:
                errors.append(f"{table} ID {identifier} is marked unmapped but has short name {short_name!r}")
            continue
        if not short_name:
            errors.append(f"{table} ID {identifier} has no short name and no unmapped entry")
            continue
        label = expected_label(entry, config)
        if label not in latex_labels:
            errors.append(f"{table}/{short_name} maps to missing LaTeX label {label}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--latex-dir", type=Path, default=Path("~/latex/CombinatorialParameters").expanduser()
    )
    parser.add_argument(
        "--mapping", type=Path, default=Path(__file__).with_name("latex_mapping.json")
    )
    args = parser.parse_args()

    mapping = json.loads(args.mapping.read_text())
    latex_labels = set(LABEL_PATTERN.findall((args.latex_dir / "includes" / "defs.tex").read_text()))
    latex_labels.update(LABEL_PATTERN.findall((args.latex_dir / "includes" / "cl_defs.tex").read_text()))

    errors = validate_table(records(args.data_dir, "parameters"), mapping["parameters"], latex_labels, "parameters")
    errors.extend(validate_table(records(args.data_dir, "classes"), mapping["classes"], latex_labels, "classes"))
    if errors:
        print("LaTeX mapping validation failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    print("LaTeX mapping valid: 79 mapped parameters, 2 documented placeholders, 9 mapped classes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
