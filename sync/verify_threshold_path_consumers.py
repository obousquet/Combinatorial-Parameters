#!/usr/bin/env python3
"""Exact bounded endpoint-parameter checks for consolidation T2.
No imported capped-threshold convention or solver is used.
"""
from itertools import combinations
from functools import lru_cache
import json
from pathlib import Path

def tp(C,n,path=True):
    t=p=0
    for mask in range(1,1<<n):
        d=mask.bit_count()
        traces={c&mask for c in C}
        if len(traces)<d+1:continue
        def connected(start):
            @lru_cache(None)
            def visit(done):
                if done==mask:return True
                rest=mask^done
                while rest:
                    bit=rest&-rest;rest-=bit
                    if (start^done^bit) in traces and visit(done|bit):return True
                return False
            return visit(0)
        if 0 in traces and connected(0):t=max(t,d)
        if path and d>p and any(connected(start) for start in traces):p=d
    return t,p

def main():
    checked=0
    for n in range(1,5):
        controls=[([1<<i for i in range(n)],(0 if n==1 else 1,min(n-1,2))),([0]+[1<<i for i in range(n)],(1,min(n,2))),([0,(1<<n)-1],(1,1)),(range(1<<n),(n,n)),([(1<<k)-1 for k in range(1,n+1)],(n-1,n-1))]
        for C,expected in controls:assert tp(C,n)==expected,(n,C,tp(C,n),expected);checked+=1
        majority=[c|((c.bit_count()>n/2)<<n) for c in range(1<<n)]
        assert tp(majority,n+1)[0]==n;checked+=1
    for r in range(3):
        n=1<<r;C=[(1<<i)|(i<<n) for i in range(n)]
        assert tp(C,n+r,False)[0]==r;checked+=1
    incomplete=[]
    for codes in combinations(range(4),3):
        C=[(1<<i)|(c<<3) for i,c in enumerate(codes)]
        incomplete.append(tp(C,5,False)[0]);checked+=1
    assert set(incomplete)=={1,2},incomplete
    C5=[]
    for h in range(32):
        if any(tuple((h>>((a+j)%5))&1 for j in range(4))==(1,0,0,1) for a in range(5)):C5.append(h)
    assert len(C5)==10 and tp(C5,5)==(2,4);checked+=1
    assert tp([0,3,5],3)==(2,2);checked+=1
    # Unit-cube restrictions check generic inequalities on every small class.
    count=0
    for n in range(1,4):
      for codes in range(1,1<<(1<<n)):
        C=[i for i in range(1<<n) if codes>>i&1];t,p=tp(C,n)
        vc=max(m.bit_count() for m in range(1<<n) if len({h&m for h in C})==1<<m.bit_count())
        diameter=max((a^b).bit_count() for a in C for b in C)
        oriented=max((a&~b).bit_count() for a in C for b in C)
        effective=0
        for c in C:effective|=c^C[0]
        assert vc<=t<=p<=diameter and t<=oriented and t<=effective.bit_count() and p<=2*t and p<len(C)
        count+=1
    data=Path(__file__).resolve().parents[1]/'data'
    read=lambda folder,id:json.loads(next((data/folder).glob(f'{id:03d}_*.json')).read_text())
    assert read('values',127)['value']==r'$\log_2 n\quad(n=2^r,\ r\ge1)$'
    assert read('values',135)['value']==r'$\min\{n,2\}$'
    for i in range(335,339):
        rec=read('relationships',i);assert rec['incomparability_strength']=='affine' and r'\mathrm P(\mathcal S_n)=2' in rec['parameter_2_larger_witness']
    assert read('relationships',126)['multiplicative_constant']=='1/3'
    print(f'PASS {checked} family cases; {count} exhaustive classes; C5 exact (T,P)=(2,4); incomplete n3 addressing T values={incomplete}; changed-record guards.')
if __name__=='__main__':main()
