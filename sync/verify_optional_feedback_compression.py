"""Finite replay of the fixed-order optional-feedback compression proof.

Enumerates every nonempty binary class through three coordinates, every
fixed order, and every realizable partial sample. Exact minimax recursion
counts reports, not unreported errors. The all-n proof remains in the survey.
"""
from functools import lru_cache
from itertools import permutations, product

@lru_cache(None)
def game(words, order):
    if not order:
        return 0, 0
    x, tail = order[0], order[1:]
    silence = game(words, tail)[0]
    options = []
    for y in (0, 1):
        opposite = tuple(w for w in words if (w >> x & 1) != y)
        options.append(max(silence, 1 + game(opposite, tail)[0]) if opposite else silence)
    return min(options), options.index(min(options))

def encode(words, order, sample):
    retained = set()
    for t, x in enumerate(order):
        y = game(words, order[t:])[1]
        if sample[x] != -1 and sample[x] != y:
            retained.add(x)
            words = tuple(w for w in words if (w >> x & 1) != y)
    return frozenset(retained)

def decode(words, order, retained):
    labels = {}
    for t, x in enumerate(order):
        y = game(words, order[t:])[1]
        labels[x] = 1-y if x in retained else y
        if x in retained:
            words = tuple(w for w in words if (w >> x & 1) != y)
            assert words
    return labels

def main():
    classes = orders = samples = 0
    for n in range(4):
        for mask in range(1, 1 << (1 << n)):
            words = tuple(w for w in range(1 << n) if mask >> w & 1)
            classes += 1
            realizable = [s for s in product((-1, 0, 1), repeat=n)
                          if any(all(b == -1 or (w >> x & 1) == b
                                     for x,b in enumerate(s)) for w in words)]
            for order in permutations(range(n)):
                orders += 1
                bound = game(words, order)[0]
                outputs = {}
                for sample in realizable:
                    key = encode(words, order, sample)
                    assert len(key) <= bound
                    labels = outputs.setdefault(key, decode(words, order, key))
                    assert all(b == -1 or labels[x] == b for x,b in enumerate(sample))
                    samples += 1
    for n in range(1,9):
        words = tuple(1 << i for i in range(n))
        assert game(words, tuple(range(n)))[0] == (n >= 2)
    print(f'PASS: {classes} classes, {orders} fixed orders, {samples} realizable sample replays.')
    print('PASS: singleton optional-feedback values through n=8. Finite evidence only.')

if __name__ == '__main__':
    main()
