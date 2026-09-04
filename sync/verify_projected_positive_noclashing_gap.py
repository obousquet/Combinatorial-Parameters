#!/usr/bin/env python3
"""Exhaustively verify the finite projected-positive-NCTD separation."""

from itertools import combinations

CLASS = ("001", "010", "111")


def candidates(concept, width):
    return [
        (subset, tuple(concept[i] for i in subset))
        for size in range(width + 1)
        for subset in combinations(range(len(concept)), size)
        if all(concept[i] == "1" for i in subset)
    ]


def consistent(sample, concept):
    subset, labels = sample
    return all(concept[i] == label for i, label in zip(subset, labels))


def nctd_positive(concepts):
    for width in range(len(concepts[0]) + 1):
        choices = [candidates(concept, width) for concept in concepts]
        assigned = [None] * len(concepts)

        def extend(index):
            if index == len(concepts):
                return True
            for sample in choices[index]:
                if all(
                    not (
                        consistent(sample, concepts[previous])
                        and consistent(assigned[previous], concepts[index])
                    )
                    for previous in range(index)
                ):
                    assigned[index] = sample
                    if extend(index + 1):
                        return True
            assigned[index] = None
            return False

        if extend(0):
            return width
    raise AssertionError("all positive coordinates teach every finite class")


def trace(concepts, subset):
    return tuple(sorted({"".join(concept[i] for i in subset) for concept in concepts}))


def main():
    assert nctd_positive(CLASS) == 1
    assert trace(CLASS, (1, 2)) == ("01", "10", "11")
    assert nctd_positive(trace(CLASS, (1, 2))) == 2
    assert max(
        nctd_positive(trace(CLASS, subset))
        for size in range(4)
        for subset in combinations(range(3), size)
    ) == 2
    print("C_pNC+: positive NCTD = 1; projected positive NCTD = 2")


if __name__ == "__main__":
    main()
