#!/usr/bin/env python3
"""Verify the finite NCTD/AN gap and the singleton-plus-empty TD/AN family.

The all-n proofs are database-owned. The bounded replay below checks signed
sample inclusion (not just coordinate inclusion) and rejects invalid maps.
"""

import json
from itertools import combinations
from pathlib import Path


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


def verify_singleton_empty_family():
    data = Path(__file__).resolve().parents[1] / 'data'
    record = json.loads((data / 'values/1161_antichain_number_singletons_plus_empty_set.json').read_text())
    assert record['value'] == '$1$' and record['status'] == 'established'
    assert record['class_id'] == '#classes/singletons_plus_empty_set'
    assert record['parameter_id'] == '#parameters/antichain_number' and record['proof']

    def valid(concepts, teacher):
        return (all(consistent(teacher[h], h) for h in concepts)
                and all(incomparable(teacher[h], teacher[g])
                        for h, g in combinations(concepts, 2)))

    pairs = 0
    for n in range(1, 13):
        empty = '0' * n
        concepts = (empty,) + tuple('0' * i + '1' + '0' * (n-i-1) for i in range(n))
        teacher = {empty: ((0,), ('0',))}
        teacher.update({h: ((i,), ('1',)) for i, h in enumerate(concepts[1:])})
        assert valid(concepts, teacher)
        # The map is an antichain of LABELED samples even when domains agree.
        assert teacher[empty][0] == teacher[concepts[1]][0]
        pairs += n * (n + 1) // 2
        bad = dict(teacher)
        bad[empty] = ((), ())
        assert not valid(concepts, bad)
        bad[empty] = ((0,), ('1',))
        assert not valid(concepts, bad)
        assert not valid(concepts, {h: ((), ()) for h in concepts})
        # Exhaust exact ordinary teachers only in the small fixed controls.
        if n <= 6:
            sizes = [min(len(s[0]) for s in samples(h, n)
                         if all(not consistent(s, g) for g in concepts if g != h))
                     for h in concepts]
            assert sizes == [n] + [1] * n
    relation = json.loads((data / 'relationships/491_teaching_dimension_antichain_number.json').read_text())
    assert relation['witness'] == '#classes/singletons_plus_empty_set'
    assert relation['witness_strength'] == 'unbounded'
    print(f'Singletons plus empty: 12 domains, {pairs} signed-sample pairs; '
          'six exact TD controls, empty/inconsistent-map controls rejected.')


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
    verify_singleton_empty_family()


if __name__ == "__main__":
    main()
