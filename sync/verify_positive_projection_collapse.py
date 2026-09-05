#!/usr/bin/env python3
"""Independent finite regression for the positive projection-closure theorem.

Computes recursive teaching by optimizing all first removals, no-clashing
teaching by backtracking all positive maps, and projected degree directly.
The universal proof is prop:positive-projection-collapse in the survey.
"""
from functools import lru_cache


def submasks(mask):
    subset = mask
    while True:
        yield subset
        if subset == 0:
            return
        subset = (subset - 1) & mask


@lru_cache(None)
def positive_teaching_size(h, family):
    options = [s.bit_count() for s in submasks(h)
               if all(g == h or s & g != s for g in family)]
    return min(options) if options else None


@lru_cache(None)
def positive_rtd(family):
    if len(family) <= 1:
        return 0
    choices = []
    for h in family:
        teaching_size = positive_teaching_size(h, family)
        if teaching_size is not None:
            choices.append(max(teaching_size, positive_rtd(tuple(g for g in family if g != h))))
    assert choices, "an inclusion-maximal concept always has a positive teaching set"
    return min(choices)


@lru_cache(None)
def positive_nctd(family):
    if len(family) <= 1:
        return 0
    for width in range(max(h.bit_count() for h in family) + 1):
        options = {h: [s for s in submasks(h) if s.bit_count() <= width] for h in family}
        targets = sorted(family, key=lambda h: len(options[h]))

        def assign(index, mapping):
            if index == len(targets):
                return True
            h = targets[index]
            for sample in options[h]:
                if all(sample & g != sample or old_sample & h != old_sample
                       for g, old_sample in mapping):
                    if assign(index + 1, mapping + [(h, sample)]):
                        return True
            return False

        if assign(0, []):
            return width
    raise AssertionError("the full positive support map is no-clashing")


def positive_degree(family):
    members = set(family)
    return max(sum(h ^ (1 << i) in members for i in range(h.bit_length()) if h & (1 << i))
               for h in family)


def main():
    checked = 0
    for n in range(4):
        for encoded in range(1, 1 << (1 << n)):
            family = tuple(h for h in range(1 << n) if encoded & (1 << h))
            projections = {tuple(sorted({h & mask for h in family})) for mask in range(1 << n)}
            degree = max(positive_degree(trace) for trace in projections)
            teaching = max(positive_rtd(trace) for trace in projections)
            noclash = max(positive_nctd(trace) for trace in projections)
            assert degree == teaching == noclash, (n, family, degree, teaching, noclash)
            # Check the stronger intermediate lemma for every finite positive
            # teaching problem, not just the eventual elimination order.
            for h in family:
                minimum = positive_teaching_size(h, family)
                assert minimum is None or minimum <= degree
            checked += 1
    print(f"Positive projected RTD = NCTD = maximum positive degree on all {checked} nonempty classes on 0..3 coordinates.")
    print("Independent recurrences/map search and the finite-positive-teaching lemma passed.")


if __name__ == "__main__":
    main()
