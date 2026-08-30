#!/usr/bin/env python3
"""Normalize and deduplicate structured weekly glossary entries."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata


PAGE_PATTERN = re.compile(r"^W\d{2,3}-P\d{3,4}$", re.IGNORECASE)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value or "")).strip()


def normalized_key(term: str) -> str:
    return clean(term).casefold()


def read_entries(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ValueError("input must be a list or an object containing an entries list")
    return entries


def dedupe(entries: list[dict]) -> dict:
    unique: list[dict] = []
    positions: dict[str, int] = {}
    duplicates: list[dict] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"entry {index + 1} must be an object")
        term = clean(str(entry.get("term", "")))
        zh = clean(str(entry.get("zh", "")))
        page = clean(str(entry.get("page", ""))).upper()
        if not term or not zh:
            raise ValueError(f"entry {index + 1} requires non-empty term and zh")
        if not PAGE_PATTERN.fullmatch(page):
            raise ValueError(f"entry {index + 1} has invalid page label: {page}")
        key = normalized_key(term)
        if key in positions:
            kept = unique[positions[key]]
            duplicates.append({"term": term, "keptPage": kept["page"], "discardedPage": page})
            continue
        positions[key] = len(unique)
        unique.append({"term": term, "zh": zh, "page": page})
    return {"count": len(unique), "entries": unique, "duplicates": duplicates}


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = dedupe(read_entries(args.input.expanduser().resolve()))
        if args.output:
            write_json_atomic(args.output.expanduser().resolve(), result)
        else:
            json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
    except Exception as exc:
        print(f"glossary_dedupe: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
