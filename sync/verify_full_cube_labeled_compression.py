#!/usr/bin/env python3
"""Replay the DB-owned stable two-coordinate certificate and symbolic guards.

Checks all partial samples through eight coordinates, including deletion
stability. The general block proof and lower bound remain in value records.
"""
from itertools import product
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


if __name__ == "__main__":
    main()
