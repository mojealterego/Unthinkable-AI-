#!/usr/bin/env python3
"""Fail CI when a source requirement disappears; does not imply that features are implemented."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("D1", "D2", "D3", "D4", "D5", "D6")

def records(relative, fields):
    path = ROOT / relative
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="|"))
    assert rows and tuple(rows[0]) == fields, f"{path}: invalid header"
    assert all(all(row[k].strip() for k in fields) for row in rows), f"{path}: empty field"
    return rows

def main():
    directives = records("requirements/user-directives.psv", ("id", "domain", "requirement"))
    candidates = records("requirements/source-candidates.psv",
                         ("id", "document", "location", "source_named_concept"))
    assert len(directives) == 146, "User directive count changed: inspect original message"
    assert len(candidates) == 53, "Source concept count changed: inspect page evidence"
    assert [x["id"] for x in directives] == [f"U-{n:03d}" for n in range(1, 147)], "User ID gap/duplicate"
    assert [x["id"] for x in candidates] == [f"X-{n:03d}" for n in range(1, 54)], "Candidate ID gap/duplicate"
    assert all(row["document"] in SOURCES for row in candidates), "Unknown source document"
    reg = records_csv("requirements/requirements.csv")
    domains = {x["ID"].split("-")[0] for x in reg}
    assert all(x["domain"] in domains for x in directives), "User requirement domain not in master register"
    print(f"Sources verified: {len(directives)} user directives, {len(candidates)} review candidates; implementation NOT certified")

def records_csv(relative):
    with (ROOT / relative).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

if __name__ == "__main__":
    main()
