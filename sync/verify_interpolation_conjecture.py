#!/usr/bin/env python3
"""Check the counterexample to the draft interpolation-degree conjecture.

For a finite Boolean class H, SCVC(H) is the minimum VC dimension of a
coordinate projection H|S for which the number of shattered subsets is at
least |H|.  The script verifies the four-concept counterexample and, as a
sanity check, enumerates all nonempty classes on domains of size at most 3.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations, permutations


COUNTEREXAMPLE = ("001", "010", "011", "100")
REVERSE_COUNTEREXAMPLE = ("0110", "0111", "1000", "1001")
EFFECTIVE_VC_RADIUS_COUNTEREXAMPLE = ("000", "011", "101", "110")
SCVC_VC_SEPARATION = ("0000", "1001", "1100", "1111")


def trivial_concepts(dimension: int) -> tuple[str, ...]:
    return ("0" * dimension, "1" * dimension)


def singletons(dimension: int, *, include_empty: bool = False) -> tuple[str, ...]:
    concepts = ["".join("1" if index == coordinate else "0" for index in range(dimension)) for coordinate in range(dimension)]
    return tuple((["0" * dimension] if include_empty else []) + concepts)


def halfintervals(dimension: int) -> tuple[str, ...]:
    return tuple("1" * size + "0" * (dimension - size) for size in range(1, dimension + 1))


def full_cube(dimension: int) -> tuple[str, ...]:
    return tuple(format(value, f"0{dimension}b") for value in range(2**dimension))


def projection(concepts: tuple[str, ...], coordinates: tuple[int, ...]) -> tuple[str, ...]:
    return tuple(sorted({"".join(concept[index] for index in coordinates) for concept in concepts}))


def vc_dimension(concepts: tuple[str, ...]) -> int:
    dimension = len(concepts[0])
    for size in range(dimension, -1, -1):
        for coordinates in combinations(range(dimension), size):
            if len(projection(concepts, coordinates)) == 2**size:
                return size
    raise AssertionError("the empty set is always shattered")


def shattered_set_count(concepts: tuple[str, ...]) -> int:
    dimension = len(concepts[0])
    return sum(
        len(projection(concepts, coordinates)) == 2**len(coordinates)
        for size in range(dimension + 1)
        for coordinates in combinations(range(dimension), size)
    )


def rank(matrix: list[list[int]]) -> int:
    rows = [[Fraction(entry) for entry in row] for row in matrix]
    pivot_row = 0
    for column in range(len(rows[0])):
        pivot = next((row for row in range(pivot_row, len(rows)) if rows[row][column]), None)
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        divisor = rows[pivot_row][column]
        rows[pivot_row] = [entry / divisor for entry in rows[pivot_row]]
        for row in range(len(rows)):
            if row != pivot_row and rows[row][column]:
                factor = rows[row][column]
                rows[row] = [entry - factor * base for entry, base in zip(rows[row], rows[pivot_row])]
        pivot_row += 1
        if pivot_row == len(rows):
            break
    return pivot_row


def interpolation_degree(concepts: tuple[str, ...]) -> int:
    dimension = len(concepts[0])
    for degree in range(dimension + 1):
        monomials = [
            coordinates
            for size in range(degree + 1)
            for coordinates in combinations(range(dimension), size)
        ]
        evaluations = [
            [all(concept[index] == "1" for index in monomial) for monomial in monomials]
            for concept in concepts
        ]
        if rank(evaluations) == len(concepts):
            return degree
    raise AssertionError("all Boolean monomials interpolate on a finite Boolean class")


def scvc(concepts: tuple[str, ...]) -> int:
    dimension = len(concepts[0])
    admissible = [
        vc_dimension(projection(concepts, coordinates))
        for size in range(dimension + 1)
        for coordinates in combinations(range(dimension), size)
        if shattered_set_count(projection(concepts, coordinates)) >= len(concepts)
    ]
    assert admissible
    return min(admissible)


def effective_vc_radius(concepts: tuple[str, ...]) -> int:
    """Largest k for which every k-subset of the effective range is shattered."""
    effective_coordinates = tuple(
        coordinate
        for coordinate in range(len(concepts[0]))
        if len({concept[coordinate] for concept in concepts}) > 1
    )
    return max(
        size
        for size in range(len(effective_coordinates) + 1)
        if all(
            len(projection(concepts, coordinates)) == 2**size
            for coordinates in combinations(effective_coordinates, size)
        )
    )


def downshift(concepts: tuple[str, ...], coordinate: int) -> tuple[str, ...]:
    """Apply the standard binary downshift at one coordinate."""
    shifted = set(concepts)
    for concept in concepts:
        if concept[coordinate] == "1":
            lowered = concept[:coordinate] + "0" + concept[coordinate + 1 :]
            if lowered not in shifted:
                shifted.remove(concept)
                shifted.add(lowered)
    return tuple(sorted(shifted))


def minimum_order_shattered_dimension(concepts: tuple[str, ...]) -> int:
    """Minimum largest downshifted face over all coordinate orders."""
    dimension = len(concepts[0])
    largest_faces = []
    for order in permutations(range(dimension)):
        shifted = concepts
        for coordinate in order:
            shifted = downshift(shifted, coordinate)
        # A fully downshifted binary family is downward closed, so its largest
        # shattered face is the largest support of one of its members.
        largest_faces.append(max(concept.count("1") for concept in shifted))
    return min(largest_faces)


def exhaustive_small_cube_check() -> int:
    counterexamples = 0
    for dimension in range(1, 4):
        cube = full_cube(dimension)
        for mask in range(1, 1 << len(cube)):
            concepts = tuple(concept for index, concept in enumerate(cube) if mask & (1 << index))
            counterexamples += interpolation_degree(concepts) != scvc(concepts)
    return counterexamples


def benchmark_check() -> None:
    for dimension in range(1, 5):
        assert scvc(trivial_concepts(dimension)) == 1
        assert scvc(full_cube(dimension)) == dimension
        assert scvc(singletons(dimension, include_empty=True)) == 1
    for dimension in range(2, 5):
        assert scvc(singletons(dimension)) == 1
        assert scvc(halfintervals(dimension)) == 1


def main() -> None:
    assert interpolation_degree(COUNTEREXAMPLE) == 1
    assert scvc(COUNTEREXAMPLE) == 2
    assert interpolation_degree(REVERSE_COUNTEREXAMPLE) == 2
    assert scvc(REVERSE_COUNTEREXAMPLE) == 1
    assert interpolation_degree(EFFECTIVE_VC_RADIUS_COUNTEREXAMPLE) == 1
    assert effective_vc_radius(EFFECTIVE_VC_RADIUS_COUNTEREXAMPLE) == 2
    assert minimum_order_shattered_dimension(EFFECTIVE_VC_RADIUS_COUNTEREXAMPLE) == 2
    assert vc_dimension(SCVC_VC_SEPARATION) == 2
    assert scvc(SCVC_VC_SEPARATION) == 1
    benchmark_check()
    count = exhaustive_small_cube_check()
    assert count == 26
    print("Interpolation conjecture refuted: intdeg(C_int)=1, SCVC(C_int)=2.")
    print("Neither one-sided comparison holds: intdeg(C_rev)=2, SCVC(C_rev)=1.")
    print("The proposed intdeg >= VCR bound also fails: intdeg(C_even)=1, VCR(C_even)=2.")
    print("C_even also has OSH_min=2, strictly above its interpolation degree 1.")
    print(f"Small-cube sanity check found {count} counterexamples through dimension 3.")


if __name__ == "__main__":
    main()
