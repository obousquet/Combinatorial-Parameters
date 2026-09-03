#!/usr/bin/env python3
"""Exactly verify C_bo separates best mistakes from minimum order shattering."""

from functools import cache
from itertools import permutations


# Bit i is the label at x_(i+1), hence the strings are 1100, 0010, 0110,
# 0001, and 1001 when written in coordinate order.
CONCEPTS = frozenset({0b0011, 0b0100, 0b0110, 0b1000, 0b1001})
DIMENSION = 4


def downshift(concepts: frozenset[int], coordinate: int) -> frozenset[int]:
    shifted = set(concepts)
    for concept in concepts:
        lowered = concept ^ (1 << coordinate)
        if concept & (1 << coordinate) and lowered not in shifted:
            shifted.remove(concept)
            shifted.add(lowered)
    return frozenset(shifted)


def order_shattering_dimension(order: tuple[int, ...]) -> int:
    shifted = CONCEPTS
    for coordinate in order:
        shifted = downshift(shifted, coordinate)
    # A fully downshifted binary family is downward closed, and its maximum
    # support size equals the maximum dimension of a shattered face.
    return max(concept.bit_count() for concept in shifted)


def fixed_order_mistakes(order: tuple[int, ...]) -> int:
    @cache
    def solve(version_space: tuple[int, ...], position: int) -> int:
        if len(version_space) <= 1 or position == DIMENSION:
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
        return min(max(zero_cost, 1 + one_cost), max(1 + zero_cost, one_cost))

    return solve(tuple(sorted(CONCEPTS)), 0)


def main() -> None:
    orders = tuple(permutations(range(DIMENSION)))
    order_shattering = {order: order_shattering_dimension(order) for order in orders}
    mistakes = {order: fixed_order_mistakes(order) for order in orders}
    assert min(order_shattering.values()) == 1, order_shattering
    assert min(mistakes.values()) == 2, mistakes
    print("C_bo: best mistakes = 2; minimum order-shattered dimension = 1")


if __name__ == "__main__":
    main()
