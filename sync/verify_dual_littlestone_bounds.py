#!/usr/bin/env python3
"""Check the dual counting bound and witness orientation on small classes."""

from functools import lru_cache
from itertools import combinations, product
from math import floor, log2

from audit_witness_strength import strict_verified, unbounded_verified


@lru_cache(None)
def littlestone(rows: tuple[tuple[int, ...], ...]) -> int:
    if len(rows) <= 1:
        return 0
    best = 0
    for coordinate in range(len(rows[0])):
        zero = tuple(row for row in rows if not row[coordinate])
        one = tuple(row for row in rows if row[coordinate])
        if zero and one:
            best = max(best, 1 + min(littlestone(zero), littlestone(one)))
    return best


def main() -> None:
    checked = 0
    for n in range(1, 4):
        cube = list(product((0, 1), repeat=n))
        for size in range(1, len(cube) + 1):
            for family in combinations(cube, size):
                dual = tuple(sorted(set(zip(*family))))
                effective = sum(len(set(column)) == 2 for column in zip(*family))
                dimension = littlestone(dual)
                assert dimension <= floor(log2(effective + 2))
                assert dimension <= size
                checked += 1
    # E=0 still allows two distinct constant functions in the dual.
    assert littlestone(((0,), (1,))) == 1
    relation = {"relationship_type": "log_upper", "status": "established"}
    small = {"value": "$1$", "value_class": "omega_1"}
    large = {"value": "$8$", "value_class": "omega_n"}
    assert strict_verified(relation, small, large) is True
    assert strict_verified(relation, large, small) is False
    assert unbounded_verified(relation, small, large) is True
    assert unbounded_verified(relation, large, small) is False
    relation["status"] = "refuted"
    assert strict_verified(relation, large, small) is True
    assert unbounded_verified(relation, large, small) is True
    print(f"Dual Littlestone counting bound checked on {checked} classes; upper-bound witness orientation passed.")


if __name__ == "__main__":
    main()
