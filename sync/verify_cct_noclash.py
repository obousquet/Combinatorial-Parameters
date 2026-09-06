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
    lower = density/2
    assert rf'\lceil{lower.numerator}n/{lower.denominator}\rceil' in value['details']
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
            'one_inclusion_edges':edges,'exact_base_value':'unresolved: 2 or 3',
            'minimum_rotation_equivariant_width':3,
            'projection_bound_asserted':False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path('data'))
    args = parser.parse_args()
    print(json.dumps(verify(args.data_dir),indent=2))


if __name__ == '__main__':
    main()
