#!/usr/bin/env python3
"""Report provenance-packet coverage for citations used by the database.

Literature packets live in the companion survey checkout.  A packet does not
prove every fact citing a work; it records where the primary source was
checked and its usable scope, so that subsequent completion passes can target
the most-used unsupported sources first.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


CITATION_PATTERN = re.compile(r"\\cite\{([^}]+)\}")
BIB_KEY_PATTERN = re.compile(r"^@\w+\{([^,]+),", re.MULTILINE)
REQUIRED_PACKET_FILES = ("metadata.json", "source-map.md", "key-results.md")


def cited_keys(data_dir: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in data_dir.rglob("*"):
        if not path.is_file() or path.suffix not in {".json", ".tex"}:
            continue
        if path.name == "schema.json":
            continue
        for group in CITATION_PATTERN.findall(path.read_text()):
            counts.update(key.strip() for key in group.split(",") if key.strip())
    return counts


def bibliography_keys(data_dir: Path) -> set[str]:
    bibliography = data_dir / "latex" / "references.bib"
    return set(BIB_KEY_PATTERN.findall(bibliography.read_text()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--latex-dir",
        type=Path,
        default=Path("~/latex/CombinatorialParameters").expanduser(),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Print at most this many missing packets (zero means all).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return nonzero if a cited bibliography entry lacks a complete packet.",
    )
    args = parser.parse_args()

    counts = cited_keys(args.data_dir)
    bib_keys = bibliography_keys(args.data_dir)
    packet_root = args.latex_dir / "literature"
    missing_bibliography = sorted(set(counts) - bib_keys)
    incomplete: list[tuple[str, int, list[str]]] = []
    for key, count in counts.items():
        packet = packet_root / key
        absent = [name for name in REQUIRED_PACKET_FILES if not (packet / name).is_file()]
        if absent:
            incomplete.append((key, count, absent))
    incomplete.sort(key=lambda item: (-item[1], item[0]))

    print(f"Cited bibliography keys: {len(counts)}")
    print(f"Complete literature packets: {len(counts) - len(incomplete)}")
    if missing_bibliography:
        print(f"Citation keys missing from bibliography: {len(missing_bibliography)}")
        for key in missing_bibliography:
            print(f"  {key}")
    else:
        print("Citation keys missing from bibliography: 0")

    print(f"Incomplete literature packets: {len(incomplete)}")
    shown = incomplete if not args.limit else incomplete[: args.limit]
    for key, count, absent in shown:
        print(f"  {key}: {count} citations; missing {', '.join(absent)}")
    if args.limit and len(incomplete) > args.limit:
        print(f"  ... {len(incomplete) - args.limit} more")

    return 1 if args.check and (missing_bibliography or incomplete) else 0


if __name__ == "__main__":
    raise SystemExit(main())
