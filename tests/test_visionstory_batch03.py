"""VisionStory PDF batch 3: voice search, job filters and private MP4 archive.

No real API key, public DNS request, paid call or external media transfer.
"""
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.gateway.app import app
from services.visionstory.client import VisionStoryRest
from services.visionstory.archive import (
    VisionStoryError, _resolve_public_ip, save_completed_mp4, validate_download_url
)

AUTH = {"Authorization": "Bearer unit-gateway"}
API = "/api/cinema/visionstory"
MP4 = b"\x00\x00\x00\x18ftypisom" + bytes(2000)


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.status = "created"

    def __call__(self, method, path, payload):
        self.calls.append((method, path))
        if path.startswith("/api/v1/voices"):
            return {"data": {"public_voices": [], "my_voices": [], "next_cursor": 0}}
        if path.startswith("/api/v1/ai_videos"):
            return {"data": {"videos": [], "next_cursor": 0}}
        if path.startswith("/api/v1/video?video_id="):
            return {"data": {
                "status": self.status,
                "video_url": "https://media.example/result.mp4",
            }}
        raise AssertionError("Unexpected request " + method + " " + path)


class FakeResponse:
    status = 200

    def __init__(self, contents=MP4):
        self.contents = contents
        self.position = 0

    def getheader(self, name, default=None):
        if name == "Content-Type":
            return "video/mp4"
        if name == "Content-Length":
            return str(len(self.contents))
        return default

    def read(self, amount):
        out = self.contents[self.position:self.position + amount]
        self.position += len(out)
        return out


class FakeConnection:
    def __init__(self, *args, contents=MP4, **kwargs):
        self.response = FakeResponse(contents)

    def request(self, *args, **kwargs):
        pass

    def getresponse(self):
        return self.response

    def close(self):
        pass


class VisionStoryPdf03(unittest.TestCase):
    def setUp(self):
        self.backend = FakeProvider()
        self.http = TestClient(app)
        secret = patch("services.ai_studio.omni_orchestrator.API_KEY", "unit-gateway")
        client = patch(
            "services.visionstory.router.configured_client",
            return_value=VisionStoryRest("unit-provider", transport=self.backend),
        )
        secret.start()
        client.start()
        self.addCleanup(secret.stop)
        self.addCleanup(client.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        env = patch.dict(os.environ, {
            "VISIONSTORY_MEDIA_DIR": self.temp.name,
            "VISIONSTORY_MEDIA_ALLOWED_HOSTS": "media.example",
        })
        env.start()
        self.addCleanup(env.stop)

    def test_voice_locale_provider_cursor(self):
        result = self.http.get(
            API + "/voices?locale=en-GB&provider=MINIMAX&limit=50&cursor=7",
            headers=AUTH,
        )
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIn(
            ("GET", "/api/v1/voices?locale=en-GB&provider=minimax&limit=50&cursor=7"),
            self.backend.calls,
        )
        result2 = self.http.get(API + "/voices", headers=AUTH)
        self.assertEqual(result2.status_code, 200)
        self.assertIn(("GET", "/api/v1/voices"), self.backend.calls)

    def test_invalid_filters_fail_before_remote_requests(self):
        for route in (
            "/voices?limit=501", "/voices?limit=0", "/voices?provider=bogus",
            "/voices?cursor=2", "/voices?locale=bad%%",
            "/ai-videos?status=queued,bogus", "/ai-videos?limit=101",
            "/ai-videos?status=queued,queued", "/ai-videos?cursor=-1",
        ):
            self.assertEqual(self.http.get(API + route, headers=AUTH).status_code, 422)
        self.assertEqual(self.backend.calls, [])

    def test_ai_video_status_filter_and_pagination(self):
        r = self.http.get(
            API + "/ai-videos?status=queued,creating&limit=100&cursor=6",
            headers=AUTH,
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn(
            ("GET", "/api/v1/ai_videos?limit=100&cursor=6&status=queued%2Ccreating"),
            self.backend.calls,
        )

    def test_hostname_allowlist_and_private_dns_protection(self):
        for url in (
            "http://media.example/x.mp4",
            "https://other.example/x.mp4",
            "https://user:pass@media.example/x.mp4",
            "https://media.example:8443/x.mp4",
        ):
            with self.assertRaises(VisionStoryError):
                validate_download_url(url, {"media.example"})
        self.assertEqual(
            validate_download_url("https://media.example/x.mp4?sig=redacted", {"media.example"}),
            ("media.example", "/x.mp4?sig=redacted"),
        )
        for ip in ("127.0.0.1", "169.254.169.254", "10.0.0.5", "::1"):
            records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))]
            with patch(
                "services.visionstory.archive.socket.getaddrinfo", return_value=records
            ), self.assertRaises(VisionStoryError):
                _resolve_public_ip("media.example")

    def test_authenticated_archive_and_download_of_mp4(self):
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch(
            "services.visionstory.archive.socket.getaddrinfo", return_value=records
        ), patch("services.visionstory.archive.PinnedHTTPS", FakeConnection):
            r = self.http.post(API + "/talking-video/job123/archive", headers=AUTH)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["bytes"], len(MP4))
        path = Path(self.temp.name) / "job123.mp4"
        self.assertEqual(path.read_bytes(), MP4)
        self.assertEqual(self.http.get(API + "/talking-video/job123/file").status_code, 401)
        downloaded = self.http.get(API + "/talking-video/job123/file", headers=AUTH)
        self.assertEqual(downloaded.status_code, 200, downloaded.text[:300])
        self.assertEqual(downloaded.content, MP4)
        self.assertEqual(downloaded.headers["cache-control"], "private, no-store")

    def test_archiving_cannot_start_another_paid_render(self):
        self.backend.status = "creating"
        denied = self.http.post(API + "/talking-video/job123/archive", headers=AUTH)
        self.assertEqual(denied.status_code, 409)
        self.assertFalse(any(method == "POST" for method, path in self.backend.calls))
        self.assertFalse(Path(self.temp.name, "job123.mp4").exists())

    def test_invalid_mp4_is_not_written_to_project(self):
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch(
            "services.visionstory.archive.socket.getaddrinfo", return_value=records
        ), patch(
            "services.visionstory.archive.PinnedHTTPS",
            lambda *args, **kwargs: FakeConnection(contents=b"not mp4"),
        ):
            with self.assertRaises(VisionStoryError):
                save_completed_mp4("job123", "https://media.example/file.mp4")
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    def test_capabilities_explain_scope(self):
        r = self.http.get(API + "/capabilities", headers=AUTH)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["voice_locale_provider_pagination"])
        self.assertTrue(r.json()["ai_video_status_filters"])
        self.assertTrue(r.json()["operator_managed_mp4_archive"])


if __name__ == "__main__":
    unittest.main()
