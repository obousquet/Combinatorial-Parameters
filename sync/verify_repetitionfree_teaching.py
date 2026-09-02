#!/usr/bin/env python3
"""Verify teaching-set statistics for the repetition-free separation class."""

from __future__ import annotations

from itertools import combinations, product


CLASS = (
    "00000", "11000", "01000", "01010", "01011", "01110", "01101",
    "01111", "10100", "10010", "10011", "10110", "10101",
)
EXPECTED_SIZES = (2, 2, 4, 4, 3, 3, 3, 3, 3, 4, 3, 3, 3)


def minimum_teaching_set_size(target: str, concepts: tuple[str, ...]) -> int:
    """Return the least coordinate-set that distinguishes ``target``."""
    for size in range(len(target) + 1):
        for coordinates in combinations(range(len(target)), size):
            if all(
                any(target[index] != other[index] for index in coordinates)
                for other in concepts
                if other != target
            ):
                return size
    raise AssertionError("a full coordinate set must teach a distinct concept")


def largest_star_dimension(
    center: str | None = None, *, hollow: bool = False
) -> int:
    """Compute a (possibly hollow) star maximum over coordinate projections."""
    dimension = len(CLASS[0])
    best = 0
    for size in range(dimension + 1):
        for coordinates in combinations(range(dimension), size):
            traces = {"".join(concept[index] for index in coordinates) for concept in CLASS}
            centres = (
                ("".join(center[index] for index in coordinates),)
                if center is not None
                else ("".join(bits) for bits in product("01", repeat=size))
            )
            for trace in centres:
                if (trace in traces) == hollow:
                    continue
                if all(
                    trace[:index] + str(1 - int(trace[index])) + trace[index + 1:]
                    in traces
                    for index in range(size)
                ):
                    best = max(best, size)
    return best


def main() -> None:
    sizes = tuple(minimum_teaching_set_size(concept, CLASS) for concept in CLASS)
    assert sizes == EXPECTED_SIZES, (sizes, EXPECTED_SIZES)
    assert sum(sizes) == 40
    assert largest_star_dimension() == 4
    assert largest_star_dimension(hollow=True) == 4
    minimum_centered_star = min(
        largest_star_dimension(center) for center in map("".join, product("01", repeat=5))
    )
    assert minimum_centered_star == 3
    print(f"individual minimum teaching-set sizes: {sizes}")
    print("sum: 40; average teaching dimension: 40/13")
    print("star number: 4; co-VC dimension: 4; minimum star number: 3")


if __name__ == "__main__":
    main()
