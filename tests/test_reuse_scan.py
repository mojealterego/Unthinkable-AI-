"""Unit tests: scan is read-only and never interprets a name as safe code."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reuse_scan import classify_paths, source_inventory, inspect_repo

class ReuseAuditTests(unittest.TestCase):
    def test_source_inventory_has_unique_scoped_names(self):
        repos = source_inventory()
        self.assertGreaterEqual(len(repos), 600)
        self.assertIn("mojealterego/ODYN-Diffusion-Android", repos)

    def test_scan_detects_sources_tests_workflow_and_license(self):
        result = classify_paths([
            "lib/main.dart", "test/widget_test.dart", ".github/workflows/flutter.yml", "LICENSE",
        ], truncated=False)
        self.assertEqual(result["code_files_seen"], 2)
        self.assertTrue(result["tests_seen"])
        self.assertTrue(result["ci_seen"])
        self.assertEqual(result["license_files_seen"], 1)
        self.assertFalse(result["tree_truncated"])

    def test_truncated_tree_is_not_misrepresented_as_complete(self):
        self.assertTrue(classify_paths([], truncated=True)["tree_truncated"])

    def test_malformed_name_rejected_before_api_access(self):
        with self.assertRaises(ValueError):
            inspect_repo("evil.example/a", "")

if __name__ == "__main__":
    unittest.main()
