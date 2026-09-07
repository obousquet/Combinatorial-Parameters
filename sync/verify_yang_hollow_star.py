#!/usr/bin/env python3
"""Bounded replay of hollow-star Yang bounds and the plane-deletion diagnostic.

Universal proofs live in the survey. Compare two homological formulations on
all classes through three coordinates, not a proxy such as VC dimension.
The plane enumeration concerns only the q^2 relevant independent bits at
q=2,3; it does not calculate sign rank or enumerate all incidence deletions.
"""
from fractions import Fraction
from functools import cache
import importlib.util
import json
from pathlib import Path

from verify_upper_branch_comparisons import star, subsets


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def binary_rank(columns: list[int]) -> int:
    basis: dict[int, int] = {}
    for column in columns:
        while column:
            pivot = column.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = column
                break
            column ^= basis[pivot]
    return len(basis)


@cache
def literal_homology(facets: tuple[int, ...]) -> tuple[int, ...]:
    """Independent bit-matrix boundaries, with the augmented empty face."""
    faces = {part for facet in facets for part in subsets(facet)}
    by_size = {size: sorted(f for f in faces if f.bit_count() == size)
               for size in range(max(faces).bit_length() + 2)}
    if faces == {0}:
        return (-1,)
    top = max(f.bit_count() for f in faces)
    ranks = {top + 1: 0}
    for size in range(1, top + 1):
        rows = {f: i for i, f in enumerate(by_size[size - 1])}
        columns = [sum(1 << rows[f ^ (1 << x)] for x in range(f.bit_length())
                       if f >> x & 1) for f in by_size[size]]
        ranks[size] = binary_rank(columns)
    return tuple(size - 1 for size in range(1, top + 1)
                 if len(by_size[size]) - ranks[size] - ranks[size + 1])


def literal_yang(n: int, words: tuple[int, ...]) -> int:
    facets = [sum(1 << (2 * x + (h >> x & 1)) for x in range(n)) for h in words]
    best = 0
    for selected in range(1 << (2 * n)):
        restricted = tuple(sorted({f & selected for f in facets}))
        best = max(best, max((j + 1 for j in literal_homology(restricted)), default=0))
    return best


def covc(n: int, words: tuple[int, ...]) -> int:
    best = 0
    for support in range(1 << n):
        traces = {h & support for h in words}
        for missing in subsets(support):
            if missing not in traces and all(missing ^ (1 << x) in traces
                                            for x in range(n) if support >> x & 1):
                best = max(best, support.bit_count())
    return best


def check_classes(calc) -> int:
    checked = 0
    for n in range(4):
        monotone_yang: dict[int, int] = {0: 0}
        monotone_hollow: dict[int, int] = {0: 0}
        for mask in range(1, 1 << (1 << n)):
            words = tuple(h for h in range(1 << n) if mask >> h & 1)
            y = literal_yang(n, words)
            assert all(calc.yang_profile(words, n, p)['dimension'] == y for p in (0, 2, 3))
            c = covc(n, words)
            s = star(n, words)
            monotone_yang[mask] = max([y] + [monotone_yang[mask ^ (1 << h)] for h in words])
            monotone_hollow[mask] = max([c] + [monotone_hollow[mask ^ (1 << h)] for h in words])
            assert y >= c - 1, (n, words, y, c)
            assert monotone_hollow[mask] == max(s, c), (n, words)
            assert monotone_yang[mask] >= monotone_hollow[mask] - 1
            checked += 1
    return checked


def check_boundary_values(calc) -> int:
    checked = 0
    for n in range(1, 6):
        words = (0,) + tuple(1 << x for x in range(n))
        dimensions = [calc.yang_profile(tuple(h for i, h in enumerate(words) if mask >> i & 1),
                                       n, 2)['dimension']
                      for mask in range(1, 1 << len(words))]
        assert max(dimensions) == max(1, n - 1)
        if n <= 3:
            assert calc.yang_profile(tuple(range(1 << n)), n, 2)['dimension'] == n
        checked += len(dimensions)
    assert calc.yang_profile((0, 1), 1, 2)['dimension'] == 1  # rejects old n-1 value
    return checked


def multiply(a: list[int], b: list[int]) -> list[int]:
    result = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i + j] += x * y
    return result


def check_planes(geometry) -> tuple[int, int, int]:
    pairs = patterns = evaluations = 0
    for q in (2, 3):
        lines = geometry.projective_lines(q)
        n = len(lines)
        # Every ordered pair of original lines satisfies the trial geometry.
        for l0 in range(n):
            for l in range(n):
                if l0 == l:
                    continue
                domain = sorted(set(lines[l]) - set(lines[l0]))
                assert len(domain) == q
                trials = [(i, x) for x in domain for i, line in enumerate(lines)
                          if i != l and x in line]
                assert len(trials) == len(set(trials)) == q * q
                assert all(set(lines[i]) & set(domain) == {x} for i, x in trials)
                pairs += 1
        domain = sorted(set(lines[1]) - set(lines[0]))
        groups = [[(i, x) for i, line in enumerate(lines) if i != 1 and x in line]
                  for x in domain]
        trials = [trial for group in groups for trial in group]
        success = 0
        for assignment in range(1 << (q * q)):
            rows = [0] * n
            for bit, (i, x) in enumerate(trials):
                if assignment >> bit & 1:
                    rows[i] |= 1 << x
            good = all(any(assignment >> (j * q + a) & 1 for a in range(q)) for j in range(q))
            traces = {row & sum(1 << x for x in domain) for row in rows}
            assert good == ({0} | {1 << x for x in domain} <= traces)
            success += good
            patterns += 1
        probability = Fraction(success, 1 << (q * q))
        assert probability == (1 - Fraction(1, 2**q)) ** q
        assert probability >= 1 - Fraction(q, 2**q)
        # Explicit polynomial factorization on three fixed deletion outcomes.
        for mode in range(3):
            for i, line in enumerate(lines):
                positive = [x for x in line if mode == 0 or (mode == 1 and (i + x) % 2)]
                poly = [1]
                for x in positive:
                    poly = multiply(poly, [x * x, -2 * x, 1])
                poly = [-2 * a for a in poly]
                poly[0] += 1  # twice p_A, avoiding fractions
                assert len(poly) <= 2 * q + 3
                for x in range(n):
                    value = sum(a * x**j for j, a in enumerate(poly))
                    assert (value > 0) == (x in positive) and value != 0
                    evaluations += 1
    return pairs, patterns, evaluations


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    survey = Path.home() / 'latex/CombinatorialParameters'
    calc = load('yang_ambiguity', survey / 'scripts/explore_yang_torsion_encoding.py')
    geometry = load('plane_geometry', survey / 'scripts/verify_geometric_containers.py')
    print(f'All {check_classes(calc)} small classes: independent literal/ambiguity homology and hollow-star bounds pass.')
    print(f'Singleton-plus-empty boundary replay: {check_boundary_values(calc)} subfamilies pass.')
    pairs, patterns, evaluations = check_planes(geometry)
    print(f'Plane replay: {pairs} line pairs, {patterns} relevant-bit patterns, {evaluations} polynomial evaluations pass.')
    for id_, left, right in [(523, 'yang_dimension', 'covc_dimension'),
                             (524, 'monotonic_yang_dimension', 'monotonic_covc_dimension')]:
        record = json.loads(next((root / 'data/relationships').glob(f'{id_}_*.json')).read_text())
        assert record['parameter_1_id'] == '#parameters/' + left
        assert record['parameter_2_id'] == '#parameters/' + right
        assert record['status'] == 'established' and record['relationship_type'] == 'larger_c'
        assert record['multiplicative_constant'] == record['additive_constant'] == '1'
        assert record['latex_proof_label'] == 'prop:yang-hollow-star'
    value = json.loads(next((root / 'data/values').glob('584_*.json')).read_text())
    assert value['value'] == r'$\max\{1,n-1\}$'
    print('Record orientations, affine offsets, proof pointers and n=1 correction pass.')


if __name__ == '__main__':
    main()
