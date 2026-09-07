#!/usr/bin/env python3
"""Read and verify the DB-owned six-cube decoder and fixed-block upper bound.

No solver or discovery search. The decoder table and value proof are owned by
data/values/743_proper_labeled_sample_compression_full_cube.json.
"""

from itertools import combinations, product
import json
from math import comb
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / 'data/values/743_proper_labeled_sample_compression_full_cube.json'


def samples(n: int):
    for pattern in product((-1, 0, 1), repeat=n):
        yield (sum(1 << x for x, b in enumerate(pattern) if b >= 0),
               sum(1 << x for x, b in enumerate(pattern) if b == 1))


def decoder() -> dict[tuple[int, int], int]:
    proof = json.loads(RECORD.read_text())['proof']
    odd = {int(i): int(h) for i, h in re.findall(r'\\rho\((\d)\^1\)=(\d+)', proof)}
    assert set(odd) == {1, 3, 5}
    table = {int(i): tuple(map(int, (a, b, c)))
             for i, a, b, c in re.findall(r'([0-5])&(\d+)&(\d+)&(\d+)', proof)}
    assert set(table) == set(range(6))
    result = {(0, 0): 0}
    for i in range(6):
        result[1 << i, 0] = 63 ^ (1 << i)
        result[1 << i, 1 << i] = 63 if i % 2 == 0 else odd[i]
    for i, j in combinations(range(6), 2):
        m = (1 << i) | (1 << j)
        result[m, 0], result[m, m] = 63 ^ m, m
        for a, b in ((i, j), (j, i)):
            distance = (b - a) % 6
            result[m, 1 << a] = (1 << a) if distance <= 2 else table[a][distance - 3]
    assert set(result) == {s for s in samples(6) if s[0].bit_count() <= 2}
    assert all(0 <= h < 64 and h & m == y for (m, y), h in result.items())
    triples = [h for h in odd.values()]
    triples += [h for row in table.values() for h in row if h.bit_count() == 3]
    assert len(triples) == len(set(triples)) == 20
    assert set(triples) == {h for h in range(64) if h.bit_count() == 3}
    for i in range(6):
        assert table[i][0] == sum(1 << ((i + j) % 6) for j in range(3))
    return result


def encode(sample: tuple[int, int], rho: dict) -> tuple[int, int]:
    """Implement the case proof, independently of exhaustive key selection."""
    mask, positives = sample
    negatives = mask ^ positives
    if not negatives:
        if positives.bit_count() <= 2:
            return positives, positives
        even = positives & sum(1 << x for x in (0, 2, 4))
        if even:
            bit = even & -even
            return bit, bit
        return 2, 2
    if negatives.bit_count() <= 2:
        return negatives, 0
    if not positives:
        return 0, 0
    if positives.bit_count() == 2:
        return positives, positives
    if positives.bit_count() == 1:
        i = positives.bit_length() - 1
        near = negatives & sum(1 << ((i + j) % 6) for j in (1, 2))
        bit = near & -near if near else 1 << ((i + 3) % 6)
        return positives | bit, positives
    assert positives.bit_count() == negatives.bit_count() == 3 and mask == 63
    return next(u for u, h in sorted(rho.items()) if h == positives)


def literals(mask: int, labels: int, n: int) -> frozenset[tuple[int, int]]:
    return frozenset((x, labels >> x & 1) for x in range(n) if mask >> x & 1)


def main() -> None:
    rho = decoder()
    partial = list(samples(6))
    encoded = {}
    for sample in partial:
        mask, labels = sample
        key = encode(sample, rho)
        assert key[0].bit_count() <= 2
        assert key[0] & mask == key[0] and labels & key[0] == key[1]
        assert rho[key] & mask == labels
        s = literals(mask, labels, 6)
        valid = [u for u, h in rho.items() if literals(*u, 6) <= s <= literals(63, h, 6)]
        assert key in valid
        encoded[sample] = key
    assert len(partial) == 729
    restrictions = 0
    for domain in range(64):
        for mask, labels in partial:
            if mask & domain == mask:
                key = encoded[mask, labels]
                restricted_output = rho[key] & domain
                assert key[0] & domain == key[0] and restricted_output & mask == labels
                restrictions += 1
    assert restrictions == 4096
    products = 0
    for s, t in product(partial, repeat=2):
        u, v = encoded[s], encoded[t]
        mask, labels = s[0] | t[0] << 6, s[1] | t[1] << 6
        km, ky = u[0] | v[0] << 6, u[1] | v[1] << 6
        assert km.bit_count() <= 4 and km & mask == km and labels & km == ky
        # Recover the two keys from the transmitted union, not encoder state.
        output = rho[km & 63, ky & 63] | rho[km >> 6, ky >> 6] << 6
        assert output & mask == labels
        products += 1
    assert products == 3**12
    pair = {(0, 0): 0, (1, 0): 2, (1, 1): 3, (2, 0): 1, (2, 2): 3}
    for s in samples(2):
        assert any(u[0] & s[0] == u[0] and s[1] & u[0] == u[1] and h & s[0] == s[1]
                   for u, h in pair.items())
    residual_checks = 0
    for n in (7, 8):
        for mask, labels in samples(n):
            u = encoded[mask & 63, labels & 63]
            m, y = mask >> 6, labels >> 6
            choices = pair if n == 8 else {(0, 0): 0, (1, 0): 0, (1, 1): 1}
            v = next(v for v, h in choices.items()
                     if v[0] & m == v[0] and y & v[0] == v[1] and h & m == y)
            km, ky = u[0] | v[0] << 6, u[1] | v[1] << 6
            output = rho[km & 63, ky & 63] | choices[km >> 6, ky >> 6] << 6
            assert km.bit_count() <= 3 and output & mask == labels
            residual_checks += 1
    assert residual_checks == 8748
    residual = (0, 1, 1, 2, 2, 2)
    exact = {}
    for n in range(1, 13):
        lower = next(k for k in range(n + 1)
                     if sum(2**i * comb(n, i) for i in range(k + 1)) >= 2**n)
        upper = 2 * (n // 6) + residual[n % 6]
        assert lower <= upper
        if lower == upper:
            exact[n] = upper
    assert exact == {1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 11: 4, 12: 4}
    # The fractional counting threshold is attained at six coordinates.
    assert sum(2**i * comb(6, i) for i in range(3)) == 73 >= 64 > 13
    unstable = [(s, u, (s[0] ^ (1 << x), s[1] & ~(1 << x)))
                for s, u in encoded.items() for x in range(6)
                if s[0] >> x & 1 and not u[0] >> x & 1
                and rho[encode((s[0] ^ (1 << x), s[1] & ~(1 << x)), rho)] != rho[u]]
    assert unstable  # No accidental stable-compression claim.
    for filename in ('743_proper_labeled_sample_compression_full_cube.json',
                     '1126_labeled_sample_compression_full_cube.json'):
        value = json.loads((ROOT / 'data/values' / filename).read_text())
        assert value['status'] == 'established' and value['value'] == r'$\Theta(n)$'
        assert 'n=6q+r' in value['details'] and 'n/3+O(1)' in value['details']
        assert '(0,1,1,2,2,2)' in value['details']
    for record_id, status in ((156, 'established'), (158, 'established'),
                              (513, 'refuted'), (516, 'refuted')):
        record_path, = (ROOT / 'data/relationships').glob(f'{record_id}_*.json')
        relation = json.loads(record_path.read_text())
        assert relation['status'] == status and relation['witness_strength'] == 'strict'
        assert relation['witness'] == '#classes/full_cube'
        assert '3/2' in relation['details'] + relation['witness_verification']
    print(f'PASS: {len(rho)} keys, {len(partial)} literal/case sample replays, '
          f'{restrictions} restrictions, {products} two-block samples, '
          f'{residual_checks} short-remainder samples; exact values {exact}; '
          f'non-stability control {unstable[0]}. No solver or larger-cube search.')


if __name__ == '__main__':
    main()
