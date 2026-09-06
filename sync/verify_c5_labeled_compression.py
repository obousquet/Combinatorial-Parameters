"""Exact message-free labeled compression of C5 is two.

Uses the database's existing C5 constructor. No claim follows from a solver
timeout; accepted tables are independently replayed on every actual sample.
"""

from itertools import product
from pathlib import Path
import json
import sys

from verify_projected_teaching_values import warmuth_c5

type Sample = tuple[int, int]


def samples(concepts: tuple[int, ...], n: int) -> list[Sample]:
    return sorted({(mask, h & mask) for h in concepts for mask in range(1 << n)})


def available(s: Sample, keys: list[Sample]) -> list[int]:
    mask, labels = s
    return [i for i, (submask, sublabels) in enumerate(keys)
            if submask & mask == submask and labels & submask == sublabels]


def replay(decoder: list[int], keys: list[Sample], partial: list[Sample]) -> list[Sample]:
    return [s for s in partial
            if not any(decoder[i] & s[0] == s[1] for i in available(s, keys))]


def width_one_exists(concepts: tuple[int, ...], n: int) -> tuple[bool, dict[str, int]]:
    """Enumerate distinct keys for the ten full inputs; only one key remains.

    Every valid width-one decoder has such an injection. Prune only when a
    partial sample has neither a good assigned key nor any unassigned key.
    At a leaf try every total output for the remaining key independently.
    """
    keys = [(0, 0)] + [(1 << x, label << x) for x in range(n) for label in (0, 1)]
    assert len(concepts) == len(keys) - 1
    partial = samples(concepts, n)
    allowed = [available(s, keys) for s in partial]
    all_samples = (1 << len(partial)) - 1
    coverage = [[sum(1 << j for j, s in enumerate(partial)
                     if i in allowed[j] and word & s[0] == s[1])
                 for word in range(1 << n)] for i in range(len(keys))]
    reachable = [sum(1 << j for j in range(len(partial)) if i in allowed[j])
                 for i in range(len(keys))]
    full_keys = {h: set(available(((1 << n) - 1, h), keys)) for h in concepts}
    nodes = leaves = pruned = 0

    def search(todo: tuple[int, ...], free: frozenset[int], covered: int) -> bool:
        nonlocal nodes, leaves, pruned
        nodes += 1
        possible = covered
        for i in free:
            possible |= reachable[i]
        if possible != all_samples:
            pruned += 1
            return False
        if not todo:
            leaves += 1
            assert len(free) == 1
            i = next(iter(free))
            return any(covered | coverage[i][word] == all_samples for word in range(1 << n))
        h = min(todo, key=lambda h: len(full_keys[h] & free))
        remaining = tuple(g for g in todo if g != h)
        for i in sorted(full_keys[h] & free):
            if search(remaining, free - {i}, covered | coverage[i][h]):
                return True
        return False

    answer = search(concepts, frozenset(range(len(keys))), 0)
    return answer, {'nodes': nodes, 'leaves': leaves, 'pruned': pruned}


def exhaustive_lower() -> None:
    n = 5
    concepts = tuple(sorted(sum(bit << x for x, bit in enumerate(h)) for h in warmuth_c5()))
    partial = samples(concepts, n)
    possible, counts = width_one_exists(concepts, n)
    assert not possible
    assert counts == {'nodes': 39811, 'leaves': 5848, 'pruned': 17773}
    assert width_one_exists(tuple(range(4)), 2)[0]
    print('EXHAUSTIVE LOWER PASS', counts, '; full two-cube positive control passes')

    # Compact independently replayed upper rule: majority in the version
    # space of the key, with ties one only for a two-positive key.
    upper_keys = [s for s in partial if s[0].bit_count() <= 2]
    table = []
    for mask, labels in upper_keys:
        version = [h for h in concepts if h & mask == labels]
        tie = mask.bit_count() == labels.bit_count() == 2
        table.append(sum((2 * sum((h >> x) & 1 for h in version) > len(version)
                          or (tie and 2 * sum((h >> x) & 1 for h in version) == len(version))) << x
                         for x in range(n)))
    assert not replay(table, upper_keys, partial)
    assert replay([0] * len(upper_keys), upper_keys, partial)
    # A second representation verifies coverage without the bit-mask list helper.
    unpack = lambda s: frozenset((x, (s[1] >> x) & 1) for x in range(n) if s[0] & (1 << x))
    literal_keys = [unpack(u) for u in upper_keys]
    for sample in partial:
        literals = unpack(sample)
        assert any(key <= literals and all((word >> x) & 1 == y for x, y in literals)
                   for key, word in zip(literal_keys, table))
    record = json.loads((Path(__file__).resolve().parents[1] /
                         'data/values/1138_labeled_sample_compression_warmuth_c5.json').read_text())
    assert record['value'] == '$2$' and record['status'] == 'established'
    assert 'ties as one exactly when the key consists of two positive examples' in record['proof']
    print('UPPER PASS', len(partial), 'samples;', len(upper_keys), 'keys')


def main() -> None:
    from z3 import And, Bool, Or, Solver, is_true, sat

    n = 5
    concepts = tuple(sorted(sum(bit << x for x, bit in enumerate(h)) for h in warmuth_c5()))
    keys = [(0, 0)] + [(1 << x, label << x) for x in range(n) for label in (0, 1)]
    partial = samples(concepts, n)
    assert len(concepts) == 10
    rotate = lambda h, x: ((h << x) | (h >> (n - x))) & 31
    cyclic_cases = 0
    for negative, positive, empty in product(concepts, concepts, concepts):
        if negative & 1 or not positive & 1:
            continue
        table = [empty] + [rotate(h, x) for x in range(n) for h in (negative, positive)]
        cyclic_cases += 1
        if not replay(table, keys, partial):
            print('CYCLIC TABLE', table, 'samples', len(partial), flush=True)
            return
    print('Cyclic proper tables rejected:', cyclic_cases, flush=True)
    solver = Solver()
    solver.set(timeout=15000)
    bits = [[Bool(f'd_{i}_{x}') for x in range(n)] for i in range(len(keys))]
    for s in partial:
        solver.add(Or(*[And(*[bits[i][x] == bool(s[1] & (1 << x))
                             for x in range(n) if s[0] & (1 << x)])
                        for i in available(s, keys)]))
    status = solver.check()
    print('Unrestricted status:', status, 'samples', len(partial), flush=True)
    if status == sat:
        model = solver.model()
        table = [sum(int(is_true(model.eval(bits[i][x], model_completion=True))) << x
                     for x in range(n)) for i in range(len(keys))]
        assert not replay(table, keys, partial)
        print('TABLE', table, 'proper', all(h in concepts for h in table))
    else:
        print('No independently checked negative certificate; no mathematical lower bound imported.')


if __name__ == '__main__':
    if '--discover' in sys.argv:
        main()
    else:
        exhaustive_lower()
