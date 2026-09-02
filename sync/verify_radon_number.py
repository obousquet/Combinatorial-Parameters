#!/usr/bin/env python3
"""Exact finite checks for the Radon-number benchmark values.

The convex hull of a set of binary hypotheses is the intersection of all
version spaces containing it: it fixes precisely the coordinates on which the
hypotheses agree.  This script enumerates Radon-independent subsets for the
two elementary families whose database records have piecewise or structural
proofs.
"""

from itertools import combinations


def hull(hypotheses: tuple[tuple[int, ...], ...], subset: tuple[int, ...]) -> set[int]:
    fixed = []
    for coordinate in range(len(hypotheses[0])):
        labels = {hypotheses[index][coordinate] for index in subset}
        fixed.append(next(iter(labels)) if len(labels) == 1 else None)
    return {
        index
        for index, hypothesis in enumerate(hypotheses)
        if all(label is None or hypothesis[coordinate] == label for coordinate, label in enumerate(fixed))
    }


def radon_independent(hypotheses: tuple[tuple[int, ...], ...], subset: tuple[int, ...]) -> bool:
    for split in range(1, (1 << len(subset)) - 1):
        left = tuple(subset[index] for index in range(len(subset)) if split & (1 << index))
        right = tuple(subset[index] for index in range(len(subset)) if not split & (1 << index))
        if hull(hypotheses, left) & hull(hypotheses, right):
            return False
    return True


def radon_number(hypotheses: tuple[tuple[int, ...], ...]) -> int:
    for size in range(len(hypotheses), 0, -1):
        if any(radon_independent(hypotheses, subset) for subset in combinations(range(len(hypotheses)), size)):
            return size
    raise AssertionError("a singleton must be Radon independent")


def singleton_plus_empty_set(dimension: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(coordinate == index) for coordinate in range(dimension)) for index in range(dimension)) + (
        (0,) * dimension,
    )


def halfintervals(dimension: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(coordinate >= cut) for coordinate in range(dimension)) for cut in range(dimension + 1))


def main() -> None:
    for dimension in range(1, 8):
        expected_singletons = 2 if dimension <= 2 else 3
        assert radon_number(singleton_plus_empty_set(dimension)) == expected_singletons
        assert radon_number(halfintervals(dimension)) == 2
    print("Radon-number benchmark checks passed for dimensions 1 through 7.")


if __name__ == "__main__":
    main()
