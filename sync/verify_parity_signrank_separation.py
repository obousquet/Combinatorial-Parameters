#!/usr/bin/env python3
"""Exact bounded checks for parity/Yang separation and functional rank control.

Atminas's partition theorem and Forster's sign-rank inequality are imported
theorems, not consequences of this finite replay. No sign-rank solver is used.
The parity benchmark uses 2n coefficient bits; d below is a diagnostic dimension.
"""
from fractions import Fraction
from functools import cache
from itertools import combinations
import json
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import sys

from verify_yang_hollow_star import load, literal_yang
from verify_upper_branch_comparisons import eluder, star, subsets
from audit_witness_strength import unbounded_verified
from audit_relationship_witnesses import reverse_bound_path


def parity_words(d: int, coordinates: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sum(((a & x).bit_count() % 2) << j for j, x in enumerate(coordinates))
                 for a in range(1 << d))


@cache
def affine_span(points: tuple[int, ...]) -> frozenset[int]:
    assert points
    origin = points[0]
    span = {0}
    for a in points:
        span |= {v ^ a ^ origin for v in tuple(span)}
    return frozenset(v ^ origin for v in span)


def affine_dimension(points: tuple[int, ...]) -> int:
    return len(affine_span(points)).bit_length() - 1


def ambiguity_faces(points: tuple[int, ...], coordinates: tuple[int, ...]) -> set[int]:
    whole = (1 << len(points)) - 1
    faces = {0}
    for x in coordinates:
        side = sum(1 << i for i, a in enumerate(points) if (a & x).bit_count() % 2)
        if side not in (0, whole):
            faces.update(subsets(side))
            faces.update(subsets(whole ^ side))
    return faces


def check_closure(points: tuple[int, ...], coordinates: tuple[int, ...]) -> int:
    faces = ambiguity_faces(points, coordinates)
    image: dict[int, int] = {}
    for face in faces - {0}:
        chosen = tuple(a for i, a in enumerate(points) if face >> i & 1)
        span = affine_span(chosen)
        closed = sum(1 << i for i, a in enumerate(points) if a in span)
        assert closed in faces and face & closed == face
        actual = tuple(a for i, a in enumerate(points) if closed >> i & 1)
        assert affine_span(actual) == span
        image[closed] = affine_dimension(actual)
        assert image[closed] < affine_dimension(points)
    for smaller, bigger in combinations(image, 2):
        if smaller & bigger == smaller:
            assert image[smaller] < image[bigger]
        if smaller & bigger == bigger:
            assert image[bigger] < image[smaller]
    return len(faces) - 1


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    calc = load('ambiguity', Path.home() / 'latex/CombinatorialParameters/scripts/explore_yang_torsion_encoding.py')
    classes = closures = literal_checks = fields = 0
    for d in range(4):
        full = tuple(range(1 << d))
        projections = {full, tuple(1 << i for i in range(d)), tuple(range(1, 1 << d))}
        # Direct subclass enumeration, including sets that are NOT affine spaces.
        for mask in range(1, 1 << (1 << d)):
            points = tuple(a for a in range(1 << d) if mask >> a & 1)
            dimension = affine_dimension(points)
            for coordinates in projections:
                encoded = parity_words(d, coordinates)
                words = tuple(sorted({encoded[a] for a in points}))
                closures += check_closure(points, coordinates)
                y = calc.yang_profile(words, len(coordinates), 2)['dimension']
                assert y <= dimension <= d
                if coordinates == full:
                    # All affine level hyperplanes are present: the nonspanning
                    # complex's value equals affine dimension on these controls.
                    assert y == dimension
                    for prime in (0, 3):
                        assert calc.yang_profile(words, len(coordinates), prime)['dimension'] == y
                        fields += 1
                if len(coordinates) <= 4:
                    assert literal_yang(len(coordinates), words) == y
                    literal_checks += 1
            classes += 1
        words = parity_words(d, full)
        if d <= 2:
            assert star(len(full), words) == eluder(len(full), words) == d
    matrices = pairs = 0
    for d in range(7):
        n = 1 << d
        words = parity_words(d, tuple(range(n)))
        assert len(set(words)) == n
        assert sum(len({h >> x & 1 for h in words}) == 2 for x in range(n)) == n - 1
        for a in range(n):
            for b in range(n):
                dot = n - 2 * (words[a] ^ words[b]).bit_count()
                assert dot == (n if a == b else 0)
                pairs += 1
        matrices += 1
    # Excluded matching size is S+2, not S: identity_t contains star t-1.
    for t in range(2, 8):
        identity = tuple(1 << i for i in range(t))
        assert star(t, identity) == t - 1
        complement = tuple(((1 << t) - 1) ^ h for h in identity)
        assert star(t, complement) == t - 1
    # All 2K2-free blocks through 3x3 have nested row neighbourhoods and
    # an explicit rank-two threshold factorization; zero padding assembles blocks.
    blocks = 0
    for mask in range(1 << 9):
        rows = tuple((mask >> (3 * i)) & 7 for i in range(3))
        if any(a & b not in (a, b) for a, b in combinations(rows, 2)):
            continue
        order = sorted(range(3), key=lambda x: sum(1 << i for i, row in enumerate(rows) if row >> x & 1))
        for row in rows:
            bits = [row >> x & 1 for x in order]
            assert bits == sorted(bits)
            first = bits.index(1) if 1 in bits else 3
            threshold = Fraction(2 * first - 1, 2)
            assert all((Fraction(j) - threshold > 0) == bool(bit) for j, bit in enumerate(bits))
        blocks += 1
    r = json.loads(next((root / 'data/relationships').glob('525_*.json')).read_text())
    assert r['relationship_type'] == 'functional_upper' and r['status'] == 'established'
    assert unbounded_verified(r, {'value_class': 'omega_1'}, {'value_class': 'omega_n'})
    assert reverse_bound_path(r, {'base': {r['parameter_1_id']: [(r['parameter_2_id'], 999)]}}) == [999]
    for id_ in (526, 527, 528):
        record = json.loads(next((root / 'data/relationships').glob(f'{id_}_*.json')).read_text())
        assert record['incomparability_strength'] == 'affine'
        assert '#classes/parity_functions' in record['parameter_1_larger_witness']
        assert '#classes/singletons_plus_empty_set' in record['parameter_2_larger_witness']
    for id_ in (1200, 1201, 1203, 1204, 1205):
        value = json.loads(next((root / 'data/values').glob(f'{id_}_*.json')).read_text())
        assert value['value'] == '$2n$' and value['class_id'] == '#classes/parity_functions'
    lower = json.loads(next((root / 'data/values').glob('1202_*.json')).read_text())
    assert lower['value'] == r'$\ge2^n$' and lower['value_class'] == 'omega_2^n'
    # An actual graph-hook comparison, not a text search: popup cards properly
    # contain functional facts even though the Hasse edges and ranks omit them.
    sys.path.insert(0, str(root.parent / 'math_database'))
    import load_utils
    graph_hook = load('parameter_graph', root / 'data/make_graph.py')
    table_cache = load_utils.get_table_entries_cache(str(root / 'data'))

    class WithoutFunctional:
        def get_table_entries(self, table):
            entries = table_cache.get_table_entries(table)
            return [e for e in entries if e.get('relationship_type') != 'functional_upper'] if table == 'relationships' else entries

        def __getattr__(self, name):
            return getattr(table_cache, name)

    with redirect_stdout(StringIO()):
        graph = graph_hook.generate(table_cache)
        removed = graph_hook.generate(WithoutFunctional())
    assert graph == removed
    assert all(edge.get('ref') != '#relationships/525' for edge in graph['edges'])
    print(f'Parity replay: {classes} subclasses, {closures} closure faces, {literal_checks} independent literal checks, {fields} extra field checks.')
    print(f'Hadamard replay: {matrices} matrices, {pairs} exact row inner products; 12 matching/star controls; {blocks} threshold blocks.')
    print('Functional orientation, affine-incomparability guards and identical graph/ranks with functional records removed pass. No universal theorem or exact sign rank is inferred from this census.')


if __name__ == '__main__':
    main()
