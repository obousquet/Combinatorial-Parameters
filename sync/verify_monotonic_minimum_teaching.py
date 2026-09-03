#!/usr/bin/env python3
"""Verify the finite witness separating min teaching from its monotonic version."""

from __future__ import annotations

from itertools import combinations


CONCEPTS = ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1))


def minimum_teaching_size(family: tuple[tuple[int, ...], ...]) -> int:
    """Return the least teaching-set size attained by a concept in ``family``."""
    for size in range(4):
        for target in family:
            for coordinates in combinations(range(3), size):
                if all(
                    any(target[index] != other[index] for index in coordinates)
                    for other in family
                    if other != target
                ):
                    return size
    raise AssertionError("all concepts are distinguished by the full coordinate set")


def monotonic_minimum_teaching_size() -> int:
    return max(
        minimum_teaching_size(subfamily)
        for size in range(1, len(CONCEPTS) + 1)
        for subfamily in combinations(CONCEPTS, size)
    )


def main() -> None:
    assert minimum_teaching_size(CONCEPTS) == 1
    square = CONCEPTS[:4]
    assert minimum_teaching_size(square) == 2
    assert monotonic_minimum_teaching_size() == 2
    print("C_mts: TS_min = 1; TS_min^* = 2")


if __name__ == "__main__":
    main()
