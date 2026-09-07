#!/usr/bin/env python3
"""Exact finite regression for prop:order-stable-installation.

Enumerate every nonempty H, every ordered G containing H, every eligible
width and every key-consistent initial decoder on domains of size 0..2.
Check stable key selection and each reverse-preference installation step.
This is calibration of the survey proof, not a proof by finite enumeration.
No solver, randomness or external dependencies are used.
"""

from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path

type Sample = tuple[int, int]


def literals(sample: Sample, n: int) -> frozenset[tuple[int, int]]:
    mask, word = sample
    return frozenset((x, (word >> x) & 1) for x in range(n) if mask >> x & 1)


def below(a: Sample, b: Sample) -> bool:
    return a[0] & b[0] == a[0] and b[1] & a[0] == a[1]


def covered(outputs: tuple[int, ...] | list[int], covers: list[dict[int, int]]) -> int:
    result = 0
    for output, options in zip(outputs, covers, strict=True):
        result |= options[output]
    return result


def verify() -> None:
    counts: Counter[str] = Counter()
    wrong_direction_control = None
    for n in range(3):
        words = tuple(range(1 << n))
        for size in range(1, len(words) + 1):
            for g_set in combinations(words, size):
                for h_bits in range(1, 1 << size):
                    h = tuple(g_set[i] for i in range(size) if h_bits >> i & 1)
                    samples = sorted({(m, v & m) for v in h for m in range(1 << n)})
                    lit = {s: literals(s, n) for s in samples}
                    for a, b in product(samples, repeat=2):
                        assert below(a, b) == (lit[a] <= lit[b])
                    for g in permutations(g_set):
                        counts['ordered_classes'] += 1
                        first = {s: next(v for v in g if v & s[0] == s[1]) for s in samples}
                        rank = {v: i for i, v in enumerate(g)}
                        for k in range(n + 1):
                            keys = sorted((s for s in samples if s[0].bit_count() <= k),
                                          key=lambda s: (s[0].bit_count(), s))
                            eligible = {s: [u for u in keys if below(u, s) and first[u] == first[s]]
                                        for s in samples}
                            if not all(eligible.values()):
                                counts['ineligible_widths'] += 1
                                continue
                            counts['order_schemes'] += 1
                            selected = {s: options[0] for s, options in eligible.items()}
                            for s, t in product(samples, repeat=2):
                                if below(selected[s], t) and below(t, s):
                                    assert first[t] == first[s]
                                    assert selected[t] == selected[s]
                                    counts['stability_intervals'] += 1
                            choices = [tuple(v for v in words if v & u[0] == u[1]) for u in keys]
                            covers = [{v: sum(1 << i for i, s in enumerate(samples)
                                              if lit[u] <= lit[s] <= literals(((1 << n) - 1, v), n))
                                       for v in options} for u, options in zip(keys, choices, strict=True)]
                            final = [first[u] for u in keys]
                            order = sorted(range(len(keys)), key=lambda i: rank[final[i]], reverse=True)
                            all_samples = (1 << len(samples)) - 1
                            assert covered(final, covers) == all_samples
                            for initial in product(*choices):
                                counts['initial_decoders'] += 1
                                proper = set(g) == set(h) and set(initial) <= set(h)
                                state = list(initial)
                                old = covered(state, covers)
                                for i in order:
                                    if state[i] == final[i]:
                                        continue
                                    state[i] = final[i]
                                    new = covered(state, covers)
                                    assert old & ~new == 0, (n, h, g, k, initial, keys[i])
                                    if proper:
                                        assert set(state) <= set(h)
                                        counts['proper_changes'] += 1
                                    counts['changes'] += 1
                                    counts['neutral_changes'] += new == old
                                    old = new
                                assert old == all_samples
                                # Negative control: reversing the direction need not preserve coverage.
                                if wrong_direction_control is None:
                                    state = list(initial)
                                    old = covered(state, covers)
                                    for i in reversed(order):
                                        state[i] = final[i]
                                        new = covered(state, covers)
                                        if old & ~new:
                                            lost = next(s for j, s in enumerate(samples) if (old & ~new) >> j & 1)
                                            wrong_direction_control = (n, h, g, k, initial, keys[i], lost)
                                            break
                                        old = new
    assert wrong_direction_control is not None
    assert counts['proper_changes'] and counts['neutral_changes']
    print(dict(counts))
    print('Preferred-first negative control (n, H, G, k, initial, changed key, lost sample):',
          wrong_direction_control)


def check_singleton_witness() -> None:
    """Guard the stronger singleton witness, not a ratio claim on full cubes."""
    data = Path(__file__).resolve().parents[1] / 'data'
    records = {}
    for vid in (26, 46, 388, 1157):
        records[vid] = json.loads(next((data / 'values').glob(f'{vid:03d}_*.json')).read_text())
        assert records[vid]['class_id'] == '#classes/singletons'
        assert records[vid]['status'] == 'established'
    assert records[26]['value'] == '$n$'
    assert records[46]['value'] == '$n-1$'
    assert records[388]['value'] == '$1$'
    assert records[1157]['value'] == r'$\Theta(n)$'
    assert records[1157]['value_class'] == 'omega_n'
    assert 'prop:proper-compression-covc' in records[1157]['proof']
    assert 'prop:order-stable-installation' in records[1157]['proof']
    relation = json.loads(next((data / 'relationships').glob('156_*.json')).read_text())
    assert relation['status'] == 'established'
    assert relation['witness'] == '#classes/singletons'
    assert relation['witness_strength'] == 'unbounded'
    print('Singleton linear-order bound and upgraded unbounded witness agree.')


def check_catalogue() -> None:
    data = Path(__file__).resolve().parents[1] / 'data'
    for rid, left, right in (
        (517, 'order_sample_compression', 'stable_labeled_sample_compression'),
        (518, 'proper_ordered_sample_compression', 'proper_stable_labeled_sample_compression'),
    ):
        record = json.loads(next((data / 'relationships').glob(f'{rid}_*.json')).read_text())
        assert record['parameter_1_id'] == f'#parameters/{left}'
        assert record['parameter_2_id'] == f'#parameters/{right}'
        assert record['relationship_type'] == 'larger'
        assert record['status'] == 'established'
        assert record['latex_proof_label'] == 'prop:order-stable-installation'
        assert record['witness'] == '#classes/full_cube'
        assert record['witness_strength'] == 'strict'
    for vid, value in ((741, '$n$'), (742, '$n$'),
                       (1047, r'$\lceil n/2\rceil$'), (744, r'$\lceil n/2\rceil$')):
        record = json.loads(next((data / 'values').glob(f'{vid:03d}_*.json')).read_text())
        assert record['class_id'] == '#classes/full_cube'
        assert record['status'] == 'established'
        assert record['value'] == value
    assert 3 > (3 + 1) // 2
    print('Both relationship records and their strict full-cube endpoint values agree.')


if __name__ == '__main__':
    verify()
    check_catalogue()
    check_singleton_witness()
