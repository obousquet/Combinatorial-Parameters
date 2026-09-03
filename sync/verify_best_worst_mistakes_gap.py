#!/usr/bin/env python3
"""Exactly verify the finite C_bw separation of best and worst mistakes."""

from functools import cache
from itertools import permutations


# Bit i is the label at x_(i+1).  Thus these are 000, 100, 010, 101 when
# strings are written in coordinate order x_1,x_2,x_3.
CONCEPTS = (0b000, 0b001, 0b010, 0b101)
COORDINATES = range(3)


def fixed_order_mistakes(order: tuple[int, ...]) -> int:
    """Optimal transductive minimax mistakes for one presentation order."""

    @cache
    def solve(version_space: tuple[int, ...], position: int) -> int:
        if len(version_space) <= 1 or position == len(order):
            return 0
        coordinate = order[position]
        zero = tuple(h for h in version_space if not (h >> coordinate) & 1)
        one = tuple(h for h in version_space if (h >> coordinate) & 1)
        if not zero:
            return solve(one, position + 1)
        if not one:
            return solve(zero, position + 1)
        zero_cost = solve(zero, position + 1)
        one_cost = solve(one, position + 1)
        # Predict 0 or 1, respectively, then let the target choose a branch.
        return min(max(zero_cost, 1 + one_cost), max(1 + zero_cost, one_cost))

    return solve(CONCEPTS, 0)


def main() -> None:
    values = {order: fixed_order_mistakes(order) for order in permutations(COORDINATES)}
    assert min(values.values()) == 1, values
    assert max(values.values()) == 2, values
    assert values[(1, 0, 2)] == values[(2, 0, 1)] == 1, values
    assert values[(0, 1, 2)] == values[(0, 2, 1)] == 2, values
    print("C_bw: best mistakes = 1; worst mistakes = 2")


if __name__ == "__main__":
    main()
