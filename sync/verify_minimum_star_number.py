#!/usr/bin/env python3
"""Exact finite checks for Warmuth's C_5 star benchmark values.

This verifies Warmuth's C_5 class directly from its cyclic ``1001``
definition.  It enumerates every possible centre labeling and every coordinate
subset, so the results are exact implementations of the minimum-star and
hollow-star (co-VC) definitions.
"""

from __future__ import annotations

from fractions import Fraction
from functools import cache
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


def hollow_star_number(concepts: set[tuple[int, ...]]) -> int:
    """Return the largest hollow star occurring in a coordinate projection."""
    dimension = len(next(iter(concepts)))
    answer = 0
    for size in range(dimension + 1):
        for points in combinations(range(dimension), size):
            traces = {
                tuple(hypothesis[index] for index in points)
                for hypothesis in concepts
            }
            for centre in product((0, 1), repeat=size):
                if centre in traces:
                    continue
                if all(
                    tuple(
                        1 - centre[position] if index == position else centre[index]
                        for index in range(size)
                    )
                    in traces
                    for position in range(size)
                ):
                    answer = max(answer, size)
    return answer


def randomized_littlestone_dimension(concepts: set[tuple[int, ...]]) -> Fraction:
    """Compute half the maximum expected random-branch depth exactly.

    For a finite class, an internal node may query any coordinate that splits
    its current version space.  The two child trees are independent, giving
    the recurrence ``R(V)=max_x (1+R(V_0)+R(V_1))/2``.  Fractions avoid any
    rounding in the benchmark result.
    """
    hypotheses = tuple(sorted(concepts))
    dimension = len(hypotheses[0])

    @cache
    def value(indices: tuple[int, ...]) -> Fraction:
        best = Fraction(0)
        for coordinate in range(dimension):
            zeroes = tuple(index for index in indices if hypotheses[index][coordinate] == 0)
            ones = tuple(index for index in indices if hypotheses[index][coordinate] == 1)
            if zeroes and ones:
                best = max(best, (1 + value(zeroes) + value(ones)) / 2)
        return best

    return value(tuple(range(len(hypotheses))))


def _sample_is_consistent(
    sample: tuple[tuple[int, int], ...], hypothesis: tuple[int, ...]
) -> bool:
    return all(hypothesis[coordinate] == label for coordinate, label in sample)


def noclashing_map(
    concepts: set[tuple[int, ...]], maximum_size: int
) -> list[tuple[tuple[int, int], ...]] | None:
    """Return a width-bounded no-clashing map, or ``None`` if none exists."""
    hypotheses = tuple(sorted(concepts))
    dimension = len(hypotheses[0])
    options = [
        [
            tuple((coordinate, hypothesis[coordinate]) for coordinate in support)
            for size in range(maximum_size + 1)
            for support in combinations(range(dimension), size)
        ]
        for hypothesis in hypotheses
    ]
    mapping: list[tuple[tuple[int, int], ...] | None] = [None] * len(hypotheses)

    def extend(index: int) -> bool:
        if index == len(hypotheses):
            return True
        for sample in options[index]:
            if all(
                assigned is None
                or not (
                    _sample_is_consistent(sample, hypotheses[other])
                    and _sample_is_consistent(assigned, hypotheses[index])
                )
                for other, assigned in enumerate(mapping[:index])
            ):
                mapping[index] = sample
                if extend(index + 1):
                    return True
                mapping[index] = None
        return False

    if not extend(0):
        return None
    return [sample for sample in mapping if sample is not None]


def main() -> None:
    concepts = warmuth_c5()
    assert len(concepts) == 10
    value = minimum_star_number(concepts)
    assert value == 3
    covc = hollow_star_number(concepts)
    assert covc == 4
    randomized_littlestone = randomized_littlestone_dimension(concepts)
    assert randomized_littlestone == Fraction(13, 8)
    assert noclashing_map(concepts, 1) is None
    nctd_map = noclashing_map(concepts, 2)
    assert nctd_map is not None
    assert max(map(len, nctd_map)) == 2
    print(
        "Warmuth C_5 minimum star number: "
        f"{value}; co-VC dimension: {covc}; randomized Littlestone dimension: "
        f"{randomized_littlestone}; no-clashing teaching dimension: 2"
    )


if __name__ == "__main__":
    main()
