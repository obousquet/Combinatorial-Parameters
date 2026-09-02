#!/usr/bin/env python3
"""Backfill only definitional monotonicity-evidence entries.

This does not claim a foundational property.  It records consequences of
already declared properties so the evidence audit can distinguish those from
facts that still need a direct proof or citation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RULES = {
    "doubly_monotonic": (
        ("monotonic", "p_monotonic"),
        "By definition, being monotonic under both subfamilies and projections is doubly monotonic.",
    ),
    "c_monotonic": (
        ("doubly_monotonic",),
        "A conditioning is restriction to a subfamily followed by a projection; hence doubly monotonicity implies c-monotonicity.",
    ),
    "strict_c_monotonic": (
        ("strictly_monotonic",),
        "By definition, strictly monotonic means doubly monotonic and strictly c-monotonic.",
    ),
    "strictly_monotonic": (
        ("doubly_monotonic", "strict_c_monotonic"),
        "By definition, a doubly monotonic strictly c-monotonic parameter is strictly monotonic.",
    ),
}

NEGATIVE_RULES = {
    "doubly_monotonic": (
        ("monotonic", "p_monotonic"),
        "By definition, doubly monotonicity requires both subfamily monotonicity and projection monotonicity; the recorded failure of one of them rules it out.",
    ),
    "strict_c_monotonic": (
        ("c_monotonic",),
        "Strict c-monotonicity includes c-monotonicity, so the recorded failure of c-monotonicity rules it out.",
    ),
    "tight_strict_c_monotonic": (
        ("strict_c_monotonic",),
        "Tight strict c-monotonicity includes strict c-monotonicity, so the recorded failure of the latter rules it out.",
    ),
    "strictly_monotonic": (
        ("doubly_monotonic", "strict_c_monotonic"),
        "By definition, strictly monotonicity requires both doubly monotonicity and strict c-monotonicity; the recorded failure of one of them rules it out.",
    ),
}

# These are direct arguments for classifications made in the catalogue.  They
# deliberately live next to the mechanical definitional rules so the audit can
# distinguish a proved classification from an unlabelled Boolean.
DIRECT_EVIDENCE = {
    ("effective_range", "monotonic"): "Adding concepts cannot make a previously varying coordinate constant.",
    ("effective_range", "p_monotonic"): "Projection deletes coordinates and can only discard varying coordinates, never create one.",
    ("size", "monotonic"): "A subfamily has no more concepts than its containing class.",
    ("size", "p_monotonic"): "Projection maps concepts to concepts and may identify them, so its image has no larger cardinality.",
    ("oriented_diameter", "monotonic"): "Every oriented-diameter witness in a subfamily is also a witness in the containing class.",
    ("oriented_diameter", "p_monotonic"): "Projecting an oriented-diameter witness only deletes coordinates, so it cannot increase its length.",
    ("diameter", "monotonic"): "Every pair of concepts in a subfamily remains a pair in the containing class.",
    ("diameter", "p_monotonic"): "Deleting coordinates cannot increase Hamming distance between two concepts.",
    ("hamming_radius", "monotonic"): "Every Hamming ball containing a class also contains each of its subfamilies.",
    ("hamming_radius", "p_monotonic"): "Projecting a containing Hamming ball gives a ball of no greater radius containing the projected class.",
    ("threshold_dimension", "monotonic"): "A threshold witness contained in a subfamily remains contained in the larger class.",
    ("threshold_dimension", "p_monotonic"): "A threshold witness in a projection is already realized by the original class on those coordinates.",
    ("path_dimension", "monotonic"): "A path witness contained in a subfamily remains contained in the larger class.",
    ("path_dimension", "p_monotonic"): "A path witness in a projection is already realized by the original class on those coordinates.",
    ("log_shattering", "monotonic"): "Adding concepts can only add shattered sets.",
    ("log_shattering", "p_monotonic"): "Every set shattered by a projection is shattered by the original class on the same coordinates.",
    ("vc_dimension", "monotonic"): "Every set shattered by a subfamily is also shattered by the containing class.",
    ("vc_dimension", "p_monotonic"): "Every set shattered by a projection is shattered by the original class on the same coordinates.",
    ("yang_dimension", "p_monotonic"): "Yang proves that restricting the domain (projection) cannot increase the projective dimension of the canonical ideal.",
    ("unlabeled_sample_compression", "monotonic"): "Restricting a compression scheme to a subfamily preserves its size and reconstruction guarantee.",
    ("unlabeled_sample_compression", "p_monotonic"): "Projecting a compression scheme and deleting projected-away coordinates preserves its size and reconstruction guarantee.",
    ("littlestone_dimension", "monotonic"): "Every shattered Littlestone tree for a subfamily is also shattered by the containing class.",
    ("littlestone_dimension", "p_monotonic"): "Every shattered Littlestone tree for a projection is realized by the original class on the same queried coordinates.",
    ("littlestone_dimension", "tight_strict_c_monotonic"): "The defining Littlestone recurrence takes the larger branch value when branches differ and one plus their common value when they agree.",
    ("star_number", "monotonic"): "Every star contained in a subfamily remains a star in the containing class.",
    ("star_number", "p_monotonic"): "A star in a projection is realized by the original class on its star coordinates.",
    ("densest_subgraph_twice", "c_monotonic"): "Conditioning gives an induced subgraph of the one-inclusion graph.  The maximum subgraph density cannot increase on an induced subgraph.",
    ("double_density_or_average_degree", "c_monotonic"): "Counterexample: H={000,001,110} has average degree 2/3, while conditioning its first coordinate to 0 leaves an edge of average degree 1.",
    ("minimum_degree", "c_monotonic"): "Counterexample: H={000,001,110} has an isolated vertex and hence minimum degree 0, while conditioning its first coordinate to 0 leaves an edge of minimum degree 1.",
    ("effective_vc_radius", "c_monotonic"): "Counterexample: H={000,001,010,100,110} has effective VC radius 1; conditioning its last coordinate to 0 gives the full two-cube, of effective VC radius 2.",
    ("interpolation_degree", "c_monotonic"): "Restrict an interpolating basis to the conditioned fibre and substitute the fixed coordinates.  This cannot increase the degree needed to interpolate functions on that fibre.",
    ("recursive_teaching_dimension", "c_monotonic"): "Restrict a recursive teaching order to the conditioned fibre and delete its fixed coordinates from each teaching set.  Every remaining batch still has no larger teaching sets.",
    ("teaching_dimension", "c_monotonic"): "For each target in the conditioned fibre, delete fixed coordinates from a teaching set in the original class.  It remains a teaching set in the fibre.",
    ("hitting_size", "c_monotonic"): "Counterexample: for H={{x,a},{x,b}}, {x} is a hitting set, whereas conditioning x=1 gives {{a},{b}}, whose hitting size is 2.",
    ("relative_hitting_size", "c_monotonic"): "This is equal to maximum teaching-set size; the latter is c-monotonic by restricting each teaching set to the unfixed coordinates.",
    ("membership_query_complexity", "c_monotonic"): "A membership-query learner for the original class learns a conditioned fibre by answering every query on a fixed coordinate for free and simulating all other queries.",
    ("worst_mistakes", "c_monotonic"): "A mistake-bound learner for the original class restricts to a conditioned fibre by answering fixed-coordinate predictions for free; its mistake bound cannot increase.",
    ("best_mistakes", "c_monotonic"): "Restrict an optimal prediction strategy to the conditioned fibre, treating fixed-coordinate labels as known; no additional mistakes are needed.",
    ("partial_equivalence_queries_complexity", "c_monotonic"): "Simulate a learner for the original class, extending each fibre hypothesis with the fixed labels.  Partial-equivalence answers restrict back to valid answers on the fibre.",
    ("selfdirected_queries_complexity", "c_monotonic"): "A self-directed strategy for the original class restricts to the fibre after removing fixed coordinates, so its worst-case query count cannot increase.",
    ("proper_stable_sample_compression", "c_monotonic"): "For a conditioned sample, append the fixed labeled coordinates, compress in the original class, and delete fixed coordinates from the compressed set.  Reconstruction restricted to the fibre remains proper and stable.",
    ("proper_unlabeled_sample_compression", "c_monotonic"): "For a conditioned sample, append the fixed labeled coordinates, compress in the original class, and delete fixed coordinates from the compressed set; restriction of reconstruction remains proper.",
    ("proper_labeled_sample_compression", "c_monotonic"): "For a conditioned sample, append the fixed labeled coordinates, apply the original proper compression scheme, and restrict the reconstruction back to the fibre.",
    ("proper_stable_labeled_sample_compression", "c_monotonic"): "The standard restriction of a proper stable labeled compression scheme to a conditioned fibre preserves its size, propriety, and stability.",
    ("covc_dimension", "c_monotonic"): "A hollow star in a conditioned fibre can be lifted by adjoining the fixed labels.  It is then a hollow star in the original class, so conditioning cannot increase co-VC dimension.",
    ("positive_teaching_dimension", "c_monotonic"): "Restrict a positive teaching set to unfixed coordinates.  It is still positive and distinguishes the target inside the conditioned fibre.",
    ("preferencebased_teaching_dimension", "c_monotonic"): "Restrict the preference order and the teaching map to the conditioned fibre, deleting fixed coordinates from samples; the teaching guarantee is preserved.",
    ("noclashing_teaching_dimension", "c_monotonic"): "Restrict a no-clashing teacher mapping to the conditioned fibre and delete fixed coordinates.  A clash in the fibre would already be a clash in the original class.",
    ("maximum_teaching_set_size", "c_monotonic"): "Restrict every target's teaching set to the unfixed coordinates.  The restricted sample still distinguishes the target within the conditioned fibre.",
    ("monotonic_minimum_teaching_set_size", "c_monotonic"): "It is the maximum over subfamilies of minimum teaching-set size.  Conditioning a subfamily is a subfamily of the conditioned fibre, and restricting teaching sets cannot increase their sizes.",
    ("proper_ordered_sample_compression", "c_monotonic"): "Restriction to a conditioned fibre commutes with an ordered proper compression scheme after fixed coordinates are removed from its sample and reconstruction.",
    ("largest_strongly_shattered_set", "c_monotonic"): "A cube contained in a conditioned fibre lifts to a cube in the original class by adjoining the fixed labels, so its dimension cannot increase.",
    ("degeneracy", "c_monotonic"): "Conditioning gives an induced subgraph of the one-inclusion graph, and graph degeneracy cannot increase under induced subgraphs.",
    ("maximum_degree", "c_monotonic"): "Conditioning gives an induced subgraph of the one-inclusion graph, so maximum degree cannot increase.",
    ("maximum_positive_degree", "c_monotonic"): "After fixing the conditioned labels, the oriented one-inclusion graph of the fibre is an induced oriented subgraph, so maximum positive degree cannot increase.",
    ("positive_noclashing_teaching_dimension", "c_monotonic"): "Restrict a positive no-clashing teacher mapping to the conditioned fibre and delete fixed coordinates.  Positivity and no-clashing are preserved.",
    ("distinguishing_range", "c_monotonic"): "A coordinate set distinguishing a target in the original class remains distinguishing in a conditioned fibre after fixed coordinates are deleted.",
    ("positive_recursive_teaching_dimension", "c_monotonic"): "Restrict a positive recursive teaching order to the conditioned fibre and delete fixed coordinates from its positive teaching sets.",
    ("minimum_teaching_set_size", "c_monotonic"): "Counterexample: H={000,001,010,100,110} has minimum teaching-set size 1; conditioning its last coordinate to 0 gives the full two-cube, whose minimum teaching-set size is 2.",
    ("extended_teaching_dimension", "c_monotonic"): "For any target labeling on a conditioned fibre, extend it with the fixed labels.  A specifying set in the original class may discard fixed coordinates and still specifies the target in the fibre; hence XTD is c-monotonic.",
    ("monotonic_yang_dimension", "monotonic"): "This is immediate from Y*(H)=max_{G subseteq H} Y(G): every subfamily of a subfamily of H is also a subfamily of H.",
    ("monotonic_yang_dimension", "p_monotonic"): "For a projection pi(H), every subfamily is the projection of a subfamily of H.  Yang dimension is projection-monotonic, so taking maxima over subfamilies preserves the bound.",
}


FLAGS = (
    "monotonic",
    "p_monotonic",
    "c_monotonic",
    "doubly_monotonic",
    "strict_c_monotonic",
    "tight_strict_c_monotonic",
    "strictly_monotonic",
)


def transfer_equality_evidence(data_dir: Path, *, write: bool, changed: list[str]) -> None:
    """Copy per-property provenance through established exact equalities.

    Exact equality identifies the two parameter functions, so it transfers a
    proved monotonicity classification.  This records the transfer explicitly
    rather than leaving one spelling of the same parameter as an audit gap.
    """
    paths = sorted((data_dir / "parameters").glob("[0-9]*.json"))
    entries = {entry["short_name"]: (path, entry) for path in paths for entry in [json.loads(path.read_text())]}
    equalities: list[tuple[str, str, str]] = []
    for path in sorted((data_dir / "relationships").glob("[0-9]*.json")):
        relationship = json.loads(path.read_text())
        if relationship.get("relationship_type") != "equivalence":
            continue
        if relationship.get("status", "established") != "established":
            continue
        left = relationship["parameter_1_id"].rsplit("/", 1)[-1]
        right = relationship["parameter_2_id"].rsplit("/", 1)[-1]
        equalities.append((left, right, relationship["short_name"]))

    touched: set[str] = set()
    while True:
        progress = False
        for left, right, equality_name in equalities:
            for target, source in ((left, right), (right, left)):
                target_entry = entries[target][1]
                source_entry = entries[source][1]
                target_evidence = target_entry.setdefault("monotonicity_evidence", {})
                source_evidence = source_entry.get("monotonicity_evidence", {})
                for flag in FLAGS:
                    if target_entry.get(flag) is None or target_evidence.get(flag):
                        continue
                    if target_entry.get(flag) != source_entry.get(flag):
                        continue
                    source_fact = source_evidence.get(flag, {})
                    if not any(source_fact.get(key) for key in ("proof", "latex_proof_label", "references")):
                        continue
                    target_evidence[flag] = {
                        "proof": (
                            f"This parameter is exactly equal to {source_entry['name']} "
                            f"by the established relationship `{equality_name}`; its "
                            f"{flag.replace('_', ' ')} classification transfers unchanged."
                        ),
                        "kind": "equality_transfer",
                    }
                    changed.append(f"{target}: {flag} (equality transfer from {source})")
                    touched.add(target)
                    progress = True
        if not progress:
            break

    if write:
        for short_name in touched:
            path, entry = entries[short_name]
            path.write_text(json.dumps(entry, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    changed: list[str] = []
    for path in sorted((args.data_dir / "parameters").glob("[0-9]*.json")):
        entry = json.loads(path.read_text())
        evidence = entry.setdefault("monotonicity_evidence", {})
        for flag, (premises, proof) in RULES.items():
            if entry.get(flag) is not True or flag in evidence:
                continue
            if all(entry.get(premise) is True for premise in premises):
                evidence[flag] = {"proof": proof, "kind": "definitional_consequence"}
                changed.append(f"{entry['short_name']}: {flag}")
        for flag, (premises, proof) in NEGATIVE_RULES.items():
            if entry.get(flag) is not False or flag in evidence:
                continue
            if any(entry.get(premise) is False for premise in premises):
                evidence[flag] = {"proof": proof, "kind": "definitional_consequence"}
                changed.append(f"{entry['short_name']}: {flag}")
        for (short_name, flag), proof in DIRECT_EVIDENCE.items():
            if entry["short_name"] != short_name or entry.get(flag) is None or flag in evidence:
                continue
            evidence[flag] = {"proof": proof, "kind": "direct_argument"}
            changed.append(f"{entry['short_name']}: {flag}")
        if args.write and any(item.startswith(entry["short_name"] + ":") for item in changed):
            path.write_text(json.dumps(entry, indent=2) + "\n")

    transfer_equality_evidence(args.data_dir, write=args.write, changed=changed)

    print(f"Monotonicity evidence entries added: {len(changed)}")
    for item in changed:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
