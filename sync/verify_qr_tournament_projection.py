#!/usr/bin/env python3
"""Bounded regression for class #41's signed extensions and NC teacher.

This checks the database definition directly. It is not a computation of
projected NCTD or a proof of the all-prime character-sum theorem.
"""

from itertools import combinations, islice


def qr_class(p: int) -> tuple[int, ...]:
    assert p % 4 == 3 and all(p % d for d in range(2, int(p**0.5) + 1))
    residues = {x * x % p for x in range(1, p)}
    return tuple(
        sum(1 << b for b in range(p) if (a - b) % p in residues)
        for a in range(p)
    )


def external_patterns(words: tuple[int, ...], coords: tuple[int, ...]) -> set[int]:
    return {
        sum(((word >> b) & 1) << j for j, b in enumerate(coords))
        for a, word in enumerate(words)
        if a not in coords
    }


def main() -> None:
    checked_sets = checked_pairs = 0
    for p in (3, 7, 19, 23, 31, 163):
        words = qr_class(p)
        assert len(set(words)) == p
        # Coordinate a has label zero in C_a. For each pair, one of these
        # singleton teachers is inconsistent with the other concept.
        for a, b in combinations(range(p), 2):
            assert not (words[a] >> a) & 1
            assert ((words[a] >> b) & 1) != ((words[b] >> a) & 1)
            checked_pairs += 1
        k = 1
        while p > (k + 1) ** 2 * 2 ** (2 * (k + 1) - 2):
            k += 1
        coordinate_sets = combinations(range(p), k)
        # Exhaust all sets for p<=31; only a declared fixed pilot for p=163.
        if p == 163:
            coordinate_sets = islice(coordinate_sets, 64)
        count = 0
        for coords in coordinate_sets:
            assert external_patterns(words, coords) == set(range(1 << k))
            count += 1
        checked_sets += count
        print(f"p={p}: k={k}, {count} signed-extension sets checked")

    # Outside the theorem's numerical hypothesis, extension can fail.
    assert external_patterns(qr_class(3), (0, 1)) != set(range(4))
    # Independently count cube edges used by the lower-bound proof.
    for k in range(1, 7):
        edges = [(u, v) for u, v in combinations(range(1 << k), 2)
                 if (u ^ v).bit_count() == 1]
        assert len(edges) == k * 2 ** (k - 1)
    print(f"Passed: {checked_sets} extension sets, {checked_pairs} NC pairs, "
          "six cube edge counts, one hypothesis negative control.")


if __name__ == "__main__":
    main()
