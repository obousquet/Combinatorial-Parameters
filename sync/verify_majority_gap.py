#!/usr/bin/env python3
"""Verify the finite separation between majority and optimal EQ complexity."""

from __future__ import annotations

from functools import cache


WORDS = (0b0000, 0b0001, 0b0010, 0b0011, 0b0100, 0b0101, 0b0111, 0b1000)
WIDTH = 4


def split(state: tuple[int, ...], coordinate: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return (
        tuple(word for word in state if not (word >> coordinate) & 1),
        tuple(word for word in state if (word >> coordinate) & 1),
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

    return rank(WORDS)


def majority_complexity() -> int:
    @cache
    def cost(state: tuple[int, ...]) -> int:
        if len(state) < 2:
            return 0
        branch_costs = []
        for coordinate in range(WIDTH):
            zero, one = split(state, coordinate)
            # The majority query predicts 1 only for a strict majority.
            minority = zero if len(one) > len(zero) else one
            if minority:
                branch_costs.append(cost(minority))
        return 1 + max(branch_costs)

    return cost(WORDS)


def main() -> None:
    assert littlestone_dimension() == 2
    assert majority_complexity() == 3
    print("C_maj: Ldim = EQ = 2; majority complexity = 3")


if __name__ == "__main__":
    main()
