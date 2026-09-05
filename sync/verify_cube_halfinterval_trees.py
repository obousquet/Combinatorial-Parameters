#!/usr/bin/env python3
"""Exact constrained-tree regression for cube times half-interval classes.

Enumerate coordinate subsets and all their labelled fibres; do not use the
product formula inside the solver. Cache only actual subfamilies. The
first-block decomposition is exact because suffixes start at a block boundary.
"""
from functools import lru_cache
from itertools import combinations


type Family = tuple[int, ...]


def product_class(m: int, n: int) -> Family:
    return tuple(sorted(a | (((1 << i) - 1) << m)
                        for a in range(1 << m) for i in range(1, n + 1)))


def evaluators(width: int):
    masks = {q: [sum(1 << i for i in subset) for subset in combinations(range(width), q)]
             for q in range(width + 1)}

    def fibres(family: Family, mask: int) -> tuple[Family, ...]:
        parts: dict[int, list[int]] = {}
        for h in family:
            parts.setdefault(h & mask, []).append(h)
        return tuple(tuple(part) for part in parts.values()) if len(parts) == 1 << mask.bit_count() else ()

    @lru_cache(None)
    def vc(family: Family) -> int:
        return max(q for q in masks if any(fibres(family, mask) for mask in masks[q]))

    @lru_cache(None)
    def block(family: Family, k: int) -> int:
        answer = min(vc(family), k - 1)
        for mask in masks.get(k, []):
            parts = fibres(family, mask)
            if parts:
                answer = max(answer, k + min(block(part, k) for part in parts))
        return answer

    @lru_cache(None)
    def prefix(family: Family, k: int) -> int:
        answer = min(vc(family), k - 1)
        for mask in masks.get(k, []):
            parts = fibres(family, mask)
            if parts:
                answer = max(answer, k + min(block(part, 1) for part in parts))
        return answer

    return vc, block, prefix


def main() -> None:
    checked = 0
    for m in range(1, 4):
        for n in range(2, 9):
            family = product_class(m, n)
            vc, block, prefix = evaluators(m + n)
            ell = n.bit_length() - 1
            assert vc(family) == m + 1
            assert block(family, 1) == m + ell
            for k in range(2, 6):
                b = block(family, k)
                pl = prefix(family, k)
                assert b == m + min(ell, m // (k - 1) + 1), (m, n, k, b)
                assert pl == (m + ell if k <= m + 1 else m + 1), (m, n, k, pl)
                checked += 1
            print(f"m={m}, n={n}: exact VC/L/B2..B5/PL2..PL5 passed", flush=True)
    print(f"All {checked} product/block-size cases passed; includes truncated blocks and k>VC.")


if __name__ == '__main__':
    main()
