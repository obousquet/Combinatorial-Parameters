#!/usr/bin/env python3
"""Generate or independently replay finite projected-teaching certificates.

The producer uses bitset fibres. The checker instead compares the actual
projected words at every recorded removal, without using the producer's
partitions or its peeling decisions. No solver is involved.
"""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import re


def masks(n: int, size: int) -> list[int]:
    return [sum(1 << x for x in positions) for positions in combinations(range(n),size)]


def construction(data_dir: Path) -> tuple[list[int], int, list[int]]:
    base_definition = json.loads((data_dir/'classes/050_chen_teaching_products.json').read_text())['definition']
    words = re.findall(r'\\mathtt\{([01]{12})\}',base_definition)
    assert len(words) == 9
    base = sorted({int((word[i:]+word[:i])[::-1],2) for word in words for i in range(12)})
    definition = json.loads((data_dir/'classes/051_chen_neighbor_puncture.json').read_text())['definition']
    removed_words = re.findall(r'\\mathtt\{([01]{12})\}',definition)
    assert len(removed_words) == 1
    removed = int(removed_words[0][::-1],2)
    assert removed in base
    family = sorted(set(base)-{removed}|{removed ^ (1 << x) for x in range(12)})
    assert removed not in family and len(base) == 100 and len(family) == 109
    return base,removed,family


def fingerprint(family: list[int]) -> str:
    return sha256(json.dumps(family,separators=(',',':')).encode()).hexdigest()


def produce(family: list[int]) -> dict:
    partitions = []
    for mask in range(4096):
        fibres = {}
        for i,h in enumerate(family):
            fibres[h & mask] = fibres.get(h & mask,0) | (1 << i)
        partitions.append(tuple(fibres.values()))
    small_masks = masks(12,4)
    plans = {}
    for projection in range(4096):
        if projection.bit_count() <= 4:
            continue
        # One valid mask per original fibre is enough, but the chosen mask
        # must lie in this projection.
        tests = {group:mask for mask in small_masks if mask & projection == mask
                 for group in partitions[mask]}
        remaining = (1 << len(family))-1
        live = set(partitions[projection])
        plan = []
        while live:
            previous = len(live)
            for group,mask in tests.items():
                current = group & remaining
                if current in live:
                    representative = (current & -current).bit_length()-1
                    plan.append([family[representative] & projection,mask])
                    live.remove(current)
                    remaining ^= current
            assert len(live) < previous, ('Unpeeled projection',projection)
        plans[str(projection)] = plan
    return {'class_short_name':'chen_neighbor_puncture','concepts_sha256':fingerprint(family),
            'threshold':4,'plans':plans}


def replay_plan(family: list[int], projection: int, plan: list[list[int]]) -> int:
    remaining = {h & projection for h in family}
    for target,sample_mask in plan:
        assert target in remaining
        assert sample_mask & projection == sample_mask and sample_mask.bit_count() <= 4
        consistent = {h for h in remaining if h & sample_mask == target & sample_mask}
        assert consistent == {target}, (projection,target,sample_mask,consistent)
        remaining.remove(target)
    assert not remaining, ('Incomplete certificate',projection)
    return len(plan)


def verify(data_dir: Path, certificate: dict) -> dict:
    base,removed,family = construction(data_dir)
    assert certificate['class_short_name'] == 'chen_neighbor_puncture'
    assert certificate['concepts_sha256'] == fingerprint(family) and certificate['threshold'] == 4
    expected = {str(p) for p in range(4096) if p.bit_count() > 4}
    assert certificate['plans'].keys() == expected
    steps = sum(replay_plan(family,int(p),plan) for p,plan in certificate['plans'].items())
    # Failure injection: an empty sample cannot teach the first target of
    # the non-singleton full projection. Ensure the independent checker rejects it.
    broken = [row[:] for row in certificate['plans']['4095']]
    broken[0][1] = 0
    try:
        replay_plan(family,4095,broken)
    except AssertionError:
        pass
    else:
        raise AssertionError('Checker accepted an invalid teaching sample')
    # Independent finite lower data: the Chen base has no four-example teacher.
    for mask in masks(12,4):
        counts = Counter(h & mask for h in base)
        assert min(counts.values()) >= 2
    # Every missing-point sample with at most eleven coordinates is realized
    # by a neighbor at an omitted coordinate; verify the five-coordinate layer.
    for mask in masks(12,5):
        assert any(h & mask == removed & mask for h in family)
    shattered = next(mask for mask in masks(12,4) if len({h & mask for h in family}) == 16)
    assert all(len({h & mask for h in family}) < 32 for mask in masks(12,5))
    assert all(len({h >> x & 1 for h in family}) == 2 for x in range(12))
    radius,center = min((max((h ^ c).bit_count() for h in family),c) for c in range(4096))
    assert radius == 8
    return {'class_short_name':'chen_neighbor_puncture','size':len(family),'effective_range':12,
            'VC':4,'shattered_coordinate_mask':shattered,'RTD':4,'projected_RTD':4,
            'projections':4096,'nontrivial_projection_plans':len(expected),'removals_replayed':steps,
            'radius':radius,'enclosing_center':center,'OSC_lower_bound':5,'OSC_upper_bound':radius,
            'OSC_bound_scope':'Analytic order/trace-completion argument; not an OSC solver result.',
            'bad_certificate_rejected':True,'concepts_sha256':fingerprint(family)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,default=Path('data'))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--generate-certificate',type=Path)
    group.add_argument('--check-certificate',type=Path)
    args = parser.parse_args()
    if args.generate_certificate:
        certificate = produce(construction(args.data_dir)[2])
        result = verify(args.data_dir,certificate)
        # This is generated mathematical certificate data, not another definition.
        encoded = json.dumps(certificate,sort_keys=True,separators=(',',':')).encode()
        args.generate_certificate.write_bytes(gzip.compress(encoded,mtime=0))
    else:
        certificate = json.loads(gzip.decompress(args.check_certificate.read_bytes()))
        result = verify(args.data_dir,certificate)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
