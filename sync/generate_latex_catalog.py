#!/usr/bin/env python3
"""Generate database-owned LaTeX catalogue sections.

The generated file is deliberately limited to fields that have a single
structured owner in ``data/``. It must not be edited by hand.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CATEGORY_NAMES = {
    "basic": "Basic",
    "graph-based": "Graph-based",
    "shattering": "Shattering",
    "algebraic": "Algebraic",
    "compression": "Compression",
    "teaching": "Teaching and Hitting",
    "queries": "Queries",
    "holes": "Holes and Homology",
}


def records(data_dir: Path, table: str) -> list[dict]:
    return [
        json.loads(path.read_text())
        for path in sorted((data_dir / table).glob("[0-9]*.json"))
    ]


def definition_label(entry: dict, mapping: dict) -> str:
    config = mapping["parameters"]
    return config["label_overrides"].get(
        entry["short_name"],
        config["default_label_template"].format(short_name=entry["short_name"]),
    )


def colour(entry: dict) -> str:
    """Match the monotonicity colour key stated in main.tex."""
    if entry.get("strictly_monotonic"):
        return "yellow!30"
    if entry.get("doubly_monotonic"):
        return "green!10"
    if entry.get("p_monotonic"):
        return "orange!30"
    if entry.get("monotonic"):
        return "blue!20"
    return "pink!30"


def marker(value: bool | None) -> str:
    if value is None:
        return ""
    return "Y" if value else "N"


def generate_parameter_table(data_dir: Path, mapping: dict) -> str:
    lines = [
        "% GENERATED from data/parameters by sync/generate_latex_catalog.py; do not edit.",
        "\\begin{center}",
        "\\begin{longtable}{|p{1.4in}|p{2.7in}|l|c|c|c|c|c|c|}",
        "\\caption{List of Combinatorial Parameters}\\\\",
        "\\hline",
        "Symbol & Name & Def & $P^\\dagger$ & $P^*$ & $P^p$ & $P^{p*}$ & Str\\\\",
        "\\hline",
        "\\endhead",
    ]
    placeholders = {int(identifier) for identifier in mapping["parameters"].get("unmapped_database_ids", {})}
    entries = [entry for entry in records(data_dir, "parameters") if entry["id"] not in placeholders]
    for category, category_name in CATEGORY_NAMES.items():
        category_entries = [entry for entry in entries if entry.get("category") == category]
        if not category_entries:
            continue
        lines.extend(
            [
                "\\multicolumn{2}{|c|}{{\\bf " + category_name + "}} & "
                "\\multicolumn{6}{|l|}{Section \\ref{sec:" + category_name + "}}\\\\",
                "\\hline",
            ]
        )
        for entry in category_entries:
            lines.extend(
                [
                    "\\cellcolor{" + colour(entry) + "} " + entry["symbol"]
                    + " & " + entry["name"]
                    + " & \\ref{" + definition_label(entry, mapping) + "}"
                    + " & " + marker(entry.get("symmetric"))
                    + " & " + marker(entry.get("monotonic"))
                    + " & " + marker(entry.get("p_monotonic"))
                    + " & " + marker(entry.get("doubly_monotonic"))
                    + " & " + marker(entry.get("strictly_monotonic"))
                    + "\\\\",
                    "\\hline",
                ]
            )
    lines.extend(["\\end{longtable}", "\\end{center}", ""])
    return "\n".join(lines)


def reference_short_name(reference: str) -> str:
    """Return the final short-name component of a #table/short_name reference."""
    return reference.rsplit("/", 1)[-1]


def math_mode(value: str) -> str:
    return value if value.startswith("$") and value.endswith("$") else "$" + value + "$"


def generate_value_table(data_dir: Path, mapping: dict) -> str:
    parameters = {
        entry["short_name"]: entry
        for entry in records(data_dir, "parameters")
        if entry.get("short_name")
    }
    classes = records(data_dir, "classes")
    values: dict[tuple[str, str], str] = {}
    for entry in records(data_dir, "values"):
        key = (
            reference_short_name(entry["parameter_id"]),
            reference_short_name(entry["class_id"]),
        )
        if key in values:
            raise ValueError(f"duplicate database value for {key}")
        values[key] = entry.get("value", "")

    lines = [
        "% GENERATED from data/parameters, data/classes, and data/values by sync/generate_latex_catalog.py; do not edit.",
        "\\begin{center}",
        "\\begin{longtable}{|p{1.2in}|" + "|".join("p{0.4in}" for _ in classes) + "|}",
        "\\caption{Values of the parameters for the main classes}\\\\\\hline",
        "Parameter & " + " & ".join(math_mode(entry["symbol"]) for entry in classes) + "\\\\",
        "\\hline",
        "\\hline",
        "\\endhead",
    ]
    placeholders = {int(identifier) for identifier in mapping["parameters"].get("unmapped_database_ids", {})}
    entries = [
        entry
        for entry in records(data_dir, "parameters")
        if entry["id"] not in placeholders
    ]
    for category, category_name in CATEGORY_NAMES.items():
        category_entries = [entry for entry in entries if entry.get("category") == category]
        if not category_entries:
            continue
        lines.extend(
            [
                "\\multicolumn{" + str(len(classes) + 1) + "}{|l|}{{\\bf " + category_name + "}}\\\\",
                "\\hline",
            ]
        )
        for entry in category_entries:
            row = [entry["symbol"]]
            row.extend(values.get((entry["short_name"], class_entry["short_name"]), "") for class_entry in classes)
            lines.extend([" & ".join(row) + "\\\\", "\\hline"])
    lines.extend(["\\end{longtable}", "\\end{center}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--mapping", type=Path, default=Path(__file__).with_name("latex_mapping.json")
    )
    parser.add_argument(
        "--section",
        choices=["parameter-table", "value-table"],
        default="parameter-table",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if OUTPUT is absent or differs, without modifying it",
    )
    args = parser.parse_args()

    mapping = json.loads(args.mapping.read_text())
    generators = {
        "parameter-table": generate_parameter_table,
        "value-table": generate_value_table,
    }
    output = generators[args.section](args.data_dir, mapping)
    if args.check:
        if not args.output.is_file() or args.output.read_text() != output:
            print(f"Generated LaTeX is out of date: {args.output}")
            return 1
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
