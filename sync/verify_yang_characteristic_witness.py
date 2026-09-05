#!/usr/bin/env python3
"""Verify the database-owned anchored torsion witness, with exact arithmetic.

The defining triples are read from the class definition, not maintained as a
second fixture. Reuse the survey's ambiguity-complex calculator; optionally
cross-check with the separate YangDim cube-interval implementation.
"""
import argparse
import importlib.util
import json
import re
from itertools import combinations
from pathlib import Path


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def determinant(matrix: list[list[int]]) -> int:
    """Fraction-free Bareiss determinant with exact divisions."""
    a = [row[:] for row in matrix]
    sign, previous = 1, 1
    for k in range(len(a) - 1):
        pivot = next((i for i in range(k, len(a)) if a[i][k]), None)
        if pivot is None:
            return 0
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            sign *= -1
        for i in range(k + 1, len(a)):
            for j in range(k + 1, len(a)):
                numerator = a[i][j] * a[k][k] - a[i][k] * a[k][j]
                assert numerator % previous == 0
                a[i][j] = numerator // previous
            a[i][k] = 0
        previous = a[k][k]
    return sign * a[-1][-1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    parser.add_argument('--survey-dir', type=Path, default=Path.home() / 'latex/CombinatorialParameters')
    parser.add_argument('--crosscheck-lattice', type=Path)
    parser.add_argument('--check-report', type=Path)
    args = parser.parse_args()
    record = json.loads((args.data_dir / 'classes/048_anchored_torsion.json').read_text())
    triples = [tuple(map(int, word)) for word in re.findall(r'\b[1-6]{3}\b', record['definition'])]
    assert len(triples) == len(set(triples)) == 10
    assert all(tuple(sorted(t)) == t and len(set(t)) == 3 for t in triples)
    h = (0,) + tuple(1 + sum(1 << i for i, f in enumerate(triples, 1) if v not in f)
                     for v in range(1, 7))
    assert len(set(h)) == 7
    calc = load_module('ambiguity_calculator', args.survey_dir / 'scripts/explore_yang_torsion_encoding.py')
    facets = tuple(sum(1 << (v - 1) for v in f) for f in triples)
    assert set(facets) | {63 ^ f for f in facets} == {sum(1 << i for i in t) for t in combinations(range(6), 3)}
    edges = list(combinations(range(1, 7), 2))
    assert {e for f in triples for e in combinations(f, 2)} == set(edges)
    cycle_edges = [e for e in edges if e[0] != 1]
    boundary = [[0] * 10 for _ in cycle_edges]
    for col, f in enumerate(triples):
        for removed in range(3):
            edge = f[:removed] + f[removed + 1:]
            if edge in cycle_edges:
                boundary[cycle_edges.index(edge)][col] = (-1) ** removed
    det = determinant(boundary)
    assert abs(det) == 2
    fields = {}
    lattice = load_module('lattice_calculator', args.crosscheck_lattice) if args.crosscheck_lattice else None
    words = tuple(tuple((concept >> i) & 1 for i in range(11)) for concept in h)
    for p in (0, 2, 3, 5):
        assert calc.homology(facets, p) == (((1, 1), (2, 1)) if p == 2 else ())
        columns = [{i: boundary[i][j] for i in range(10) if boundary[i][j]} for j in range(10)]
        assert calc.rank(columns, p) == (9 if p == 2 else 10)
        profile = calc.yang_profile(h, 11, p)
        assert profile['version_spaces'] == 75
        assert profile['dimension'] == (4 if p == 2 else 3)
        expected = {0: 7, 1: 21, 2: 35, 3: 21, 4: 1} if p == 2 else {0: 7, 1: 21, 2: 35, 3: 20}
        assert profile['total_betti'] == expected
        fields[p] = profile
        if lattice and p in (2, 3):
            totals = {}
            cubes = lattice.cube_lattice(words)
            for cube in cubes:
                below = lattice.strict_interval_below(cubes, cube)
                for q, mult in lattice.reduced_homology_of_order_complex(below, p).items():
                    totals[q + 1] = totals.get(q + 1, 0) + mult
            assert totals == expected, (p, totals, expected)
    assert max(len({concept & mask for concept in h}) for mask in (1 << x for x in range(11))) == 2
    assert all(len({(concept >> x) & 1 for concept in h}) == 2 for x in range(11))
    assert len({concept & 6 for concept in h}) == 4  # x1,x2 are shattered
    report = {'class': record['short_name'], 'coordinate_order': 'x0,...,x10',
              'concepts': [''.join(map(str, word)) for word in words],
              'cycle_edges': cycle_edges, 'integral_boundary': boundary,
              'determinant': det, 'fields': fields,
              'independent_interval_crosscheck': bool(lattice)}
    rendered = json.dumps(report, indent=2)
    if args.check_report:
        assert json.loads(rendered) == json.loads(args.check_report.read_text())
    print(rendered)


if __name__ == '__main__':
    main()
