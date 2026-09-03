#!/usr/bin/env python3
"""Exhaustively check coded-singleton membership-query values for small n."""

from __future__ import annotations

from functools import cache
from itertools import product


def concepts(n: int) -> tuple[tuple[int, ...], ...]:
    r = (n + 1 - 1).bit_length()
    return tuple(
        tuple(int(index == target) for index in range(1, n + 1))
        + tuple((target >> bit) & 1 for bit in range(r))
        for target in range(n + 1)
    )


def query_complexity(words: tuple[tuple[int, ...], ...]) -> int:
    width = len(words[0])

    @cache
    def solve(state: tuple[int, ...]) -> int:
        if len(state) < 2:
            return 0
        choices = []
        for coordinate in range(width):
            zero = tuple(index for index in state if not words[index][coordinate])
            one = tuple(index for index in state if words[index][coordinate])
            if zero and one:
                choices.append(1 + max(solve(zero), solve(one)))
        return min(choices)

    return solve(tuple(range(len(words))))


def projected_complexity(words: tuple[tuple[int, ...], ...]) -> int:
    width = len(words[0])
    answer = 0
    for mask in range(1 << width):
        coordinates = tuple(index for index in range(width) if mask & (1 << index))
        traces = tuple(sorted(set(tuple(word[index] for index in coordinates) for word in words)))
        answer = max(answer, query_complexity(traces))
    return answer


def main() -> None:
    for n in range(1, 6):
        words = concepts(n)
        assert query_complexity(words) == (n + 1 - 1).bit_length()
        assert projected_complexity(words) == n
    print("C_code: MQ = ceil(log2(n+1)); projected MQ = n (checked n=1,...,5)")


if __name__ == "__main__":
    main()
