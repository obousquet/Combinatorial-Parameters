#!/usr/bin/env python3
"""Exact finite checks for Minimum Star Number benchmark values.

This currently verifies Warmuth's C_5 class directly from its cyclic
``1001`` definition.  It enumerates every possible centre labeling and every
coordinate subset, so the result is an exact implementation of the definition
of the minimum star number.
"""

from __future__ import annotations

from itertools import combinations, product


def warmuth_c5() -> set[tuple[int, ...]]:
    concepts: set[tuple[int, ...]] = set()
    for start in range(5):
        for free_label in (0, 1):
            concept: list[int | None] = [None] * 5
            for offset, label in enumerate((1, 0, 0, 1)):
                concept[(start + offset) % 5] = label
            concept[(start + 4) % 5] = free_label
            concepts.add(tuple(concept))
    return concepts


def centered_star_number(
    concepts: set[tuple[int, ...]], centre: tuple[int, ...]
) -> int:
    dimension = len(centre)
    answer = 0
    for size in range(dimension + 1):
        for points in combinations(range(dimension), size):
            has_centre = any(
                all(hypothesis[j] == centre[j] for j in points)
                for hypothesis in concepts
            )
            has_each_leaf = all(
                any(
                    hypothesis[i] != centre[i]
                    and all(
                        hypothesis[j] == centre[j]
                        for j in points
                        if j != i
                    )
                    for hypothesis in concepts
                )
                for i in points
            )
            if has_centre and has_each_leaf:
                answer = max(answer, size)
    return answer


def minimum_star_number(concepts: set[tuple[int, ...]]) -> int:
    dimension = len(next(iter(concepts)))
    return min(
        centered_star_number(concepts, centre)
        for centre in product((0, 1), repeat=dimension)
    )


def main() -> None:
    concepts = warmuth_c5()
    assert len(concepts) == 10
    value = minimum_star_number(concepts)
    assert value == 3
    print(f"Warmuth C_5 minimum star number: {value}")


if __name__ == "__main__":
    main()
