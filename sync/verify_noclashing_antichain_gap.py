#!/usr/bin/env python3
"""Verify the finite NCTD/AN gap and the singleton-plus-empty TD/AN family.

The all-n proofs are database-owned. The bounded replay below checks signed
sample inclusion (not just coordinate inclusion) and rejects invalid maps.
"""

import json
from collections import Counter
from itertools import combinations, permutations, product
from math import comb, factorial
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


def uniform_teacher(concepts, width):
    """Find an actual matching to consistent samples of exactly this width."""
    assigned = {}

    def augment(h, seen):
        for s in samples(h, width):
            if len(s[0]) != width or s in seen:
                continue
            seen.add(s)
            if s not in assigned or augment(assigned[s], seen):
                assigned[s] = h
                return True
        return False

    if not all(augment(h, set()) for h in concepts):
        return None
    return {h: s for s, h in assigned.items()}


def valid_teacher(concepts, teacher):
    return (set(concepts) == set(teacher)
            and all(consistent(teacher[h], h) for h in concepts)
            and all(incomparable(teacher[h], teacher[g])
                    for h, g in combinations(concepts, 2)))


def verify_cube_and_monotonicity():
    cube_checks = 0
    for n in range(9):
        cube = tuple(''.join(bits) for bits in product('01', repeat=n))
        expected = next(k for k in range(n+1) if 2**k * comb(n, k) >= 2**n)
        # Build matchings; do not use the size inequality as a feasibility oracle.
        for k in range(expected+1):
            teacher = uniform_teacher(cube, k)
            assert (teacher is not None) == (k == expected)
            if teacher is not None:
                assert valid_teacher(cube, teacher)
            cube_checks += 1
        if n:
            assert 5 * expected > n
        # Exact chain incidences check the probabilities used by the lower proof.
        if n <= 4:
            visits = Counter()
            for h in cube:
                for order in permutations(range(n)):
                    for j in range(n+1):
                        coords = tuple(sorted(order[:j]))
                        visits[(coords, tuple(h[i] for i in coords))] += 1
            for s, count in visits.items():
                j = len(s[0])
                assert count * 2**j * comb(n, j) == 2**n * factorial(n)

    cube3 = tuple(''.join(bits) for bits in product('01', repeat=3))
    padded = tuple(h + '00' for h in cube3)
    teachers = {
        '00000': ((3,), ('0',)), '11100': ((4,), ('0',)),
        '00100': ((2,), ('1',)), '01000': ((1,), ('1',)),
        '10000': ((0,), ('1',)), '01100': ((0,), ('0',)),
        '10100': ((1,), ('0',)), '11000': ((2,), ('0',)),
        '00011': ((3,), ('1',)),
    }
    original = tuple(teachers)
    assert valid_teacher(original, teachers)
    assert all({h[i] for h in original} == {'0', '1'} for i in range(5))
    conditioned = tuple(h[:3] + h[4:] for h in original if h[3] == '0')
    assert len(conditioned) == 8
    singleton_samples = {s for h in conditioned for s in samples(h, 1) if len(s[0]) == 1}
    assert len(singleton_samples) == 7
    assert uniform_teacher(conditioned, 1) is None
    assert valid_teacher(conditioned, uniform_teacher(conditioned, 2))
    assert valid_teacher(padded, {h: teachers[h] for h in padded})
    assert uniform_teacher(cube3, 1) is None

    for n in range(1, 5):
        words = tuple(''.join(bits) for bits in product('01', repeat=n))
        private = tuple(h + ''.join('1' if i == j else '0' for j in range(2**n))
                        for i, h in enumerate(words))
        teacher = {h: ((n+i,), ('1',)) for i, h in enumerate(private)}
        assert valid_teacher(private, teacher)
        assert tuple(h[:n] for h in private) == words
        # Check restrictions of the actual map without deleting ambient columns.
        for subfamily in (private[:1], private[::2], private[1:]):
            assert valid_teacher(subfamily, {h: teacher[h] for h in subfamily})

    cube2 = ('00', '01', '10', '11')
    assert valid_teacher(cube2, uniform_teacher(cube2, 1))
    for coordinate in range(2):
        for bit in '01':
            branch = tuple(h[:coordinate] + h[coordinate+1:]
                           for h in cube2 if h[coordinate] == bit)
            assert len(branch) == 2 and uniform_teacher(branch, 0) is None
            assert valid_teacher(branch, uniform_teacher(branch, 1))
    data = Path(__file__).resolve().parents[1] / 'data'
    parameter = json.loads((data / 'parameters/112_antichain_number.json').read_text())
    assert parameter['monotonic'] is True
    for flag in ('p_monotonic', 'c_monotonic', 'doubly_monotonic',
                 'strict_c_monotonic', 'tight_strict_c_monotonic', 'strictly_monotonic'):
        assert parameter[flag] is False and parameter['monotonicity_evidence'][flag]
    print(f'Cube AN: {cube_checks} matching checks on n=0..8; exact chain counts '
          'on n=0..4; active conditioning, constant deletion, four private cubes '
          'and all two-cube equal-branch controls pass.')


def subset_teacher_iteration(previous):
    """One actual STS step: enumerate subsets of all previous minimum samples."""
    containing = {}
    for h, teacher_samples in previous.items():
        for coordinates, labels in teacher_samples:
            for size in range(len(coordinates)+1):
                for chosen in combinations(range(len(coordinates)), size):
                    s = (tuple(coordinates[j] for j in chosen),
                         tuple(labels[j] for j in chosen))
                    containing.setdefault(s, set()).add(h)
    result = {}
    for h in previous:
        identifying = [s for s, targets in containing.items() if targets == {h}]
        width = min(len(s[0]) for s in identifying)
        result[h] = {s for s in identifying if len(s[0]) == width}
    return result


def verify_repeated_cubes():
    data = Path(__file__).resolve().parents[1] / 'data'
    record = json.loads((data / 'classes/055_repeated_coordinate_cube.json').read_text())
    assert record['short_name'] == 'repeated_coordinate_cube'
    assert r'h_v(z_w)=v_1' in record['definition'] and r'2^{n-1}' in record['definition']
    iterations = folds = pairs = 0
    for n in range(1, 7):
        words = tuple(''.join(v) for v in product('01', repeat=n))
        multiplicity = 2**(n-1)
        repeated = tuple(v[0]*multiplicity + v[1:] for v in words)
        domain_size = multiplicity+n-1
        assert len(set(repeated)) == 2**n
        assert all({h[j] for h in repeated} == {'0', '1'} for j in range(domain_size))
        teacher = {h: ((int(v[1:] or '0', 2),), (v[0],))
                   for h, v in zip(repeated, words)}
        assert valid_teacher(repeated, teacher)

        def group(coordinate):
            return 0 if coordinate < multiplicity else coordinate-multiplicity+1

        def fold(sample):
            coordinates, labels = sample
            observed = {group(i): bit for i, bit in zip(coordinates, labels)}
            indices = tuple(sorted(observed))
            return indices, tuple(observed[j] for j in indices)

        # Actual all-minimum ordinary teachers, not the advertised group formula.
        if n <= 4:
            initial = {}
            for h in repeated:
                candidates = [s for s in samples(h, n)
                              if all(not consistent(s, g) for g in repeated if g != h)]
                width = min(len(s[0]) for s in candidates)
                assert width == n
                initial[h] = {s for s in candidates if len(s[0]) == width}
                assert len(initial[h]) == multiplicity
            following = subset_teacher_iteration(initial)
            assert following == initial
            assert subset_teacher_iteration(following) == following
            iterations += 2
        if n <= 3:
            for h, v in zip(repeated, words):
                for s in samples(h, domain_size):
                    collapsed = fold(s)
                    assert len(collapsed[0]) <= len(s[0]) and consistent(collapsed, v)
                    for g, w in zip(repeated, words):
                        assert consistent(s, g) == consistent(collapsed, w)
                        folds += 1

        # Explicit optimal cube map: one signed example per consecutive bit pair.
        lifted = {}
        for h, v in zip(repeated, words):
            coordinates = [i if v[i] == v[i+1] else i+1 for i in range(0, n-1, 2)]
            if n % 2:
                coordinates.append(n-1)
            cube_sample = (tuple(coordinates), tuple(v[i] for i in coordinates))
            actual = tuple(0 if i == 0 else multiplicity+i-1 for i in coordinates)
            lifted[h] = (actual, cube_sample[1])
            assert fold(lifted[h]) == cube_sample and consistent(lifted[h], h)
            assert len(actual) == (n+1)//2
        for h, g in combinations(repeated, 2):
            assert no_clash(h, lifted[h], g, lifted[g])
            pairs += 1
    for identifier in (490, 502):
        path, = (data / 'relationships').glob(f'{identifier}_*.json')
        relation = json.loads(path.read_text())
        assert relation['witness'] == '#classes/repeated_coordinate_cube'
        assert relation['witness_strength'] == 'unbounded'
    expected = {1164: '$1$', 1165: '$n$', 1166: r'$\lceil n/2\rceil$',
                1167: '$n$', 1168: '$n$', 1169: '$n$', 1170: '$2^n$',
                1171: '$n-1+2^{n-1}$'}
    for path in (data / 'values').glob('*_repeated_coordinate_cube.json'):
        value = json.loads(path.read_text())
        assert value['value'] == expected.pop(value['id'])
        assert value['proof'] and value['status'] == 'established'
    assert not expected
    print(f'Repeated cubes: six active-domain AN/NC maps, {pairs} no-clashing pairs; '
          f'{iterations} all-minimum STS iterations on n=1..4, '
          f'{folds} exhaustive consistency-preserving folds on n=1..3.')


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
    verify_cube_and_monotonicity()
    verify_repeated_cubes()


if __name__ == "__main__":
    main()
