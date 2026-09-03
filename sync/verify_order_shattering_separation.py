#!/usr/bin/env python3
"""Verify a strict separation between minimum order shattering and VCR."""

from __future__ import annotations

from itertools import combinations, permutations


CLASS = ("000", "001", "010", "011", "100")


def projection(concepts: set[str], coordinates: tuple[int, ...]) -> set[str]:
    return {"".join(concept[index] for index in coordinates) for concept in concepts}


def effective_vc_radius(concepts: set[str]) -> int:
    """Compute the all-effective-subsets shattering radius."""
    effective = tuple(
        index for index in range(len(next(iter(concepts))))
        if len({concept[index] for concept in concepts}) == 2
    )
    return max(
        size
        for size in range(len(effective) + 1)
        if all(
            len(projection(concepts, coordinates)) == 2**size
            for coordinates in combinations(effective, size)
        )
    )


def downshift(concepts: set[str], coordinate: int) -> set[str]:
    """Apply one standard binary downshift."""
    shifted = set(concepts)
    for concept in tuple(concepts):
        if concept[coordinate] == "1":
            lowered = concept[:coordinate] + "0" + concept[coordinate + 1:]
            if lowered not in shifted:
                shifted.remove(concept)
                shifted.add(lowered)
    return shifted


def minimum_order_shattered_dimension(concepts: set[str]) -> int:
    """Minimize the largest downshifted face over all coordinate orders."""
    dimensions = []
    for order in permutations(range(len(next(iter(concepts))))):
        shifted = set(concepts)
        for coordinate in order:
            shifted = downshift(shifted, coordinate)
        dimensions.append(max(concept.count("1") for concept in shifted))
    return min(dimensions)


def main() -> None:
    concepts = set(CLASS)
    assert effective_vc_radius(concepts) == 1
    assert minimum_order_shattered_dimension(concepts) == 2
    print("Order-shattering separation: OSH_min(C_osh)=2, VCR(C_osh)=1.")


if __name__ == "__main__":
    main()
