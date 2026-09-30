#!/usr/bin/env python3
"""Replay the existing finite witnesses used in the Q2g correction.

Uses the existing minimax solver with accepting replies and original-class
proper proposals. This is finite evidence, not a proof of the general claims.
"""
from itertools import combinations
from verify_singleton_queries_projections import query_value


def teaching(words, n):
    return max(min(len(xs) for k in range(n + 1)
                   for xs in combinations(range(n), k)
                   if all(g == h or any(((g ^ h) >> x) & 1 for x in xs)
                          for g in words)) for h in words)


def star(words, n):
    return max(len(xs) for h in words for k in range(n + 1)
               for xs in combinations(range(n), k)
               if all(any(all(((g ^ h) >> y) & 1 == (y == x) for y in xs)
                          for g in words) for x in xs))


def main():
    for n in range(2, 6):
        words = (0,) + tuple(1 << x for x in range(n))
        assert query_value(words, n, 'proper') == 1
        assert teaching(words, n) == star(words, n) == n
    words = tuple(int(w, 2) for w in ('0001', '0011', '0100', '1000'))
    projected = tuple(sorted({w >> 1 for w in words}))
    assert query_value(words, 4, 'membership') == 2
    assert query_value(projected, 3, 'membership') == 3
    assert query_value((1, 2, 4), 3, 'proper') == 2
    assert query_value((0,), 3, 'proper') == 0
    print('PASS: center-plus-singletons n=2..5 gives Qpeq=1, TD=star=n; membership projection 2->3; proper subclass 1->2; singleton cost0. No global classification certified.')


if __name__ == '__main__':
    main()
