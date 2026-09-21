"""Exact finite witness for whole-domain versus subset-maximized mistake games."""
from functools import lru_cache
from itertools import permutations

@lru_cache(None)
def ordered(H, order):
    if not order:
        return 0
    x, tail = order[0], order[1:]
    return min(max(int(y != p) + ordered(tuple(h for h in H if h >> x & 1 == y), tail)
                   for y in (0, 1) if any(h >> x & 1 == y for h in H)) for p in (0, 1))

@lru_cache(None)
def adaptive(H, S):
    if not S:
        return 0
    return min(max(int(y != p) + adaptive(tuple(h for h in H if h >> x & 1 == y), S & ~(1 << x))
                   for y in (0, 1) if any(h >> x & 1 == y for h in H))
               for x in range(S.bit_length()) if S >> x & 1 for p in (0, 1))

for d in (1, 2):
    n = d + (1 << d)
    H = tuple(u | (1 << (d + u)) for u in range(1 << d))
    costs = [ordered(H, order) for order in permutations(range(n))]
    subsets = [adaptive(H, S) for S in range(1 << n)]
    assert min(costs) == 1
    assert adaptive(H, (1 << n)-1) == 1
    assert adaptive(H, (1 << d)-1) == max(subsets) == d
    print(f'd={d}: {len(costs)} fixed orders; {len(subsets)} subsets; best=1, full-domain adaptive=1, subset maximum={d}.')
assert max(subsets) > min(costs)
print('PASS: catalogue relationship 103 is refuted on the four-concept, six-coordinate class.')
