#!/usr/bin/env python3
"""Exact finite checks for the retained Q2h witness and weighted elimination step."""
from fractions import Fraction as F
from itertools import combinations, product


def main():
    # The code coordinates precede the three primary singleton coordinates.
    words = ((0,0,0,0,0),(0,1,1,0,0),(1,0,0,1,0),(1,1,0,0,1))
    g = words[0]
    costs = []
    for t in words:
        D = [i for i in range(5) if g[i] != t[i]]
        if not D:
            costs.append(F(1)); continue
        total = F(1)
        for x in D:
            V = [h for h in words if h[x] == t[x]]
            assert len(V) in (1,2)
            if len(V) == 2:
                proposal = V[0]
                # Acceptance or any failed coordinate identifies one candidate.
                for target in V:
                    if proposal == target: continue
                    for y in range(5):
                        if proposal[y] != target[y]:
                            assert sum(h[y] == target[y] for h in V) == 1
                total += F(1,len(D))
        costs.append(total)
    assert costs == [F(1),F(3,2),F(3,2),F(5,3)]
    assert {h[:2] for h in words} == set(product((0,1), repeat=2))
    checks = 0
    # All nontrivial classes on three coordinates, two nonuniform laws.
    cube = tuple(product((0,1), repeat=3))
    for mask in range(1,1 << len(cube)):
        V = tuple(h for i,h in enumerate(cube) if mask >> i & 1)
        if len(V) < 2: continue
        m = len(V)
        for weights in ((F(1,6),F(2,6),F(3,6)),(F(1,7),F(1,7),F(5,7))):
            mean = tuple(sum(F(h[x],m) for h in V) for x in range(3))
            distance = lambda h: sum(weights[x]*abs(h[x]-mean[x]) for x in range(3))
            g = min(V, key=distance)
            for t in V:
                if t == g: continue
                D = [x for x in range(3) if t[x] != g[x]]
                muD = sum(weights[x] for x in D)
                remaining = sum(weights[x]*sum(h[x] == t[x] for h in V) for x in D)/muD
                assert remaining <= F(m,2)
                checks += 1
    print('PASS: exact witness costs 1,3/2,3/2,5/3; VC2; proper continuation. Weighted elimination checks:', checks)
    print('Finite checks only; uniform-in-class bound is proved in the survey.')


if __name__ == '__main__': main()
