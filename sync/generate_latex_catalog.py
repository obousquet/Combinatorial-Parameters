#!/usr/bin/env python3
"""Generate database-owned LaTeX catalogue sections.

The structured records in ``data/parameters`` and ``data/classes`` are the
single editable source of catalogue definitions.  Generated LaTeX is never an
independent source.
"""

from __future__ import annotations

import argparse
import json
import re
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


def class_definition_label(entry: dict, mapping: dict) -> str:
    config = mapping["classes"]
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
        return "?"
    return "Y" if value else "N"


def generate_parameter_table(data_dir: Path, mapping: dict) -> str:
    lines = [
        "% GENERATED from data/parameters by sync/generate_latex_catalog.py; do not edit.",
        "\\begin{center}",
        "\\begin{longtable}{|p{0.9in}|p{1.95in}|l|c|c|c|c|c|c|c|c|}",
        "\\caption{List of Combinatorial Parameters}\\\\",
        "\\hline",
        "Symbol & Name & Def & $P^\\dagger$ & $P^*$ & $P^p$ & $P^c$ & $P^{p*}$ & Str & $\\mathrm{Str}_c$ & $\\mathrm{TStr}_c$\\\\",
        "\\multicolumn{11}{|l|}{Y = established; N = known failure; ? = not yet classified.}\\\\",
        "\\hline",
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
                "\\multicolumn{9}{|l|}{Section \\ref{sec:" + category_name + "}}\\\\",
                "\\hline",
            ]
        )
        for entry in category_entries:
            lines.extend(
                [
                    "\\cellcolor{" + colour(entry) + "} " + math_mode(entry["symbol"])
                    + " & " + entry["name"]
                    + " & \\ref{" + definition_label(entry, mapping) + "}"
                    + " & " + marker(entry.get("symmetric"))
                    + " & " + marker(entry.get("monotonic"))
                    + " & " + marker(entry.get("p_monotonic"))
                    + " & " + marker(entry.get("c_monotonic"))
                    + " & " + marker(entry.get("doubly_monotonic"))
                    + " & " + marker(entry.get("strictly_monotonic"))
                    + " & " + marker(entry.get("strict_c_monotonic"))
                    + " & " + marker(entry.get("tight_strict_c_monotonic"))
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


def escape_path_underscores(text: str) -> str:
    """Escape underscores in prose paths without disturbing inline math.

    Value records sometimes cite their accompanying verification checker, for
    example ``sync/verify_positive_teaching_triangle.py``.  Underscores are
    illegal in ordinary LaTeX text, while the proof normalizer below has a
    separate legacy convention for bare mathematical subscripts.  Treating
    slash-containing tokens as paths first preserves both conventions.
    """
    parts = text.split("$")
    path = re.compile(r"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")
    for index in range(0, len(parts), 2):
        parts[index] = path.sub(lambda match: match.group(0).replace("_", r"\_"), parts[index])
    return "$".join(parts)


def normalize_proof_latex(text: str) -> str:
    """Put legacy bare exponent expressions into inline math mode.

    Value proofs are LaTeX-aware prose.  A few older entries nevertheless use
    plain-text notation such as ``2^n``.  Split around existing dollar-delimited
    math before normalizing, so a correct expression like ``$n=2^d$`` is never
    altered.
    """
    # Preserve both of the TeX conventions already used by database records.
    # In particular, do not mistake the subscript in ``\(\mathcal U_n\)``
    # for a legacy bare-text expression.
    parts = re.split(
        r"(\$\$.*?\$\$|\$[^$]*\$|\\\(.*?\\\)|\\\[.*?\\\])",
        escape_path_underscores(text),
        flags=re.S,
    )
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(
            r"(?<![\\w\\\\])([A-Za-z0-9]+\^[A-Za-z0-9]+)", r"$\1$", parts[index]
        )
        parts[index] = re.sub(
            r"(?<![\\w\\\\])([A-Za-z]+_[A-Za-z0-9]+)", r"$\1$", parts[index]
        )
    return "".join(parts)


def definition_latex(text: str) -> str:
    """Render the database's Markdown-plus-TeX definition text in LaTeX.

    Definitions deliberately use the same lightweight format rendered by the
    website: inline math is dollar-delimited, display math uses ``$$...$$``,
    and bold names are Markdown emphasis.  Keeping that source format avoids
    a second hand-maintained TeX definition catalogue.
    """
    # A bold span may legitimately contain inline TeX, e.g.
    # ``**compression scheme of size $k$**``.  Convert that form before
    # splitting prose from math.  Single-star emphasis remains below so TeX
    # syntax such as ``$H^*$`` is insulated from Markdown processing.
    text = re.sub(r"\*\*(.+?)\*\*", r"\\emph{\1}", text, flags=re.S)
    parts = re.split(r"(\$\$.*?\$\$|\$[^$]*\$)", text, flags=re.S)
    for index in range(0, len(parts), 2):
        # Markdown belongs only to prose.  In particular, a TeX superscript
        # such as H^* must never be mistaken for Markdown emphasis.
        parts[index] = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\\emph{\1}", parts[index])
    text = "".join(parts)
    pieces = text.split("$$")
    rendered: list[str] = []
    for index, piece in enumerate(pieces):
        if index % 2:
            rendered.extend(["\\[", piece.strip(), "\\]"])
        else:
            rendered.append(piece.strip())
    return "\n".join(piece for piece in rendered if piece)


def generate_parameter_definitions(data_dir: Path, mapping: dict) -> str:
    """Generate every parameter definition from its structured record."""
    entries = records(data_dir, "parameters")
    placeholders = {int(identifier) for identifier in mapping["parameters"].get("unmapped_database_ids", {})}
    lines = [
        "% GENERATED from data/parameters by sync/generate_latex_catalog.py; do not edit.",
        "% The definition field is the sole authoritative catalogue definition.",
        "\\subsection{Conventions}",
        "All classes below are binary concept classes $\\mathcal H\\subseteq2^{\\mathcal X}$: a concept is identified with its positive set.  For $S\\subseteq\\mathcal X$, its coordinate projection is $\\mathcal H_{|S}=\\{h\\cap S:h\\in\\mathcal H\\}$.  For a labeling $y:S\\to\\{0,1\\}$, the conditioned class $\\mathcal H_{S=y}$ consists of concepts agreeing with $y$ on $S$, restricted to the remaining coordinates.  A set $S$ is \\emph{shattered} precisely when $\\mathcal H_{|S}=2^S$.  The one-inclusion graph has vertex set $\\mathcal H$ and an edge between two concepts whose symmetric difference has cardinality one.  A teaching set for $h\\in\\mathcal H$ is a labeled set of coordinates on which no other concept in $\\mathcal H$ agrees with $h$.",
        "",
    ]
    for category, category_name in CATEGORY_NAMES.items():
        category_entries = [
            entry for entry in entries
            if entry.get("category") == category and entry["id"] not in placeholders
        ]
        if not category_entries:
            continue
        lines.extend(["\\subsection{" + category_name + "}\\label{sec:" + category_name + "}", ""])
        for entry in category_entries:
            lines.extend(
                [
                    "\\subsubsection{" + entry["name"] + "}",
                    "\\begin{definition}[" + entry["name"] + " - {"
                    + math_mode(entry["symbol"]) + "}]\\label{"
                    + definition_label(entry, mapping) + "}",
                    definition_latex(entry.get("definition", "")) or "Definition pending.",
                    "\\end{definition}",
                    "",
                ]
            )
    return "\n".join(lines)


def generate_class_definitions(data_dir: Path, mapping: dict) -> str:
    """Generate every class definition from its structured record."""
    lines = [
        "% GENERATED from data/classes by sync/generate_latex_catalog.py; do not edit.",
        "% The definition field is the sole authoritative catalogue definition.",
        "",
    ]
    for entry in records(data_dir, "classes"):
        lines.extend(
            [
                "\\subsection{" + entry["name"] + "}\\label{"
                + class_definition_label(entry, mapping) + "}",
                "\\begin{definition}[" + entry["name"] + " - {"
                + math_mode(entry["symbol"]) + "}]",
                definition_latex(entry.get("definition", "")) or "Definition pending.",
                "\\end{definition}",
                "",
            ]
        )
    return "\n".join(lines)


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
            row = [math_mode(entry["symbol"])]
            row.extend(values.get((entry["short_name"], class_entry["short_name"]), "") for class_entry in classes)
            lines.extend([" & ".join(row) + "\\\\", "\\hline"])
    lines.extend(["\\end{longtable}", "\\end{center}", ""])
    return "\n".join(lines)


def generate_value_proofs(data_dir: Path) -> str:
    """Generate the survey appendix containing the database-owned value proofs.

    A value record remains the single editable source for its statement and
    concise derivation.  The survey imports this appendix verbatim so a reader
    of either representation reaches the same proof.
    """
    parameters = {
        entry["short_name"]: entry
        for entry in records(data_dir, "parameters")
        if entry.get("short_name")
    }
    classes = {
        entry["short_name"]: entry
        for entry in records(data_dir, "classes")
        if entry.get("short_name")
    }
    entries = [entry for entry in records(data_dir, "values") if entry.get("proof")]
    lines = [
        "% GENERATED from data/values by sync/generate_latex_catalog.py; do not edit.",
        "\\section{Proofs of catalogue values}\\label{app:value-proofs}",
        "Each statement and proof in this appendix is generated from the structured database value record; the database is the editable source of truth.",
        "",
    ]
    for entry in entries:
        parameter = parameters[reference_short_name(entry["parameter_id"])]
        class_record = classes[reference_short_name(entry["class_id"])]
        value = entry.get("value", "")
        title = entry.get("name") or parameter["name"] + " of " + class_record["name"]
        label = entry.get("short_name") or "value-" + str(entry["id"])
        lines.extend(
            [
                "\\subsection{" + title + "}\\label{val:" + label + "}",
                "\\noindent\\textbf{Statement.} The " + parameter["name"]
                + " of " + class_record["name"] + " is " + value + ".",
                "\\begin{proof}",
                normalize_proof_latex(entry["proof"]),
                "\\end{proof}",
            ]
        )
        if entry.get("references"):
            lines.append(
                "\\noindent\\textbf{Reference.} "
                + escape_path_underscores(entry["references"])
                + "."
            )
        lines.append("")
    return "\n".join(lines)


SOURCE_ASSETS = {"bibliography": "references.bib"}


def generate_source_asset(data_dir: Path, section: str) -> str:
    """Return a database-owned LaTeX source asset verbatim.

    Bibliography data remains an intentionally bibliographic source asset.
    """
    source = data_dir / "latex" / SOURCE_ASSETS[section]
    return source.read_text()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--mapping", type=Path, default=Path(__file__).with_name("latex_mapping.json")
    )
    parser.add_argument(
        "--section",
        choices=[
            "parameter-table", "value-table", "value-proofs",
            "parameter-definitions", "class-definitions", *SOURCE_ASSETS,
        ],
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
        "value-proofs": lambda data_dir, _mapping: generate_value_proofs(data_dir),
        "parameter-definitions": generate_parameter_definitions,
        "class-definitions": generate_class_definitions,
    }
    if args.section in SOURCE_ASSETS:
        output = generate_source_asset(args.data_dir, args.section)
    else:
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
