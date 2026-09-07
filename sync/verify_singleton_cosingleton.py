#!/usr/bin/env python3
"""Replay the database-owned singleton/cosingleton family and order scheme.

The value proofs cover every n >= 4. This is a fixed solver-free regression
for n = 4,...,8, not a discovery census or a numerical asymptotic argument.
"""
from functools import cache
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'


@cache
def family(n: int) -> frozenset[int]:
    record = json.loads((DATA / 'classes/052_singleton_cosingleton.json').read_text())
    assert record['id'] == 52 and record['short_name'] == 'singleton_cosingleton'
    assert r'n\ge4' in record['definition']
    assert r'\mathcal A_n=\{\{i\},[n]\setminus\{i\}:i\in[n]\}' in record['definition']
    assert n >= 4
    full = (1 << n) - 1
    return frozenset(h for i in range(n) for h in (1 << i, full ^ (1 << i)))


def vc(hypotheses: set[int] | frozenset[int], n: int) -> int:
    return max(mask.bit_count() for mask in range(1 << n)
               if len({h & mask for h in hypotheses}) == 1 << mask.bit_count())


def main() -> None:
    sample_checks = 0
    proper_checks = 0
    minimality_checks = 0
    for n in range(4, 9):
        hypotheses = family(n)
        full = (1 << n) - 1
        assert len(hypotheses) == 2 * n and vc(hypotheses, n) == 3
        order = [0, full] + [1 << i for i in range(n)] + [full ^ (1 << i) for i in range(n)]
        assert len(set(order)) == 2 * n + 2 and hypotheses <= set(order)

        def first(mask: int, labels: int) -> int:
            return next(h for h in order if h & mask == labels)

        for mask in range(1 << n):
            for positives in {h & mask for h in hypotheses}:
                negatives = mask ^ positives
                positive_bits = [1 << x for x in range(n) if positives & (1 << x)]
                negative_bits = [1 << x for x in range(n) if negatives & (1 << x)]
                if not positive_bits:
                    kernel = 0
                elif not negative_bits:
                    kernel = positive_bits[0]
                elif len(positive_bits) == 1:
                    kernel = positive_bits[0] | negative_bits[0]
                else:
                    assert len(negative_bits) == 1
                    kernel = positive_bits[0] | positive_bits[1] | negative_bits[0]
                assert kernel & mask == kernel and kernel.bit_count() <= 3
                decoded = first(kernel, positives & kernel)
                assert decoded == first(mask, positives) and decoded & mask == positives
                for x in range(n):
                    bit = 1 << x
                    if kernel & bit:
                        smaller = kernel ^ bit
                        assert first(smaller, positives & smaller) != decoded
                        minimality_checks += 1
                sample_checks += 1

        proper_order = order[2:]
        for mask in range(1 << n):
            for positives in {h & mask for h in hypotheses}:
                negatives = mask ^ positives
                bits = [1 << x for x in range(n) if positives & (1 << x)]
                if not bits:
                    i = next(x for x in range(n) if not (negatives >> x & 1))
                    kernel = (1 << i) - 1
                elif len(bits) == 1:
                    kernel = positives
                elif negatives:
                    assert negatives.bit_count() == 1
                    kernel = bits[0] | bits[1] | negatives
                else:
                    j = next(x for x in range(n) if not (positives >> x & 1))
                    kernel = ((1 << j) - 1) | bits[0] | bits[1]
                assert kernel & mask == kernel and kernel.bit_count() <= n - 1
                decoded = next(h for h in proper_order if h & kernel == positives & kernel)
                assert decoded == next(h for h in proper_order if h & mask == positives)
                assert decoded in hypotheses and decoded & mask == positives
                proper_checks += 1
        # Build the actual nonempty intersection closure, not just its advertised value.
        closed = set(hypotheses)
        while True:
            enlarged = closed | {a & b for a in closed for b in hypotheses}
            if enlarged == closed:
                break
            closed = enlarged
        assert closed == set(range(full)) and vc(closed, n) == n - 1
        degree = 0
        for mask in range(1 << n):
            trace = {h & mask for h in hypotheses}
            for h in trace:
                degree = max(degree, sum(bool(h & (1 << x)) and (h ^ (1 << x)) in trace
                                         for x in range(n)))
        assert degree == n - 1
        teachers = [min(mask.bit_count() for mask in range(1 << n)
                        if sum(g & mask == h & mask for g in hypotheses) == 1)
                    for h in hypotheses]
        assert set(teachers) == {3}
        assert all({(h >> x) & 1 for h in hypotheses} == {0, 1} for x in range(n))
        assert 0 not in hypotheses and all(1 << x in hypotheses for x in range(n))
    expected = {1127: '$3$', 1128: '$3$', 1129: '$n-1$', 1130: '$3$', 1131: '$3$',
                1132: '$3$', 1133: '$2n$', 1134: '$n$', 1135: '$n$',
                1136: '$n-1$', 1137: '$3$'}
    for path in (DATA / 'values').glob('*_singleton_cosingleton.json'):
        value = json.loads(path.read_text())
        assert value['class_id'] == '#classes/singleton_cosingleton'
        assert value['value'] == expected.pop(value['id'])
        assert value['status'] == 'established' and value['proof']
    assert not expected
    relation = json.loads((DATA / 'relationships/510_projected_positive_recursive_teaching_dimension_order_sample_compression.json').read_text())
    assert relation['witness_strength'] == 'unbounded'
    assert relation['witness'] == '#classes/singleton_cosingleton'
    assert relation['parameter_1_id'] == '#parameters/projected_positive_recursive_teaching_dimension'
    assert relation['parameter_2_id'] == '#parameters/order_sample_compression'
    assert relation['latex_proof_label'] == 'cor:order-positive-projected-teaching'
    # The same proved family strengthens the existing positive-teaching edges.
    for identifier in (458, 465, 466, 467):
        path, = (DATA / 'relationships').glob(f'{identifier}_*.json')
        witnessed = json.loads(path.read_text())
        assert witnessed['witness'] == '#classes/singleton_cosingleton'
        assert witnessed['witness_strength'] == 'unbounded'
        assert witnessed['status'] == 'established'
    # Properness is deliberately unavailable for this particular order.
    assert 0 not in family(4) and 15 not in family(4)
    print(json.dumps({'domain_sizes': [4, 5, 6, 7, 8], 'sample_checks': sample_checks,
                      'minimality_checks': minimality_checks, 'proper_order_checks': proper_checks,
                      'value_records': 11,
                      'scope': 'Exact OSC three; positive projected RTD n-1; unbounded ratio.'}, indent=2))


if __name__ == '__main__':
    main()
