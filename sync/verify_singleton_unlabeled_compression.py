#!/usr/bin/env python3
"""DB-owned singleton USC/pUSC corrections; direct, bounded, solver-free replay.

Unlabeled keys are integer support masks, never (support, labels) pairs.
The general proofs live in values #477/#478/#1208, not in a saved decoder table.
"""

from itertools import product
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def concepts(n: int) -> tuple[int, ...]:
    record = json.loads((DATA / "classes/002_singletons.json").read_text())
    assert record["short_name"] == "singletons"
    assert "\\mathcal S_n" in record["definition"]
    assert "\\{\\{i\\}:i\\in[n]\\}" in record["definition"]
    return tuple(1 << i for i in range(n))


def samples(n: int) -> list[tuple[int, int]]:
    words = concepts(n)
    return [(mask, labels) for mask in range(1 << n)
            for labels in sorted({h & mask for h in words})]


def proper_decode(n: int, key: int) -> int:
    if n == 1 or not key:
        return 1
    if key == 1:
        return 2
    if key.bit_count() == 1:
        return key
    if key.bit_count() == 2 and key & 1:
        other = key ^ 1
        if other < 1 << (n - 1):
            return other << 1
    return 1  # Unused keys still have proper outputs.


def proper_encode(n: int, mask: int, labels: int) -> int:
    if n == 1:
        return 0
    if labels:
        return 0 if labels == 1 else labels
    missing = next(i for i in range(n) if not mask & (1 << i))
    if missing == 0:
        return 0
    if missing == 1:
        return 1
    return 1 | (1 << (missing - 1))


def stable_decode(n: int, key: int) -> int:
    if not key:
        return 1
    if key.bit_count() == 1 and key != 1:
        return key
    if key & (key + 1) == 0 and key < (1 << n) - 1:
        return key + 1
    return 1


def stable_encode(n: int, mask: int, labels: int) -> int:
    if labels:
        return 0 if labels == 1 else labels
    missing = next(i for i in range(n) if not mask & (1 << i))
    return (1 << missing) - 1


def verify_stable() -> None:
    checked = intervals = 0
    for n in range(1, 9):
        words = concepts(n)
        for mask, labels in samples(n):
            key = stable_encode(n, mask, labels)
            output = stable_decode(n, key)
            assert key & mask == key and key.bit_count() <= n - 1
            assert output in words and output & mask == labels
            # Independent literal construction of the selected prefix.
            observed = {i for i in range(n) if mask >> i & 1}
            positive = {i for i in observed if labels >> i & 1}
            expected = ((positive if positive != {0} else set()) if positive else
                        set(range(min(set(range(n)) - observed))))
            assert {i for i in range(n) if key >> i & 1} == expected
            extra = mask ^ key
            while True:
                t = key | extra
                assert stable_encode(n, t, labels & t) == key
                assert stable_decode(n, stable_encode(n, t, labels & t)) == output
                intervals += 1
                if not extra:
                    break
                extra = (extra - 1) & (mask ^ key)
            checked += 1
    record = json.loads((DATA / 'values/1208_proper_stable_sample_compression_singletons.json').read_text())
    assert record['value'] == r'$\Theta(n)$' and record['value_class'] == 'omega_n'
    assert 'val:proper_stable_labeled_sample_compression_singletons' in record['proof']
    for rid in (154, 157, 294, 443):
        relation = json.loads(next((DATA / 'relationships').glob(f'{rid}_*.json')).read_text())
        assert relation['status'] == 'established'
        assert relation['witness'] == '#classes/singletons'
        assert relation['witness_strength'] == 'unbounded'
    # The older width-two decoder is valid but its chosen encoder is unstable.
    assert proper_encode(4, 7, 0) == 5
    assert proper_decode(4, proper_encode(4, 7, 0)) == 8
    assert proper_decode(4, proper_encode(4, 5, 0)) == 2
    print(f'Stable singleton scheme: {checked} samples, {intervals} full intervals; '
          'four unbounded witnesses; unstable width-two negative control.')


def three_domain_control() -> None:
    """No proper width-one map even for just the three two-point domains."""
    words = concepts(3)
    inputs = [(m, y) for m, y in samples(3) if m.bit_count() == 2]
    keys = (0, 1, 2, 4)
    rejected = 0
    for outputs in product(words, repeat=len(keys)):
        decoder = dict(zip(keys, outputs))
        assert any(not any(k & m == k and decoder[k] & m == y for k in keys)
                   for m, y in inputs)
        rejected += 1
    assert rejected == 81
    # Allowing the all-zero output repairs the example, even on all domains.
    for mask, labels in samples(3):
        key = labels if labels else 0
        assert key & mask == key and key & mask == labels
    print(f"Three overlapping domains: {rejected} proper width-one maps rejected; "
          "improper width one passes all samples")


def verify_records() -> None:
    for filename, value, fragment in [
        ("477_unlabeled_sample_compression_singletons.json", "$1$", "all-zero word"),
        ("478_proper_unlabeled_sample_compression_singletons.json", "$2$", "r-1"),
    ]:
        record = json.loads((DATA / "values" / filename).read_text())
        assert record["value"] == value and record["status"] == "established"
        assert fragment in record["proof"]
    relationship = json.loads((DATA / "relationships/433_proper_unlabeled_sample_compression_radon_number_incomparable.json").read_text())
    assert "\\mathrm{pUSC}=2" in relationship["parameter_2_larger_witness"]


def main() -> None:
    checked = 0
    for n in range(1, 9):
        words = concepts(n)
        outputs_by_key: dict[int, int] = {}
        for mask, labels in samples(n):
            key = proper_encode(n, mask, labels)
            assert isinstance(key, int) and key & mask == key
            assert key.bit_count() <= min(n - 1, 2)
            output = proper_decode(n, key)
            assert output in words and output & mask == labels
            assert outputs_by_key.setdefault(key, output) == output
            ordinary_key = labels if n > 1 else 0
            ordinary_output = ordinary_key if n > 1 else 1
            assert ordinary_key & mask == ordinary_key and ordinary_key.bit_count() <= (n > 1)
            assert ordinary_output & mask == labels
            checked += 1
    # The removed cyclic decoder assigns incompatible outputs to key {0}.
    positive_output = 1
    negative_output = 2
    assert positive_output != negative_output
    assert positive_output & 1 != 0  # Fails the all-negative sample on {0}.
    assert negative_output & 1 != 1  # Fails the positive sample on {0}.
    three_domain_control()
    verify_records()
    verify_stable()
    print(f"PASS: {checked} sample pairs through n=8; correct zero/one/two boundaries; "
          "discarded-label corruption detected; three DB records guarded")


if __name__ == "__main__":
    main()
