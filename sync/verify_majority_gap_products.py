#!/usr/bin/env python3
"""Check one and two Cartesian products of the majority-gap witness."""

from __future__ import annotations

from functools import cache
from itertools import product


BASE = (0b0000, 0b0001, 0b0010, 0b0011, 0b0100, 0b0101, 0b0111, 0b1000)


def words(factors: int) -> tuple[int, ...]:
    return tuple(
        sum(word << (4 * block) for block, word in enumerate(choice))
        for choice in product(BASE, repeat=factors)
    )


def ranks(items: tuple[int, ...], width: int) -> tuple[int, int]:
    @cache
    def split(state: tuple[int, ...], coordinate: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
        return (
            tuple(word for word in state if not (word >> coordinate) & 1),
            tuple(word for word in state if (word >> coordinate) & 1),
        )

    @cache
    def littlestone(state: tuple[int, ...]) -> int:
        answer = 0
        for coordinate in range(width):
            zero, one = split(state, coordinate)
            if zero and one:
                answer = max(answer, 1 + min(littlestone(zero), littlestone(one)))
        return answer

    @cache
    def majority(state: tuple[int, ...]) -> int:
        if len(state) < 2:
            return 0
        children = []
        for coordinate in range(width):
            zero, one = split(state, coordinate)
            if zero and one:
                children.append(majority(zero if len(one) > len(zero) else one))
        return 1 + max(children)

    return littlestone(items), majority(items)


def main() -> None:
    for factors in (1, 2):
        assert ranks(words(factors), 4 * factors) == (2 * factors, 3 * factors)
    print("C_maj^t: Ldim = 2t; majority complexity = 3t (checked t=1,2)")


if __name__ == "__main__":
    main()
