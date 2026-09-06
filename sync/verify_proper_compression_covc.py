#!/usr/bin/env python3
"""Bounded independent checks for prop:proper-compression-covc.

All proper orders through three coordinates, local hollow-star support
compatibility through size four, and a proper stable width-one control.
Finite checks are regressions, not the proof of the universal inequalities.
"""
from itertools import permutations, product
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'


def submasks(mask: int) -> list[int]:
    result = [mask]
    while mask:
        mask = (mask - 1) & result[0]
        result.append(mask)
    return result


def main() -> None:
    classes = orders = local_tests = stable_samples = 0
    for n in range(4):
        masks = [submasks(m) for m in range(1 << n)]
        for family_mask in range(1, 1 << (1 << n)):
            family = [h for h in range(1 << n) if family_mask >> h & 1]
            traces = [{h & mask for h in family} for mask in range(1 << n)]
            hollow = [(mask, labels) for mask in range(1 << n)
                      for labels in masks[mask] if labels not in traces[mask]
                      and all(labels ^ (1 << x) in traces[mask]
                              for x in range(n) if mask >> x & 1)]
            covc = max((mask.bit_count() for mask, _ in hollow), default=0)
            optimum = n
            samples = [(mask, labels) for mask in range(1 << n) for labels in traces[mask]]
            for order in permutations(family):
                first = {(mask, labels): next(h for h in order if h & mask == labels)
                         for mask, labels in samples}
                width = max(min(kernel.bit_count() for kernel in masks[mask]
                                if first[kernel, labels & kernel] == first[mask, labels])
                            for mask, labels in samples)
                assert width >= covc - 1
                optimum = min(optimum, width)
                orders += 1
            if len(family) == 1 << n:
                assert optimum == n and covc == 0
            if n == 3 and family == [0, 3, 5]:
                assert optimum == 2 and covc == 3
                improper_order = [1, 0, 3, 5]
                for mask, labels in samples:
                    first = next(h for h in improper_order if h & mask == labels)
                    assert any(kernel.bit_count() <= 1 and
                               next(h for h in improper_order if h & kernel == labels & kernel) == first
                               for kernel in masks[mask])
            classes += 1

    # The deletion sample S_i omits i. Its proper output must flip precisely i
    # on the hollow-star domain. A stable reconstruction is constant throughout
    # the Boolean interval [K_i, S_i]. Intersecting intervals cannot have
    # different outputs. This is checked directly, independently of pair counting.
    for q in range(1, 5):
        full = (1 << q) - 1
        deletions = [full ^ (1 << i) for i in range(q)]
        choices = [submasks(s) for s in deletions]
        for kernels in product(*choices):
            intervals = [{t for t in submasks(s) if t & k == k}
                         for k, s in zip(kernels, deletions)]
            compatible = all(not (intervals[i] & intervals[j])
                             for i in range(q) for j in range(i))
            covered_pairs = all(kernels[i] >> j & 1 or kernels[j] >> i & 1
                                for i in range(q) for j in range(i))
            assert compatible == covered_pairs
            if compatible:
                assert sum(k.bit_count() for k in kernels) >= q * (q - 1) // 2
                assert 2 * max(k.bit_count() for k in kernels) >= q - 1
            local_tests += 1

    # Three singletons: a cyclic negative-example decoder defeats the false
    # strengthening psLSC >= coVC - 1. All sample/key stability is verified.
    family = {1, 2, 4}

    def decode(key: tuple[int, int]) -> int:
        mask, positive = key
        if not mask:
            return 1
        if positive:
            return positive
        x = mask.bit_length() - 1
        return 1 << ((x + 1) % 3)

    def compress(mask: int, labels: int) -> tuple[int, int]:
        if not mask:
            return 0, 0
        if labels:
            return labels, labels
        return next((1 << x, 0) for x in range(3)
                    if mask >> x & 1 and decode((1 << x, 0)) & mask == 0)

    for mask in range(8):
        for labels in {h & mask for h in family}:
            key = compress(mask, labels)
            output = decode(key)
            assert output in family and output & mask == labels
            assert key[0] & mask == key[0] and key[0].bit_count() <= 1
            for smaller in submasks(mask):
                if smaller & key[0] == key[0]:
                    assert compress(smaller, labels & smaller) == key
            stable_samples += 1
    assert 0 not in family and all(1 << i in family for i in range(3))
    assert 1 < 3 - 1  # psLSC <= 1, coVC = 3.
    record = json.loads((DATA / 'classes/012_three_code_class.json').read_text())
    assert r'\{000,011,101\}' in record['definition']
    assert {h ^ 1 for h in (0, 3, 5)} == family
    expected = {796: '$1$', 810: '$3$', 868: '$1$', 869: '$2$'}
    for path in (DATA / 'values').glob('*_three_code_class.json'):
        value = json.loads(path.read_text())
        if value['id'] in expected:
            assert value['value'] == expected.pop(value['id'])
            assert value['status'] == 'established' and value['proof']
    assert not expected
    for ident, slug, c, d in [(511, 'proper_ordered_sample_compression', '1', '1'),
                              (512, 'proper_stable_labeled_sample_compression', '1/2', '1/2')]:
        path = DATA / 'relationships' / f'{ident}_{slug}_covc_dimension_affine.json'
        relation = json.loads(path.read_text())
        assert relation['parameter_1_id'] == '#parameters/' + slug
        assert relation['parameter_2_id'] == '#parameters/covc_dimension'
        assert relation['multiplicative_constant'] == c and relation['additive_constant'] == d
        assert relation['status'] == 'established' and relation['relationship_type'] == 'larger_c'
        assert relation['latex_proof_label'] == 'prop:proper-compression-covc'
        assert relation['witness'] == '#classes/full_cube' and relation['witness_strength'] == 'unbounded'
    print(json.dumps(dict(classes=classes, proper_orders=orders,
                          local_support_tests=local_tests,
                          cyclic_stable_samples=stable_samples), indent=2))


if __name__ == '__main__':
    main()
