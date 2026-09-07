#!/usr/bin/env python3
"""Exact finite checks for the triangular-word reverse range separation.

The survey proves the universal probability bound. This replay enumerates
all triangular matrices through four coordinates, including every fixed
direction-pair pattern, and checks prefix probabilities by exact counts.
"""
from collections import defaultdict
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path

from verify_upper_branch_comparisons import eluder, projected_range


def triangular_matrices(n: int) -> list[tuple[int, ...]]:
    free = [(i, j) for i in range(n) for j in range(i+1, n)]
    matrices = []
    for assignment in product((0, 1), repeat=len(free)):
        rows = [1 << i for i in range(n)]
        for (i, j), bit in zip(free, assignment):
            rows[i] |= bit << j
        matrices.append(tuple(rows + [0]))  # Row n is the permanent zero row.
    return matrices


def components(edges: tuple[tuple[int, int], ...]) -> list[set[int]] | None:
    parent: dict[int, int] = {}

    def root(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            x = parent[x]
        return x

    for u, v in edges:
        a, b = root(u), root(v)
        if a == b:
            return None  # Includes a repeated edge (a two-edge multicycle).
        parent[a] = b
    result: dict[int, set[int]] = defaultdict(set)
    for v in parent:
        result[root(v)].add(v)
    return list(result.values())


def essential_range(n: int, rows: tuple[int, ...]) -> int:
    return max(support.bit_count() for support in range(1 << n)
               if all(any((a ^ b) & support == 1 << x for a, b in combinations(rows, 2))
                      for x in range(n) if support >> x & 1))


def mathematical_audit() -> dict[str, int]:
    result = dict(classes=0, matrices=0, patterns=0, cycles=0, prefix_checks=0, fixed_bit_checks=0)
    for n in range(4):
        for mask in range(1, 1 << (1 << n)):
            rows = tuple(h for h in range(1 << n) if mask >> h & 1)
            r = essential_range(n, rows)
            assert r == projected_range(n, rows)
            e = eluder(n, rows)
            assert len(rows) <= 2**min(e, r) and max(e, r) <= len(rows)-1
            assert e <= 2**r-1 and r <= 2**e-1
            result['classes'] += 1
    for n in range(1, 5):
        matrices = triangular_matrices(n)
        total = len(matrices)
        pairs = tuple(combinations(range(n+1), 2))
        # Exact event sets: bit t represents the t-th free-bit assignment.
        compatible = {(edge, x, bit): sum(1 << t for t, rows in enumerate(matrices)
                                         if ((rows[edge[0]] ^ rows[edge[1]]) >> x & 1) == bit)
                      for edge in pairs for x in range(n) for bit in (0, 1)}
        for rows in matrices:
            assert len(set(rows)) == n+1
            assert eluder(n, rows) == n
            assert essential_range(n, rows) == projected_range(n, rows)
            result['matrices'] += 1
        for k in range(1, n+1):
            for coordinates in combinations(range(n), k):
                for edges in product(pairs, repeat=k):
                    forest = components(edges) is not None
                    previous = (1 << total)-1
                    past_coordinates = 0
                    for j, x in enumerate(coordinates):
                        current = previous
                        for r, edge in enumerate(edges):
                            current &= compatible[edge, x, int(r == j)]
                        if forest and previous:
                            assert current.bit_count() * 2**j <= previous.bit_count()
                            result['prefix_checks'] += 1
                            if n <= 3:
                                groups = components(edges[:j])
                                assert groups is not None
                                for t, rows in enumerate(matrices):
                                    if previous >> t & 1:
                                        for group in groups:
                                            assert len({rows[v] & past_coordinates for v in group}) == len(group)
                                            assert sum(v >= x for v in group) <= 1
                                            result['fixed_bit_checks'] += 1
                        previous = current
                        past_coordinates |= 1 << x
                    if not forest:
                        assert not previous
                        result['cycles'] += 1
                    else:
                        assert previous.bit_count() * 2**(k*(k-1)//2) <= total
                    result['patterns'] += 1
    # Coefficient-level proof replay of k(2+3n)-k(k-1)/2 = -3n-3.
    def multiply(a: tuple[int, ...], b: tuple[int, ...]) -> list[int]:
        return [sum(a[i]*b[j] for i in range(len(a)) for j in range(len(b)) if i+j == p)
                for p in range(len(a)+len(b)-1)]
    positive = multiply((6, 6), (2, 3))
    negative = multiply((6, 6), (5, 6))
    assert [up-Fraction(down, 2) for up, down in zip(positive, negative)] == [-3, -3, 0]
    for n in range(1, 257):
        k = 6*n+6
        assert k*(2+3*n)-k*(k-1)//2 == -3*n-3
    # The lexicographic selection is vacuous for these five small n.
    for n in range(1, 6):
        domain = 2**n
        assert 6*n+6 > domain
        rows = tuple(1 << i for i in range(domain)) + (0,)
        assert all(any((a ^ b) == 1 << x for a, b in combinations(rows, 2)) for x in range(domain))
        if n <= 3:
            assert eluder(domain, rows) == domain
    return result


def main() -> None:
    print(mathematical_audit())
    data = Path(__file__).resolve().parents[1] / 'data'
    rel = json.loads((data / 'relationships/521_projected_distinguishing_range_combinatorial_eluder_dimension.json').read_text())
    assert rel['status'] == 'refuted' and rel['witness_strength'] == 'unbounded'
    assert rel['witness'] == '#classes/triangular_code_separation'
    incomparable = json.loads((data / 'relationships/522_combinatorial_eluder_dimension_projected_distinguishing_range_incomparable.json').read_text())
    assert incomparable['status'] == 'established' and incomparable['relationship_type'] == 'incomparable'
    assert incomparable['incomparability_strength'] == 'affine'
    assert '#classes/triangular_code_separation' in incomparable['parameter_1_larger_witness']
    assert '#classes/paired_code_separation' in incomparable['parameter_2_larger_witness']
    expected = {1196: '$2^n$', 1197: '$\\Theta(n)$', 1198: '$2^n+1$', 1199: '$2^n$'}
    for path in (data / 'values').glob('[0-9]*.json'):
        record = json.loads(path.read_text())
        if record['id'] in expected:
            assert record['value'] == expected.pop(record['id'])
            assert record['class_id'] == '#classes/triangular_code_separation' and record['status'] == 'established'
    assert not expected
    print('Exact exponent polynomial, 256 evaluations, five canonical small cases and record guards pass. '
          'No large canonical tuple was computed; no bounded-versus-unbounded claim is made.')


if __name__ == '__main__':
    main()
