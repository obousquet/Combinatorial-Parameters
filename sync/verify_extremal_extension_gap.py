#!/usr/bin/env python3
"""Exhaustively verify the four-coordinate extremal-extension gap."""

from itertools import combinations


DIMENSION = 4
# Bit i is the label at x_(i+1).
CONCEPTS = frozenset({0, 1, 4, 6, 7, 9, 10, 13, 15})
ALL_CONCEPTS = range(1 << DIMENSION)


def vc_dimension(family: frozenset[int]) -> int:
    for size in range(DIMENSION, -1, -1):
        for coordinates in combinations(range(DIMENSION), size):
            mask = sum(1 << coordinate for coordinate in coordinates)
            if len({concept & mask for concept in family}) == 1 << size:
                return size
    raise AssertionError("the empty set is always shattered")


def shattered_set_count(family: frozenset[int]) -> int:
    return sum(
        len({concept & sum(1 << coordinate for coordinate in coordinates) for concept in family}) == 1 << size
        for size in range(DIMENSION + 1)
        for coordinates in combinations(range(DIMENSION), size)
    )


def main() -> None:
    assert vc_dimension(CONCEPTS) == 2
    required_mask = sum(1 << concept for concept in CONCEPTS)
    extension_dimensions = []
    for family_mask in range(1, 1 << len(ALL_CONCEPTS)):
        if family_mask & required_mask != required_mask:
            continue
        family = frozenset(concept for concept in ALL_CONCEPTS if family_mask & (1 << concept))
        if shattered_set_count(family) == len(family):
            extension_dimensions.append(vc_dimension(family))
    assert extension_dimensions
    assert min(extension_dimensions) == 3
    print("C_ex: VC = 2; extremal-extension VC dimension = 3")


if __name__ == "__main__":
    main()
