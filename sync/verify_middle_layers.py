#!/usr/bin/env python3
"""Check degeneracy and contained-cube values of the middle-two-layer family."""

from __future__ import annotations

from itertools import combinations


def family(m: int) -> tuple[int, ...]:
    width = 2 * m + 1
    return tuple(
        word
        for word in range(1 << width)
        if word.bit_count() in {m, m + 1}
    )


def degree(word: int, words: set[int], width: int) -> int:
    return sum((word ^ (1 << coordinate)) in words for coordinate in range(width))


def contained_cube_dimension(words: set[int], width: int) -> int:
    for dimension in range(width, -1, -1):
        for directions in combinations(range(width), dimension):
            fixed = [coordinate for coordinate in range(width) if coordinate not in directions]
            for fixed_bits in range(1 << len(fixed)):
                vertices = set()
                for direction_bits in range(1 << dimension):
                    word = 0
                    for index, coordinate in enumerate(fixed):
                        word |= ((fixed_bits >> index) & 1) << coordinate
                    for index, coordinate in enumerate(directions):
                        word |= ((direction_bits >> index) & 1) << coordinate
                    vertices.add(word)
                if vertices <= words:
                    return dimension
    raise AssertionError("the empty cube is always contained")


def main() -> None:
    for m in range(1, 4):
        words = set(family(m))
        width = 2 * m + 1
        assert {degree(word, words, width) for word in words} == {m + 1}
        assert contained_cube_dimension(words, width) == 1
    print("ML_m: degeneracy = m+1; largest strongly shattered set = 1")


if __name__ == "__main__":
    main()
