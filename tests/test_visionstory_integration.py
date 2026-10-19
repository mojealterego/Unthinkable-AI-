"""Unit/integration verification without live VisionStory charges or keys."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryRest

GATEWAY_KEY = "unit-gateway"
PROVIDER_KEY = "unit-provider"
HEADERS = {"Authorization": "Bearer " + GATEWAY_KEY}
PAYLOAD = {
    "avatar_id": "avatar_one", "voice_id": "voice_one",
    "model_id": "vs_character_v4",
    "text": "Witaj w Unthinkable AI.",
    "client_request_id": "stable-scene-001",
    "approved_for_paid_generation": True,
}


class Provider:
    def __init__(self, balance=50, model=True, avatar=True, voice=True):
        self.balance, self.model, self.avatar, self.voice = balance, model, avatar, voice
        self.calls = []
        self.sent = None

    def __call__(self, method, path, payload):
        self.calls.append((method, path))
        if path == "/api/v1/billing/credits":
            return {"data": {"remaining": self.balance}}
        if path == "/api/v1/models":
            entries = [{"model_id": "vs_character_v4",
                "aspect_ratios": ["9:16"], "resolutions": ["720p"]}] if self.model else []
            return {"data": {"models": entries}}
        if path == "/api/v1/avatars":
            return {"data": {"avatars": [{"avatar_id": "avatar_one"}] if self.avatar else []}}
        if path == "/api/v1/voices":
            return {"data": {"public_voices": [{"voice_id": "voice_one"}] if self.voice else []}}
        if path == "/api/v1/video" and method == "POST":
            self.sent = payload
            return {"data": {"video_id": "video_abc123"}}
        if path == "/api/v1/video?video_id=video_abc123":
            return {"data": {"status": "created", "video_id": "video_abc123",
                "video_url": "https://media.example/video.mp4", "cost_credit": 4}}
        raise AssertionError("Unexpected provider API call")


class VisionStoryTests(unittest.TestCase):
    def setUp(self):
        self.http = TestClient(app)
        p = patch("services.ai_studio.omni_orchestrator.API_KEY", GATEWAY_KEY)
        p.start()
        self.addCleanup(p.stop)

    def inject(self, provider):
        p = patch("services.visionstory.router.configured_client",
            return_value=VisionStoryRest(PROVIDER_KEY, transport=provider))
        p.start()
        self.addCleanup(p.stop)

    def test_gateway_auth_rejects_before_reaching_provider(self):
        fake = Provider()
        self.inject(fake)
        self.assertEqual(self.http.get("/api/cinema/visionstory/models").status_code, 401)
        self.assertEqual(self.http.post("/api/cinema/visionstory/talking-video",
            json=PAYLOAD).status_code, 401)
        self.assertEqual(fake.calls, [])

    def test_provider_key_missing_stops_at_preflight(self):
        with patch.dict(os.environ, {"VISIONSTORY_API_KEY": ""}):
            result = self.http.get("/api/cinema/visionstory/credits", headers=HEADERS)
        self.assertEqual(result.status_code, 503)

    def test_catalogs_and_credit_balance_from_provider(self):
        fake = Provider()
        self.inject(fake)
        for endpoint in ("credits", "models", "avatars", "voices"):
            response = self.http.get("/api/cinema/visionstory/" + endpoint, headers=HEADERS)
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([path for _, path in fake.calls], [
            "/api/v1/billing/credits", "/api/v1/models", "/api/v1/avatars",
            "/api/v1/voices",
        ])

    def test_cost_approval_and_idempotent_remote_submit(self):
        fake = Provider()
        self.inject(fake)
        denied = self.http.post("/api/cinema/visionstory/talking-video",
            json=PAYLOAD | {"approved_for_paid_generation": False}, headers=HEADERS)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(fake.calls, [])
        result = self.http.post("/api/cinema/visionstory/talking-video",
            json=PAYLOAD, headers=HEADERS)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["video_id"], "video_abc123")
        self.assertFalse(result.json()["locally_generated"])
        self.assertEqual(fake.sent["client_request_id"], "stable-scene-001")
        self.assertEqual(fake.sent["text_script"]["voice_id"], "voice_one")
        self.assertNotIn("audio_script", fake.sent)
        self.assertNotIn(PROVIDER_KEY, result.text)

    def test_credit_failure_or_missing_live_resource_blocks_paid_call(self):
        for opts, status in (
            ({"balance": 0}, 402),
            ({"model": False}, 422),
            ({"avatar": False}, 422),
            ({"voice": False}, 422),
        ):
            with self.subTest(opts=opts):
                fake = Provider(**opts)
                with patch("services.visionstory.router.configured_client",
                           return_value=VisionStoryRest(PROVIDER_KEY, transport=fake)):
                    result = self.http.post("/api/cinema/visionstory/talking-video",
                        json=PAYLOAD, headers=HEADERS)
                self.assertEqual(result.status_code, status, result.text)
                self.assertFalse(any(method == "POST" for method, _ in fake.calls))

    def test_input_validation_before_provider(self):
        fake = Provider()
        self.inject(fake)
        for change in (
            {"client_request_id": "bad"},
            {"avatar_id": "../local"},
            {"resolution": "4k"},
            {"text": ""},
        ):
            with self.subTest(change=change):
                result = self.http.post("/api/cinema/visionstory/talking-video",
                    json=PAYLOAD | change, headers=HEADERS)
                self.assertEqual(result.status_code, 422)
        self.assertEqual(fake.calls, [])

    def test_status_requires_auth_returns_job_and_retention(self):
        fake = Provider()
        self.inject(fake)
        uri = "/api/cinema/visionstory/talking-video/video_abc123"
        self.assertEqual(self.http.get(uri).status_code, 401)
        result = self.http.get(uri, headers=HEADERS)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["status"], "created")
        self.assertEqual(result.json()["download_retention_days"], 7)
        self.assertFalse(result.json()["local_file_saved"])

    def test_deletion_not_available_and_url_attack_cannot_call_provider(self):
        fake = Provider()
        self.inject(fake)
        self.assertEqual(self.http.delete(
            "/api/cinema/visionstory/talking-video/video_abc123",
            headers=HEADERS).status_code, 405)
        client = VisionStoryRest(PROVIDER_KEY, transport=fake)
        with self.assertRaises(ValueError):
            client.request("DELETE", "/api/v1/video")
        self.assertFalse(self.http.get(
            "/api/cinema/visionstory/capabilities", headers=HEADERS
        ).json()["delete_supported"])


if __name__ == "__main__":
    unittest.main()
