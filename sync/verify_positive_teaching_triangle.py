#!/usr/bin/env python3
"""Exactly verify C_{+triangle}: positive RTD 2 versus positive NCTD 1."""

from functools import cache
from itertools import permutations


# Bit i is the label at x_(i+1), so these are 110, 101, 011 in coordinate order.
CONCEPTS = (0b011, 0b101, 0b110)
DIMENSION = 3


def positive_teaching_size(target: int, family: tuple[int, ...]) -> int | None:
    for size in range(DIMENSION + 1):
        for sample in range(1 << DIMENSION):
            if sample.bit_count() == size and sample & ~target == 0 and all(sample & ~other for other in family if other != target):
                return size
    return None


def positive_recursive_teaching_dimension() -> int:
    @cache
    def solve(family: tuple[int, ...]) -> int:
        if len(family) <= 1:
            return 0
        candidates = []
        for target in family:
            size = positive_teaching_size(target, family)
            if size is not None:
                candidates.append(max(size, solve(tuple(other for other in family if other != target))))
        return min(candidates)

    return solve(CONCEPTS)


def positive_noclashing_dimension() -> int:
    for width in range(DIMENSION + 1):
        options = {
            target: [sample for sample in range(1 << DIMENSION) if sample.bit_count() <= width and sample & ~target == 0]
            for target in CONCEPTS
        }
        assigned: dict[int, int] = {}

        def search(index: int) -> bool:
            if index == len(CONCEPTS):
                return True
            target = CONCEPTS[index]
            for sample in options[target]:
                if all(not (sample & ~other == 0 and other_sample & ~target == 0) for other, other_sample in assigned.items()):
                    assigned[target] = sample
                    if search(index + 1):
                        return True
                    del assigned[target]
            return False

        if search(0):
            return width
    raise AssertionError("the full positive support always provides a finite map")


def preference_based_dimension() -> int:
    """Enumerate preference orders and their smallest teaching samples."""
    for width in range(DIMENSION + 1):
        for order in permutations(CONCEPTS):
            valid = True
            for index, target in enumerate(order):
                lower = order[index + 1 :]
                if not any(
                    sample.bit_count() <= width
                    and all((other & sample) != (target & sample) for other in lower)
                    for sample in range(1 << DIMENSION)
                ):
                    valid = False
                    break
            if valid:
                return width
    raise AssertionError("full samples always yield a preference teaching plan")


def main() -> None:
    assert positive_recursive_teaching_dimension() == 2
    assert positive_noclashing_dimension() == 1
    assert preference_based_dimension() == 1
    print("C_{+triangle}: positive RTD = 2; positive NCTD = PBTD = 1")


if __name__ == "__main__":
    main()
