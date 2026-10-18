"""Deterministic tests for the requirement register validator."""
import csv
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_requirements import validate  # noqa: E402


FIELDS = ["ID", "Domena", "Wymaganie", "Zrodla", "Priorytet", "Status", "Test_odbiorczy", "Dowod"]


def row(identifier, status="WYMAGANIE / NIEZWERYFIKOWANO WDROZENIA", proof=""):
    return {"ID": identifier, "Domena": "Test", "Wymaganie": "Działające wymaganie",
            "Zrodla": "U,D1", "Priorytet": "P0", "Status": status,
            "Test_odbiorczy": "Rzeczywisty test E2E", "Dowod": proof}


class RequirementsValidationTest(unittest.TestCase):
    def write(self, records):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        file = Path(temp.name) / "requirements.csv"
        with file.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)
        return file

    def test_accepts_two_valid_rows(self):
        result = validate(self.write([row("APP-001"), row("VIDEO-002")]), min_count=2)
        self.assertTrue(result["ok"], result["errors"])

    def test_detects_duplicate_ids(self):
        result = validate(self.write([row("APP-001"), row("APP-001")]), min_count=2)
        self.assertFalse(result["ok"])
        self.assertTrue(any("duplicate" in item for item in result["errors"]))

    def test_detects_missing_proof_on_done(self):
        result = validate(self.write([row("APP-001", status="DONE")]), min_count=1)
        self.assertFalse(result["ok"])
        self.assertTrue(any("requires evidence" in item for item in result["errors"]))

    def test_done_with_proof(self):
        result = validate(self.write([row("APP-001", status="DONE", proof="run#123")]), min_count=1)
        self.assertTrue(result["ok"], result["errors"])

    def test_rejects_missing_source(self):
        record = row("APP-001")
        record["Zrodla"] = "UNLISTED"
        result = validate(self.write([record]), min_count=1)
        self.assertFalse(result["ok"])

    def test_missing_file(self):
        result = validate(Path("/nonexistent/requirements.csv"))
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
