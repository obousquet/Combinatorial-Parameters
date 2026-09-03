#!/usr/bin/env python3
"""Verify the bit-first order gives OSH_min=1 on addressing classes."""


def addressing(concept_count: int) -> tuple[frozenset[int], int]:
    bit_count = (concept_count - 1).bit_length()
    concepts = []
    for index in range(concept_count):
        code = sum(((index >> bit) & 1) << (concept_count + bit) for bit in range(bit_count))
        concepts.append((1 << index) | code)
    return frozenset(concepts), bit_count


def downshift(concepts: frozenset[int], coordinate: int) -> frozenset[int]:
    shifted = set(concepts)
    for concept in concepts:
        lowered = concept ^ (1 << coordinate)
        if concept & (1 << coordinate) and lowered not in shifted:
            shifted.remove(concept)
            shifted.add(lowered)
    return frozenset(shifted)


def bit_first_order_shattering_dimension(concept_count: int) -> int:
    concepts, bit_count = addressing(concept_count)
    for coordinate in range(concept_count, concept_count + bit_count):
        concepts = downshift(concepts, coordinate)
    for coordinate in range(concept_count):
        concepts = downshift(concepts, coordinate)
    return max(concept.bit_count() for concept in concepts)


def main() -> None:
    for concept_count in range(2, 33):
        assert bit_first_order_shattering_dimension(concept_count) == 1
    print("Addressing: bit-first downshifting gives OSH_min = 1")


if __name__ == "__main__":
    main()
