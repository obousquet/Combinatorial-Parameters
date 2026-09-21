"""Finite regression for the teaching transcript; the survey owns the proof.

Independently compute recursive teaching by simultaneous deletion, and check
both the transcript invariant and the inequality on every domain restriction.
"""
from functools import lru_cache

@lru_cache(None)
def policy(H, S):
    if not S:
        return 0, None, None
    return min((max((y != p) + policy(tuple(h for h in H if (h >> x & 1) == y), S ^ (1 << x))[0]
                    for y in (0, 1) if any((h >> x & 1) == y for h in H)), x, p)
               for x in range(S.bit_length()) if S >> x & 1 for p in (0, 1))

def subsets(S):
    T = S
    while True:
        yield T
        if not T:
            break
        T = (T - 1) & S

@lru_cache(None)
def teaching_sizes(H, S):
    return tuple(min(T.bit_count() for T in subsets(S)
                     if all(g == h or (g & T) != (h & T) for g in H)) for h in H)

@lru_cache(None)
def rtd(H, S):
    result = 0
    while H:
        sizes = teaching_sizes(H, S)
        minimum = min(sizes)
        result = max(result, minimum)
        H = tuple(h for h, size in zip(H, sizes) if size > minimum)
    return result

def transcript(H, S):
    original, domain = H, S
    K = labels = 0
    while S:
        _, x, p = policy(H, S)
        y = 1 - p if any((h >> x & 1) != p for h in H) else p
        if y != p:
            K |= 1 << x
            labels |= y << x
        H = tuple(h for h in H if (h >> x & 1) == y)
        S ^= 1 << x
        assert H == tuple(h for h in original if (h & K) == labels)
    assert len(H) == 1
    assert K.bit_count() <= policy(original, domain)[0]
    assert min(teaching_sizes(original, domain)) <= K.bit_count()

classes = projections = 0
for n in range(4):
    domain = (1 << n) - 1
    for mask in range(1, 1 << (1 << n)):
        H = tuple(h for h in range(1 << n) if mask >> h & 1)
        maximum_rtd = maximum_cost = 0
        for S in subsets(domain):
            trace = tuple(sorted({h & S for h in H}))
            transcript(trace, S)
            cost = policy(trace, S)[0]
            assert rtd(trace, S) <= cost
            maximum_rtd = max(maximum_rtd, rtd(trace, S))
            maximum_cost = max(maximum_cost, cost)
            projections += 1
        assert maximum_rtd <= maximum_cost
        classes += 1
print(f'PASS: {classes} nonempty classes, {projections} domain restrictions; transcript invariant and independently computed recursive teaching bounds.')
