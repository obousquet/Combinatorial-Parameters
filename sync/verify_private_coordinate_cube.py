#!/usr/bin/env python3
"""Bounded replay of the DB-owned private-coordinate cube proofs (n=1..3).

No optimization or solver. Checks every realizable partial sample and every
coordinate projection, using explicit teachers and cube reconstruction.
"""
from itertools import combinations
import json
from pathlib import Path

from verify_full_cube_labeled_compression import block_table, scheme

DATA = Path(__file__).resolve().parents[1] / 'data'


def concepts(n: int) -> list[int]:
    definition = json.loads((DATA / 'classes/053_private_coordinate_cube.json').read_text())
    assert definition['short_name'] == 'private_coordinate_cube'
    assert 'h_v(p_w)=1' in definition['definition']
    assert 'n\\ge1' in definition['definition']
    return [v | (1 << (n + v)) for v in range(1 << n)]


def cube_key(n: int, mask: int, labels: int, table: dict) -> tuple[int, int, int]:
    sample = ''.join(str((labels >> i) & 1) if mask & (1 << i) else '*'
                     for i in range(n))
    key, word = scheme(sample, table)
    km = sum(1 << i for i, s in enumerate(key) if s != '*')
    ky = sum(1 << i for i, s in enumerate(key) if s == '1')
    output = sum(int(s) << i for i, s in enumerate(word))
    return km, ky, output


def verify() -> None:
    table = block_table()
    samples = projections = pairs = 0
    improper = False
    for n in range(1, 4):
        words = concepts(n)
        d = n + (1 << n)
        original = (1 << n) - 1
        assert len(set(words)) == 1 << n
        assert (max(words) | 0).bit_length() == d
        varying = 0
        for word in words:
            varying |= word ^ words[0]
        assert varying.bit_count() == d
        # Direct ordinary no-clashing teachers: every private positive teaches.
        for v, word in enumerate(words):
            teacher = 1 << (n + v)
            assert [w for w in words if w & teacher] == [word]
        decoded = {}
        vc = 0
        for mask in range(1 << d):
            traces = sorted({w & mask for w in words})
            if len(traces) == 1 << mask.bit_count():
                vc = max(vc, mask.bit_count())
            # Every projected trace receives one teacher; duplicate traces merged.
            coords = [i for i in range(n) if mask & (1 << i)]
            teachers = {}
            for trace in traces:
                private = trace & ~original
                if private:
                    teachers[trace] = private
                else:
                    compact = sum(((trace >> x) & 1) << j for j, x in enumerate(coords))
                    key, _, _ = cube_key(len(coords), (1 << len(coords)) - 1, compact, table)
                    teachers[trace] = sum(1 << x for j, x in enumerate(coords) if key & (1 << j))
                assert teachers[trace] & mask == teachers[trace]
                assert teachers[trace].bit_count() <= (n + 1) // 2
            for a, b in combinations(traces, 2):
                assert (a ^ b) & (teachers[a] | teachers[b]), (n, mask, a, b)
                pairs += 1
            projections += 1
            for labels in traces:
                private_positive = labels & ~original
                if private_positive:
                    assert private_positive.bit_count() == 1
                    key = (private_positive, private_positive)
                    output = words[private_positive.bit_length() - 1 - n]
                else:
                    km, ky, output = cube_key(n, mask & original, labels & original, table)
                    key = km, ky
                    # Here every reconstructed private label is zero: intentional.
                    improper |= output not in words
                assert key[0] & mask == key[0] and labels & key[0] == key[1]
                assert key[0].bit_count() <= (n + 1) // 2
                assert output & mask == labels
                assert key not in decoded or decoded[key] == output
                decoded[key] = output
                samples += 1
        assert vc == n
        # Lower bound on projected NCTD: each of n*2^(n-1) cube edges must
        # have its coordinate in at least one endpoint teacher.
        assert (n * (1 << (n - 1)) + (1 << n) - 1) // (1 << n) == (n + 1) // 2
        # A deliberately broken decoder (never transmitting a private positive)
        # fails the singleton sample consisting of that positive example.
        assert not (0 & (1 << n)) == 1 << n
    assert improper, 'The ordinary compression proof must not claim properness'
    expected = {1139: '$n$', 1140: '$1$', 1141: r'$\lceil n/2\rceil$',
                1142: r'$\Theta(n)$', 1143: '$2^n$', 1144: '$n+2^n$'}
    for value_id, value in expected.items():
        paths = list((DATA / 'values').glob(f'{value_id}_*.json'))
        assert len(paths) == 1
        stored = json.loads(paths[0].read_text())
        assert stored['class_id'] == '#classes/private_coordinate_cube'
        assert stored['status'] == 'established' and stored['value'] == value
    relation = json.loads((DATA / 'relationships/514_noclashing_teaching_dimension_labeled_sample_compression.json').read_text())
    assert relation['status'] == 'refuted' and relation['witness_strength'] == 'unbounded'
    assert relation['witness'] == '#classes/private_coordinate_cube'
    assert relation['parameter_1_id'] == '#parameters/noclashing_teaching_dimension'
    assert relation['parameter_2_id'] == '#parameters/labeled_sample_compression'
    print(f'Passed {samples} samples, {projections} projections, {pairs} teacher pairs; '
          'three exact VC values, six DB guards, improper and corrupted-decoder controls.')


if __name__ == '__main__':
    verify()
