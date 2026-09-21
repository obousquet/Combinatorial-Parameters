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

# A partial query on private coordinates has exactly one possible counterexample.
for d in range(1,5):
    H = tuple(u | (1 << (d+u)) for u in range(1 << d))
    for u,h in enumerate(H):
        assert [i for i in range(1 << d) if h >> (d+i) & 1] == [u]

# Exact subset games for the direct small-class arguments.
for n in range(1,7):
    intervals = tuple((1 << k)-1 for k in range(1,n+1))
    assert max(adaptive(intervals,S) for S in range(1 << n)) == int(n >= 2)
assert max(adaptive((0,3,5),S) for S in range(8)) == 1

# Grid-box traces on the proposed shattering sets, including empty labels.
from itertools import product
for n,d in [(2,1),(2,2),(3,1),(3,2)]:
    points = list(product(range(n),repeat=d))
    intervals = [(a,b) for a in range(n) for b in range(a,n)]
    boxes = tuple(sum(1 << i for i,x in enumerate(points)
                      if all(a <= v <= b for v,(a,b) in zip(x,bounds)))
                  for bounds in product(intervals,repeat=d))
    if n == 2:
        selected = [i for i,x in enumerate(points) if sum(x)==1]
    else:
        selected = [i for i,x in enumerate(points) if sum(abs(v-1) for v in x)==1]
    traces = {tuple(h >> i & 1 for i in selected) for h in boxes}
    assert len(traces) == 1 << len(selected)
    if len(points) <= 4:
        value = max(adaptive(boxes,S) for S in range(1 << len(points)))
        assert value == len(selected)
        print(f'Grid n={n}, d={d}: exact subset maximum {value}.')
print('PASS: partial-query witness, half-interval boundaries, three-code game and box shattering controls.')
