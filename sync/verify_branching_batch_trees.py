#!/usr/bin/env python3
"""Exact finite checks for zero-extended paths in branching batch trees.

Enumerate all realizable traces, including off-path zero labels. The generic
dimension solver does not assume that shattered coordinates share a tree node.
Full optimization is limited to domains of at most ten coordinates; larger
cases check exact VC, all path realizers, and the matching leaf-count bound.
"""
import argparse
import json
from functools import lru_cache
from itertools import product
from pathlib import Path

type Family = tuple[int, ...]


def branching_class(b: int, n: int):
    alphabet = range(1 << b)
    nodes = [v for depth in range(n) for v in product(alphabet, repeat=depth)]
    coordinates = [(v, j) for v in nodes for j in range(b)]
    index = {x: i for i, x in enumerate(coordinates)}
    leaves = list(product(alphabet, repeat=n))
    concepts = []
    for leaf in leaves:
        h = 0
        for depth, letter in enumerate(leaf):
            for j in range(b):
                if letter & (1 << j):
                    h |= 1 << index[(leaf[:depth], j)]
        concepts.append(h)
    return tuple(sorted(concepts)), coordinates, dict(zip(leaves, concepts))


def evaluators(width: int):
    def fibres(family: Family, mask: int) -> tuple[Family, ...]:
        groups: dict[int, list[int]] = {}
        for h in family:
            groups.setdefault(h & mask, []).append(h)
        return tuple(tuple(v) for v in groups.values())

    @lru_cache(None)
    def shattered(family: Family) -> tuple[int, ...]:
        found = []
        def extend(mask: int, start: int) -> None:
            found.append(mask)
            for x in range(start, width):
                larger = mask | (1 << x)
                if len(fibres(family, larger)) == 1 << larger.bit_count():
                    extend(larger, x + 1)
        extend(0, 0)
        return tuple(found)

    @lru_cache(None)
    def block(family: Family, k: int) -> int:
        masks = shattered(family)
        best = min(k - 1, max(mask.bit_count() for mask in masks))
        for mask in masks:
            if mask.bit_count() == k:
                best = max(best, k + min(block(part, k) for part in fibres(family, mask)))
        return best

    def prefix(family: Family, k: int) -> int:
        masks = shattered(family)
        best = min(k - 1, max(mask.bit_count() for mask in masks))
        for mask in masks:
            if mask.bit_count() == k:
                best = max(best, k + min(block(part, 1) for part in fibres(family, mask)))
        return best

    return shattered, block, prefix


def check_compression(family: Family, coordinates, paths, b: int) -> int:
    """Replay the DB-owned closure scheme; no solver or inferred decoder labels."""
    members = set(family)
    supports = {h: frozenset(i for i in range(len(coordinates)) if h >> i & 1)
                for h in family}
    for word, h in paths.items():
        last_batch = [i for i, (v, _) in enumerate(coordinates) if v == word[:-1]]
        assert len(last_batch) == b
        assert all(h ^ (1 << i) in members for i in last_batch)
        for other, g in paths.items():
            # Check both the literal intersection and the claimed leaf construction.
            intersection = h & g
            assert intersection in members
            assert supports[intersection] == supports[h] & supports[g]
            if word != other:
                split = next(i for i, (a, a2) in enumerate(zip(word, other)) if a != a2)
                merged = word[:split] + (word[split] & other[split],) + (0,) * (len(word) - split - 1)
                assert paths[merged] == intersection
    if len(coordinates) > 10:
        return 0  # Structural checks only: never enumerate 3^42 partial samples.

    order = sorted(family, key=lambda h: (h.bit_count(), h))

    @lru_cache(None)
    def closure(positive: int) -> int:
        extensions = [h for h in family if h & positive == positive]
        assert extensions
        result = extensions[0]
        for h in extensions[1:]:
            result &= h
        assert result in members
        return result

    @lru_cache(None)
    def basis(positive: int) -> int:
        key = positive
        for x in range(len(coordinates)):
            if key >> x & 1 and closure(key ^ (1 << x)) == closure(positive):
                key ^= 1 << x
        assert key.bit_count() <= b
        assert all(closure(key ^ (1 << x)) != closure(key)
                   for x in range(len(coordinates)) if key >> x & 1)
        return key

    # Reverse the support order to obtain and independently replay a teaching plan.
    remaining = set(family)
    for h in reversed(order):
        key = basis(h)
        assert [g for g in remaining if g & key == key] == [h]
        remaining.remove(h)

    count = 0
    for mask in range(1 << len(coordinates)):
        for positive in {h & mask for h in family}:
            key = basis(positive)
            q_sample = next(h for h in order if h & mask == positive)
            q_key = next(h for h in order if h & key == key)
            assert q_sample == q_key == closure(positive)
            # An independent literal-set replay checks every retained/omitted label.
            sample = {(x, (positive >> x) & 1) for x in range(len(coordinates))
                      if mask >> x & 1}
            literal_key = {(x, 1) for x in range(len(coordinates)) if key >> x & 1}
            assert literal_key <= sample
            decoded = next(h for h in order
                           if all(int(x in supports[h]) == y for x, y in literal_key))
            assert all(int(x in supports[decoded]) == y for x, y in sample)
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compression-only', action='store_true',
                        help='skip the older recursive tree-depth optimizations')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    for number, parameter in [(1153, 'proper_ordered_sample_compression'),
                              (1154, 'order_sample_compression'),
                              (1155, 'recursive_teaching_dimension'),
                              (1156, 'monotone_recursive_teaching_dimension')]:
        record = json.loads((root / 'data' / 'values' /
                            f'{number}_{parameter}_branching_batch_tree.json').read_text())
        assert record['value'] == '$b$' and record['status'] == 'established'
        assert record['class_id'] == '#classes/branching_batch_tree'
        assert record['parameter_id'] == f'#parameters/{parameter}'
    cases = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]
    optimized = 0
    samples = 0
    for b, n in cases:
        family, coordinates, paths = branching_class(b, n)
        width = len(coordinates)
        assert len(set(family)) == len(family) == 1 << (b * n)
        assert width == b * ((1 << (b * n)) - 1) // ((1 << b) - 1)
        shattered, block, prefix = evaluators(width)
        masks = shattered(family)
        assert max(mask.bit_count() for mask in masks) == b
        for mask in masks:
            owners = {v for i, (v, _) in enumerate(coordinates) if mask & (1 << i)}
            assert len(owners) <= 1, (b, n, mask, owners)
        # Every leaf realizes its prescribed path, with zero on every off-path node.
        for leaf, h in paths.items():
            for i, (v, j) in enumerate(coordinates):
                expected = (leaf[len(v)] >> j) & 1 if leaf[:len(v)] == v else 0
                assert (h >> i) & 1 == expected
        replayed = check_compression(family, coordinates, paths, b)
        samples += replayed
        if width <= 10 and not args.compression_only:
            assert block(family, 1) == b * n
            assert block(family, b) == b * n
            for k in range(2, b + 3):
                assert prefix(family, k) == (b * n if k <= b else b)
                value = block(family, k)
                assert max(b, k * n * (b // k)) <= value <= b * n
                if k > b:
                    assert value == b
                elif b % k == 0:
                    assert value == b * n
            optimized += 1
        print(f'b={b}, n={n}: {len(family)} concepts, {width} coordinates, VC={b}; '
              f'path depth={b*n}; full optimization={width <= 10 and not args.compression_only}; '
              f'order samples={replayed}', flush=True)
    print(f'All {len(cases)} families passed; {optimized} independently optimized.')
    print(f'Intersection/last-batch checks passed; {samples} proper order samples; '
          'four database value guards.')


if __name__ == '__main__':
    main()
