#!/usr/bin/env python3
"""Definition-driven exact checks of the 100-concept teaching example.

All binary words and teaching masks are enumerated, without a SAT solver.
Projection RTD <=5 is checked by singleton-fibre peeling. If a projection
has a nonempty residual, it witnesses RTD >=6; RTD <=floor(log2(100))=6.
Only the base is enumerated; product values use the mathematical proof.
"""
import argparse
from itertools import combinations
import json
from pathlib import Path
import re


def masks(n: int, size: int):
    return [sum(1 << i for i in coordinates) for coordinates in combinations(range(n), size)]


def verify(data_dir: Path, source: Path | None = None) -> dict:
    record = json.loads((data_dir / 'classes/050_chen_teaching_products.json').read_text())
    words = re.findall(r'\\mathtt\{([01]{12})\}', record['definition'])
    assert len(words) == 9
    if source:
        page = source.read_text().split('\f')[6]
        extracted = [''.join(row.split()) for row in re.findall(r'^\s*([01](?:\s+[01]){11})\s*$', page, re.M)]
        assert words == extracted, 'Definition/source matrix mismatch'
    orbits = [{word[i:] + word[:i] for i in range(12)} for word in words]
    assert [len(orbit) for orbit in orbits] == [12] * 8 + [4]
    concepts = tuple(sorted(int(word[::-1], 2) for word in set.union(*orbits)))
    assert len(concepts) == 100
    partitions = []
    for mask in range(1 << 12):
        groups = {}
        for i, h in enumerate(concepts):
            groups[h & mask] = groups.get(h & mask, 0) | (1 << i)
        partitions.append(tuple(groups.values()))
    shattered = next(mask for mask in masks(12, 3) if len(partitions[mask]) == 8)
    assert all(len(partitions[mask]) < 16 for mask in masks(12, 4))
    assert all(group.bit_count() != 1 for mask in masks(12, 4) for group in partitions[mask])
    teaching = {}
    for mask in masks(12, 5):
        for group in partitions[mask]:
            if group.bit_count() == 1:
                teaching.setdefault(group.bit_length() - 1, mask)
    assert len(teaching) == 100
    # All targets have teaching size five, so min-TS = RTD = TD = five.
    assert all(len(partitions[1 << coordinate]) == 2 for coordinate in range(12))
    projection_failures = []
    for projection in range(1 << 12):
        if projection.bit_count() <= 5:
            continue
        live = set(partitions[projection])
        remaining = (1 << 100) - 1
        tests = [group for mask in masks(12, 5) if mask & projection == mask
                 for group in partitions[mask]]
        while live:
            previous = len(live)
            for group in tests:
                current = group & remaining
                if current in live:
                    live.remove(current)
                    remaining ^= current
            if len(live) == previous:
                projection_failures.append({'projection': projection,
                                            'residual_concepts': sorted({concepts[(group & -group).bit_length()-1] & projection for group in live})})
                break
    return {'class_id': record['id'], 'base_coordinates': 12, 'base_size': 100,
            'rotation_orbit_sizes': [len(orbit) for orbit in orbits],
            'base_VC': 3, 'shattered_triple': shattered, 'four_coordinate_sets_checked': 495,
            'base_minimum_teaching_size': 5, 'base_TD': 5, 'base_RTD': 5,
            'teaching_masks': [{'concept': concepts[i], 'mask': teaching[i]} for i in range(100)],
            'projections_checked': 4096, 'base_projected_RTD': 6 if projection_failures else 5,
            'width_five_projection_failures': projection_failures,
            'scope': 'Exact base computation; all-power formulae require the product argument.'}


def product_regression() -> None:
    def profile(family: tuple[int, ...], n: int) -> tuple[int, int, int, int, int]:
        dimension = max(mask.bit_count() for mask in range(1 << n)
                        if len({h & mask for h in family}) == 1 << mask.bit_count())
        def teaching(h: int, remaining: tuple[int, ...]) -> int:
            return min(mask.bit_count() for mask in range(1 << n)
                       if all(g == h or g & mask != h & mask for g in remaining))
        def recursive(remaining: tuple[int, ...]) -> int:
            width = 0
            while remaining:
                size, h = min((teaching(h, remaining), h) for h in remaining)
                width = max(width, size)
                remaining = tuple(g for g in remaining if g != h)
            return width
        sizes = [teaching(h, family) for h in family]
        projected = max(recursive(tuple(sorted({h & mask for h in family})))
                        for mask in range(1 << n))
        return dimension, min(sizes), max(sizes), recursive(family), projected
    families = [tuple(h for h in range(4) if selected & (1 << h)) for selected in range(1,16)]
    profiles = {family: profile(family, 2) for family in families}
    for left in families:
        for right in families:
            product = tuple(sorted(h | (g << 2) for h in left for g in right))
            assert profile(product, 4) == tuple(a+b for a,b in zip(profiles[left], profiles[right]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--check-report', type=Path)
    args = parser.parse_args()
    product_regression()
    result = verify(args.data_dir, args.source)
    if args.check_report:
        assert result == json.loads(args.check_report.read_text())
        print('Definition, source (if requested), all teaching masks, all 4096 projections and 225 product-pair regressions verified.')
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
