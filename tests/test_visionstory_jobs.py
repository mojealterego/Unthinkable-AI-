"""SQLite paid-job ledger acceptance without real VisionStory API or charges."""
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryError, VisionStoryRest
from services.visionstory.jobs import JobLedger, configured_ledger

ROOT = "/api/cinema/visionstory"
AUTH = {"Authorization": "Bearer ledger-gateway"}
BODY = {
    "avatar_id": "owned_avatar1", "model_id": "model_a",
    "voice_id": "voice_a", "text": "Scena główna.",
    "client_request_id": "stablejob_001",
    "approved_for_paid_generation": True,
}

class Provider:
    def __init__(self):
        self.create_calls = 0
        self.fail_create = False

    def __call__(self, method, path, payload):
        if path == "/api/v1/billing/credits":
            return {"data": {"remaining": 100}}
        if path == "/api/v1/models":
            return {"data": {"models": [{"model_id": "model_a",
                "aspect_ratios": ["9:16"], "resolutions": ["720p"]}]}}
        if path == "/api/v1/avatars":
            return {"data": {"avatars": [{"avatar_id": "owned_avatar1"}]}}
        if path == "/api/v1/voices":
            return {"data": {"voices": [{"voice_id": "voice_a"}]}}
        if path == "/api/v1/video" and method == "POST":
            self.create_calls += 1
            if self.fail_create:
                raise VisionStoryError("Provider outcome is uncertain")
            return {"data": {"video_id": "video_abc123"}}
        raise AssertionError("Unexpected provider call")

class JobLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "visionstory-jobs.db")

    def test_persists_across_reopen_and_blocks_payload_mismatch(self):
        first = JobLedger(self.path)
        self.assertIsNone(first.begin("avatar_video", "idempotent_1001", {"text": "Hello"}))
        first.finish("avatar_video", "idempotent_1001", "video_123")
        reopened = JobLedger(self.path)
        self.assertEqual(reopened.begin("avatar_video", "idempotent_1001",
                                        {"text": "Hello"}), "video_123")
        with self.assertRaises(VisionStoryError):
            reopened.begin("avatar_video", "idempotent_1001", {"text": "Changed"})
        self.assertNotIn("Hello", repr(reopened.list_jobs()))
        self.assertEqual(reopened.list_jobs()[0]["state"], "submitted")

    def test_timeout_is_ambiguous_and_never_replayed(self):
        one = JobLedger(self.path)
        self.assertIsNone(one.begin("ai_video", "idempotent_2002", {"prompt": "Cinema"}))
        one.mark_ambiguous("ai_video", "idempotent_2002")
        reopened = JobLedger(self.path)
        with self.assertRaises(VisionStoryError):
            reopened.begin("ai_video", "idempotent_2002", {"prompt": "Cinema"})
        self.assertEqual(reopened.list_jobs()[0]["state"], "ambiguous")

    def test_two_concurrent_writers_cannot_submit_twice(self):
        ledger = JobLedger(self.path)
        def execute(_):
            try:
                ledger.begin("ai_video", "parallel_3003", {"model": "video"})
                return "RESERVED"
            except VisionStoryError:
                return "CONFLICT"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(execute, (0, 1)))
        self.assertEqual(sorted(results), ["CONFLICT", "RESERVED"])

    def test_production_can_require_durable_storage(self):
        with patch.dict(os.environ, {
            "VISIONSTORY_REQUIRE_DURABLE_JOBS": "1",
            "VISIONSTORY_JOB_DB_PATH": "",
        }):
            with self.assertRaises(VisionStoryError):
                configured_ledger()

    def test_gateway_reuses_existing_provider_video_without_second_charge(self):
        provider = Provider()
        with patch.dict(os.environ, {
            "VISIONSTORY_JOB_DB_PATH": self.path,
            "VISIONSTORY_REQUIRE_DURABLE_JOBS": "1",
        }), patch("services.ai_studio.omni_orchestrator.API_KEY", "ledger-gateway"), \
             patch("services.visionstory.router.configured_client",
                   return_value=VisionStoryRest("provider-fixture", transport=provider)):
            http = TestClient(app)
            first = http.post(ROOT + "/talking-video", json=BODY, headers=AUTH)
            self.assertEqual(first.status_code, 200, first.text)
            second = http.post(ROOT + "/talking-video", json=BODY, headers=AUTH)
            self.assertEqual(second.status_code, 200, second.text)
            self.assertTrue(second.json()["reused_existing_job"])
            self.assertEqual(provider.create_calls, 1)
            jobs = http.get(ROOT + "/jobs", headers=AUTH)
            self.assertEqual(jobs.status_code, 200, jobs.text)
            self.assertEqual(jobs.json()["jobs"][0]["video_id"], "video_abc123")
            self.assertNotIn(BODY["text"], jobs.text)

    def test_gateway_keeps_ambiguous_failed_submission_fenced(self):
        provider = Provider()
        provider.fail_create = True
        with patch.dict(os.environ, {
            "VISIONSTORY_JOB_DB_PATH": self.path,
            "VISIONSTORY_REQUIRE_DURABLE_JOBS": "1",
        }), patch("services.ai_studio.omni_orchestrator.API_KEY", "ledger-gateway"), \
             patch("services.visionstory.router.configured_client",
                   return_value=VisionStoryRest("provider-fixture", transport=provider)):
            http = TestClient(app)
            failed = http.post(ROOT + "/talking-video", json=BODY, headers=AUTH)
            self.assertEqual(failed.status_code, 502, failed.text)
            retried = http.post(ROOT + "/talking-video", json=BODY, headers=AUTH)
            self.assertEqual(retried.status_code, 409, retried.text)
            self.assertEqual(provider.create_calls, 1)
            self.assertEqual(JobLedger(self.path).list_jobs()[0]["state"], "ambiguous")

if __name__ == "__main__":
    unittest.main()
