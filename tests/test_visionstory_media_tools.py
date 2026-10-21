"""Mock-only coverage for owner media, avatar, voice and image capabilities."""
import base64
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryRest

API = "/api/cinema/visionstory"
AUTH = {"Authorization": "Bearer test-key"}
PNG = {"mime_type": "image/png", "data": base64.b64encode(b"\x89PNG\r\n\x1a\n" + bytes(32)).decode()}
MP3 = {"mime_type": "audio/mpeg", "data": base64.b64encode(b"ID3" + bytes(32)).decode()}

class Provider:
    def __init__(self):
        self.calls = []
        self.remaining = 20

    def __call__(self, method, path, payload):
        self.calls.append((method, path, payload))
        if path.startswith("/api/v1/assets"):
            return {"data": {"assets": [{"asset_id": "item01", "kind": "image"}], "next_cursor": 0}}
        if path == "/api/v1/asset":
            return {"data": {"asset_id": "item01"}}
        if path == "/api/v1/avatar":
            return {"data": {"avatar_id": "avatar_new01"}}
        if path == "/api/v1/avatars":
            return {"data": {"avatars": [{"avatar_id": "avatar_owned01"}]}}
        if path == "/api/v1/avatar/framing":
            return {"data": {"avatar_id": payload["avatar_id"], "zoom": payload["zoom"]}}
        if path == "/api/v1/voice":
            return {"data": {"voice_id": "voice_new01"}}
        if path == "/api/v1/image/models":
            return {"data": {"models": [{"model_id": "image_model1", "credit_per_image": 3,
                "credit_by_resolution": {"1K": 3, "2K": 5},
                "params": {"aspect_ratio": {"values": ["1:1"]},
                    "resolution": {"values": ["1K", "2K"]},
                    "prompt": {"max_length": 2000}, "refs": {"max": 2}}}]}}
        if path == "/api/v1/billing/credits":
            return {"data": {"remaining": self.remaining}}
        if path == "/api/v1/image":
            return {"data": {"url": "https://media.example/result.png", "cost_credit": 5}}
        raise AssertionError("Unexpected provider call " + method + " " + path)

class MediaToolTests(unittest.TestCase):
    def setUp(self):
        self.provider = Provider()
        self.http = TestClient(app)
        a = patch("services.ai_studio.omni_orchestrator.API_KEY", "test-key")
        b = patch("services.visionstory.media_tools.configured_client",
                  return_value=VisionStoryRest("provider-fixture", transport=self.provider))
        a.start(); b.start()
        self.addCleanup(a.stop); self.addCleanup(b.stop)

    def test_assets_require_gateway_auth_and_transfer_approval(self):
        self.assertEqual(self.http.get(API + "/assets").status_code, 401)
        listing = self.http.get(API + "/assets?kind=image&limit=20", headers=AUTH)
        self.assertEqual(listing.status_code, 200, listing.text)
        self.assertEqual(listing.json()["next_cursor"], 0)
        data = {"inline_data": PNG, "confirmed_media_rights": True,
                "approved_external_upload": True}
        denied = self.http.post(API + "/assets/upload", headers=AUTH,
                                json=data | {"approved_external_upload": False})
        self.assertEqual(denied.status_code, 403)
        upload = self.http.post(API + "/assets/upload", headers=AUTH, json=data)
        self.assertEqual(upload.status_code, 200, upload.text)
        self.assertEqual(upload.json()["asset_id"], "item01")

    def test_portrait_avatar_and_framing_require_owner_and_consent(self):
        payload = {"inline_data": PNG, "confirmed_image_rights": True,
                   "confirmed_subject_consent": True, "approved_external_upload": True}
        denied = self.http.post(API + "/avatars/create", headers=AUTH,
                                json=payload | {"confirmed_subject_consent": False})
        self.assertEqual(denied.status_code, 403)
        result = self.http.post(API + "/avatars/create", headers=AUTH, json=payload)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["avatar_id"], "avatar_new01")
        framing = {"avatar_id": "avatar_owned01", "aspect_ratio": "9:16",
                   "zoom": 1.2, "offset_x": 0, "offset_y": -0.25,
                   "confirmed_framing_change": True}
        result = self.http.post(API + "/avatars/framing", headers=AUTH, json=framing)
        self.assertEqual(result.status_code, 200, result.text)
        public = self.http.post(API + "/avatars/framing", headers=AUTH,
                                json=framing | {"avatar_id": "public01"})
        self.assertEqual(public.status_code, 403)

    def test_voice_clone_requires_voice_owner_permission(self):
        body = {"inline_data": MP3, "confirmed_voice_owner_consent": True,
                "approved_external_upload": True}
        denied = self.http.post(API + "/voices/clone", headers=AUTH,
                                json=body | {"confirmed_voice_owner_consent": False})
        self.assertEqual(denied.status_code, 403)
        success = self.http.post(API + "/voices/clone", headers=AUTH, json=body)
        self.assertEqual(success.status_code, 200, success.text)
        self.assertEqual(success.json()["voice_id"], "voice_new01")

    def test_image_generation_uses_live_model_and_exact_approved_cost(self):
        body = {"model_id": "image_model1", "prompt": "Studio portrait",
                "aspect_ratio": "1:1", "resolution": "2K",
                "confirmed_reference_rights": True,
                "approved_for_paid_generation": True,
                "max_approved_credits": 5}
        denied = self.http.post(API + "/images/generate", headers=AUTH,
                                json=body | {"max_approved_credits": 4})
        self.assertEqual(denied.status_code, 409, denied.text)
        self.assertFalse(any(p == "/api/v1/image" for _, p, _ in self.provider.calls))
        result = self.http.post(API + "/images/generate", headers=AUTH, json=body)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["cost_credit"], 5)
        self.assertFalse(result.json()["automatic_retry"])

    def test_image_estimate_does_not_charge_and_includes_exact_resolution_price(self):
        body = {
            "model_id": "image_model1", "prompt": "Studio portrait",
            "aspect_ratio": "1:1", "resolution": "2K",
        }
        answer = self.http.post(API + "/images/estimate", headers=AUTH, json=body)
        self.assertEqual(answer.status_code, 200, answer.text)
        self.assertFalse(answer.json()["generation_submitted"])
        self.assertEqual(answer.json()["credits_estimated"], 5)
        self.assertEqual(answer.json()["resolution"], "2K")
        self.assertFalse(any(method == "POST" and path == "/api/v1/image"
                             for method, path, _ in self.provider.calls))

    def test_image_estimate_rejects_bad_model_options_without_paid_request(self):
        cases = [
            {"resolution": "4K"},
            {"aspect_ratio": "21:9"},
            {"prompt": "x" * 2001},
            {"refs": [{"asset_id": "ref1"}] * 3},
            {"model_id": "does_not_exist"},
        ]
        for change in cases:
            self.provider.calls.clear()
            with self.subTest(change=change):
                body = {"model_id": "image_model1", "prompt": "Portrait",
                        "resolution": "2K", "aspect_ratio": "1:1"} | change
                result = self.http.post(
                    API + "/images/estimate", headers=AUTH, json=body
                )
                self.assertEqual(result.status_code, 422, result.text)
                self.assertFalse(any(method == "POST" for method, _, _ in self.provider.calls))

    def test_image_explicit_resolution_requires_verified_price(self):
        self.provider.calls.clear()
        data = {"model_id": "image_model1", "prompt": "Edit portrait",
                "aspect_ratio": "1:1", "resolution": "1K",
                "confirmed_reference_rights": True,
                "approved_for_paid_generation": True,
                "max_approved_credits": 3}
        result = self.http.post(API + "/images/generate", headers=AUTH, json=data)
        self.assertEqual(result.status_code, 200, result.text)
        outgoing = [body for method, path, body in self.provider.calls
                    if method == "POST" and path == "/api/v1/image"]
        self.assertEqual(len(outgoing), 1)
        self.assertEqual(outgoing[0]["resolution"], "1K")

    def test_image_sync_operation_receives_long_vendor_timeout(self):
        import io
        import json
        from unittest.mock import patch
        seen = []
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass
            def read(self, size):
                return json.dumps({"data": {"url": "https://cdn.example/img.png"}}).encode()
        class Opener:
            def open(self, request, timeout):
                seen.append(timeout)
                return Response()
        with patch("services.visionstory.client.urllib.request.build_opener",
                   return_value=Opener()):
            client = VisionStoryRest("fake-provider")
            result = client.request("POST", "/api/v1/image", {
                "model_id": "image_model1", "prompt": "Create",
            })
        self.assertEqual(result["url"], "https://cdn.example/img.png")
        self.assertGreaterEqual(seen[0], 180)

    def test_invalid_media_never_reaches_provider(self):
        denied = self.http.post(API + "/assets/upload", headers=AUTH,
            json={"url": "https://127.0.0.1/test.png",
                  "confirmed_media_rights": True, "approved_external_upload": True})
        self.assertEqual(denied.status_code, 422)
        self.assertEqual(self.provider.calls, [])

if __name__ == "__main__":
    unittest.main()
