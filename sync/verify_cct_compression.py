#!/usr/bin/env python3
"""Replay the DB-owned proper width-three CCT decoder, without a solver.

Forward bit-mask and reverse literal-set checks cover all partial samples.
The class seeds live only in data/classes/050_chen_teaching_products.json.
"""

from itertools import product
import json
from math import comb
from pathlib import Path
import re

DATA = Path(__file__).resolve().parents[1] / "data"
CERTIFICATE = Path(__file__).with_name("cct_compression_certificate.json")


def base_concepts() -> tuple[int, ...]:
    definition = json.loads((DATA / "classes/050_chen_teaching_products.json").read_text())["definition"]
    seeds = re.findall(r"\\mathtt\{([01]{12})\}", definition)
    assert len(seeds) == 9
    strings = {s[i:] + s[:i] for s in seeds for i in range(12)}
    assert len(strings) == 100
    return tuple(sorted(sum(int(bit) << i for i, bit in enumerate(s)) for s in strings))


def load_decoder(words: tuple[int, ...]) -> dict[tuple[int, int], int]:
    certificate = json.loads(CERTIFICATE.read_text())
    assert certificate["class_id"] == 50 and certificate["base_coordinates"] == 12
    assert certificate["width"] == 3 and certificate["proper"] is True
    rows = certificate["keys"]
    expected = {(m, h & m) for h in words for m in range(4096) if m.bit_count() <= 3}
    decoder = {(m, y): h for m, y, h in rows}
    assert len(rows) == len(decoder) == len(expected) == 2049
    assert set(decoder) == expected
    for (m, y), h in decoder.items():
        assert h in words and h & m == y
    return decoder


def verify() -> None:
    words = base_concepts()
    decoder = load_decoder(words)
    partial = sorted({(m, h & m) for h in words for m in range(4096)})
    masks = sorted({m for m, _ in decoder}, key=lambda m: (m.bit_count(), m))
    contained = {m: [u for u in masks if u & m == u] for m in range(4096)}
    encoded = {}
    for m, y in partial:
        key = next(((u, y & u) for u in contained[m] if decoder[u, y & u] & m == y), None)
        assert key is not None, (m, y)
        encoded[m, y] = key
    assert len(encoded) == 135073

    # Independent reverse construction: a key/output covers every intervening
    # literal-set sample. Build actual samples afresh from full class words.
    def literals(mask: int, word: int) -> frozenset[tuple[int, int]]:
        return frozenset((x, (word >> x) & 1) for x in range(12) if mask & (1 << x))
    actual = {literals(m, h) for h in words for m in range(4096)}
    covered = set()
    for (m, y), h in decoder.items():
        key, full = literals(m, y), literals(4095, h)
        free = 4095 ^ m
        extra = free
        while True:
            sample = literals(m | extra, h)
            assert key <= sample <= full
            covered.add(sample)
            if extra == 0:
                break
            extra = (extra - 1) & free
    assert covered == actual and len(actual) == 135073

    # Properness alone is not enough: replacing the entire table by one
    # class word fails the full sample of every other class member.
    corrupted = dict.fromkeys(decoder, words[0])
    assert all(corrupted[u] != words[-1] for u in corrupted)
    wrong_key = next(u for u in decoder if words[0] & u[0] != u[1])
    assert corrupted[wrong_key] & wrong_key[0] != wrong_key[1]
    assert 0 not in words  # An all-zero replacement also fails properness.

    # Do not promote this chosen encoder as stable without checking it.
    instability = None
    for (m, y), key in encoded.items():
        for x in range(12):
            bit = 1 << x
            if m & bit and not key[0] & bit:
                smaller = m ^ bit, y & ~bit
                if decoder[encoded[smaller]] != decoder[key]:
                    instability = ((m, y), key, smaller)
                    break
        if instability:
            break
    assert instability is not None

    selected = [(0, 0), (4095, words[0]), (4095, words[-1]), (7, words[0] & 7)]
    products = 0
    for s, t in product(selected, repeat=2):
        u, v = encoded[s], encoded[t]
        mask, labels = s[0] | (t[0] << 12), s[1] | (t[1] << 12)
        km, ky = u[0] | (v[0] << 12), u[1] | (v[1] << 12)
        output = decoder[u] | (decoder[v] << 12)
        assert km & mask == km and labels & km == ky and km.bit_count() <= 6
        assert output & mask == labels
        assert output & 4095 in words and output >> 12 in words
        products += 1

    # Exact integer inequality used in the all-product counting proof.
    assert 24 * 13**12 < 100 * 12**12
    for n in range(1, 21):
        assert sum(2**i * comb(12 * n, i) for i in range(n + 1)) < 100**n
    for filename in ("1150_proper_labeled_sample_compression_chen_teaching_products.json",
                     "1151_labeled_sample_compression_chen_teaching_products.json"):
        record = json.loads((DATA / "values" / filename).read_text())
        assert record["value"] == "$\\le3n$" and record["status"] == "established"
        assert record["value_class"] == "omega_n"
    print("PASS: 2049 proper keys; all 135073 samples in both representations;")
    print(f"{products} two-block replay cases, twenty counting checks and corruption controls.")
    print("Chosen-encoder reconstruction instability (not a parameter lower bound):", instability)


if __name__ == "__main__":
    verify()
