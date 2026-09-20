#!/usr/bin/env python3
"""Exact singleton teaching and order/stability checks, including n=1."""
from itertools import combinations

def subsets(mask):
 s=mask
 while True:
  yield s
  if not s:break
  s=(s-1)&mask

def main():
 samples_count=intervals=teaching_cases=order_cases=0
 for n in range(1,8):
  words=tuple(1<<i for i in range(n));full=(1<<n)-1
  samples=sorted({(m,h&m) for h in words for m in range(1<<n)})
  for size in range(1,n+1):
   for members in combinations(words,size):
    for h in members:
     ordinary=min(u.bit_count() for u in range(1<<n) if sum(g&u==h&u for g in members)==1)
     positive=min(u.bit_count() for u in subsets(h) if sum(g&u==u for g in members)==1)
     assert ordinary==positive==int(size>1)
     teaching_cases+=1
  order=((words[0],) if n==1 else (0,)+words)
  def encode(m,y):return y if n>1 else 0
  def decode(u):return u if u else (words[0] if n==1 else 0)
  max_proper=0
  for m,y in samples:
   u=encode(m,y);h=decode(u)
   assert u&m==u and h&m==y
   assert next(g for g in order if g&m==y)==h
   assert next(g for g in order if g&u==y&u)==h
   for v in subsets(m):
    if v&u!=u:continue
    assert encode(v,y&v)==u and decode(encode(v,y&v))==h
    intervals+=1
   first=next(g for g in words if g&m==y)
   costs=[v.bit_count() for v in subsets(m) if next(g for g in words if g&v==y&v)==first]
   max_proper=max(max_proper,min(costs));order_cases+=1
   samples_count+=1
  assert max_proper==n-1
  # Last proper hypothesis requires all earlier-coordinate negatives.
  m=full^words[-1]
  for v in subsets(m):
   assert (next(g for g in words if not g&v)==words[-1])==(v==m)
 print(f'PASS n=1,...,7: {teaching_cases} target/subfamily teaching checks, '
       f'{samples_count} realizable samples, {intervals} exact-key stable intervals, '
       f'{order_cases} proper-order optimizations; last-hypothesis lower certificates pass.')
if __name__=='__main__':main()
