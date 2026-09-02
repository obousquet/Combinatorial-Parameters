#!/usr/bin/env python3
"""Exhaustively verify finite witnesses for properness restrictions.

The three-code class is C_triangle={000,011,101} on three coordinates.  This
script checks the database conventions for unlabeled compression: a code is an
unlabeled subset of the sample support; all samples assigned one code must be
consistent with one reconstruction, which is additionally required to lie in
the class in the proper model.
"""

from functools import cache


CONCEPTS = (0b000, 0b011, 0b101)
DIMENSION = 3


def realizable_samples():
    """Return all partial binary samples (support mask, values mask)."""
    samples = []
    for support in range(1 << DIMENSION):
        for values in range(1 << DIMENSION):
            if values & ~support:
                continue
            if any((concept ^ values) & support == 0 for concept in CONCEPTS):
                samples.append((support, values))
    return tuple(samples)


def compression_exists(size, proper):
    """Exhaustively decide whether a (proper) unlabeled scheme of this size exists."""
    samples = realizable_samples()
    choices = []
    for support, _ in samples:
        allowed = []
        code = support
        while True:
            if code.bit_count() <= size:
                allowed.append(code)
            if code == 0:
                break
            code = (code - 1) & support
        choices.append(tuple(allowed))

    order = tuple(sorted(range(len(samples)), key=lambda index: len(choices[index])))
    # A code state is (constraints' support, constraints' values, possible proper reconstructions).
    initial = tuple((0, 0, (1 << len(CONCEPTS)) - 1) for _ in range(1 << DIMENSION))

    @cache
    def assign(position, states):
        if position == len(order):
            return True
        support, values = samples[order[position]]
        states_list = list(states)
        for code in choices[order[position]]:
            old_support, old_values, old_concepts = states_list[code]
            overlap = old_support & support
            if (old_values ^ values) & overlap:
                continue
            new_support = old_support | support
            new_values = (old_values & old_support) | (values & support)
            new_concepts = old_concepts
            if proper:
                new_concepts = sum(
                    1 << index
                    for index, concept in enumerate(CONCEPTS)
                    if (concept ^ new_values) & new_support == 0
                )
                if not new_concepts:
                    continue
            states_list[code] = (new_support, new_values, new_concepts)
            if assign(position + 1, tuple(states_list)):
                return True
            states_list[code] = (old_support, old_values, old_concepts)
        return False

    return assign(0, initial)


def proper_equivalence_one_query_fails():
    """No proposal in C_triangle has singleton response classes at every error point."""
    for proposal in CONCEPTS:
        response_sizes = [
            sum(((target >> coordinate) & 1) != ((proposal >> coordinate) & 1) for target in CONCEPTS)
            for coordinate in range(DIMENSION)
        ]
        if all(size <= 1 for size in response_sizes):
            return False
    return True


def main():
    assert compression_exists(1, proper=False)
    assert not compression_exists(0, proper=False)
    assert not compression_exists(1, proper=True)
    assert compression_exists(2, proper=True)
    assert proper_equivalence_one_query_fails()
    # The improper query 001 has one distinct disagreement coordinate per target.
    proposal = 0b001
    responses = [
        tuple(target for target in CONCEPTS if ((target >> coordinate) & 1) != ((proposal >> coordinate) & 1))
        for coordinate in range(DIMENSION)
    ]
    assert {response for response in responses if response} == {(0b000,), (0b011,), (0b101,)}
    print("Three-code class: USC=1 < pUSC=2; EQ=1 < pEQ=2")


if __name__ == "__main__":
    main()
