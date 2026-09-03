#!/usr/bin/env python3
"""Verify a finite strict gap between RTD and projected RTD."""

from __future__ import annotations

from itertools import combinations


CONCEPTS = ((0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0))


def minimum_teaching_size(family: tuple[tuple[int, ...], ...]) -> int:
    width = len(family[0])
    for size in range(width + 1):
        for target in family:
            for coordinates in combinations(range(width), size):
                if all(
                    any(target[index] != other[index] for index in coordinates)
                    for other in family
                    if other != target
                ):
                    return size
    raise AssertionError("full coordinates distinguish every target")


def rtd(family: tuple[tuple[int, ...], ...]) -> int:
    return max(
        minimum_teaching_size(subfamily)
        for size in range(1, len(family) + 1)
        for subfamily in combinations(family, size)
    )


def projected_rtd() -> int:
    answer = 0
    for mask in range(1 << 3):
        coordinates = tuple(index for index in range(3) if mask & (1 << index))
        traces = tuple(sorted({tuple(word[index] for index in coordinates) for word in CONCEPTS}))
        answer = max(answer, rtd(traces))
    return answer


def main() -> None:
    assert rtd(CONCEPTS) == 1
    assert projected_rtd() == 2
    print("C_rtdp: RTD = 1; projected RTD = 2")


if __name__ == "__main__":
    main()
