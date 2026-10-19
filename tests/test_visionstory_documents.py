"""VisionStory PDF contracts: safe tests with no live provider calls."""
import base64
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryRest

AUTH = {"Authorization": "Bearer fixture-secret"}


class MockProvider:
    def __init__(self):
        self.calls = []
        self.sent = []

    def __call__(self, method, path, body):
        self.calls.append((method, path))
        replies = {
            "/api/v1/billing/credits": {"remaining": 50},
            "/api/v1/models": {"models": [{
                "model_id": "vs_character_v4", "aspect_ratios": ["9:16"],
                "resolutions": ["720p"], "max_duration_seconds": 600,
            }]},
            "/api/v1/avatars": {
                "my_avatars": [{"avatar_id": "avatar1"}],
                "public_avatars": [{"avatar_id": "avatar2"}],
            },
            "/api/v1/avatars?is_public=true": {"avatars": [{"avatar_id": "avatar2"}]},
            "/api/v1/voices": {"public_voices": [{"voice_id": "voice1"}], "my_voices": []},
            "/api/v1/ai_video/models": {"models": [{"model_id": "seedance-2.5"}]},
            "/api/v1/image/models": {"models": [{"model_id": "nano-banana-2"}]},
            "/api/v1/videos": {"videos": [{"video_id": "video_1"}]},
            "/api/v1/video?video_id=video_1": {
                "video_id": "video_1", "status": "success",
                "video_url": "https://media.example/video.mp4",
            },
        }
        if path == "/api/v1/video" and method == "POST":
            self.sent.append(body)
            return {"data": {"video_id": "video_1"}}
        if path not in replies:
            raise AssertionError("Unexpected provider call " + method + " " + path)
        return {"data": replies[path]}


class VisionStoryPdfTests(unittest.TestCase):
    def setUp(self):
        self.provider = MockProvider()
        self.http = TestClient(app)
        gateway = patch("services.ai_studio.omni_orchestrator.API_KEY", "fixture-secret")
        remote = patch("services.visionstory.router.configured_client",
                       return_value=VisionStoryRest("provider-fixture", transport=self.provider))
        gateway.start()
        remote.start()
        self.addCleanup(gateway.stop)
        self.addCleanup(remote.stop)

    def post(self, **changes):
        body = {
            "avatar_id": "avatar1", "model_id": "vs_character_v4",
            "client_request_id": "scene00001",
            "approved_for_paid_generation": True,
            "confirmed_audio_rights": True,
            "audio_script": {"inline_data": {
                "mime_type": "audio/mpeg",
                "data": base64.b64encode(b"ID3" + bytes(512)).decode(),
            }, "denoise": True},
            "emotion": "singing", "background_color": "#00b140",
        }
        return self.http.post("/api/cinema/visionstory/talking-video",
                              json=body | changes, headers=AUTH)

    def test_inline_mp3_asynchronous_generation(self):
        answer = self.post()
        self.assertEqual(answer.status_code, 200, answer.text)
        payload = self.provider.sent[0]
        self.assertEqual(payload["audio_script"]["inline_data"]["mime_type"], "audio/mpeg")
        self.assertTrue(payload["audio_script"]["denoise"])
        self.assertEqual(payload["emotion"], "singing")
        self.assertEqual(payload["background_color"], "#00b140")
        self.assertEqual(payload["client_request_id"], "scene00001")
        self.assertNotIn("text_script", payload)
        self.assertEqual(answer.json()["video_id"], "video_1")

    def test_audio_url_with_optional_converted_voice(self):
        answer = self.post(audio_script={
            "audio_url": "https://my-media.example/narration.mp3",
            "voice_change": True, "voice_id": "voice1",
        })
        self.assertEqual(answer.status_code, 200, answer.text)
        self.assertEqual(self.provider.sent[0]["audio_script"]["voice_id"], "voice1")
        self.assertIn(("GET", "/api/v1/voices"), self.provider.calls)

    def test_rejects_unauthorized_audio_and_unsafe_inputs_without_rendering(self):
        errors = (
            {"confirmed_audio_rights": False},
            {"audio_script": {"audio_url": "http://example.com/x.mp3"}},
            {"audio_script": {"audio_url": "https://127.0.0.1/a.mp3"}},
            {"audio_script": {"audio_url": "https://metadata.google.internal/x.mp3"}},
            {"audio_script": {"inline_data": {"mime_type": "audio/wav", "data": "invalid base64"}}},
            {"audio_script": {"inline_data": {"mime_type": "text/html", "data": "QUJD"}}},
            {"audio_script": {"audio_url": "https://example.com/a.mp3",
                              "inline_data": {"mime_type": "audio/mp3", "data": "QUJD"}}},
            {"audio_script": {"audio_url": "https://example.com/a.mp3",
                              "voice_change": True}},
            {"text": "Both text and audio", "voice_id": "voice1"},
            {"emotion": "unexpected"},
            {"background_color": "invalid"},
        )
        for change in errors:
            with self.subTest(change=change):
                result = self.post(**change)
                self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.provider.sent, [])

    def test_three_distinct_model_catalogs_and_recent_videos(self):
        for suffix, expected in (
            ("/models", "vs_character_v4"),
            ("/models/ai-video", "seedance-2.5"),
            ("/models/image", "nano-banana-2"),
        ):
            result = self.http.get("/api/cinema/visionstory" + suffix, headers=AUTH)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()["models"][0]["model_id"], expected)
        result = self.http.get("/api/cinema/visionstory/videos/recent", headers=AUTH)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["videos"][0]["video_id"], "video_1")

    def test_public_avatar_catalog_and_provider_completed_state(self):
        public = self.http.get("/api/cinema/visionstory/avatars/public", headers=AUTH)
        self.assertEqual(public.status_code, 200, public.text)
        self.assertEqual(public.json()["avatars"][0]["avatar_id"], "avatar2")
        completed = self.http.get(
            "/api/cinema/visionstory/talking-video/video_1", headers=AUTH)
        self.assertEqual(completed.status_code, 200, completed.text)
        self.assertEqual(completed.json()["status"], "created")
        self.assertEqual(completed.json()["download_retention_days"], 7)

    def test_gateway_denies_unauthed_discovery_and_render(self):
        for suffix in ("models/ai-video", "models/image", "videos/recent", "avatars/public"):
            self.assertEqual(self.http.get(
                "/api/cinema/visionstory/" + suffix).status_code, 401)
        self.assertEqual(self.http.post(
            "/api/cinema/visionstory/talking-video", json={}
        ).status_code, 401)


if __name__ == "__main__":
    unittest.main()
