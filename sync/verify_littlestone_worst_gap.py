#!/usr/bin/env python3
"""Verify a finite strict gap between Littlestone and worst-order mistakes."""

from __future__ import annotations

from functools import cache
from itertools import permutations


WORDS = (0b0000, 0b0001, 0b0010, 0b1000, 0b1011, 0b1100, 0b1101, 0b1111)
WIDTH = 4


def split(state: tuple[int, ...], coordinate: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (
        tuple(index for index in state if not (WORDS[index] >> coordinate) & 1),
        tuple(index for index in state if (WORDS[index] >> coordinate) & 1),
    )


def littlestone_dimension() -> int:
    @cache
    def rank(state: tuple[int, ...]) -> int:
        answer = 0
        for coordinate in range(WIDTH):
            zero, one = split(state, coordinate)
            if zero and one:
                answer = max(answer, 1 + min(rank(zero), rank(one)))
        return answer

    return rank(tuple(range(len(WORDS))))


def fixed_order_mistakes(order: tuple[int, ...]) -> int:
    @cache
    def cost(state: tuple[int, ...], position: int) -> int:
        if len(state) < 2 or position == len(order):
            return 0
        zero, one = split(state, order[position])
        if not zero or not one:
            return cost(state, position + 1)
        zero_cost = cost(zero, position + 1)
        one_cost = cost(one, position + 1)
        return min(
            max(zero_cost, 1 + one_cost),
            max(1 + zero_cost, one_cost),
        )

    return cost(tuple(range(len(WORDS))), 0)


def main() -> None:
    assert littlestone_dimension() == 3
    order_values = {fixed_order_mistakes(order) for order in permutations(range(WIDTH))}
    assert order_values == {2}
    print("C_lw: Littlestone dimension = 3; worst mistakes = 2")


if __name__ == "__main__":
    main()
