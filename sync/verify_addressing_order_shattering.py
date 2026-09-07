#!/usr/bin/env python3
"""Verify Addressing counts, encoding scope, hitting sets and bit-first shifts.

The database owns individual value proofs; the survey owns the encoding
counterexamples. These small exact checks do not classify arbitrary codes.
"""

import json
from itertools import combinations
from pathlib import Path


def addressing(concept_count: int) -> tuple[frozenset[int], int]:
    bit_count = (concept_count - 1).bit_length()
    concepts = []
    for index in range(concept_count):
        code = sum(((index >> bit) & 1) << (concept_count + bit) for bit in range(bit_count))
        concepts.append((1 << index) | code)
    return frozenset(concepts), bit_count


def downshift(concepts: frozenset[int], coordinate: int) -> frozenset[int]:
    shifted = set(concepts)
    for concept in concepts:
        lowered = concept ^ (1 << coordinate)
        if concept & (1 << coordinate) and lowered not in shifted:
            shifted.remove(concept)
            shifted.add(lowered)
    return frozenset(shifted)


def bit_first_order_shattering_dimension(concept_count: int) -> int:
    concepts, bit_count = addressing(concept_count)
    for coordinate in range(concept_count, concept_count + bit_count):
        concepts = downshift(concepts, coordinate)
    for coordinate in range(concept_count):
        concepts = downshift(concepts, coordinate)
    return max(concept.bit_count() for concept in concepts)


def encoded(codes: tuple[int, ...]) -> frozenset[int]:
    return frozenset((1 << i) | (code << len(codes)) for i, code in enumerate(codes))


def vc(concepts: frozenset[int], domain: int) -> int:
    for k in range(len(concepts).bit_length()-1, -1, -1):
        for coordinates in combinations(range(domain), k):
            mask = sum(1 << j for j in coordinates)
            if len({h & mask for h in concepts}) == 1 << k:
                return k
    raise AssertionError("The empty coordinate set is shattered")


def hitting(concepts: frozenset[int], domain: int) -> int:
    for k in range(domain+1):
        for coordinates in combinations(range(domain), k):
            mask = sum(1 << j for j in coordinates)
            if all(h & mask for h in concepts):
                return k
    raise AssertionError("Every concept here is nonempty")


def code_hitting(codes: tuple[int, ...], bits: int) -> int:
    return min(mask.bit_count() + sum(code & mask == 0 for code in codes)
               for mask in range(1 << bits))


def verify_conventions() -> None:
    for n in range(1, 17):
        concepts, r = addressing(n)
        assert len(concepts) == n
        assert encoded(tuple(range(n))) == concepts
        active = sum(len({(h >> j) & 1 for h in concepts}) == 2 for j in range(n+r))
        assert active == (n+r if n >= 2 else 0)
        # Querying the r bits gives distinct answers; fewer binary answers
        # cannot distinguish n targets. Explicitly check that counting bound.
        assert len({h >> n for h in concepts}) == n
        assert (r == 0 and n == 1) or (1 << (r-1)) < n <= (1 << r)
        # Actual all-coordinate distinguishing-set optimization, not just bits.
        distinguishing = None
        for k in range(r+1):
            if any(len({h & sum(1 << j for j in coordinates) for h in concepts}) == n
                   for coordinates in combinations(range(n+r), k)):
                distinguishing = k
                break
        assert distinguishing == r
        # The absent all-zero private trace and its n one-flip neighbours.
        assert {h & ((1 << n)-1) for h in concepts} == {1 << i for i in range(n)}
    for r in range(4):
        codes = tuple(range(1 << r))
        assert hitting(encoded(codes), len(codes)+r) == code_hitting(codes, r) == r+1
    canonical = tuple(range(11))
    low_weight = tuple(code for code in range(16) if code.bit_count() <= 2)
    two_bits_hit = tuple(code for code in range(16) if code & 3)[:11]
    assert len(low_weight) == len(two_bits_hit) == 11
    assert vc(encoded(canonical), 15) == 3
    assert vc(encoded(low_weight), 15) == 2
    assert hitting(encoded(canonical), 15) == code_hitting(canonical, 4) == 5
    assert hitting(encoded(two_bits_hit), 15) == code_hitting(two_bits_hit, 4) == 2

    data = Path(__file__).resolve().parents[1] / "data"
    records = {r["id"]: r for p in (data / "values").glob("*addressing.json")
               if (r := json.loads(p.read_text()))["class_id"] == "#classes/addressing"}
    expected = {
        68: "$n$", 119: r"$\log_2 n$", 21: "$n$", 529: "$n-1$",
        322: r"$\lceil\log_2 n\rceil$", 337: r"$\lceil\log_2 n\rceil$",
        319: r"$\log_2n+1\quad(n=2^r)$",
    }
    for key, value in expected.items():
        assert records[key]["value"] == value
    assert records[319]["value_class"] == "omega_log_n"
    scoped = (100, 101, 229, 244, 305, 561, 580, 582, 679, 689, 732, 758, 759, 763, 771, 127, 1010)
    for key in scoped:
        assert "n=2^r" in records[key]["value"] and "Scope:" in records[key]["details"]
    nontrivial = (6, 291, 351, 359, 361, 369, 376, 379, 382,
                  490, 491, 492, 590, 694, 892, 998, 1009)
    for key in nontrivial:
        assert records[key]["value"] == r"$1\quad(n\ge2)$"
    relation = json.loads((data / "relationships/424_hitting_size_log_size_ratio_incomparable.json").read_text())
    assert "$r+1$" in relation["parameter_1_larger_witness"]
    print("Addressing conventions: 16 count/range/distinguishing checks, four exact full-code "
          "hitting optimizations; n=11 encodings give VC 3/2 and hitting size 5/2.")
    print("Seven corrected-value guards, seventeen complete-code and seventeen nontrivial scope guards, "
          "and the repaired incomparability witness passed.")


def main() -> None:
    for concept_count in range(2, 33):
        assert bit_first_order_shattering_dimension(concept_count) == 1
    print("Addressing: bit-first downshifting gives OSH_min = 1")
    verify_conventions()


if __name__ == "__main__":
    main()
