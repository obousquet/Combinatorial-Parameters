#!/usr/bin/env python3
"""Exactly verify C_+ separates maximum positive degree from strong shattering."""

from itertools import combinations


CONCEPTS = frozenset({0b111, 0b110, 0b101, 0b011})
DIMENSION = 3


def maximum_positive_degree() -> int:
    return max(
        sum((concept ^ (1 << coordinate)) in CONCEPTS for coordinate in range(DIMENSION) if concept & (1 << coordinate))
        for concept in CONCEPTS
    )


def largest_strongly_shattered_set() -> int:
    for size in range(DIMENSION, -1, -1):
        for support in combinations(range(DIMENSION), size):
            support_mask = sum(1 << coordinate for coordinate in support)
            outside = tuple(coordinate for coordinate in range(DIMENSION) if coordinate not in support)
            for base_bits in range(1 << len(outside)):
                base = sum((base_bits >> index & 1) << coordinate for index, coordinate in enumerate(outside))
                if all((base | subset) in CONCEPTS for subset in range(1 << DIMENSION) if subset & ~support_mask == 0):
                    return size
    raise AssertionError("the empty set is always strongly shattered by a nonempty class")


def main() -> None:
    assert maximum_positive_degree() == 3
    assert largest_strongly_shattered_set() == 1
    print("C_+: maximum positive degree = 3; largest strongly shattered set = 1")


if __name__ == "__main__":
    main()
