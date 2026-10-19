"""New VisionStory API contracts from the owner's batch VS-004..006.

Provider is mocked: no API key, no paid media processing, no remote calls.
"""
import base64
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.gateway.app import app
from services.visionstory.client import VisionStoryRest

AUTH = {"Authorization": "Bearer test-gateway-key"}
URL = "/api/cinema/visionstory"


class Provider:
    def __init__(self, *, remaining=30):
        self.calls = []
        self.remaining = remaining
        self.last_payload = None

    def __call__(self, method, path, payload):
        self.calls.append((method, path))
        if path == "/api/v1/billing/credits":
            return {"data": {"remaining": self.remaining}}
        if path.startswith("/api/v1/avatars"):
            return {"data": {"avatars": [{"avatar_id": "avatar_a"}], "next_cursor": 0}}
        if method == "POST" and path == "/api/v1/media/understand":
            self.last_payload = payload
            return {"data": {
                "output": {"category": "interview", "confidence": 0.9},
                "usage": {"input_tokens": 33, "output_tokens": 17},
                "cost_credit": 1,
            }}
        raise AssertionError("Unexpected provider call: " + method + " " + path)


class VisionStoryNewFunctionsTests(unittest.TestCase):
    def setUp(self):
        self.provider = Provider()
        self.http = TestClient(app)
        gateway = patch("services.ai_studio.omni_orchestrator.API_KEY", "test-gateway-key")
        client = patch("services.visionstory.router.configured_client",
            return_value=VisionStoryRest("mock-provider-key", transport=self.provider))
        gateway.start()
        client.start()
        self.addCleanup(gateway.stop)
        self.addCleanup(client.stop)

    def payload(self, **overrides):
        return {
            "prompt": "Classify this media by genre.",
            "inputs": [{"asset_id": "owned_asset_100"}],
            "schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["category", "confidence"],
                "additionalProperties": False,
            },
            "confirmed_media_rights": True,
            "approved_for_paid_generation": True,
            **overrides,
        }

    def test_cursor_paginated_owned_and_public_avatar_catalogs(self):
        owned = self.http.get(URL + "/avatars?limit=2&cursor=17", headers=AUTH)
        self.assertEqual(owned.status_code, 200, owned.text)
        self.assertEqual(owned.json()["next_cursor"], 0)
        public = self.http.get(URL + "/avatars/public?limit=5&cursor=10", headers=AUTH)
        self.assertEqual(public.status_code, 200, public.text)
        self.assertIn(("GET", "/api/v1/avatars?is_public=false&limit=2&cursor=17"), self.provider.calls)
        self.assertIn(("GET", "/api/v1/avatars?is_public=true&limit=5&cursor=10"), self.provider.calls)
        before = len(self.provider.calls)
        for route in ("/avatars?limit=101", "/avatars?cursor=-1",
                      "/avatars/public?limit=0", "/avatars/public?cursor=-3"):
            self.assertEqual(self.http.get(URL + route, headers=AUTH).status_code, 422)
        self.assertEqual(before, len(self.provider.calls))

    def test_auth_denies_discovery_before_provider(self):
        self.assertEqual(self.http.get(URL + "/avatars?limit=2").status_code, 401)
        self.assertEqual(self.http.post(URL + "/media/understand",
            json=self.payload()).status_code, 401)
        self.assertEqual(self.provider.calls, [])

    def test_paid_approval_media_rights_and_insufficient_credits(self):
        for change in (
            {"approved_for_paid_generation": False},
            {"confirmed_media_rights": False},
        ):
            result = self.http.post(URL + "/media/understand",
                json=self.payload(**change), headers=AUTH)
            self.assertEqual(result.status_code, 403)
        self.assertEqual(self.provider.calls, [])
        self.provider.remaining = 0
        result = self.http.post(URL + "/media/understand",
            json=self.payload(), headers=AUTH)
        self.assertEqual(result.status_code, 402)
        self.assertIsNone(self.provider.last_payload)
        self.assertEqual(self.provider.calls, [("GET", "/api/v1/billing/credits")])

    def test_media_contract_returns_validated_schema_output_and_real_cost(self):
        result = self.http.post(URL + "/media/understand",
            json=self.payload(), headers=AUTH)
        self.assertEqual(result.status_code, 200, result.text)
        answer = result.json()
        self.assertEqual(answer["output"]["category"], "interview")
        self.assertEqual(answer["usage"]["output_tokens"], 17)
        self.assertEqual(answer["cost_credit"], 1)
        self.assertFalse(answer["retry_after_timeout"])
        self.assertFalse(answer["local_file_saved"])
        self.assertEqual(self.provider.calls, [
            ("GET", "/api/v1/billing/credits"),
            ("POST", "/api/v1/media/understand"),
        ])
        assert self.provider.last_payload is not None
        self.assertNotIn("approved_for_paid_generation", self.provider.last_payload)
        self.assertNotIn("confirmed_media_rights", self.provider.last_payload)
        self.assertEqual(len(self.provider.last_payload["inputs"]), 1)

    def test_inline_audio_and_mixed_media(self):
        encoded = base64.b64encode(b"ID3" + bytes(32)).decode("ascii")
        data = self.payload(inputs=[
            {"asset_id": "asset_23"},
            {"url": "https://cdn.example/media/video.mp4"},
            {"inline_data": {"mime_type": "audio/mpeg", "data": encoded}},
        ])
        result = self.http.post(URL + "/media/understand", json=data, headers=AUTH)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(self.provider.last_payload["inputs"]), 3)

    def test_rejects_dangerous_or_invalid_inputs_pre_provider(self):
        invalid = (
            {"inputs": []},
            {"inputs": [{"asset_id": "good"}] * 9},
            {"inputs": [{"asset_id": "one", "url": "https://example.org/a.jpg"}]},
            {"inputs": [{"url": "http://example.org/image.jpg"}]},
            {"inputs": [{"url": "https://127.0.0.1/image.png"}]},
            {"inputs": [{"url": "https://10.0.0.10/a.png"}]},
            {"inputs": [{"url": "https://local.internal/a.png"}]},
            {"inputs": [{"inline_data": {"mime_type": "application/json", "data": "YWJj"}}]},
            {"inputs": [{"inline_data": {"mime_type": "image/png", "data": "not_base64"}}]},
            {"schema": {"type": "string"}},
            {"schema": {"type": "object", "properties": {}}},
            {"schema": {"type": "object", "properties": {"field": {"$ref": "https://evil.example/schema"}}}},
            {"prompt": ""},
            {"prompt": "A" * 5001},
        )
        for index, change in enumerate(invalid):
            with self.subTest(case=index):
                result = self.http.post(URL + "/media/understand",
                    json=self.payload(**change), headers=AUTH)
                self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.provider.calls, [])

    def test_capability_registry_reports_only_implemented_operations(self):
        r = self.http.get(URL + "/capabilities", headers=AUTH)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["avatar_cursor_pagination"])
        self.assertTrue(r.json()["media_understanding_structured"])
        self.assertTrue(r.json()["media_understanding_requires_paid_approval"])


if __name__ == "__main__":
    unittest.main()
