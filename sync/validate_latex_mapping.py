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


def survey_labels(latex_dir: Path) -> set[str]:
    """Return labels from LaTeX-authored survey prose, excluding generated files."""
    labels = set()
    for source in latex_dir.rglob("*.tex"):
        if "generated" in source.parts:
            continue
        labels.update(LABEL_PATTERN.findall(source.read_text()))
    return labels


def validate_relationship_proof_labels(
    entries: list[dict], latex_labels: set[str]
) -> list[str]:
    errors = []
    for entry in entries:
        label = entry.get("latex_proof_label")
        if not label:
            continue
        name = entry.get("short_name", f"ID {entry['id']}")
        if label not in latex_labels:
            errors.append(
                f"relationship/{name} points to missing survey proof label {label}"
            )
        if not entry.get("proof_source"):
            errors.append(
                f"relationship/{name} has latex_proof_label but no proof_source"
            )
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
    # Definition sources are database-owned and copied into the LaTeX checkout.
    # Read the authoritative files here so validation does not accidentally rely
    # on a stale generated copy.
    latex_labels = set()
    for source in (
        args.data_dir / "latex" / "parameter_definitions.tex",
        args.data_dir / "latex" / "class_definitions.tex",
    ):
        if source.is_file():
            latex_labels.update(LABEL_PATTERN.findall(source.read_text()))

    parameter_entries = records(args.data_dir, "parameters")
    class_entries = records(args.data_dir, "classes")
    relationship_entries = records(args.data_dir, "relationships")
    errors = validate_table(parameter_entries, mapping["parameters"], latex_labels, "parameters")
    errors.extend(validate_table(class_entries, mapping["classes"], latex_labels, "classes"))
    proof_labels = survey_labels(args.latex_dir)
    errors.extend(validate_relationship_proof_labels(relationship_entries, proof_labels))
    if errors:
        print("LaTeX mapping validation failed:", *errors, sep="\n- ", file=sys.stderr)
        return 1
    placeholders = mapping["parameters"].get("unmapped_database_ids", {})
    mapped_parameters = len(parameter_entries) - len(placeholders)
    print(
        "LaTeX mapping valid: "
        f"{mapped_parameters} mapped parameters, {len(placeholders)} documented placeholders, "
        f"{len(class_entries)} mapped classes, "
        f"{sum(bool(entry.get('latex_proof_label')) for entry in relationship_entries)} "
        "relationship proof labels."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
