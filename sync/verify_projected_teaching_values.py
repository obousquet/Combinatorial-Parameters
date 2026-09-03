#!/usr/bin/env python3
"""Verify finite projected minimum-teaching benchmarks used by the catalogue."""

from __future__ import annotations

from itertools import combinations


def warmuth_c5() -> tuple[tuple[int, ...], ...]:
    concepts: set[tuple[int, ...]] = set()
    for start in range(5):
        for free_bit in (0, 1):
            word: list[int | None] = [None] * 5
            for offset, bit in enumerate((1, 0, 0, 1)):
                word[(start + offset) % 5] = bit
            word[(start + 4) % 5] = free_bit
            concepts.add(tuple(bit for bit in word if bit is not None))
    return tuple(sorted(concepts))


def minimum_teaching_size(traces: tuple[tuple[int, ...], ...]) -> int:
    """Minimum teaching-set size among the distinct traces in a finite class."""
    width = len(traces[0])
    for size in range(width + 1):
        for target in traces:
            for coordinates in combinations(range(width), size):
                if all(
                    any(other[index] != target[index] for index in coordinates)
                    for other in traces
                    if other != target
                ):
                    return size
    raise AssertionError("a full coordinate set must teach every distinct trace")


def projected_minimum_teaching_size(concepts: tuple[tuple[int, ...], ...]) -> int:
    """Maximum, over projections, of the projected minimum teaching-set size."""
    answer = 0
    for mask in range(1 << 5):
        coordinates = tuple(index for index in range(5) if mask & (1 << index))
        traces = tuple(sorted({tuple(word[index] for index in coordinates) for word in concepts}))
        if len(traces) > 1:
            answer = max(answer, minimum_teaching_size(traces))
    return answer


def main() -> None:
    concepts = warmuth_c5()
    assert len(concepts) == 10
    assert projected_minimum_teaching_size(concepts) == 3

    maximum = 0
    for family_mask in range(1, 1 << len(concepts)):
        family = tuple(
            concept for index, concept in enumerate(concepts) if family_mask & (1 << index)
        )
        maximum = max(maximum, projected_minimum_teaching_size(family))
    assert maximum == 3
    print("Warmuth C_5: TS_min^p = TS_min^{*p} = 3")


if __name__ == "__main__":
    main()
