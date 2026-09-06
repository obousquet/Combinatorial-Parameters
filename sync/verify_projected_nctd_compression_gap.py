#!/usr/bin/env python3
"""Exact width-one compression search by finite output-domain splitting.

Every branch is an exhaustive good/bad partition of a key's possible total
outputs. Unit propagation is only applied when a sample has one usable key.
No external solver or floating-point computation is used.
"""
from itertools import combinations
import json
from pathlib import Path
import re

from verify_full_cube_labeled_compression import block_table, scheme

DATA = Path(__file__).resolve().parents[1] / 'data'


def class_words() -> tuple[int, ...]:
    record = json.loads((DATA / 'classes/054_antipodal_six_code.json').read_text())
    words = re.findall(r'\\mathtt\{([01]{4})\}', record['definition'])
    assert len(words) == 6
    return tuple(sorted(sum(int(bit) << x for x, bit in enumerate(word)) for word in words))


def samples(words: tuple[int, ...], n: int) -> list[tuple[int, int]]:
    return sorted({(m, h & m) for h in words for m in range(1 << n)})


def width_one(words: tuple[int, ...], n: int) -> tuple[list[int] | None, dict[str, int]]:
    keys = [(0, 0)] + [(1 << x, y << x) for x in range(n) for y in (0, 1)]
    partial = samples(words, n)
    compatible = lambda m, y: sum(1 << h for h in range(1 << n) if h & m == y)
    constraints = [(tuple(i for i, (km, ky) in enumerate(keys) if km & m == km and y & km == ky),
                    compatible(m, y)) for m, y in partial]
    stats = dict(nodes=0, splits=0, prunes=0, units=0)

    def search(domains: list[int]) -> list[int] | None:
        stats['nodes'] += 1
        while True:
            changed = False
            pending = []
            for allowed, good in constraints:
                if any(domains[i] & ~good == 0 for i in allowed):
                    continue
                possible = [i for i in allowed if domains[i] & good]
                if not possible:
                    stats['prunes'] += 1
                    return None
                if len(possible) == 1:
                    i = possible[0]
                    domains[i] &= good
                    stats['units'] += 1
                    changed = True
                else:
                    pending.append((possible, good))
            if not changed:
                break
        if not pending:
            return [(d & -d).bit_length() - 1 for d in domains]
        possible, good = min(pending, key=lambda item: (len(item[0]),
                              sum((domains[i] & item[1]).bit_count() for i in item[0])))
        i = min(possible, key=lambda i: (domains[i] & good).bit_count())
        stats['splits'] += 1
        for restriction in (good, ~good):
            branch = domains.copy()
            branch[i] &= restriction
            assert branch[i] and branch[i] != domains[i]
            result = search(branch)
            if result is not None:
                return result
        return None

    result = search([compatible(m, y) for m, y in keys])
    if result is not None:
        assert all(any(km & m == km and y & km == ky and word & m == y
                       for (km, ky), word in zip(keys, result)) for m, y in partial)
    return result, stats


def injection_check(words: tuple[int, ...], n: int) -> tuple[bool, dict[str, int]]:
    """Independent exhaustion: inject full concepts into keys, then fill free keys.

    Uses sets of labeled coordinates for availability/consistency. Only the
    aggregate sets of covered samples are packed into integers for speed.
    """
    unpack = lambda m, y: frozenset((x, (y >> x) & 1) for x in range(n) if m & (1 << x))
    full = {h: unpack((1 << n) - 1, h) for h in range(1 << n)}
    keys = [frozenset()] + [frozenset({(x, y)}) for x in range(n) for y in (0, 1)]
    partial = sorted({frozenset(subset) for h in words for k in range(n + 1)
                      for subset in combinations(sorted(full[h]), k)},
                     key=lambda s: (len(s), sorted(s)))
    reachable = [sum(1 << j for j, s in enumerate(partial) if u <= s) for u in keys]
    coverage = [{h: sum(1 << j for j, s in enumerate(partial) if u <= s <= literals)
                 for h, literals in full.items() if u <= literals} for u in keys]
    all_samples = (1 << len(partial)) - 1
    stats = dict(injections=0, residual_nodes=0, prunes=0)

    def possible(free: tuple[int, ...], covered: int) -> bool:
        for i in free:
            covered |= reachable[i]
        return covered == all_samples

    def fill(free: tuple[int, ...], covered: int) -> bool:
        stats['residual_nodes'] += 1
        if covered == all_samples:
            return True
        if not possible(free, covered):
            stats['prunes'] += 1
            return False
        if not free:
            return False
        i, *rest = free
        return any(fill(tuple(rest), covered | added) for added in coverage[i].values())

    def assign(todo: tuple[int, ...], free: tuple[int, ...], covered: int) -> bool:
        if not possible(free, covered):
            stats['prunes'] += 1
            return False
        if not todo:
            stats['injections'] += 1
            return fill(free, covered)
        h = min(todo, key=lambda h: sum(keys[i] <= full[h] for i in free))
        return any(assign(tuple(g for g in todo if g != h), tuple(j for j in free if j != i),
                          covered | coverage[i][h]) for i in free if keys[i] <= full[h])
    return assign(words, tuple(range(len(keys))), 0), stats


def check_teacher(words: tuple[int, ...], teachers: dict[int, int]) -> int:
    assert set(teachers) == set(words)
    for a, b in combinations(words, 2):
        assert (a ^ b) & ((1 << teachers[a]) | (1 << teachers[b])), (a, b)
    return len(words) * (len(words) - 1) // 2


def verify() -> None:
    words = class_words()
    proof = json.loads((DATA / 'values/1145_projected_noclashing_teaching_dimension_antipodal_six_code.json').read_text())['proof']
    rows = re.findall(r'([01]{4})&(\d)&([01])', proof)
    teacher = {sum(int(bit) << x for x, bit in enumerate(word)): int(x) for word, x, _ in rows}
    for word, x, label in rows:
        assert word[int(x)] == label
    pair_checks = check_teacher(words, teacher)
    projection_count = 1
    table = block_table()
    vc = 0
    for mask in range(15):
        coords = [x for x in range(4) if mask & (1 << x)]
        projected = tuple(sorted({sum(((h >> x) & 1) << i for i, x in enumerate(coords)) for h in words}))
        n = len(coords)
        if len(projected) == 1 << n:
            vc = max(vc, n)
        if n == 3:
            absent = sorted(set(range(8)) - set(projected))
            assert len(absent) == 2 and absent[0] ^ absent[1] == 7
            neighbors = {h: sorted(g for g in projected if (h ^ g).bit_count() == 1) for h in projected}
            assert all(len(v) == 2 for v in neighbors.values())
            cycle = [min(projected)]
            while len(cycle) < 6:
                cycle.append(next(g for g in neighbors[cycle[-1]] if g not in cycle))
            assert cycle[0] in neighbors[cycle[-1]]
            mapping = {h: (h ^ cycle[(i + 1) % 6]).bit_length() - 1 for i, h in enumerate(cycle)}
            pair_checks += check_teacher(projected, mapping)
            # These projections themselves genuinely have one-example compression.
            assert width_one(projected, n)[0] is not None
        elif n:
            mapping = {}
            for h in projected:
                key, _ = scheme(''.join(str((h >> x) & 1) for x in range(n)), table)
                mapping[h] = next(i for i, b in enumerate(key) if b != '*')
            pair_checks += check_teacher(projected, mapping)
        else:
            assert projected == (0,)
        projection_count += 1
    assert vc == 2
    result, domain_stats = width_one(words, 4)
    assert result is None
    assert domain_stats == dict(nodes=215, splits=107, prunes=108, units=824)
    possible, injection_stats = injection_check(words, 4)
    assert not possible
    assert injection_stats == dict(injections=656, residual_nodes=17840, prunes=16964)
    assert width_one(tuple(range(4)), 2)[0] is not None
    assert injection_check(tuple(range(4)), 2)[0]
    assert width_one(tuple(range(8)), 3)[0] is None
    for removed in words:
        assert width_one(tuple(h for h in words if h != removed), 4)[0] is not None
    deletion_checks = 0
    for m, y in samples(words, 4):
        s = ''.join(str((y >> x) & 1) if m & (1 << x) else '*' for x in range(4))
        key, output = scheme(s, table)
        assert sum(b != '*' for b in key) <= 2
        assert all(k == '*' or k == b for k, b in zip(key, s))
        assert all(b == '*' or b == o for b, o in zip(s, output))
        for x in range(4):
            if s[x] != '*' and key[x] == '*':
                assert scheme(s[:x] + '*' + s[x + 1:], table) == (key, output)
                deletion_checks += 1
    # Negative control for the no-clashing checker.
    try:
        check_teacher(words, dict.fromkeys(words, 0))
    except AssertionError:
        pass
    else:
        raise AssertionError('corrupted teaching assignment accepted')
    for value_id, expected in ((1145, '$1$'), (1146, '$1$'), (1147, '$2$'), (1148, '$2$'), (1149, '$2$')):
        value = json.loads(next((DATA / 'values').glob(f'{value_id}_*.json')).read_text())
        assert value['value'] == expected and value['status'] == 'established'
    for rid in (442, 515):
        relation = json.loads(next((DATA / 'relationships').glob(f'{rid}_*.json')).read_text())
        assert relation['witness'] == '#classes/antipodal_six_code' and relation['witness_strength'] == 'strict'
        assert relation['status'] == ('established' if rid == 442 else 'refuted')
    print('Domain exhaustion:', domain_stats, '; independent injection exhaustion:', injection_stats)
    print(f'Passed {projection_count} projections, {pair_checks} teacher pairs, '
          f'63 compression samples, {deletion_checks} stability deletions; '
          'six concept-deletion compressions, five value guards, two witness guards '
          'and positive/negative controls.')


if __name__ == '__main__':
    verify()
