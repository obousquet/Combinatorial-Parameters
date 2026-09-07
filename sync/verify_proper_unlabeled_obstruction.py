#!/usr/bin/env python3
"""Independent finite replay of the balanced six-split obstruction.

No SAT solver: enumerate all singleton-key decoder choices for every possible
proper empty-key output, rejecting duplicated traces on a shattered pair.
This test does not assume stability and does not restrict keys on larger samples.
"""
from functools import cache
from itertools import combinations, product
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'


def balanced_splits(m: int) -> tuple[tuple[frozenset[int], ...], tuple[int, ...]]:
    coordinates = tuple(frozenset((0,) + tail) for tail in combinations(range(1, 2*m), m-1))
    words = tuple(sum(1 << i for i, a in enumerate(coordinates) if v in a) for v in range(2*m))
    return coordinates, words


def singleton_decoder_count(n: int, words: tuple[int, ...], empty: int) -> int:
    options = [tuple(h for h in words if (h ^ empty) >> i & 1) for i in range(n)]
    pairs = [(i,j) for i,j in combinations(range(n),2)
             if len({(h >> i & 1, h >> j & 1) for h in words}) == 4]
    surviving = 0
    for outputs in product(*options):
        # Direct restriction of the first three available keys. If two agree,
        # the fourth key cannot cover both remaining labels, whatever it says.
        if all(len({(h >> i & 1, h >> j & 1)
                    for h in (empty, outputs[i], outputs[j])}) == 3 for i,j in pairs):
            surviving += 1
    return surviving


def proper_queries(n: int, words: tuple[int, ...]) -> int:
    @cache
    def depth(version: tuple[int, ...]) -> int:
        if len(version) <= 1:
            return 0  # Stop once identified; no final confirmation query.
        choices = []
        for proposal in words:  # Allow every proper proposal, even outside V.
            replies = [tuple(h for h in version if (h ^ proposal) >> x & 1) for x in range(n)]
            if version in replies:
                continue  # An adversary can return a previously known bit forever.
            choices.append(1 + max((depth(v) for v in replies if v), default=0))
        return min(choices)
    return depth(words)


def main() -> None:
    coordinates, words = balanced_splits(3)
    n = len(coordinates)
    assert n == 10 and len(set(words)) == 6
    assert all(sum(v in a for v in range(6)) == 3 for a in coordinates)
    assert all(len({(h >> i & 1, h >> j & 1) for h in words}) == 4
               for i,j in combinations(range(n),2))
    assert all((h ^ g).bit_count() == 6 for h,g in combinations(words,2))
    # Literal set-incidence cross-check, independent of the bit encoding.
    for u,v in combinations(range(6),2):
        assert sum((u in a) != (v in a) for a in coordinates) == 6
    assert n * (6-1) == 50 > n*(n-1)//2 == 45
    counts = [singleton_decoder_count(n, words, h) for h in words]
    assert counts == [0]*6
    assert proper_queries(n, words) == 3
    # Controls: the m=2 parity class reaches the counting threshold exactly
    # and DOES admit these local decoder choices. Do not reject equality.
    small_x, small_h = balanced_splits(2)
    assert len(small_x) == 3
    assert all(singleton_decoder_count(3, small_h, h) > 0 for h in small_h)
    assert proper_queries(3, small_h) == 2
    # Cubes and singletons calibrate the query-counting convention.
    assert proper_queries(2, (0,1,2,3)) == 2
    assert proper_queries(3, (1,2,4)) == 2
    assert proper_queries(3, (0,1,2,4)) == 1
    # The positive-key decoder is a valid IMPROPER unlabeled scheme on every
    # partial sample; direct retained-key stability also holds. It must not be
    # excluded by our necessary condition for proper reconstruction.
    samples = intervals = improper = 0
    for support in range(1 << n):
        for labels in {h & support for h in words}:
            key = labels
            assert key & support == key and key & support == labels
            improper += key not in words
            part = support ^ key
            while True:
                smaller = key | part
                assert labels & smaller == key
                intervals += 1
                if not part:
                    break
                part = (part-1) & (support ^ key)
            samples += 1
    assert improper > 0
    for ident, expected in {1181:'$10$',1182:'$6$',1183:'$3$',1184:'$+\\infty$',
                            1185:'$+\\infty$',1186:'$2$',1187:'$2$',1188:'$2$'}.items():
        record=json.loads(next((DATA/'values').glob(f'{ident}_*.json')).read_text())
        assert record['value']==expected and record['status']=='established'
        assert record['class_id']=='#classes/balanced_six_split'
    for ident in (159,188,189):
        record=json.loads(next((DATA/'relationships').glob(f'{ident:03}_*.json')).read_text())
        assert record['status']=='refuted' and record['witness']=='#classes/balanced_six_split'
    print(json.dumps({'coordinates':n,'concepts':len(words),'shattered_pairs':45,
                      'pairwise_distance':6,'singleton_maps_examined':6*3**10,
                      'surviving_maps_by_empty_output':counts,'proper_queries':3,
                      'improper_control_samples':samples,'control_stability_intervals':intervals},indent=2))


if __name__ == '__main__':
    main()
