#!/usr/bin/env python3
"""Read-only triage of the 633 discovered GitHub repositories.

Never import files or grant runtime privileges based on name or a repository badge.
Results are CI artifacts; human review and licensing gates remain mandatory.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
EXT = (".py", ".rs", ".dart", ".kt", ".kts", ".cpp", ".c", ".cs", ".ts", ".js")


def source_inventory() -> list[str]:
    with (ROOT / "docs" / "REUSE_INVENTORY.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    names = [row["repository"] for row in rows]
    if len(names) != len(set(names)) or any(not NAME.fullmatch(n) for n in names):
        raise ValueError("Invalid or duplicate repository names in inventory")
    return names


def classify_paths(paths: list[str], *, truncated: bool) -> dict[str, object]:
    """Evidence from the actual returned tree, not from project branding."""
    return {
        "tree_truncated": truncated,
        "code_files_seen": sum(p.lower().endswith(EXT) for p in paths),
        "tests_seen": any(
            "/test/" in ("/" + p.lower()) or
            "/tests/" in ("/" + p.lower()) or
            p.lower().startswith("test_") for p in paths
        ),
        "ci_seen": any(p.startswith(".github/workflows/") for p in paths),
        "license_files_seen": sum(
            p.split("/")[-1].upper().startswith(("LICENSE", "LICENCE", "COPYING"))
            for p in paths
        ),
    }


def get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Unthinkable-Reuse-Audit/1.0",
        **({"Authorization": "Bearer " + token} if token else {}),
    })
    with urllib.request.urlopen(req, timeout=18) as response:
        value = json.load(response)
    if not isinstance(value, dict):
        raise ValueError("Unexpected GitHub API JSON")
    return value


def inspect_repo(repo: str, token: str) -> dict[str, object]:
    if not NAME.fullmatch(repo):
        raise ValueError("Unsafe repo identifier")
    prefix = "https://api.github.com/repos/" + repo
    item: dict[str, object] = {
        "repository": repo,
        "metadata_checked": False,
        "license_spdx": "UNVERIFIED",
        "code_files_seen": 0,
        "tests_seen": False,
        "ci_seen": False,
        "license_files_seen": 0,
        "tree_truncated": False,
        "fork": False,
        "status": "ERROR",
        "error_type": "",
    }
    try:
        meta = get_json(prefix, token)
        item["metadata_checked"] = True
        item["fork"] = meta.get("fork") is True
        branch = meta.get("default_branch")
        if not isinstance(branch, str) or not branch:
            raise ValueError("Repository has no known default branch")
        declared = meta.get("license")
        if isinstance(declared, dict) and declared.get("spdx_id"):
            item["license_spdx"] = declared["spdx_id"]
        tree = get_json(prefix + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1", token)
        paths = [f.get("path", "") for f in tree.get("tree", []) if f.get("type") == "blob"]
        item.update(classify_paths(paths, truncated=tree.get("truncated") is True))
        item["status"] = "TRIAGED"
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TimeoutError) as exc:
        item["error_type"] = type(exc).__name__
    return item


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=-1, help="-1 rotates daily, otherwise explicit offset")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--out", type=Path, default=Path("reuse-scan.csv"))
    args = parser.parse_args()
    if not (1 <= args.limit <= 50):
        raise SystemExit("Limit must be 1..50")
    names = source_inventory()
    offset = args.offset
    if offset == -1:
        offset = ((dt.datetime.now(dt.timezone.utc).timetuple().tm_yday - 1) * args.limit) % len(names)
    if offset < 0 or offset >= len(names):
        raise SystemExit("Offset must be within inventory")
    selected = names[offset: offset + args.limit]
    token = os.environ.get("GITHUB_TOKEN", "")
    results = [inspect_repo(name, token) for name in selected]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"Audited metadata/tree for {len(results)} repos starting at {offset}; "
          f"{sum(x['status'] == 'TRIAGED' for x in results)} triaged, "
          "no code imported or automatically certified")


if __name__ == "__main__":
    main()
