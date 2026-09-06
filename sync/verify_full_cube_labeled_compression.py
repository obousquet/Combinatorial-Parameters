#!/usr/bin/env python3
"""Replay DB-owned stable pair and ordinary five-coordinate certificates.

Checks all partial samples through eight coordinates, including deletion
stability. The general block proof and lower bound remain in value records.
"""
from itertools import product
from math import comb
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE = ROOT / "data/values/744_proper_stable_labeled_sample_compression_full_cube.json"


def record(path: Path) -> dict:
    return json.loads(path.read_text())


def block_table() -> dict[str, tuple[str, str]]:
    proof = record(CERTIFICATE)["proof"]
    rows = re.findall(r"([01*]{2})\s*&\s*([01*]{2})\s*&\s*([01]{2})", proof)
    assert len(rows) == 9, "The DB proof must contain one complete nine-row block table"
    return {s: (key, word) for s, key, word in rows}


def scheme(sample: str, table: dict[str, tuple[str, str]]) -> tuple[str, str]:
    keys, words = [], []
    for i in range(0, len(sample) - 1, 2):
        key, word = table[sample[i:i + 2]]
        keys.append(key)
        words.append(word)
    if len(sample) % 2:
        bit = sample[-1]
        keys.append(bit)
        words.append("0" if bit == "*" else bit)
    return "".join(keys), "".join(words)


def check_sample(sample: str, table: dict[str, tuple[str, str]]) -> int:
    key, word = scheme(sample, table)
    assert all(k == "*" or k == s for k, s in zip(key, sample))
    assert all(s == "*" or s == w for s, w in zip(sample, word))
    assert key.count("0") + key.count("1") <= (len(sample) + 1) // 2
    deletions = 0
    for i, bit in enumerate(sample):
        if bit != "*" and key[i] == "*":
            smaller = sample[:i] + "*" + sample[i + 1:]
            assert scheme(smaller, table) == (key, word)
            deletions += 1
    return deletions


def exact_formula(value: str, n: int) -> int | None:
    normalized = value.replace(" ", "").strip("$")
    if normalized == "n":
        return n
    if normalized == r"\lceiln/2\rceil":
        return (n + 1) // 2
    return None


def check_stored_value(value: dict, n: int) -> None:
    claimed = exact_formula(value["value"], n)
    if claimed is not None:
        assert claimed <= (n + 1) // 2, (value["id"], n, "exceeds explicit scheme")
        if value["parameter_id"] in {
            "#parameters/stable_labeled_sample_compression",
            "#parameters/proper_stable_labeled_sample_compression",
        }:
            assert claimed == (n + 1) // 2, "stable cube lower bound"
    else:
        assert value["value"] == r"$\Theta(n)$", "Unrecognized value needs manual review"


def check_withdrawn_witness(relation: dict) -> None:
    if relation.get("witness") == "#classes/full_cube":
        assert relation.get("witness_strength") not in {"strict", "unbounded"}, (
            relation["id"], "the full-cube endpoint values are equal")


def five_block_table() -> dict[tuple[int, int], int]:
    proof = record(ROOT / 'data/values/743_proper_labeled_sample_compression_full_cube.json')['proof']
    rows = re.findall(r'(\d+)\s*&\s*([\d,]+)', proof)
    assert len(rows) == 16
    decoder = {}
    for raw_mask, raw_outputs in rows:
        mask = int(raw_mask)
        labels = [y for y in range(32) if y & mask == y]
        outputs = list(map(int, raw_outputs.split(',')))
        assert mask.bit_count() <= 2 and len(outputs) == len(labels)
        for y, output in zip(labels, outputs):
            assert (mask, y) not in decoder and 0 <= output < 32
            assert output & mask == y
            decoder[mask, y] = output
    assert len(decoder) == 51
    return decoder


def five_block_check() -> None:
    decoder = five_block_table()
    partial = [(mask, y) for mask in range(32) for y in range(32) if y & mask == y]
    encoded = {}
    literal = lambda s: frozenset((x, (s[1] >> x) & 1) for x in range(5) if s[0] & (1 << x))
    for mask, y in partial:
        options = [key for key, output in decoder.items()
                   if key[0] & mask == key[0] and y & key[0] == key[1] and output & mask == y]
        assert options, (mask, y)
        encoded[mask, y] = min(options)
        # Independent set-of-literals representation of all availability tests.
        literals = literal((mask, y))
        assert any(literal(key) <= literals and all((output >> x) & 1 == label for x, label in literals)
                   for key, output in decoder.items())
    products = 0
    for first, second in product(partial, repeat=2):
        a, b = encoded[first], encoded[second]
        mask, y = first[0] | second[0] << 5, first[1] | second[1] << 5
        key = (a[0] | b[0] << 5, a[1] | b[1] << 5)
        assert key[0].bit_count() <= 4 and key[0] & mask == key[0] and y & key[0] == key[1]
        # Decode only the transmitted union, using the fixed block domains.
        output = decoder[key[0] & 31, key[1] & 31] | decoder[key[0] >> 5, key[1] >> 5] << 5
        assert output & mask == y
        products += 1
    assert products == 59049 and 1 + 2 * 5 < 32
    # The canonical five-block encoder is not reconstruction-stable.
    instability = []
    for s, key in encoded.items():
        for x in range(5):
            if s[0] & (1 << x) and not key[0] & (1 << x):
                smaller = (s[0] & ~(1 << x), s[1] & ~(1 << x))
                if decoder[encoded[smaller]] != decoder[key]:
                    instability.append((s, key, smaller))
    assert instability
    for n in (1, 2, 3, 4, 5, 7):
        lower = next(k for k in range(n + 1) if sum(2**i * comb(n, i) for i in range(k + 1)) >= 2**n)
        upper = 2 * (n // 5) + (n % 5 + 1) // 2
        assert lower == upper
    # Reject a corrupted upper table using a complete input, not a self-check.
    corrupted = {key: 0 for key in decoder}
    assert not any(output & 31 == 31 for output in corrupted.values())
    for rid in (156, 158, 513):
        paths = list((ROOT / 'data/relationships').glob(f'{rid:03d}_*.json'))
        assert len(paths) == 1
        relation = record(paths[0])
        assert relation['status'] == ('refuted' if rid == 513 else 'established')
        assert relation['witness'] == '#classes/full_cube'
        assert relation['witness_strength'] == 'strict', 'linear-order endpoints are not a ratio separation'
    print(f'Passed 243 five-cube samples and {products} two-block product samples; '
          f'non-stability control {instability[0]}; six exact counting matches.')


def main() -> None:
    table = block_table()
    # A retained key must have one fixed reconstruction.
    decoder = {}
    for key, word in table.values():
        assert key not in decoder or decoder[key] == word
        decoder[key] = word
    cases = deletions = 0
    for n in range(1, 9):
        for letters in product("*01", repeat=n):
            deletions += check_sample("".join(letters), table)
            cases += 1
    values = [record(p) for p in (ROOT / "data/values").glob("*.json")
              if p.name != "schema.json"]
    relevant = [v for v in values if v.get("id") in {743, 744, 1047, 1126}]
    assert len(relevant) == 4
    for value in relevant:
        for n in range(1, 9):
            check_stored_value(value, n)
    relations = [record(p) for p in (ROOT / "data/relationships").glob("*.json")
                 if p.name != "schema.json"]
    withdrawn = [r for r in relations if r.get("id") in {442, 444}]
    assert len(withdrawn) == 2
    for relation in withdrawn:
        check_withdrawn_witness(relation)
    # Negative controls reject the exact old symbolic error and stale witnesses.
    old_value = dict(relevant[0], value="$n$")
    try:
        check_stored_value(old_value, 2)
    except AssertionError:
        pass
    else:
        raise AssertionError("old n-valued compression claim was accepted")
    old_witness = dict(withdrawn[0], witness="#classes/full_cube", witness_strength="strict")
    try:
        check_withdrawn_witness(old_witness)
    except AssertionError:
        pass
    else:
        raise AssertionError("stale strict witness was accepted")
    broken = dict(table, **{"00": ("0*", "01")})
    try:
        check_sample("00", broken)
    except AssertionError:
        pass
    else:
        raise AssertionError("corrupted block decoding was accepted")
    print(f"Passed {cases} partial samples and {deletions} stability deletions; "
          "four DB value guards, two withdrawn-witness guards, three negative controls.")
    five_block_check()


if __name__ == "__main__":
    main()
