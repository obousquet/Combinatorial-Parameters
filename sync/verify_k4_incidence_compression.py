#!/usr/bin/env python3
"""Solver-free K4 finite proper-compression/query counterexample replay.

The DB owns the benchmark proofs. This enumerates all width-two decoder
menus and independently replays the explicit reserved-key upper construction.
No SAT model, inferred encoder ordering, or untransmitted label is used.
"""
from functools import cache
from itertools import combinations, product
import json
from pathlib import Path

from verify_proper_unlabeled_obstruction import proper_queries

DATA = Path(__file__).resolve().parents[1] / 'data'
EDGES = tuple(combinations(range(4), 2))
STARS = tuple(sum(1 << i for i, e in enumerate(EDGES) if v in e) for v in range(4))
WORDS = (0,) + STARS
TYPES = (2, 0, 1, 1, 0, 2)  # ab, ac, ad, bc, bd, cd
PAIR_MASKS = tuple((1 << i) | (1 << j) for i, j in combinations(range(6), 2))
MATCHINGS = tuple((1 << i) | (1 << j) for i, j in combinations(range(6), 2)
                  if set(EDGES[i]).isdisjoint(EDGES[j]))
RESERVED = tuple(sorted(MATCHINGS + STARS, key=lambda k: (k.bit_count(), k)))
PARITY_TO_STAR = {0: STARS[0], 3: STARS[1], 6: STARS[2], 5: STARS[3]}


def parts(mask):
    part = mask
    while True:
        yield part
        if not part:
            break
        part = (part - 1) & mask


def parity_decode(key):
    return key ^ (((key << 1) & 7) | (key >> 2))


def decode(key):
    if key in RESERVED:
        return 0
    compressed_types = sum(1 << t for t in {TYPES[i] for i in range(6) if key >> i & 1})
    return PARITY_TO_STAR[parity_decode(compressed_types)]


def encode(support, labels):
    if not any(h & support == labels for h in STARS):
        assert labels == 0
        return next(k for k in RESERVED if k & support == k)
    seen = {}
    for i in range(6):
        if support >> i & 1:
            label = ((labels ^ STARS[0]) >> i) & 1
            assert TYPES[i] not in seen or seen[TYPES[i]] == label
            seen[TYPES[i]] = label
    source_support = sum(1 << t for t in seen)
    source_labels = sum(label << t for t, label in seen.items())
    candidates = [k for k in parts(source_support) if parity_decode(k) & source_support == source_labels]
    assert len(candidates) == (2 if source_support == 7 else 1)
    source_key = min(candidates, key=lambda k: (k.bit_count(), k))
    key = sum(1 << next(i for i in range(6) if TYPES[i] == t and support >> i & 1)
              for t in seen if source_key >> t & 1)
    assert key not in RESERVED and key.bit_count() <= 2
    return key


def upper_replay():
    samples = intervals = new_branch = 0
    for support in range(64):
        vertices_covered = set().union(*(set(EDGES[i]) for i in range(6) if support >> i & 1))
        is_cover = len(vertices_covered) == 4
        assert is_cover == any(k & support == k for k in RESERVED)
        for labels in {h & support for h in WORDS}:
            key = encode(support, labels)
            output = decode(key)
            assert key & support == key and key.bit_count() <= 3
            assert output in WORDS and output & support == labels
            if key in RESERVED:
                assert labels == 0 and is_cover
                new_branch += 1
            # Independent literal consistency, including the empty concept.
            output_edges = set() if output == 0 else {e for e in EDGES if STARS.index(output) in e}
            assert all((EDGES[i] in output_edges) == bool(labels >> i & 1)
                       for i in range(6) if support >> i & 1)
            for extra in parts(support ^ key):
                t = key | extra
                assert encode(t, labels & t) == key
                assert decode(encode(t, labels & t)) == output
                intervals += 1
            samples += 1
    assert len(MATCHINGS) == 3 and len(STARS) == 4
    # Omitting the decoder override makes the new branch invalid.
    matching = MATCHINGS[0]
    old_output = PARITY_TO_STAR[parity_decode(1 << TYPES[(matching & -matching).bit_length() - 1])]
    assert old_output & matching != 0 and decode(matching) == 0
    print(f'Upper scheme: {samples} samples, {intervals} exact-key stability intervals, '
          f'{new_branch} reserved-key samples; all 64 edge-cover tests pass.')


def lower_replay():
    counts = []
    for root in WORDS:
        menus = tables = 0
        options = [tuple(h for h in WORDS if (h ^ root) >> i & 1) for i in range(6)]
        for singles in product(*options):
            pair_options = []
            for (i, j), mask in zip(combinations(range(6), 2), PAIR_MASKS):
                traces = {h & mask for h in WORDS}
                old = {h & mask for h in (root, singles[i], singles[j])}
                choices = tuple(h for h in WORDS if old | {h & mask} == traces)
                if not choices:
                    break
                pair_options.append(choices)
            else:
                menus += 1
                assert root != 0
                # Check the analytical missing sample, not a solver's arbitrary core.
                sample = root  # The three edges of the empty-output vertex star.
                assert {h for h in WORDS if h & sample == 0} == {0}
                for pairs in product(*pair_options):
                    rho = {0: root, **{1 << i: h for i, h in enumerate(singles)},
                           **dict(zip(PAIR_MASKS, pairs))}
                    assert all(h & sample != 0 for k, h in rho.items() if k & sample == k)
                    tables += 1
        counts.append((menus, tables))
    assert counts == [(0, 0)] + [(2, 16)] * 4
    print(f'Lower replay: all five empty outputs; viable (singleton menus, pair tables) '
          f'{counts}; all 64 pair tables miss the root-star zero sample.')


def basic_values():
    assert EDGES == ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    assert WORDS == (0, 7, 25, 42, 52)
    assert proper_queries(6, WORDS) == 2
    vc = max(s.bit_count() for s in range(64) if len({h & s for h in WORDS}) == 1 << s.bit_count())
    @cache
    def littlestone(words):
        if not words:
            return -1
        return max([0] + [1 + min(littlestone(tuple(h for h in words if not (h >> i & 1))),
                                  littlestone(tuple(h for h in words if h >> i & 1)))
                          for i in range(6) if len({h >> i & 1 for h in words}) == 2])
    assert vc == littlestone(WORDS) == 2
    assert sum(len({h >> i & 1 for h in WORDS}) == 2 for i in range(6)) == 6
    assert len(set(WORDS)) == 5
    for ident, value in ((1209, 2), (1210, 3), (1211, 3), (1212, 2), (1213, 2),
                         (1214, 2), (1215, 6), (1216, 5)):
        r = json.loads(next((DATA / 'values').glob(f'{ident}_*.json')).read_text())
        assert r['value'] == f'${value}$' and r['status'] == 'established'
        assert r['class_id'] == '#classes/k4_incidence_with_empty'
    r = json.loads(next((DATA / 'relationships').glob('529_*.json')).read_text())
    assert r['status'] == 'refuted' and r['witness_strength'] == 'strict'
    assert r['witness'] == '#classes/k4_incidence_with_empty'
    r = json.loads(next((DATA / 'relationships').glob('159_*.json')).read_text())
    assert r['status'] == 'refuted' and 'k4_incidence_with_empty' in r['details']
    assert r['witness'] == '#classes/balanced_six_split'  # Retain stronger global witness.
    print('Exact Qpeq, VC, Littlestone, size and range, eight values and two refutations guarded.')


def clique_control():
    # The next clique is an existence failure, not a larger finite witness.
    edges = tuple(combinations(range(5), 2))
    stars = tuple(sum(1 << i for i, e in enumerate(edges) if v in e) for v in range(5))
    words = (0,) + stars
    assert proper_queries(len(edges), words) == 2
    adjacent = 0
    for i, j in combinations(range(len(edges)), 2):
        if set(edges[i]) & set(edges[j]):
            mask = (1 << i) | (1 << j)
            assert len({h & mask for h in words}) == 4
            adjacent += 1
    assert adjacent == 30
    for m in range(5, 11):
        assert m * (m - 1) // 2 > m
        assert (m - 1) * (m - 2) // 2 > m - 1
    print('Clique-amplification guard: K5 has Qpeq two and 30 shattered adjacent pairs; '
          'both root-type orientation counts fail for m=5..10 (no finite-width claim).')


if __name__ == '__main__':
    upper_replay()
    lower_replay()
    basic_values()
    clique_control()
