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


def compression_exists(size, proper, stable=False):
    """Decide whether an unlabeled scheme of this size exists.

    With ``stable=True``, also impose that removing every unselected example
    leaves the compression set unchanged.
    """
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

    if stable:
        # Every one-point deletion is assigned before the sample itself.
        order = tuple(
            sorted(
                range(len(samples)),
                key=lambda index: (samples[index][0].bit_count(), index),
            )
        )
        sample_indices = {sample: index for index, sample in enumerate(samples)}
    else:
        order = tuple(sorted(range(len(samples)), key=lambda index: len(choices[index])))
    # A code state is (constraints' support, constraints' values, possible proper reconstructions).
    initial = tuple((0, 0, (1 << len(CONCEPTS)) - 1) for _ in range(1 << DIMENSION))

    @cache
    def assign(position, states, assigned=()):
        if position == len(order):
            return True
        sample_index = order[position]
        support, values = samples[sample_index]
        states_list = list(states)
        for code in choices[sample_index]:
            if stable:
                # A deleted example not retained by this code must leave the
                # compressor's output equal to this code.
                if any(
                    assigned[sample_indices[(support ^ (1 << coordinate), values & ~(1 << coordinate))]] != code
                    for coordinate in range(DIMENSION)
                    if (support & (1 << coordinate)) and not (code & (1 << coordinate))
                ):
                    continue
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
            if stable:
                assigned_list = list(assigned)
                assigned_list[sample_index] = code
                next_assigned = tuple(assigned_list)
            else:
                next_assigned = assigned
            if assign(position + 1, tuple(states_list), next_assigned):
                return True
            states_list[code] = (old_support, old_values, old_concepts)
        return False

    initial_assigned = tuple(-1 for _ in samples) if stable else ()
    return assign(0, initial, initial_assigned)


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


def membership_query_one_fails():
    """No single coordinate partitions the three targets into singletons."""
    for coordinate in range(DIMENSION):
        response_sizes = [
            sum((target >> coordinate) & 1 == answer for target in CONCEPTS)
            for answer in (0, 1)
        ]
        if max(response_sizes) <= 1:
            return False
    return True


def proper_stable_labeled_size_one_exists():
    """Check an explicit proper stable labelled scheme of size one.

    A labelled code is the pair (support mask, retained labels).  The table
    was found by finite search, but is checked directly here so the displayed
    value has a short, independently reproducible certificate.
    """
    compression = {
        (0b000, 0b000): (0b000, 0b000),
        (0b001, 0b000): (0b001, 0b000),
        (0b001, 0b001): (0b001, 0b001),
        (0b010, 0b000): (0b010, 0b000),
        (0b010, 0b010): (0b010, 0b010),
        (0b011, 0b000): (0b010, 0b000),
        (0b011, 0b001): (0b001, 0b001),
        (0b011, 0b011): (0b010, 0b010),
        (0b100, 0b000): (0b100, 0b000),
        (0b100, 0b100): (0b100, 0b100),
        (0b101, 0b000): (0b001, 0b000),
        (0b101, 0b001): (0b100, 0b000),
        (0b101, 0b101): (0b100, 0b100),
        (0b110, 0b000): (0b010, 0b000),
        (0b110, 0b010): (0b100, 0b000),
        (0b110, 0b100): (0b100, 0b100),
        (0b111, 0b000): (0b010, 0b000),
        (0b111, 0b011): (0b100, 0b000),
        (0b111, 0b101): (0b100, 0b100),
    }
    decoder = {
        (0b000, 0b000): 0b000,
        (0b001, 0b000): 0b000,
        (0b001, 0b001): 0b101,
        (0b010, 0b000): 0b000,
        (0b010, 0b010): 0b011,
        (0b100, 0b000): 0b011,
        (0b100, 0b100): 0b101,
    }
    samples = realizable_samples()
    if set(compression) != set(samples):
        return False
    for sample, code in compression.items():
        support, values = sample
        code_support, code_values = code
        reconstruction = decoder[code]
        if code_values & ~code_support or code_support & ~support:
            return False
        if code_values != values & code_support or code_support.bit_count() > 1:
            return False
        if reconstruction not in CONCEPTS or (reconstruction ^ values) & support:
            return False
        for coordinate in range(DIMENSION):
            if support & (1 << coordinate) and not (code_support & (1 << coordinate)):
                deleted = (support ^ (1 << coordinate), values & ~(1 << coordinate))
                if compression[deleted] != code:
                    return False
    return True


def main():
    assert compression_exists(1, proper=False)
    assert not compression_exists(0, proper=False)
    assert not compression_exists(1, proper=True)
    assert compression_exists(2, proper=True)
    assert compression_exists(1, proper=False, stable=True)
    assert not compression_exists(1, proper=True, stable=True)
    assert compression_exists(2, proper=True, stable=True)
    assert proper_stable_labeled_size_one_exists()
    assert proper_equivalence_one_query_fails()
    assert membership_query_one_fails()
    # The improper query 001 has one distinct disagreement coordinate per target.
    proposal = 0b001
    responses = [
        tuple(target for target in CONCEPTS if ((target >> coordinate) & 1) != ((proposal >> coordinate) & 1))
        for coordinate in range(DIMENSION)
    ]
    assert {response for response in responses if response} == {(0b000,), (0b011,), (0b101,)}
    print(
        "Three-code class: USC=1 < pUSC=2; sUSC=1 < psUSC=2; "
        "LSC=sLSC=pLSC=psLSC=1; EQ=MEQ=1 < pEQ=MPEQ=MQ=2"
    )


if __name__ == "__main__":
    main()
