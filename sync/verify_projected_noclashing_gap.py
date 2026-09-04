#!/usr/bin/env python3
"""Exhaustively verify the finite projected-NCTD separation class."""

from itertools import combinations


CLASS = ("0000", "0001", "0010", "0011", "0100", "1101")


def samples(concept, width):
    """All labelled coordinate samples of size at most the supplied width."""
    n = len(concept)
    return [
        (subset, tuple(concept[index] for index in subset))
        for size in range(width + 1)
        for subset in combinations(range(n), size)
    ]


def consistent(sample, concept):
    subset, labels = sample
    return all(concept[index] == label for index, label in zip(subset, labels))


def has_no_clashing_teacher(concepts, width):
    """Decide the finite NCTD feasibility problem by backtracking."""
    possibilities = [samples(concept, width) for concept in concepts]
    chosen = [None] * len(concepts)

    def extend(index):
        if index == len(concepts):
            return True
        for sample in possibilities[index]:
            if all(
                not (
                    consistent(sample, concepts[prior])
                    and consistent(chosen[prior], concepts[index])
                )
                for prior in range(index)
            ):
                chosen[index] = sample
                if extend(index + 1):
                    return True
        chosen[index] = None
        return False

    return extend(0)


def nctd(concepts):
    for width in range(len(concepts[0]) + 1):
        if has_no_clashing_teacher(concepts, width):
            return width
    raise AssertionError("every finite binary class has an all-coordinate teacher")


def trace(concepts, subset):
    return tuple(
        sorted({"".join(concept[index] for index in subset) for concept in concepts})
    )


def main():
    assert nctd(CLASS) == 1
    trace_123 = trace(CLASS, (1, 2, 3))
    assert trace_123 == ("000", "001", "010", "011", "100", "101")
    assert nctd(trace_123) == 2

    maximum = max(
        nctd(trace(CLASS, subset))
        for size in range(len(CLASS[0]) + 1)
        for subset in combinations(range(len(CLASS[0])), size)
    )
    assert maximum == 2
    print("C_pNC: NCTD = 1; projected NCTD = 2")


if __name__ == "__main__":
    main()
