#!/usr/bin/env python3
"""Read-only CI triage plus idempotent issue creation. No LLM, no code mutation."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

TRACKED = frozenset({
    "Flutter Android smoke build",
    "Specification integrity",
    "Source trace integrity",
})
MARKER_PREFIX = "<!-- unthinkable-ci-watch: "
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def newest_failures(runs: list[dict]) -> list[dict]:
    """Only evaluate the newest main-branch run per tracked workflow."""
    newest: dict[str, dict] = {}
    for run in sorted(runs, key=lambda x: x.get("created_at", ""), reverse=True):
        name = run.get("name")
        if name in TRACKED and run.get("head_branch") == "main" and name not in newest:
            newest[name] = run
    return [r for r in newest.values() if r.get("status") == "completed"
            and r.get("conclusion") == "failure"]


def marker(name: str) -> str:
    return f"{MARKER_PREFIX}{name} -->"


def missing_issues(failures: list[dict], existing: list[dict]) -> list[dict]:
    bodies = [issue.get("body") or "" for issue in existing if "pull_request" not in issue]
    return [run for run in failures if not any(marker(run["name"]) in body for body in bodies)]


def request(repo: str, token: str, method: str, endpoint: str, data=None):
    body = None if data is None else json.dumps(data).encode("utf-8")
    url = f"https://api.github.com/repos/{repo}/{endpoint}"
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Unthinkable-CI-Watch/1.0",
        **({"Content-Type": "application/json"} if body is not None else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not REPO_PATTERN.fullmatch(repo) or not token:
        print("Missing expected GITHUB_REPOSITORY / GITHUB_TOKEN context", file=sys.stderr)
        return 2

    runs = request(repo, token, "GET", "actions/runs?branch=main&per_page=100").get("workflow_runs", [])
    problems = newest_failures(runs)
    if not problems:
        print("Latest CI results healthy or pending; no issue created")
        return 0

    existing = []
    for page in range(1, 6):
        segment = request(repo, token, "GET", f"issues?state=open&per_page=100&page={page}")
        existing.extend(segment)
        if len(segment) < 100:
            break

    for run in missing_issues(problems, existing):
        name = run["name"]
        link = run.get("html_url", "")
        issue = {
            "title": f"CI regression: {name}",
            "body": (
                f"{marker(name)}\n"
                f"Automated health check found a failing workflow on `main`.\n\n"
                f"- Workflow: {name}\n- Run: {link}\n"
                f"- Commit: `{run.get('head_sha', 'unknown')}`\n\n"
                "Human action required: inspect job logs, fix the regression, "
                "run full tests, and close only after independent verification.\n"
                "This workflow does **not** alter source files, grants or model permissions."
            ),
        }
        result = request(repo, token, "POST", "issues", issue)
        print(f"Created CI issue #{result['number']}: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
