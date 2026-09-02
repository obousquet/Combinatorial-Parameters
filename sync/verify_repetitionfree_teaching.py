#!/usr/bin/env python3
"""Verify teaching-set statistics for the repetition-free separation class."""

from __future__ import annotations

from functools import cache
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


def vc_dimension() -> int:
    """Compute the largest shattered coordinate set."""
    dimension = len(CLASS[0])
    largest = 0
    for size in range(dimension + 1):
        for coordinates in combinations(range(dimension), size):
            traces = {"".join(concept[index] for index in coordinates) for concept in CLASS}
            if len(traces) == 2**size:
                largest = max(largest, size)
    return largest


def littlestone_dimension(concepts: tuple[str, ...]) -> int:
    """Compute Littlestone dimension by the standard restriction recurrence."""
    dimension = len(CLASS[0])

    @cache
    def recurse(current: tuple[str, ...]) -> int:
        best = 0
        for coordinate in range(dimension):
            zero = tuple(concept for concept in current if concept[coordinate] == "0")
            one = tuple(concept for concept in current if concept[coordinate] == "1")
            if zero and one:
                best = max(best, 1 + min(recurse(zero), recurse(one)))
        return best

    return recurse(concepts)


def hamming_distance(first: str, second: str) -> int:
    return sum(left != right for left, right in zip(first, second))


def one_inclusion_adjacency() -> tuple[frozenset[int], ...]:
    """Return the adjacency sets of the class's one-inclusion graph."""
    adjacency = [set() for _ in CLASS]
    for left, right in combinations(range(len(CLASS)), 2):
        if hamming_distance(CLASS[left], CLASS[right]) == 1:
            adjacency[left].add(right)
            adjacency[right].add(left)
    return tuple(frozenset(neighbours) for neighbours in adjacency)


def largest_contained_cube_dimension() -> int:
    """Compute the largest strongly shattered coordinate set."""
    dimension = len(CLASS[0])
    largest = 0
    for size in range(dimension + 1):
        for coordinates in combinations(range(dimension), size):
            complement = tuple(index for index in range(dimension) if index not in coordinates)
            for fixed in product("01", repeat=len(complement)):
                traces = {
                    tuple(concept[index] for index in coordinates)
                    for concept in CLASS
                    if tuple(concept[index] for index in complement) == fixed
                }
                if len(traces) == 2**size:
                    largest = max(largest, size)
    return largest


def main() -> None:
    sizes = tuple(minimum_teaching_set_size(concept, CLASS) for concept in CLASS)
    assert sizes == EXPECTED_SIZES, (sizes, EXPECTED_SIZES)
    assert min(sizes) == 2
    assert max(sizes) == 4
    assert sum(sizes) == 40
    assert largest_star_dimension() == 4
    assert largest_star_dimension(hollow=True) == 4
    minimum_centered_star = min(
        largest_star_dimension(center) for center in map("".join, product("01", repeat=5))
    )
    assert minimum_centered_star == 3
    assert len(CLASS) == 13
    assert all({concept[index] for concept in CLASS} == {"0", "1"} for index in range(5))
    assert vc_dimension() == 3
    assert littlestone_dimension(CLASS) == 3
    assert max(hamming_distance(first, second) for first in CLASS for second in CLASS) == 5
    assert min(
        max(hamming_distance(centre, concept) for concept in CLASS)
        for centre in map("".join, product("01", repeat=5))
    ) == 4
    adjacency = one_inclusion_adjacency()
    degrees = tuple(map(len, adjacency))
    assert degrees == (1, 1, 3, 3, 2, 2, 1, 3, 2, 2, 1, 2, 1)
    assert max(degrees) == 3 and min(degrees) == 1
    assert sum(degrees) == 24
    densest_average_degree = max(
        sum(sum(neighbour in subset for neighbour in adjacency[vertex]) for vertex in subset)
        / len(subset)
        for size in range(1, len(CLASS) + 1)
        for subset in combinations(range(len(CLASS)), size)
    )
    assert densest_average_degree == 2
    degeneracy = max(
        min(sum(neighbour in subset for neighbour in adjacency[vertex]) for vertex in subset)
        for size in range(1, len(CLASS) + 1)
        for subset in combinations(range(len(CLASS)), size)
    )
    assert degeneracy == 2
    assert largest_contained_cube_dimension() == 2
    print(f"individual minimum teaching-set sizes: {sizes}")
    print("minimum teaching-set size: 2; teaching dimension / maximum teaching-set size: 4")
    print("sum: 40; average teaching dimension: 40/13")
    print("star number: 4; co-VC dimension: 4; minimum star number: 3")
    print("size: 13; effective range: 5; VC dimension: 3; Littlestone dimension: 3")
    print("diameter: 5; Hamming radius: 4")
    print("minimum/maximum degree: 1/3; average degree: 24/13; densest-subgraph value: 2")
    print("degeneracy: 2; largest strongly shattered set: 2")


if __name__ == "__main__":
    main()
