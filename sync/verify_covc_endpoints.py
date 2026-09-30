#!/usr/bin/env python3
"""Exact small-class diagnostics; these are not proofs for arbitrary domains."""
from itertools import product

def traces(H,S):
    return {sum(((h>>i)&1)<<j for j,i in enumerate(S)) for h in H}
def supports(n):
    return [tuple(i for i in range(n) if (s>>i)&1) for s in range(1<<n)]
def covc(H,n):
    best=0
    for S in supports(n):
        T=traces(H,S);k=len(S)
        for t in set(range(1<<k))-T:
            if all((t^(1<<i)) in T for i in range(k)):best=max(best,k)
    return best
def vc(H,n):return max(len(S) for S in supports(n) if len(traces(H,S))==1<<len(S))
def ample(H,n):
    sh=sum(len(traces(H,S))==1<<len(S) for S in supports(n))
    return sh==len(H)
def effective(H,n):return sum(len(traces(H,(i,)))==2 for i in range(n))
def cube_codimension(H,n):
    cubes=[]
    for w in product((-1,0,1),repeat=n):
        C=frozenset(h for h in range(1<<n) if all(b<0 or (h>>i)&1==b for i,b in enumerate(w)))
        if not C.intersection(H):cubes.append((C,w.count(-1)))
    return max(n-d for C,d in cubes if not any(C<D for D,_ in cubes)) if cubes else 0

def main():
    count=0;ample_count=0
    for n in range(4):
        for mask in range(1,1<<(1<<n)):
            H={h for h in range(1<<n) if (mask>>h)&1};q=covc(H,n)
            assert q==cube_codimension(H,n),(H,n,q)
            assert q<=max(1,effective(H,n)),(H,n,q)
            if ample(H,n):
                ample_count+=1;assert q<=vc(H,n)+1
            for w in product((-1,0,1),repeat=n):
                free=tuple(i for i,b in enumerate(w) if b<0)
                F={h for h in H if all(b<0 or (h>>i)&1==b for i,b in enumerate(w))}
                if F:assert covc(traces(F,free),len(free))<=q
            count+=1
    for n in range(1,7):
        singleton={0}; punctured=set(range(1<<n))-{0}
        assert (covc(singleton,n),effective(singleton,n))==(1,0)
        assert ample(punctured,n) and covc(punctured,n)==n and vc(punctured,n)==n-1
        assert covc({0}|{1<<i for i in range(n)},n)==(0 if n==1 else 2)
        assert covc({0,(1<<n)-1},n)==(0 if n==1 else 2)
        assert covc({(1<<i)-1 for i in range(1,n+1)},n)==(1 if n<=2 else 2)
    print(f'PASS: {count} nonempty classes on at most3coordinates; {ample_count} ample classes; cube formula, coVC bound and nonempty conditioning checked.')
    print('PASS: punctured cubes, singletons and three corrected benchmark families through6coordinates. No general theorem certified by this finite run.')
if __name__=='__main__':main()
