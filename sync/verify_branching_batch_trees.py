#!/usr/bin/env python3
"""Exact finite checks for zero-extended paths in branching batch trees.

Enumerate all realizable traces, including off-path zero labels. The generic
dimension solver does not assume that shattered coordinates share a tree node.
Full optimization is limited to domains of at most ten coordinates; larger
cases check exact VC, all path realizers, and the matching leaf-count bound.
"""
from functools import lru_cache
from itertools import product

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


def main() -> None:
    cases = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]
    optimized = 0
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
        if width <= 10:
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
              f'path depth={b*n}; full optimization={width <= 10}', flush=True)
    print(f'All {len(cases)} families passed; {optimized} independently optimized.')


if __name__ == '__main__':
    main()
