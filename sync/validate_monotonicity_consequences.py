#!/usr/bin/env python3
"""Check direct inequalities forced by registered monotonicity constructions.

For ``B^*(H)=max_{G subseteq H} B(G)``, every recorded inequality
``A >= B`` yields ``A >= B^*`` when ``A`` is monotonic under subfamilies.
This checker deliberately considers only direct established records and never
uses transitive graph reachability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SUPPORTED_TYPES = {"larger", "larger_c", "log", "sqrt", "inv_log"}


def load_records(directory: Path) -> list[dict]:
    return [json.loads(path.read_text()) for path in sorted(directory.glob("[0-9]*.json"))]


def short(reference: str) -> str:
    return reference.rsplit("/", 1)[-1]


def write_consequences(
    relationships_dir: Path, missing: list[tuple[dict, dict, dict]]
) -> None:
    """Materialize proof-carrying direct consequences approved by this checker."""
    used_ids = [entry["id"] for entry in load_records(relationships_dir)]
    next_id = max(used_ids, default=0) + 1
    for source, construction, consequence in missing:
        upper = consequence["parameter_1_id"]
        derived = consequence["parameter_2_id"]
        upper_short, base_short, derived_short = (
            short(upper),
            short(construction["base_parameter_id"]),
            short(derived),
        )
        record = {
            "id": next_id,
            "parameter_1_id": upper,
            "parameter_2_id": derived,
            "relationship_type": consequence["relationship_type"],
            "details": "Consequence of the registered max-over-subfamilies construction.",
            "status": "established",
            "proof": (
                f"For every subfamily $\\mathcal G\\subseteq\\mathcal H$, "
                f"the direct relationship {source['short_name']} bounds "
                f"{base_short} on $\\mathcal G$ by {upper_short} on "
                "$\\mathcal G$.  Monotonicity of the upper parameter gives "
                "the same bound by its value on $\\mathcal H$; taking the "
                "maximum over $\\mathcal G$ proves the displayed consequence."
            ),
            "derivation": f"max_subfamilies from #relationships/{source['short_name']}",
            "short_name": f"{upper_short}_{derived_short}",
            "name": f"{upper_short} / {derived_short}",
        }
        if source.get("references"):
            record["references"] = source["references"]
        path = relationships_dir / f"{next_id:03d}_{record['short_name']}.json"
        path.write_text(json.dumps(record, indent=2) + "\n")
        print(f"Materialized {path}")
        next_id += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--constructions", type=Path, default=Path("sync/monotonicity_constructions.json"))
    parser.add_argument("--check", action="store_true", help="fail when a forced direct consequence is absent")
    parser.add_argument("--write", action="store_true", help="materialize missing proof-carrying consequences")
    args = parser.parse_args()

    parameters = {entry["short_name"]: entry for entry in load_records(args.data_dir / "parameters")}
    relationships = load_records(args.data_dir / "relationships")
    recorded = {
        (entry["parameter_1_id"], entry["parameter_2_id"], entry["relationship_type"])
        for entry in relationships
        if entry.get("status", "established") == "established"
    }
    constructions = json.loads(args.constructions.read_text())["constructions"]
    missing: list[tuple[dict, dict, dict]] = []

    for construction in constructions:
        if construction["operation"] != "max_subfamilies":
            continue
        base = construction["base_parameter_id"]
        derived = construction["derived_parameter_id"]
        for relationship in relationships:
            if relationship.get("status", "established") != "established":
                continue
            if relationship.get("relationship_type") not in SUPPORTED_TYPES:
                continue
            if relationship["parameter_2_id"] != base:
                continue
            upper = relationship["parameter_1_id"]
            if upper == derived:
                continue  # The construction already includes the original class.
            if not parameters[short(upper)].get("monotonic"):
                continue
            consequence = (upper, derived, relationship["relationship_type"])
            if consequence not in recorded:
                missing.append((relationship, construction, {
                    "parameter_1_id": upper,
                    "parameter_2_id": derived,
                    "relationship_type": relationship["relationship_type"],
                }))

    if missing:
        if args.write:
            write_consequences(args.data_dir / "relationships", missing)
            return 0
        print("Missing direct monotonicity-construction consequences:")
        for source, _construction, consequence in missing:
            print(
                f"- {short(consequence['parameter_1_id'])} "
                f"{consequence['relationship_type']} {short(consequence['parameter_2_id'])} "
                f"(from {source['short_name']})"
            )
        return 1 if args.check else 0
    print("All registered direct monotonicity-construction consequences are recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
