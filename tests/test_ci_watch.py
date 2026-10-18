import importlib.util
from pathlib import Path
import unittest

module_path = Path(__file__).resolve().parents[1] / "agents" / "github_engineer" / "ci_watch.py"
spec = importlib.util.spec_from_file_location("unthinkable_ci_watch", module_path)
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


def run(name, status, conclusion, created, branch="main"):
    return {
        "name": name, "status": status, "conclusion": conclusion,
        "created_at": created, "head_branch": branch, "html_url": "https://example.com",
    }


class WatchTests(unittest.TestCase):
    def test_latest_success_prevents_stale_alert(self):
        data = [
            run("Flutter Android smoke build", "completed", "failure", "2026-01-01"),
            run("Flutter Android smoke build", "completed", "success", "2026-01-02"),
        ]
        self.assertEqual(ci.newest_failures(data), [])

    def test_pending_newest_prevents_old_alert(self):
        data = [
            run("Source trace integrity", "completed", "failure", "2026-01-01"),
            run("Source trace integrity", "in_progress", None, "2026-01-02"),
        ]
        self.assertEqual(ci.newest_failures(data), [])

    def test_failures_deduplicated_by_issue_marker(self):
        broken = [run("Specification integrity", "completed", "failure", "2026-01-01")]
        previous = [{"body": ci.marker("Specification integrity")}]
        self.assertEqual(ci.missing_issues(ci.newest_failures(broken), previous), [])
        self.assertEqual(ci.missing_issues(ci.newest_failures(broken), []), broken)

    def test_other_branches_ignored(self):
        data = [run("Flutter Android smoke build", "completed", "failure",
                    "2026-01-03", branch="feature")]
        self.assertEqual(ci.newest_failures(data), [])


if __name__ == "__main__":
    unittest.main()
