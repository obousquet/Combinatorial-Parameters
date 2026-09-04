#!/usr/bin/env python3
"""Exhaustively verify the finite NCTD-versus-antichain separation."""

from itertools import combinations


CLASS = ("000", "001", "010", "011", "100", "101")


def samples(concept, width):
    """All target-consistent labeled samples of size at most the bound."""
    return [
        (subset, tuple(concept[index] for index in subset))
        for size in range(width + 1)
        for subset in combinations(range(len(concept)), size)
    ]


def consistent(sample, concept):
    subset, labels = sample
    return all(concept[index] == label for index, label in zip(subset, labels))


def no_clash(first, first_sample, second, second_sample):
    return not (
        consistent(first_sample, second)
        and consistent(second_sample, first)
    )


def incomparable(first_sample, second_sample):
    first_coordinates, first_labels = first_sample
    second_coordinates, second_labels = second_sample
    first = dict(zip(first_coordinates, first_labels))
    second = dict(zip(second_coordinates, second_labels))
    return not (
        all(second.get(index) == label for index, label in first.items())
        or all(first.get(index) == label for index, label in second.items())
    )


def feasible(width, compatible):
    choices = [samples(concept, width) for concept in CLASS]
    selected = []

    def extend(index):
        if index == len(CLASS):
            return True
        concept = CLASS[index]
        for sample in choices[index]:
            if all(
                compatible(concept, sample, previous_concept, previous_sample)
                for previous_concept, previous_sample in selected
            ):
                selected.append((concept, sample))
                if extend(index + 1):
                    return True
                selected.pop()
        return False

    return extend(0)


def main():
    assert feasible(
        1,
        lambda _concept, sample, _previous_concept, previous_sample:
        incomparable(sample, previous_sample),
    )
    assert not feasible(
        0,
        lambda _concept, sample, _previous_concept, previous_sample:
        incomparable(sample, previous_sample),
    )
    assert not feasible(1, no_clash)
    assert feasible(2, no_clash)
    print("C_NC/AN: AN = 1; NCTD = 2")


if __name__ == "__main__":
    main()
