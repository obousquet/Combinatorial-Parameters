#!/usr/bin/env python3
"""Independent minimax query checks and projected-teaching certificates."""
from functools import lru_cache
from itertools import combinations

def masks(m):
 u=m
 while True:
  yield u
  if u==0:break
  u=(u-1)&m

def query_value(words,n,mode):
 @lru_cache(None)
 def solve(state):
  if len(state)<=1:return 0
  candidates=[]
  if mode in ('membership','mixed'):
   candidates.extend([{h for h in state if h>>x&1==b} for b in (0,1)] for x in range(n))
  if mode in ('proper','mixed','arbitrary'):
   for g in (range(1<<n) if mode=='arbitrary' else words):
    replies=[{h for h in state if (h^g)>>x&1} for x in range(n)]
    replies.append({h for h in state if h==g})
    candidates.append(replies)
  scores=[]
  for replies in candidates:
   replies=[s for s in replies if s]
   if any(len(s)==len(state) for s in replies):continue
   scores.append(1+max(solve(tuple(sorted(s))) for s in replies))
  assert scores
  return min(scores)
 return solve(tuple(sorted(words)))

def main():
 queries=projected_targets=plans=pairchecks=0
 for n in range(1,6):
  words=tuple(1<<x for x in range(n));full=(1<<n)-1
  for mode in ['membership','proper','mixed','arbitrary']:
   expected=int(n>=2) if mode=='arbitrary' else n-1
   assert query_value(words,n,mode)==expected;queries+=1
  assert all({x for x in range(n) if h>>x&1}=={i} for i,h in enumerate(words))
  projected_query=0
  for domain in range(1<<n):
   traces=tuple(sorted({h&domain for h in words}))
   q=query_value(traces,n,'membership');projected_query=max(projected_query,q);queries+=1
   assert q==(domain.bit_count() if domain!=full else n-1)
  assert projected_query==n-1
  for size in range(1,n+1):
   for family in combinations(words,size):
    maxima={h:0 for h in family}
    for domain in range(1<<n):
     traces=sorted({h&domain for h in family})
     teacher={h:(h if len(traces)>1 else 0) for h in traces}
     for a,b in combinations(traces,2):
      assert (a^b)&(teacher[a]|teacher[b]);pairchecks+=1
     remaining=sorted(traces,key=lambda h:h==0)
     for i,h in enumerate(remaining):
      u=h if len(remaining[i:])>1 else 0
      assert u.bit_count()<=1 and sum(g&u==h&u for g in remaining[i:])==1
      plans+=1
     for h in family:
      ts=min(u.bit_count() for u in masks(domain) if sum(g&u==h&u for g in traces)==1)
      maxima[h]=max(maxima[h],ts);projected_targets+=1
    assert set(maxima.values())=={size-1}
 print(f'PASS n=1,...,5: {queries} minimax query values, {projected_targets} projected target teaching optima, '
       f'{plans} positive recursive steps, {pairchecks} no-clashing pair checks. All subfamilies included; no literature equivalence assumed.')
if __name__=='__main__':main()
