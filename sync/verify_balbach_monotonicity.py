#!/usr/bin/env python3
"""Check the Balbach recursion, constant padding and monotonicity proofs.

The two solvers use target-consistent coordinate subsets versus a complete
ternary-sample scan. No formula for BTD is used to compute its iterates.
The universal proof is survey-owned; this is a bounded regression only.
"""

import json
from functools import cache
from itertools import product
from pathlib import Path

from verify_noclashing_antichain_gap import consistent, samples


@cache
def history(concepts: tuple[str, ...]) -> tuple[tuple[int, ...], ...]:
    if not concepts:
        return ((),)
    d = len(concepts[0])
    choices = {h: samples(h, d) for h in concepts}
    initial = tuple(min(len(s[0]) for s in choices[h]
                        if all(g == h or not consistent(s, g) for g in concepts))
                    for h in concepts)
    stages = [initial]
    for _ in range(sum(initial)+1):
        previous = dict(zip(concepts, stages[-1], strict=True))
        following = tuple(min(len(s[0]) for s in choices[h]
                              if len(s[0]) <= previous[h]
                              and all(g == h or previous[g] < len(s[0])
                                      or not consistent(s, g) for g in concepts))
                          for h in concepts)
        assert all(a <= b for a, b in zip(following, stages[-1], strict=True))
        if following == stages[-1]:
            return tuple(stages)
        stages.append(following)
    raise AssertionError("Nonincreasing finite recursion did not stabilize")


def independent_history(concepts: tuple[str, ...]) -> tuple[tuple[int, ...], ...]:
    d = len(concepts[0])
    universe = tuple(product("*01", repeat=d))
    widths = [sum(a != "*" for a in s) for s in universe]
    owners = [{i for i, h in enumerate(concepts)
               if all(a == "*" or a == b for a, b in zip(s, h, strict=True))}
              for s in universe]
    initial = tuple(min(w for w, own in zip(widths, owners) if own == {i})
                    for i in range(len(concepts)))
    stages = [initial]
    for _ in range(sum(initial)+1):
        filtered = [{i for i in own if stages[-1][i] >= w}
                    for w, own in zip(widths, owners)]
        following = tuple(min(w for w, own in zip(widths, filtered) if own == {i})
                          for i in range(len(concepts)))
        if following == stages[-1]:
            return tuple(stages)
        stages.append(following)
    raise AssertionError("Independent recursion did not stabilize")


def btd(concepts: tuple[str, ...]) -> int:
    return max(history(concepts)[-1], default=0)


def cube_product_checks() -> None:
    families = []
    for d in range(3):
        cube = tuple("".join(v) for v in product("01", repeat=d))
        families.extend(tuple(h for i, h in enumerate(cube) if mask >> i & 1)
                        for mask in range(1, 1 << len(cube)))
    # This factor actually changes between iterations, unlike a full cube.
    families.append(("000", "100", "010", "001"))
    checked = 0
    for factor in families:
        for m in range(3):
            cube = tuple("".join(v) for v in product("01", repeat=m))
            combined = tuple(v+h for v in cube for h in factor)
            expected = tuple(tuple(m+b for _ in cube for b in stage)
                             for stage in history(factor))
            assert history(combined) == expected
            assert independent_history(combined) == expected
            checked += 1
    for n in range(1, 8):
        intervals = tuple("1"*i+"0"*(n-i) for i in range(1, n+1))
        assert history(intervals) == independent_history(intervals)
        assert btd(intervals) == min(2, n-1)
        assert len(history(intervals)) == 1
    for m in (1, 2):
        cube = tuple("".join(v) for v in product("01", repeat=m))
        for n in (2, 3, 4):
            intervals = tuple("1"*i+"0"*(n-i) for i in range(1, n+1))
            combined = tuple(v+h for v in cube for h in intervals)
            assert history(combined) == independent_history(combined)
            assert btd(combined) == m+min(2, n-1)
    for n in range(1, 4):
        cube = tuple("".join(v) for v in product("01", repeat=n))
        core = tuple("1"+v for v in cube)
        repeated = tuple(v[1:]+v[0]*(2**(n-1)) for v in cube)
        for family in (core, repeated):
            assert history(family) == independent_history(family)
            assert history(family) == ((n,)*len(cube),)
    # An old ordinary sample need not remain admissible: the zero target's
    # original size-three teacher loses its target after its value drops to 2.
    factor = families[-1]
    assert history(factor)[-1][0] == 2
    filtered = [h for h, b in zip(factor, history(factor)[-1], strict=True)
                if b >= 3 and h == "000"]
    assert filtered == []
    print(f"{checked} full-iterate cube products, seven interval sizes, six interval products, "
          "six core/repeated cubes and the old-sample rejection control passed.")


def main() -> None:
    cube_product_checks()
    classes = paddings = fibres = subclasses = 0
    for d in range(4):
        cube = tuple("".join(v) for v in product("01", repeat=d))
        assert btd(cube) == d
        for mask in range(1, 1 << len(cube)):
            concepts = tuple(h for i, h in enumerate(cube) if mask >> i & 1)
            stages = history(concepts)
            assert independent_history(concepts) == stages
            classes += 1
            for padding in ("0", "01"):
                padded = tuple(h+padding for h in concepts)
                assert history(padded) == stages
                assert independent_history(padded) == stages
                paddings += 1
            flipped = tuple(sorted("".join("1" if a == "0" else "0" for a in h)
                                   for h in concepts))
            assert btd(flipped) == btd(concepts)
            for j in range(d):
                for bit in "01":
                    fibre = tuple(h[:j]+h[j+1:] for h in concepts if h[j] == bit)
                    assert btd(fibre) <= btd(concepts)
                    fibres += 1
            for submask in range(1 << len(concepts)):
                smaller = tuple(h for i, h in enumerate(concepts) if submask >> i & 1)
                assert btd(smaller) <= btd(concepts)
                subclasses += 1
    # A nontrivial reduction: singleton targets stay at one; the zero target
    # starts at d, then drops to two, not to the subset-teaching value one.
    for d in range(2, 6):
        family = ("0"*d,) + tuple("0"*j+"1"+"0"*(d-j-1) for j in range(d))
        assert history(family) == independent_history(family)
        assert history(family)[0] == (d,) + (1,)*d
        assert history(family)[-1] == (2,) + (1,)*d
    for n in (1, 2):
        words = tuple("".join(v) for v in product("01", repeat=n))
        private = tuple(v+"0"*i+"1"+"0"*(len(words)-i-1) for i, v in enumerate(words))
        assert btd(private) == 1 and independent_history(private) == history(private)
        assert btd(tuple(h[:n] for h in private)) == n
        if n == 2:
            assert all(btd(tuple(h[1:] for h in private if h[0] == bit)) == 1 for bit in "01")
    assert btd(()) == 0 and btd(("",)) == 0
    data = Path(__file__).resolve().parents[1] / "data"
    parameter = json.loads((data / "parameters/092_balbach_teaching_dimension.json").read_text())
    for flag in ("monotonic", "symmetric", "c_monotonic"):
        assert parameter[flag] is True
    for flag in ("p_monotonic", "doubly_monotonic", "strictly_monotonic",
                 "strict_c_monotonic", "tight_strict_c_monotonic"):
        assert parameter[flag] is False
    assert all(e["latex_proof_label"] == "prop:balbach-monotonicity"
               for e in parameter["monotonicity_evidence"].values())
    assert "target itself must survive" in parameter["definition"]
    value = json.loads((data / "values/1176_balbach_teaching_dimension_private_coordinate_cube.json").read_text())
    assert value["value"] == "$1$" and value["status"] == "established"
    assert value["parameter_id"] == "#parameters/balbach_teaching_dimension"
    assert value["class_id"] == "#classes/private_coordinate_cube"
    for value_id, class_id, formula in (
        (1177, "halfintervals", r"$\min\{2,n-1\}$"),
        (1178, "common_core_cube", "$n$"),
        (1179, "repeated_coordinate_cube", "$n$"),
        (1180, "cube_halfinterval_product", r"$m+\min\{2,n-1\}$"),
    ):
        record = json.loads((data / "values" /
                             f"{value_id}_balbach_teaching_dimension_{class_id}.json").read_text())
        assert record["value"] == formula and record["status"] == "established"
        assert record["parameter_id"] == "#parameters/balbach_teaching_dimension"
        assert record["class_id"] == f"#classes/{class_id}"
    relation = json.loads((data / "relationships/255_teaching_dimension_balbach_teaching_dimension.json").read_text())
    assert relation["latex_proof_label"] == "prop:balbach-monotonicity"
    assert "proof" not in relation and "preceding stage" in relation["proof_source"]
    assert relation["witness_strength"] == "unbounded"
    print(f"Balbach: {classes} classes in two solvers, {paddings} constant paddings, "
          f"{fibres} coordinate fibres, {subclasses} subclass comparisons.")
    print("Four singleton-plus-empty reductions and two private-cube controls passed; "
          "equal branches 1/1 have whole value 1. No larger census.")
    print("Eight property/proof links, target-retention wording and private-cube value guarded.")
    print("Four benchmark formulae and the repaired TD comparison proof guarded.")


if __name__ == "__main__":
    main()
