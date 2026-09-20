#!/usr/bin/env python3
"""An exact counterexample to key erasure, not to monotonicity of pUSC."""
from itertools import product

# Coordinates (a,x); a is constant one. Each key has one fixed proper output.
H = {(1, 0), (1, 1)}
rho = {frozenset(): (1, 0), frozenset({0}): (1, 1),
       frozenset({1}): (1, 1)}

def encode(s):
    if s.get(1) == 1:
        return frozenset({0}) if 0 in s else frozenset({1})
    return frozenset()

samples = []
for values in product((None, 0, 1), repeat=2):
    s = {i: v for i, v in enumerate(values) if v is not None}
    if not any(all(h[i] == v for i, v in s.items()) for h in H):
        continue
    key = encode(s)
    assert key <= s.keys() and len(key) <= 1
    assert rho[key] in H
    assert all(rho[key][i] == v for i, v in s.items())
    samples.append(s)
assert len(samples) == 6
# After conditioning a=1, samples x=0 and x=1 force different x outputs,
# yet the proposed erasure sends both selected keys to the empty key.
keys = [encode({0: 1, 1: b}) - {0} for b in (0, 1)]
assert keys == [frozenset(), frozenset()]
# The conditioned class itself still has proper, reconstruction-stable width 1.
for b in (None, 0, 1):
    key = frozenset({1}) if b == 1 else frozenset()
    output = int(bool(key))
    assert b is None or output == b
# The counterexample encoder is not stable: deleting unselected x changes output.
assert encode({0: 1, 1: 1}) == frozenset({0})
assert rho[encode({0: 1, 1: 1})] != rho[encode({0: 1})]
print('PASS: all 6 original samples; forced empty-key collision after erasure.')
print('Both original and conditioned classes have pUSC=psUSC=1; no monotonicity counterexample.')
