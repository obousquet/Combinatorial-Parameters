"""Check the fixed-interleaving identity against the full joint minimax game.

The imported solver allows predictions based on reports from either factor;
no factorization is imposed on its policy. The survey supplies the all-n proof.
"""
from itertools import permutations
from verify_optional_feedback_compression import game


def classes(n):
    return [tuple(h for h in range(1 << n) if mask >> h & 1)
            for mask in range(1, 1 << (1 << n))]

pairs = interleavings = 0
for n in range(3):
    for m in range(3):
        for H in classes(n):
            for G in classes(m):
                joint = tuple(sorted(h | (g << n) for h in H for g in G))
                joint_minimum = n + m
                for order in permutations(range(n + m)):
                    left = tuple(x for x in order if x < n)
                    right = tuple(x - n for x in order if x >= n)
                    value = game(joint, order)[0]
                    assert value == game(H, left)[0] + game(G, right)[0], (H, G, order)
                    joint_minimum = min(joint_minimum, value)
                    interleavings += 1
                optimum_left = min(game(H, o)[0] for o in permutations(range(n)))
                optimum_right = min(game(G, o)[0] for o in permutations(range(m)))
                assert joint_minimum == optimum_left + optimum_right
                pairs += 1
print(f'PASS: {pairs} factor-class pairs, {interleavings} full-domain interleavings; fixed-order identity and optimized additivity, including empty domains.')
