"""VS-010..VS-012: AI video model guards, batch polling and 429 responses.

No paid calls, keys or external network. All VisionStory calls use fixtures.
"""
from __future__ import annotations
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryRest, VisionStoryError

PREFIX = "/api/cinema/visionstory"
HEADERS = {"Authorization": "Bearer testing-gateway"}
CLIP = {
    "model_id": "wan-3.0",
    "prompt": "Cinematic shot with consistent costume and actor",
    "duration_sec": 8,
    "resolution": "720p",
    "client_request_id": "scene-once-004",
    "refs": [{"asset_id": "asset_image_1"}],
    "confirmed_media_rights": True,
    "approved_for_paid_generation": True,
    "max_approved_credits": 20,
}
class Provider:
    def __init__(self):
        self.calls = []
    def __call__(self, method, path, payload):
        self.calls.append((method, path, payload))
        if path == "/api/v1/ai_video/models":
            return {"data": {"models": [
                {"model_id": model_id, "params": {
                    "duration_sec": {"values": [8]},
                    "resolution": {"values": ["720p"]},
                    "aspect_ratio": {"values": ["9:16", "16:9"]},
                    "prompt": {"max_length": 5000},
                    "refs": {"max": 10},
                }}
                for model_id in ["wan-3.0", "kling-3.0", "kling-3.0-omni"]
            ]}}
        if path.startswith("/api/v1/assets?"):
            return {"data": {"assets": [
                {"asset_id": "asset_video_1", "kind": "video"},
                {"asset_id": "asset_image_1", "kind": "image"},
            ], "next_cursor": 0}}
        if path.startswith("/api/v1/ai_video?video_ids="):
            return {"data": {"videos": [
                {"video_id": "job_a", "status": "queued"},
                {"video_id": "job_b", "status": "created",
                 "video_url": "https://cdn.example/job_b.mp4"},
            ]}}
        if path.startswith("/api/v1/ai_video/cost?"):
            return {"data": {"credit": 10}}
        if path == "/api/v1/billing/credits":
            return {"data": {"remaining": 100}}
        if path == "/api/v1/ai_video" and method == "POST":
            return {"data": {"video_id": "video_123", "status": "queued"}}
        raise AssertionError("Unexpected provider request: " + method + " " + path)

class Batch04(unittest.TestCase):
    def setUp(self):
        self.http = TestClient(app)
        self.fake = Provider()
        a=patch("services.ai_studio.omni_orchestrator.API_KEY", "testing-gateway")
        b=patch("services.visionstory.production.configured_client",
                 return_value=VisionStoryRest("test-provider", transport=self.fake))
        a.start(); b.start()
        self.addCleanup(a.stop); self.addCleanup(b.stop)
    def estimate(self, **kwargs):
        return self.http.post(PREFIX + "/ai-video/estimate",
            headers=HEADERS, json=CLIP | kwargs)
    def test_batch_poll_2_jobs_and_no_paid_calls(self):
        result=self.http.post(PREFIX + "/ai-video/batch-status",
            headers=HEADERS, json={"video_ids": ["job_a", "job_b"]})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(result.json()["videos"]), 2)
        self.assertEqual(result.json()["videos"][0]["status"], "queued")
        self.assertEqual(result.json()["videos"][1]["status"], "created")
        self.assertFalse(result.json()["paid_generation_started"])
        self.assertEqual([m for m,_,_ in self.fake.calls], ["GET"])
    def test_batch_validates_auth_count_duplicates(self):
        self.assertEqual(self.http.post(PREFIX + "/ai-video/batch-status",
            json={"video_ids":["job_a"]}).status_code, 401)
        for ids in [[], ["job_a", "job_a"], ["a/b"], ["x"*161],
                    [f"job_{i}" for i in range(21)]]:
            with self.subTest(ids=len(ids)):
                response=self.http.post(PREFIX + "/ai-video/batch-status",
                    headers=HEADERS,json={"video_ids":ids})
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.fake.calls, [])
    def test_wan_explicit_ratio_is_rejected_when_refs_supplied(self):
        r=self.estimate(aspect_ratio="16:9")
        self.assertEqual(r.status_code, 422, r.text)
        self.assertFalse(any("/cost?" in p for _,p,_ in self.fake.calls))
    def test_kling_3_ref_rejection(self):
        r=self.estimate(model_id="kling-3.0")
        self.assertEqual(r.status_code, 422, r.text)
    def test_kling_3_first_frame_with_explicit_ratio_rejection(self):
        r=self.estimate(model_id="kling-3.0", refs=[],
                        first_frame={"asset_id":"asset_image_1"},
                        aspect_ratio="9:16")
        self.assertEqual(r.status_code, 422, r.text)
    def test_omni_cannot_use_first_frame(self):
        r=self.estimate(model_id="kling-3.0-omni", refs=[],
                        first_frame={"asset_id":"asset_image_1"})
        self.assertEqual(r.status_code, 422, r.text)
    def test_omni_video_ref_must_disable_native_audio(self):
        r=self.estimate(model_id="kling-3.0-omni",
                        refs=[{"asset_id":"asset_video_1"}],
                        generate_audio=True)
        self.assertEqual(r.status_code, 422, r.text)
        self.assertFalse(any("/cost?" in p for _,p,_ in self.fake.calls))
        good=self.estimate(model_id="kling-3.0-omni",
                            refs=[{"asset_id":"asset_video_1"}],
                            generate_audio=False)
        self.assertEqual(good.status_code, 200, good.text)
        self.assertEqual(good.json()["credits_estimated"], 10)
    def test_omni_image_ref_keeps_native_audio(self):
        r=self.estimate(model_id="kling-3.0-omni",
                        refs=[{"asset_id":"asset_image_1"}],
                        generate_audio=True)
        self.assertEqual(r.status_code, 200, r.text)
    def test_omni_unverified_asset_kind_is_rejected(self):
        r=self.estimate(model_id="kling-3.0-omni",
                        refs=[{"asset_id":"unknown_asset_1"}],
                        generate_audio=True)
        self.assertEqual(r.status_code, 422, r.text)
    def test_429_object_and_encoded_string_concurrency_detail(self):
        for details in ({"limit": 3, "in_flight": 3},
                        '{"limit": 3, "in_flight": 3}'):
            class FakeOpener:
                def open(self, request, timeout):
                    body = json.dumps({"error":{"details": details}}).encode()
                    raise HTTPError(request.full_url, 429, "Rate limit", {},
                                    io.BytesIO(body))
            with self.subTest(details=type(details).__name__):
                with patch("services.visionstory.client.urllib.request.build_opener",
                           return_value=FakeOpener()):
                    client=VisionStoryRest("fake-test-secret")
                    with self.assertRaises(VisionStoryError) as cm:
                        client.ai_video_models()
                    self.assertEqual(cm.exception.status, 429)
                    self.assertIn("in flight", str(cm.exception))
                    self.assertNotIn("fake-test-secret", str(cm.exception))

    def test_avatar_zoom_over_four_uses_provider_limit(self):
        def avatar_provider(method, path, body):
            if method == "GET" and path == "/api/v1/avatars":
                return {"data": {"avatars": [{"avatar_id": "owned_avatar_1"}]}}
            if method == "POST" and path == "/api/v1/avatar/framing":
                return {"data": {"avatar_id": body["avatar_id"], "zoom": body["zoom"]}}
            raise AssertionError(path)
        with patch("services.visionstory.media_tools.configured_client",
                   return_value=VisionStoryRest("test-secret", transport=avatar_provider)):
            result=self.http.post(PREFIX + "/avatars/framing",
                headers=HEADERS,
                json={"avatar_id":"owned_avatar_1","aspect_ratio":"9:16",
                      "zoom":6.5,"offset_x":0,"offset_y":0,
                      "confirmed_framing_change":True})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["zoom"], 6.5)

    def test_provider_max_zoom_error_is_actionable_but_sanitized(self):
        for detail, expected in (({"max_zoom": 3.25}, "max_zoom=3.25"),
                                 ({"max_zoom": None}, "larger portrait")):
            class Opener:
                def open(self, request, timeout):
                    payload=json.dumps({"error":{"details": detail}}).encode()
                    raise HTTPError(request.full_url, 400, "Bad framing", {},
                                    io.BytesIO(payload))
            with self.subTest(detail=detail):
                with patch("services.visionstory.client.urllib.request.build_opener",
                           return_value=Opener()):
                    client=VisionStoryRest("sensitive-api-key")
                    with self.assertRaises(VisionStoryError) as cm:
                        client.request("POST", "/api/v1/avatar/framing", {
                            "avatar_id":"owned_avatar_1","aspect_ratio":"9:16",
                            "zoom":10,"offset_x":0,"offset_y":0,
                        })
                self.assertEqual(cm.exception.status, 422)
                self.assertIn(expected, str(cm.exception))
                self.assertNotIn("sensitive-api-key", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
