#!/usr/bin/env python3
"""Replay the database-owned nine-set no-clashing certificate, without SAT."""
import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import re


def rotate(bits: int, shift: int, n: int = 12) -> int:
    shift %= n
    return ((bits << shift) | (bits >> (n-shift))) & ((1 << n)-1)


def check_map(teacher: dict[int, int], n: int, width: int) -> int:
    assert all(0 <= h < (1 << n) and 0 <= s < (1 << n) and s.bit_count() <= width
               for h,s in teacher.items())
    pairs = 0
    for h,g in combinations(teacher,2):
        # Independently compare the actual labeled samples against targets.
        h_sample = [(x,(h >> x)&1) for x in range(n) if teacher[h] & (1 << x)]
        g_sample = [(x,(g >> x)&1) for x in range(n) if teacher[g] & (1 << x)]
        assert any(((g >> x)&1) != label for x,label in h_sample) or any(
            ((h >> x)&1) != label for x,label in g_sample), (h,g)
        pairs += 1
    return pairs


def pair_weights(proof: str, concepts: set[int]) -> dict[tuple[int, int], int]:
    triples = re.findall(r'\((\d+),(\d+),(\d+)\)', proof)
    assert len(triples) == 39
    weights = {}
    for first, second, raw_weight in triples:
        h, g, weight = int(first), int(second), int(raw_weight)
        assert h in concepts and g in concepts and h != g and weight > 0
        orbit = {tuple(sorted((rotate(h, t), rotate(g, t)))) for t in range(12)}
        assert not (weights.keys() & orbit), 'Overlapping pair orbits'
        for pair in orbit:
            assert set(pair) <= concepts
            weights[pair] = weight
    assert len(weights) == 460
    return weights


def coordinate_loads(concepts: set[int], weights: dict[tuple[int, int], int], n: int) -> dict[int, list[int]]:
    loads = {h: [0] * n for h in concepts}
    for (h, g), weight in weights.items():
        assert h in concepts and g in concepts and h < g and weight > 0
        for x in range(n):
            if ((h >> x) & 1) != ((g >> x) & 1):
                loads[h][x] += weight
                loads[g][x] += weight
    return loads


def verify(data_dir: Path) -> dict:
    definition = json.loads((data_dir / 'classes/050_chen_teaching_products.json').read_text())['definition']
    words = re.findall(r'\\mathtt\{([01]{12})\}',definition)
    value = json.loads((data_dir / 'values/1114_noclashing_teaching_dimension_chen_teaching_products.json').read_text())
    proof = value['proof']
    upper = re.fullmatch(r'\$\\le(\d+)n\$',value['value'])
    assert upper
    sets = re.findall(r'S_([1-9])=\\\{([0-9,]+)\\\}',proof)
    assert len(words) == len(sets) == 9
    assert [int(i) for i,_ in sets] == list(range(1,10))
    teacher = {}
    for word,(_,coordinates) in zip(words,sets):
        positions = [int(x) for x in coordinates.split(',')]
        assert len(set(positions)) == len(positions) and all(1 <= x <= 12 for x in positions)
        mask = sum(1 << (x-1) for x in positions)
        concept = int(word[::-1],2)
        for shift in range(12):
            h,s = rotate(concept,shift),rotate(mask,shift)
            assert h not in teacher or teacher[h] == s, 'Inconsistent stabilizer assignment'
            teacher[h] = s
    assert len(teacher) == 100
    pairs = check_map(teacher,12,int(upper.group(1)))
    assert pairs == 4950
    assert all(teacher[rotate(h,1)] == rotate(s,1) for h,s in teacher.items())
    edges = sum((h^g).bit_count() == 1 for h,g in combinations(teacher,2))
    assert edges == 120
    density = Fraction(2*edges,len(teacher))
    average = json.loads((data_dir / 'values/1115_double_density_or_average_degree_chen_teaching_products.json').read_text())
    assert average['value'] == f'${density.numerator}n/{density.denominator}$'
    weights = pair_weights(proof, set(teacher))
    loads = coordinate_loads(set(teacher), weights, 12)
    assert sum(weights.values()) == 1780
    assert {max(row) for row in loads.values()} == {8}
    lower = Fraction(sum(weights.values()), sum(max(row) for row in loads.values()))
    assert lower == Fraction(89, 40)
    assert rf'\lceil{lower.numerator}n/{lower.denominator}\rceil' in value['details']
    assert 2 < lower <= int(upper.group(1)) == 3
    # A one-bit edge and its square calibrate weighted counting and product scaling.
    assert coordinate_loads({0, 1}, {(0, 1): 1}, 1) == {0: [1], 1: [1]}
    square = coordinate_loads(set(range(4)), {(0, 1): 1, (0, 2): 1, (1, 3): 1, (2, 3): 1}, 2)
    assert all(row == [1, 1] for row in square.values())
    # All short stabilizer-invariant masks are empty; a symmetry constraint
    # would wrongly exclude every possible asymmetric width-two teacher.
    invariant_short_masks = [s for s in range(1 << 12) if s.bit_count() <= 2 and rotate(s,4) == s]
    assert invariant_short_masks == [0]
    last = int(words[-1][::-1],2)
    assert len({rotate(last,i) for i in range(12)}) == 4
    # Verify product assembly on the whole two-cube teacher and its square.
    cube_teacher = {0:1,1:2,3:1,2:2}
    check_map(cube_teacher,2,1)
    product_teacher = {h | (g << 2): s | (t << 2)
                       for (h,s),(g,t) in product(cube_teacher.items(),repeat=2)}
    check_map(product_teacher,4,2)
    # Mutation checks: a zero teacher must be rejected, not vacuously accepted.
    try:
        check_map({0:0,1:0},1,0)
    except AssertionError:
        pass
    else:
        raise AssertionError('A clashing map was accepted')
    return {'class_id':50,'targets':100,'checked_pairs':pairs,'width_upper_bound':3,
            'one_inclusion_edges':edges,'exact_base_value':3,
            'weighted_pairs':len(weights),'total_pair_weight':sum(weights.values()),
            'maximum_coordinate_load_per_target':8,'product_lower_coefficient':str(lower),
            'minimum_rotation_equivariant_width':3,
            'projection_bound_asserted':False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path('data'))
    args = parser.parse_args()
    print(json.dumps(verify(args.data_dir),indent=2))


if __name__ == '__main__':
    main()
