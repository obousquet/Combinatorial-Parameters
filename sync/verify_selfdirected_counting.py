"""Replay the target-to-mistake-set injection, including the failed log(n) bound."""
from functools import lru_cache
from math import comb

@lru_cache(None)
def policy(H,S):
    if not S:
        return 0,None,None
    options=[]
    for x in range(S.bit_length()):
        if not (S >> x & 1):
            continue
        for p in (0,1):
            value=max((y != p)+policy(tuple(h for h in H if h >> x & 1 == y),S & ~(1 << x))[0]
                      for y in (0,1) if any(h >> x & 1 == y for h in H))
            options.append((value,x,p))
    return min(options)

@lru_cache(None)
def littlestone(H):
    if not H:
        return -1
    if len(H)==1:
        return 0
    return max(1+min(littlestone(tuple(h for h in H if h >> x & 1 == y)) for y in (0,1))
               for x in range(max(H).bit_length()) if len({h >> x & 1 for h in H})==2)

def encode(H,S,target):
    K=0
    while S:
        _,x,p=policy(H,S);y=target >> x & 1
        if y!=p: K |= 1 << x
        H=tuple(h for h in H if h >> x & 1 == y);S &= ~(1 << x)
    return K

def decode(H,S,K):
    target=0
    while S:
        _,x,p=policy(H,S);y=p ^ (K >> x & 1)
        target |= y << x
        H=tuple(h for h in H if h >> x & 1 == y);S &= ~(1 << x)
        assert H
    return target

classes=targets=0
for n in range(4):
    S=(1 << n)-1
    for mask in range(1,1 << (1 << n)):
        H=tuple(h for h in range(1 << n) if mask >> h & 1)
        k=policy(H,S)[0];keys=[encode(H,S,h) for h in H]
        assert len(set(keys))==len(H)
        assert all(K.bit_count()<=k and decode(H,S,K)==h for h,K in zip(H,keys))
        assert 2**littlestone(H)<=len(H)<=sum(comb(n,j) for j in range(k+1))<=(n+1)**k
        classes+=1;targets+=len(H)
H=(0,1,3,7);k=policy(H,7)[0];L=littlestone(H)
assert (k,L)==(1,2) and 2**L>3**k and 2**L==4**k
print(f'PASS: {classes} classes and {targets} target encodings; every reconstructed target agrees.')
print('Threshold calibration: n=3, k=1, L=2; log(n) fails, log(n+1) is sharp here.')
