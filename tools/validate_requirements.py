#!/usr/bin/env python3
"""Validate the Unthinkable AI source-derived requirement register.

Stdlib-only and suitable for GitHub Actions or Termux.
This checks registration integrity, not feature completion.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ("ID", "Domena", "Wymaganie", "Zrodla", "Priorytet", "Status", "Test_odbiorczy")
SOURCE_CODES = frozenset({"U", "D1", "D2", "D3", "D4", "D5", "D6"})
ID_PATTERN = re.compile(r"^[A-Z]+-[0-9]{3}$")
DONE_MARKERS = {"DONE", "ACCEPTED", "DEPLOYED", "ZAKONCZONE", "GOTOWE"}


def validate(path: Path, min_count: int = 339) -> dict:
    errors: list[str] = []
    if not path.is_file():
        return {"ok": False, "total": 0, "domains": {}, "errors": [f"Missing file: {path}"]}

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = set(reader.fieldnames or ())
        missing = set(REQUIRED) - headers
        if missing:
            return {"ok": False, "total": 0, "domains": {}, "errors": [f"Missing columns: {sorted(missing)}"]}
        rows = list(reader)

    counts: Counter[str] = Counter()
    seen: set[str] = set()
    for line, row in enumerate(rows, start=2):
        identifier = (row.get("ID") or "").strip()
        if not ID_PATTERN.fullmatch(identifier):
            errors.append(f"Line {line}: malformed ID {identifier!r}")
        if identifier in seen:
            errors.append(f"Line {line}: duplicate ID {identifier}")
        seen.add(identifier)

        for key in REQUIRED:
            if not (row.get(key) or "").strip():
                errors.append(f"Line {line} {identifier}: empty {key}")

        sources = {part.strip() for part in (row.get("Zrodla") or "").split(",") if part.strip()}
        unknown = sources - SOURCE_CODES
        if unknown:
            errors.append(f"Line {line} {identifier}: unknown sources {sorted(unknown)}")
        if not sources:
            errors.append(f"Line {line} {identifier}: no source")

        prefix = identifier.split("-")[0]
        counts[prefix] += 1
        status = (row.get("Status") or "").strip().upper()
        if status in DONE_MARKERS:
            proof = (row.get("Dowod") or row.get("Evidence") or "").strip()
            if not proof:
                errors.append(f"Line {line} {identifier}: status {status} requires evidence")

    if len(rows) < min_count:
        errors.append(f"Requirements coverage dropped: {len(rows)} < {min_count}")

    return {"ok": not errors, "total": len(rows), "domains": dict(sorted(counts.items())),
            "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=Path("requirements/requirements.csv"))
    parser.add_argument("--min-count", type=int, default=339)
    parser.add_argument("--json", action="store_true", help="Machine-readable summary")
    args = parser.parse_args()
    result = validate(args.file, args.min_count)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Requirements: {result['total']}; domains: {len(result['domains'])}; valid: {result['ok']}")
        for error in result["errors"]:
            print("ERROR:", error, file=sys.stderr)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
