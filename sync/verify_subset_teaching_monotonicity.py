#!/usr/bin/env python3
"""Replay STD conditioning, product and benchmark proofs with all minimizers.

The survey owns the general product and conditioning/incomparability proofs;
the database owns the individual benchmark values and their proofs.
This solver-free regression scans actual ternary samples and cross-checks
each step against the independently represented subset-enumeration helper.
It deliberately does not launch the historical three-coordinate search.
"""

import json
from functools import cache
from itertools import product
from pathlib import Path

from verify_noclashing_antichain_gap import subset_teacher_iteration

type Teachers = dict[str, set[str]]

H = ("000", "001", "010", "011", "100")
EXPECTED: list[Teachers] = [
    dict(zip(H, map(set, (("000",), ("*01",), ("*10",), ("*11",), ("1**",))))),
    dict(zip(H, map(set, (("0**",), ("*01",), ("*10",), ("*11",), ("1**",))))),
    dict(zip(H, map(set, (("0**",), ("*0*",), ("**0",), ("*11",), ("1**",))))),
    dict(zip(H, map(set, (("0**",), ("*0*",), ("**0",), ("*1*", "**1"), ("1**",))))),
]


def contained(sample: str, other: str) -> bool:
    return all(a == "*" or a == b for a, b in zip(sample, other, strict=True))


def width(sample: str) -> int:
    return sum(a != "*" for a in sample)


def minimizers(identifying: list[str]) -> set[str]:
    assert identifying, "Every target must retain an identifying sample"
    minimum = min(map(width, identifying))
    return {s for s in identifying if width(s) == minimum}


def pair(sample: str) -> tuple[tuple[int, ...], tuple[str, ...]]:
    return (tuple(i for i, a in enumerate(sample) if a != "*"),
            tuple(a for a in sample if a != "*"))


def history(concepts: tuple[str, ...]) -> list[Teachers]:
    assert concepts and len(set(concepts)) == len(concepts)
    n = len(concepts[0])
    assert all(len(h) == n and set(h) <= {"0", "1"} for h in concepts)
    universe = tuple("".join(s) for s in product("*01", repeat=n))
    initial = {
        h: minimizers([s for s in universe
                       if {g for g in concepts if contained(s, g)} == {h}])
        for h in concepts
    }
    result = [initial]
    for _ in range(30):
        previous = result[-1]
        owners = {s: {h for h, choices in previous.items()
                      if any(contained(s, t) for t in choices)} for s in universe}
        following = {h: minimizers([s for s in universe if owners[s] == {h}])
                     for h in concepts}
        # Alternate implementation enumerates subsets, not the ternary universe.
        independently = subset_teacher_iteration(
            {h: {pair(s) for s in choices} for h, choices in previous.items()})
        assert independently == {h: {pair(s) for s in choices}
                                 for h, choices in following.items()}
        assert all(contained(s, h) for h, choices in following.items() for s in choices)
        if following == previous:
            return result
        assert following not in result, "Unexpected cycle"
        result.append(following)
    raise AssertionError("Iteration cap exceeded; this is not a convergence proof")


def std(concepts: tuple[str, ...]) -> int:
    return max(width(s) for choices in history(concepts)[-1].values() for s in choices)


def branch(concepts: tuple[str, ...], coordinate: int, label: str) -> tuple[str, ...]:
    return tuple(sorted(h[:coordinate] + h[coordinate+1:]
                        for h in concepts if h[coordinate] == label))


def verify_products_and_benchmarks() -> None:
    @cache
    def littlestone(concepts: tuple[str, ...]) -> int:
        best = 0
        for j in range(len(concepts[0])):
            zero = tuple(h for h in concepts if h[j] == "0")
            one = tuple(h for h in concepts if h[j] == "1")
            if zero and one:
                best = max(best, 1 + min(littlestone(zero), littlestone(one)))
        return best

    factors = (("",), ("0", "1"), ("10", "11"),
               ("00", "01", "10", "11"), H, ("000", "001", "010", "111"))
    products = stages = 0
    for first, second in product(factors, repeat=2):
        if len(first[0]) + len(second[0]) > 5:
            continue
        left, right = history(first), history(second)
        actual = history(tuple(a+b for a in first for b in second))
        for k in range(max(len(left), len(right), len(actual))):
            expected = {a+b: {s+t for s in left[min(k, len(left)-1)][a]
                             for t in right[min(k, len(right)-1)][b]}
                        for a in first for b in second}
            assert actual[min(k, len(actual)-1)] == expected
            stages += 1
        products += 1
    for n in range(1, 8):
        intervals = tuple("1" * i + "0" * (n-i) for i in range(1, n+1))
        assert std(intervals) == int(n >= 2)
        assert len(history(intervals)) <= 2
        assert littlestone(intervals) == n.bit_length()-1
    for n in range(3, 6):
        levels = tuple("".join(v) for v in product("01", repeat=n)
                       if 1 <= v.count("1") <= 2)
        result = history(levels)
        assert len(result) == 1 and std(levels) == n-1
        for h, choices in result[0].items():
            expected = "".join(("0" if b == "0" else "*") if h.count("1") == 1
                               else ("1" if b == "1" else "*") for b in h)
            assert choices == {expected}
    for n in (1, 2):
        cube = tuple("".join(h) for h in product("01", repeat=n))
        private = tuple(h + "0" * i + "1" + "0" * (len(cube)-i-1)
                        for i, h in enumerate(cube))
        assert std(private) == 1
    for n in range(1, 5):
        bits = (n-1).bit_length()
        addressing = tuple("0" * i + "1" + "0" * (n-i-1)
                           + (format(i, f"0{bits}b") if bits else "") for i in range(n))
        assert std(addressing) == int(n >= 2)
    data = Path(__file__).resolve().parents[1] / "data"
    expected_values = {
        "1172_subset_teaching_dimension_halfintervals": r"$\begin{cases}0&n=1,\\1&n\ge2.\end{cases}$",
        "1173_subset_teaching_dimension_addressing": r"$\begin{cases}0&n=1,\\1&n\ge2.\end{cases}$",
        "1174_subset_teaching_dimension_private_coordinate_cube": "$1$",
        "1175_subset_teaching_dimension_cube_halfinterval_product": "$m+1$",
        "103_littlestone_dimension_halfintervals": r"$\lfloor\log_2 n\rfloor$",
    }
    for stem, expected in expected_values.items():
        record = json.loads((data / "values" / f"{stem}.json").read_text())
        assert record["value"] == expected and record["status"] == "established"
        assert record["proof"]
    record = json.loads((data / "relationships/519_subset_teaching_dimension_littlestone_dimension_incomparable.json").read_text())
    assert record["relationship_type"] == "incomparable"
    assert record["latex_proof_label"] == "prop:subset-teaching-littlestone-incomparable"
    assert record["parameter_1_larger_witness"] and record["parameter_2_larger_witness"]
    print(f"Products: {products} fixed pairs, {stages} complete teacher-family stages; "
          "seven interval sizes with exact tree depths, three singleton--doubleton fixed points, "
          "two private cubes, four addressing sizes; five value guards and one incomparability guard.")


def main() -> None:
    assert history(H) == EXPECTED
    assert all({h[j] for h in H} == {"0", "1"} for j in range(3))
    assert std(H) == 1
    cube = branch(H, 0, "0")
    assert cube == ("00", "01", "10", "11") and std(cube) == 2
    assert tuple(sorted({h[1:] for h in H})) == cube
    assert branch(H, 1, "0") == ("00", "01", "10")
    assert branch(H, 1, "1") == ("00", "01")
    assert std(branch(H, 1, "0")) == std(branch(H, 1, "1")) == 1
    # Keeping the conditioned coordinate as a constant gives the same values.
    assert std(tuple(h for h in H if h[0] == "0")) == 2
    assert all(std(tuple(h for h in H if h[1] == b)) == 1 for b in "01")

    # Published Table 7 lists ordinary TS, not the full STD iteration.
    table7 = ("000", "001", "010", "111")
    stages = history(table7)
    assert len(stages) == 3 and std(table7) == 1
    assert stages[-1] == {"000": {"*0*", "**0"}, "001": {"**1"},
                          "010": {"*1*"}, "111": {"1**"}}
    assert tuple(sorted(h[1:] for h in table7)) == cube
    assert std(branch(table7, 1, "0")) == std(branch(table7, 1, "1")) == 1

    # Degenerate and standard controls, all evaluated from ordinary teachers.
    for n in range(4):
        full = tuple("".join(h) for h in product("01", repeat=n))
        assert std(full) == n and len(history(full)) == 1
        assert std(("0" * n,)) == 0
    for n in range(1, 5):
        singletons = ("0" * n,) + tuple("0" * j + "1" + "0" * (n-j-1)
                                       for j in range(n))
        assert std(singletons) == 1

    data = Path(__file__).resolve().parents[1] / "data"
    record = json.loads((data / "parameters/093_subset_teaching_dimension.json").read_text())
    for flag in ("p_monotonic", "c_monotonic", "strict_c_monotonic", "tight_strict_c_monotonic"):
        assert record[flag] is False
        evidence = record["monotonicity_evidence"][flag]
        assert evidence["latex_proof_label"] == "prop:subset-teaching-conditioning"
    # Signed containment must not identify opposite labels or erase coordinates.
    assert not contained("0*", "1*") and not contained("0*", "*0")
    assert contained("0*", "00")
    verify_products_and_benchmarks()
    print("STD: complete four-stage five-concept table; conditioning 1 -> 2; "
          "equal branches 1/1 with whole value 1; projection and retained-constant controls.")
    print("Published Table 7 replayed through stabilization; four cubes, four singletons, "
          "four singleton-plus-empty controls; every step independently cross-checked.")
    print("Four metadata/proof-link guards passed. No census or asymptotic claim.")


if __name__ == "__main__":
    main()
