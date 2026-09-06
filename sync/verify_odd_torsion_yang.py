#!/usr/bin/env python3
"""Verify the database's Odd-Torsion Dual Class and its Yang separation.

This tests the native construction and its extremal version-space bounds,
not a full Betti census on the resulting 220-coordinate Boolean class.
"""
import argparse
import importlib.util
import json
import re
from itertools import combinations
from pathlib import Path


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def construction(prime: int = 3):
    # u_0,u_1,u_2=0,1,2; v_i=3+i; cone vertex=3+3p.
    m = 3 * prime + 4
    triangles = set()
    for i in range(3 * prime):
        u, unext = i % 3, (i + 1) % 3
        v, vnext = 3 + i, 3 + (i + 1) % (3 * prime)
        for t in ((v, u, unext), (v, vnext, unext), (m - 1, v, vnext)):
            triangles.add(tuple(sorted(t)))
    original = sorted(triangles)
    edges = {e for t in triangles for e in combinations(t, 2)}
    expansions = []
    while len(edges) < m * (m - 1) // 2:
        choices = [(a, b, w) for a, b in combinations(range(m), 2) if (a, b) not in edges
                   for w in range(m) if w not in (a, b)
                   and tuple(sorted((a, w))) in edges and tuple(sorted((b, w))) in edges]
        a, b, w = min(choices)
        edges.add((a, b))
        triangles.add(tuple(sorted((a, b, w))))
        expansions.append((a, b, w))
    missing = sorted(set(combinations(range(m), 3)) - triangles)
    # No tetrahedral boundary: a useful separate check of minimal nonfaces.
    assert not any(all(t in triangles for t in combinations(s, 3)) for s in combinations(range(m), 4))
    whole = (1 << m) - 1
    facets = tuple(whole ^ sum(1 << v for v in t) for t in missing)
    # All small complementary halves must be absorbed in the Alexander dual.
    assert all(any((whole ^ f) & g == whole ^ f for g in facets) for f in facets)
    concepts = tuple(sum(1 << i for i, t in enumerate(missing) if v in t) for v in range(m))
    assert len(set(concepts)) == m
    boundary_witnesses = []
    for f in facets:
        if all(any(g != f and (f ^ (1 << v)) & g == f ^ (1 << v) and not g & (1 << v)
                   for g in facets) for v in range(m) if f & (1 << v)):
            boundary_witnesses.append(f)
    return m, original, sorted(triangles), expansions, missing, facets, concepts, boundary_witnesses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parents[1] / 'data')
    parser.add_argument('--survey-dir', type=Path, default=Path.home() / 'latex/CombinatorialParameters')
    parser.add_argument('--check-report', type=Path)
    args = parser.parse_args()
    record = json.loads((args.data_dir / 'classes/049_odd_torsion_dual.json').read_text())
    # The record is the construction's specification, not a second triangle
    # fixture. This program implements its three triangles and lexicographic
    # elementary expansions; the report is derived output only.
    prime = int(re.search(r'r=(\d+)', record['definition']).group(1))
    assert prime == 3
    calc = load('ambiguity', args.survey_dir / 'scripts/explore_yang_torsion_encoding.py')
    verifier = load('yang_verifier', Path(__file__).with_name('verify_yang_characteristic_witness.py'))
    m, original, triangles, expansions, missing, facets, concepts, witnesses = construction(prime)
    cycles = list(combinations(range(1, m), 2))
    matrix = [[0] * len(triangles) for _ in cycles]
    for j, t in enumerate(triangles):
        for i in range(3):
            e = t[:i] + t[i+1:]
            if e in cycles:
                matrix[cycles.index(e)][j] = (-1) ** i
    assert len(matrix) == len(triangles)
    det = verifier.determinant(matrix)
    assert abs(det) == 3
    columns = [{i: matrix[i][j] for i in range(len(matrix)) if matrix[i][j]}
               for j in range(len(triangles))]
    generator = {cycles.index((1, 2)): 1}  # cycle 0,1,2 after tree contraction
    assert calc.rank(columns, 3) == 65
    assert calc.rank(columns + [generator], 3) == 66
    homology = {p: calc.homology(tuple(sum(1 << v for v in t) for t in triangles), p)
                for p in (0, 2, 3, 5)}
    assert homology == {0: (), 2: (), 3: ((1, 1), (2, 1)), 5: ()}
    # Independently check the actual top boundary of the Boolean ambiguity
    # complex, not merely the predicted Alexander-duality shift.
    top_columns = []
    for f in facets:
        vertices = [v for v in range(m) if f & (1 << v)]
        top_columns.append({f ^ (1 << v): (-1) ** i for i, v in enumerate(vertices)})
    top_ranks = {p: calc.rank(top_columns, p) for p in (0, 2, 3, 5)}
    assert top_ranks == {0: 220, 2: 220, 3: 219, 5: 220}
    assert witnesses
    assert (0, 1, 2) in missing and (0, 2, 4) in missing and (0, 3, 4) in missing
    # Exact all-version-space size classification; no homology enumeration.
    all_concepts = (1 << len(concepts)) - 1
    columns = [sum(1 << i for i, h in enumerate(concepts) if h & (1 << x))
               for x in range(len(missing))]
    spaces = {all_concepts}
    for col in columns:
        spaces |= {part for s in tuple(spaces) for part in (s & col, s & (all_concepts ^ col)) if part}
    proper_max = max(s.bit_count() for s in spaces if s != all_concepts)
    assert proper_max == m - 3
    f = witnesses[0]
    s = f
    assert s in spaces and s.bit_count() == m - 3
    halves = {s & col for col in columns if 0 < s & col < s}
    halves |= {s ^ half for half in tuple(halves)}
    assert all(s ^ (1 << v) in halves for v in range(m) if s & (1 << v))
    assert [v for v in range(m) if s & (1 << v)] == list(range(3, 13))
    assert all(col.bit_count() == 3 for col in columns)
    vc_pair = [missing.index(t) for t in ((0, 1, 2), (0, 2, 4))]
    assert len({tuple((h >> x) & 1 for x in vc_pair) for h in concepts}) == 4
    report = {'class': record['short_name'], 'vertices': m,
                     'initial_triangles': original, 'elementary_expansions': expansions,
                     'triangles': triangles, 'missing_triangles': len(missing), 'determinant': det,
                     'homology_of_source': homology, 'top_ambiguity_boundary_ranks': top_ranks,
                     'concept_count': len(concepts),
                     'coordinate_count': len(columns), 'version_spaces': len(spaces),
                     'nonexceptional_proper_size_max': proper_max,
                     'simplex_boundary_space_old_vertices': [v for v in range(m) if f & (1 << v)],
                     'simplex_boundary_degree': s.bit_count()-1,
                     'Y3': m-3, 'Y0_and_other_prime_values': m-4,
                     'VC': 2, 'Littlestone': 2,
                     'scope': 'Top boundary ranks, integral source and all version-space sizes; not a full Betti census.'}
    rendered = json.dumps(report, indent=2)
    if args.check_report:
        assert json.loads(rendered) == json.loads(args.check_report.read_text())
    print(rendered)


if __name__ == '__main__':
    main()
