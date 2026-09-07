#!/usr/bin/env python3
"""Bounded, solver-free replay of upper-branch comparisons.

Universal proofs are in the survey. Enumerations verify implementations and
finite witnesses, not universal claims. Bit zero is the rightmost written bit.
"""
from functools import cache
from itertools import permutations
import json
from pathlib import Path

from verify_proper_unlabeled_obstruction import proper_queries


def subsets(mask: int):
    part = mask
    while True:
        yield part
        if not part:
            return
        part = (part - 1) & mask


def eluder(n: int, words: tuple[int, ...]) -> int:
    def anchored(base: int) -> int:
        @cache
        def extend(seen: int) -> int:
            version = [h for h in words if (h ^ base) & seen == 0]
            return max((1 + extend(seen | (1 << x)) for x in range(n)
                        if any((h ^ base) >> x & 1 for h in version)), default=0)
        return extend(0)
    return max(map(anchored, words), default=0)


def literal_eluder(n: int, words: tuple[int, ...]) -> int:
    rows = [tuple(h >> x & 1 for x in range(n)) for h in words]
    best = 0
    for base in rows:
        for order in permutations(range(n)):
            used = []
            for x in order:
                if not any(h[x] != base[x] and all(h[y] == base[y] for y in used)
                           for h in rows):
                    break
                used.append(x)
            best = max(best, len(used))
    return best


def projected_range(n: int, words: tuple[int, ...]) -> int:
    return max(min(key.bit_count() for key in subsets(support)
                   if len({h & key for h in words}) == len({h & support for h in words}))
               for support in range(1 << n))


def star(n: int, words: tuple[int, ...]) -> int:
    best = 0
    for support in range(1 << n):
        traces = {h & support for h in words}
        if any(all(center ^ (1 << x) in traces for x in range(n) if support >> x & 1)
               for center in traces):
            best = max(best, support.bit_count())
    return best


def worst_consistent_queries(n: int, words: tuple[int, ...]) -> int:
    """Worst over ALL consistent choices, not just an optimal learner."""
    @cache
    def depth(version: tuple[int, ...]) -> int:
        if len(version) <= 1:
            return 0
        return max(1 + max((depth(reply) for x in range(n)
                            if (reply := tuple(h for h in version if (h ^ g) >> x & 1))),
                           default=0) for g in version)
    return depth(words)


def check_order(n: int, words: tuple[int, ...], order: tuple[int, ...], s: int) -> int:
    checked = 0
    for support in range(1 << n):
        for labels in {h & support for h in words}:
            chosen = next(h for h in order if h & support == labels)
            eligible = {key for key in subsets(support)
                        if next(h for h in order if (h ^ labels) & key == 0) == chosen}
            for key in eligible:
                if any(key ^ (1 << x) in eligible for x in range(n) if key >> x & 1):
                    continue
                # Replay the native proof: a minimal key gives one earlier
                # proper neighbour at every key coordinate, with chosen center.
                earlier = order[:order.index(chosen)]
                for x in range(n):
                    if key >> x & 1:
                        assert any((h ^ chosen) & key == 1 << x for h in earlier)
                assert key.bit_count() <= s
                checked += 1
    return checked


def main() -> None:
    classes = orders = keys = 0
    gaps = [0, 0]
    for n in range(4):
        for class_mask in range(1, 1 << (1 << n)):
            words = tuple(h for h in range(1 << n) if class_mask >> h & 1)
            e = eluder(n, words)
            assert e == literal_eluder(n, words)
            assert proper_queries(n, words) <= worst_consistent_queries(n, words) <= e
            r = projected_range(n, words)
            gaps[0] += e > r
            gaps[1] += r > e
            chosen_orders = permutations(words) if n <= 2 else {words, words[::-1]}
            s = star(n, words)
            for order in chosen_orders:
                keys += check_order(n, words, order, s)
                orders += 1
            classes += 1
    reverse = (0b000, 0b001, 0b011, 0b110)
    assert eluder(3, reverse) == 3 and projected_range(3, reverse) == 2
    original = tuple(int(w, 2) for w in
                     ('00111', '01000', '01001', '01111', '10000', '10010', '10100', '11111'))
    assert eluder(5, original) == literal_eluder(5, original) == 4
    assert projected_range(5, original) == 5
    # Unbounded witness family: one fixed key-only proper decoder, all samples.
    samples = 0
    for n in range(1, 8):
        words = (0,) + tuple(1 << x for x in range(n))
        assert eluder(n, words) == n and proper_queries(n, words) == 1
        assert star(n, words) == n
        for support in range(1 << n):
            for labels in {h & support for h in words}:
                key = labels  # Empty key, or the one positive labeled example.
                decoded = key
                assert key.bit_count() <= 1 and decoded in words
                assert decoded & support == labels
                samples += 1
    data = Path(__file__).resolve().parents[1] / 'data'
    rel = json.loads((data / 'relationships/030_star_number_proper_ordered_sample_compression.json').read_text())
    assert rel['status'] == 'established' and rel['witness_strength'] == 'unbounded'
    assert rel['latex_proof_label'] == 'prop:proper-order-star'
    query = json.loads((data / 'relationships/520_combinatorial_eluder_dimension_proper_equivalence_queries_complexity.json').read_text())
    assert query['status'] == 'established' and query['witness_strength'] == 'unbounded'
    assert query['latex_proof_label'] == 'prop:proper-queries-eluder'
    expected = {1189: ('$1$', 'proper_ordered_sample_compression', 'singletons_plus_empty_set'),
                1190: ('$3$', 'combinatorial_eluder_dimension', 'eluder_range_reverse_separation'),
                1191: ('$2$', 'projected_distinguishing_range', 'eluder_range_reverse_separation')}
    for path in (data / 'values').glob('[0-9]*.json'):
        record = json.loads(path.read_text())
        if record['id'] in expected:
            value, parameter, family = expected.pop(record['id'])
            assert record['value'] == value and record['status'] == 'established'
            assert record['parameter_id'] == '#parameters/' + parameter
            assert record['class_id'] == '#classes/' + family
    assert not expected
    print(f'Checked {classes} classes, {orders} proper orders, {keys} minimal keys; '
          f'exact range gaps (Edim>Rp, Rp>Edim)={gaps}.')
    print(f'Both opposing range witnesses and {samples} singleton-plus-empty samples pass; '
          'query bounds include successful final queries. Record guards pass.')


if __name__ == '__main__':
    main()
