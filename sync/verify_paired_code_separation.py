#!/usr/bin/env python3
"""Finite audits of the paired-code probabilistic separation proof.

This does NOT find the canonical large tuple or estimate a random asymptotic
ratio. The universal existence/extraction proofs are in the survey. It checks
the conditional event probabilities, paired-witness extraction, essential
coordinates, collisions, and the exact exponent used in that proof.
"""
from fractions import Fraction
from itertools import permutations, product
import json
from pathlib import Path

from verify_upper_branch_comparisons import eluder, projected_range


def pair_words(words: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({h for i, w in enumerate(words) for h in (w, w ^ (1 << i))}))


def check_extraction(words: tuple[int, ...]) -> int:
    """Enumerate actual anchored sequences, then extract distinct pair rows."""
    n = len(words)
    concepts = pair_words(words)
    representation = {h: next(i for i, w in enumerate(words) if h in (w, w ^ (1 << i)))
                      for h in concepts}
    count = 0
    for base in concepts:
        anchor = representation[base]

        def walk(support: int, sequence: tuple[tuple[int, int], ...]) -> None:
            nonlocal count
            selected = []
            groups = set()
            assert len({h for _, h in sequence}) == len(sequence)
            for x, h in sequence:
                group = representation[h]
                if group != anchor and group not in groups:
                    groups.add(group)
                    selected.append((x, h))
            # t <= 1 + 2k, where k is the number of nonanchor pairs used.
            assert len(sequence) <= 1 + 2*len(selected)
            for j, (x, h) in enumerate(selected):
                assert (h ^ base) >> x & 1
                assert all(not ((h ^ base) >> y & 1) for y, _ in selected[:j])
            count += 1
            for x in range(n):
                if support >> x & 1:
                    continue
                for h in concepts:
                    if not ((h ^ base) & support) and (h ^ base) >> x & 1:
                        walk(support | (1 << x), sequence + ((x, h),))

        walk(0, ())
    return count


def probability_audit() -> int:
    """Exact conditional probabilities, independent literal-bit evaluation."""
    checks = 0
    for n in (2, 3):
        rows = tuple(product((0, 1), repeat=n))
        for m in range(1, n):
            for a in range(n):
                for indices in permutations([i for i in range(n) if i != a], m):
                    for coordinates in permutations(range(n), m):
                        for signs in product((0, 1), repeat=m+1):
                            for anchor_word in rows:
                                anchor = tuple(b ^ (signs[0] if x == a else 0)
                                               for x, b in enumerate(anchor_word))
                                hits = 0
                                for trial in product(rows, repeat=m):
                                    witnesses = [tuple(b ^ (signs[j+1] if x == indices[j] else 0)
                                                       for x, b in enumerate(word))
                                                 for j, word in enumerate(trial)]
                                    hits += all(witnesses[j][coordinates[j]] != anchor[coordinates[j]]
                                                and all(witnesses[j][coordinates[k]] == anchor[coordinates[k]]
                                                        for k in range(j)) for j in range(m))
                                assert Fraction(hits, len(rows)**m) == Fraction(1, 2**(m*(m+1)//2))
                                checks += 1
    return checks


def main() -> None:
    tuples = sequences = collisions = 0
    for n in range(1, 4):
        for words in product(range(1 << n), repeat=n):
            concepts = pair_words(words)
            # Every coordinate has its actual one-bit pair, even with collisions.
            assert all(w in concepts and w ^ (1 << i) in concepts for i, w in enumerate(words))
            assert projected_range(n, concepts) == n
            assert n+1 <= len(concepts) <= 2*n
            sequences += check_extraction(words)
            collisions += len(concepts) < 2*n
            tuples += 1
    probabilities = probability_audit()
    # Polynomial-coefficient audit of the universal exponent identity.
    def multiply(a: tuple[int, ...], b: tuple[int, ...]) -> list[int]:
        return [sum(a[i]*b[j] for i in range(len(a)) for j in range(len(b)) if i+j == k)
                for k in range(len(a)+len(b)-1)]
    positive = multiply((2, 4), (1, 2))  # m(1+2n)
    negative = multiply((2, 4), (3, 4))  # m(m+1)
    assert [Fraction(start) + up - Fraction(down, 2)
            for start, up, down in zip((1, 1, 0), positive, negative)] == [0, -1, 0]
    for n in range(1, 257):
        m = 4*n + 2
        exponent = 1+n + m*(1+2*n) - m*(m+1)//2
        assert exponent == -n and Fraction(1, 2**n) < 1
    # Canonical selection is vacuous for n <= 4: m > N-1. The first tuple
    # is all zero words, so its class is the singleton-plus-empty family.
    for n in range(1, 5):
        domain = 2**n
        assert 4*n + 2 > domain-1
        words = (0,)*domain
        concepts = pair_words(words)
        assert len(concepts) == domain+1
        if n <= 3:
            assert eluder(domain, concepts) == domain <= 8*n+3
    data = Path(__file__).resolve().parents[1] / 'data'
    rel = json.loads((data / 'relationships/395_combinatorial_eluder_dimension_projected_distinguishing_range.json').read_text())
    assert rel['status'] == 'refuted' and rel['witness_strength'] == 'unbounded'
    assert rel['witness'] == '#classes/paired_code_separation'
    assert rel['latex_proof_label'] == 'cor:paired-code-range-separation'
    expected = {1192: '$2^n$', 1193: '$\\Theta(n)$',
                1194: '$\\Theta(2^n)$', 1195: '$2^n$'}
    for path in (data / 'values').glob('[0-9]*.json'):
        record = json.loads(path.read_text())
        if record['id'] in expected:
            assert record['value'] == expected.pop(record['id'])
            assert record['status'] == 'established' and record['class_id'] == '#classes/paired_code_separation'
    assert not expected
    print(f'{tuples} paired tuples ({collisions} with repeated concepts), '
          f'{sequences} anchored sequence prefixes, {probabilities} exact conditional probabilities pass.')
    print('Exact exponent polynomial, 256 exponent evaluations, four canonical small cases, and record guards pass. '
          'No large-tuple search or asymptotic inference from numerical samples.')


if __name__ == '__main__':
    main()
