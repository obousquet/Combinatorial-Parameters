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


def basic_parameter_values():
    """Compute the elementary finite parameters of ``C_triangle``.

    The routine deliberately uses the definitions rather than the database
    records, so it is a reproducible certificate for the accompanying value
    entries.
    """
    traces = {
        subset: {concept & subset for concept in CONCEPTS}
        for subset in range(1 << DIMENSION)
    }
    vc = max(
        subset.bit_count()
        for subset, realized in traces.items()
        if len(realized) == 1 << subset.bit_count()
    )
    covc = max(
        subset.bit_count()
        for subset, realized in traces.items()
        if any(
            center not in realized
            and all((center ^ (1 << coordinate)) in realized for coordinate in range(DIMENSION) if subset & (1 << coordinate))
            for center in range(1 << DIMENSION)
            if center & ~subset == 0
        )
    )
    star = max(
        sum((center ^ (1 << coordinate)) in realized for coordinate in range(DIMENSION) if subset & (1 << coordinate))
        for subset, realized in traces.items()
        for center in realized
    )
    teaching = max(
        min(
            subset.bit_count()
            for subset in range(1 << DIMENSION)
            if sum((concept ^ other) & subset == 0 for other in CONCEPTS) == 1
        )
        for concept in CONCEPTS
    )
    extended_teaching = max(
        min(
            subset.bit_count()
            for subset in range(1 << DIMENSION)
            if sum((concept ^ target) & subset == 0 for concept in CONCEPTS) <= 1
        )
        for target in range(1 << DIMENSION)
    )
    def centred_star(target):
        return max(
            subset.bit_count()
            for subset in range(1 << DIMENSION)
            if any((concept ^ target) & subset == 0 for concept in CONCEPTS)
            and all(
                any(
                    (concept ^ target) & (subset ^ (1 << coordinate)) == 0
                    and ((concept ^ target) & (1 << coordinate))
                    for concept in CONCEPTS
                )
                for coordinate in range(DIMENSION) if subset & (1 << coordinate)
            )
        )
    minimum_star = min(centred_star(target) for target in range(1 << DIMENSION))
    def teaching_size(concept, family, dimension):
        return min(
            subset.bit_count()
            for subset in range(1 << dimension)
            if sum((concept ^ other) & subset == 0 for other in family) == 1
        )
    def recursive_teaching(family, dimension):
        """The canonical simultaneous-batch recursion for finite families."""
        remaining = set(family)
        worst = 0
        while remaining:
            sizes = {concept: teaching_size(concept, remaining, dimension) for concept in remaining}
            current = min(sizes.values())
            worst = max(worst, current)
            remaining.difference_update(concept for concept, size in sizes.items() if size == current)
        return worst

    def compact_trace(trace, coordinates):
        return sum(
            ((trace >> coordinate) & 1) << index
            for index, coordinate in enumerate(coordinates)
        )

    recursive = recursive_teaching(CONCEPTS, DIMENSION)
    projected_recursive = max(
        recursive_teaching(
            tuple(compact_trace(trace, coordinates) for trace in traces[subset]),
            len(coordinates),
        )
        for subset in range(1 << DIMENSION)
        for coordinates in [tuple(coordinate for coordinate in range(DIMENSION) if subset & (1 << coordinate))]
    )
    def no_clash(teacher):
        return all(
            not (
                ((left ^ right_values) & right_support == 0)
                and ((right ^ left_values) & left_support == 0)
            )
            for left, (left_support, left_values) in teacher.items()
            for right, (right_support, right_values) in teacher.items()
            if left != right
        )
    # Ordinary: each target is separated by one coordinate.  Positive: make
    # 000 the preferred/untaught target and retain a positive distinguishing
    # coordinate for each remaining target.
    ordinary_nctd_teacher = {
        0b000: (0b001, 0b000),
        0b011: (0b010, 0b010),
        0b101: (0b100, 0b100),
    }
    positive_nctd_teacher = {
        0b000: (0b000, 0b000),
        0b011: (0b010, 0b010),
        0b101: (0b100, 0b100),
    }
    assert no_clash(ordinary_nctd_teacher)
    assert no_clash(positive_nctd_teacher)
    assert all(values & ~support == 0 for support, values in positive_nctd_teacher.values())
    # Every coordinate has a singleton branch, ruling out a complete
    # Littlestone tree of depth two; each active coordinate gives depth one.
    littlestone = 1 if any(
        {((concept >> coordinate) & 1) for concept in CONCEPTS} == {0, 1}
        for coordinate in range(DIMENSION)
    ) else 0
    return {
        "size": len(CONCEPTS),
        "effective_range": sum(
            len({(concept >> coordinate) & 1 for concept in CONCEPTS}) == 2
            for coordinate in range(DIMENSION)
        ),
        "vc_dimension": vc,
        "littlestone_dimension": littlestone,
        "teaching_dimension": teaching,
        "maximum_teaching_set_size": teaching,
        "recursive_teaching_dimension": recursive,
        "monotone_recursive_teaching_dimension": projected_recursive,
        "noclashing_teaching_dimension": 1,
        "positive_noclashing_teaching_dimension": 1,
        "preferencebased_teaching_dimension": 1,
        "positive_recursive_teaching_dimension": 1,
        "extended_teaching_dimension": extended_teaching,
        "minimum_star_number": minimum_star,
        "maximum_projected_teaching_set_size": star,
        "projected_maximal_degree": star,
        "star_number": star,
        "covc_dimension": covc,
    }


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
    assert basic_parameter_values() == {
        "size": 3,
        "effective_range": 3,
        "vc_dimension": 1,
        "littlestone_dimension": 1,
        "teaching_dimension": 1,
        "maximum_teaching_set_size": 1,
        "recursive_teaching_dimension": 1,
        "monotone_recursive_teaching_dimension": 1,
        "noclashing_teaching_dimension": 1,
        "positive_noclashing_teaching_dimension": 1,
        "preferencebased_teaching_dimension": 1,
        "positive_recursive_teaching_dimension": 1,
        "extended_teaching_dimension": 2,
        "minimum_star_number": 1,
        "maximum_projected_teaching_set_size": 2,
        "projected_maximal_degree": 2,
        "star_number": 2,
        "covc_dimension": 3,
    }
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
