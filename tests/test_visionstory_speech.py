"""Acceptance of VisionStory TTS/STT/SRT/alignment (no live billable call)."""
import base64
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.gateway.app import app
from services.visionstory.client import VisionStoryRest

AUTH = {"Authorization": "Bearer unit-audio-gateway"}
URI = "/api/cinema/visionstory/speech"
AUDIO = {"inline_data": {
    "mime_type": "audio/mpeg",
    "data": base64.b64encode(b"ID3" + bytes(512)).decode("ascii"),
}}


class FakeProvider:
    def __init__(self, balance=40):
        self.balance = balance
        self.calls = []

    def credits(self):
        self.calls.append(("credits", None))
        return {"remaining": self.balance}

    def transcribe_audio(self, payload):
        self.calls.append(("transcribe", payload))
        return {
            "text": "Dzień dobry.", "language": "pl",
            "words": [{"text": "Dzień", "start_sec": 0, "end_sec": 0.5}],
            "srt": "1\n00:00:00,000 --> 00:00:01,000\nDzień dobry.",
            "duration_sec": 1.0, "cost_credit": 1,
        }

    def align_audio(self, payload):
        self.calls.append(("align", payload))
        return {
            "words": [{"text": "Dzień", "start_sec": 0, "end_sec": 0.5}],
            "cost_credit": 1, "duration_sec": 1,
        }

    def synthesize_mp3(self, payload):
        self.calls.append(("tts", payload))
        return b"ID3" + bytes(120), {
            "cost_credit": 2, "usage_characters": len(payload["text"]),
            "duration_sec": 1.3,
        }


class SpeechAcceptance(unittest.TestCase):
    def setUp(self):
        self.fake = FakeProvider()
        self.http = TestClient(app)
        a = patch("services.ai_studio.omni_orchestrator.API_KEY", "unit-audio-gateway")
        b = patch("services.visionstory.speech.configured_client", return_value=self.fake)
        a.start()
        b.start()
        self.addCleanup(a.stop)
        self.addCleanup(b.stop)

    def transcribe_payload(self, **kwargs):
        return {
            "audio": AUDIO, "srt": True, "diarize": False,
            "confirmed_audio_rights": True,
            "approved_for_paid_generation": True,
            **kwargs,
        }

    def test_transcription_with_srt_not_diarization(self):
        r = self.http.post(URI + "/transcribe",
            json=self.transcribe_payload(), headers=AUTH)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("00:00:00,000", r.json()["srt"])
        self.assertFalse(r.json()["retry_after_timeout"])
        self.assertEqual(self.fake.calls[-1][1]["srt"], True)
        self.assertEqual(self.fake.calls[-1][1]["diarize"], False)

    def test_word_alignment(self):
        result = self.http.post(URI + "/align", headers=AUTH, json={
            "audio": {"asset_id": "audio_asset1"},
            "text": "Dzień dobry.", "confirmed_audio_rights": True,
            "approved_for_paid_generation": True,
        })
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(self.fake.calls[-1][1]["text"], "Dzień dobry.")
        self.assertEqual(result.json()["words"][0]["text"], "Dzień")

    def test_tts_returns_real_mp3_bytes_and_cost_headers(self):
        response = self.http.post(URI + "/tts", headers=AUTH, json={
            "text": "Witaj w Unthinkable AI", "voice_id": "voice_a",
            "locale": "pl-PL", "speech_rate": "normal",
            "confirmed_voice_rights": True,
            "approved_for_paid_generation": True,
        })
        self.assertEqual(response.status_code, 200, response.text[:200])
        self.assertEqual(response.headers["content-type"], "audio/mpeg")
        self.assertEqual(response.headers["x-cost-credit"], "2")
        self.assertEqual(response.content[:3], b"ID3")
        self.assertEqual(self.fake.calls[-1][1]["voice_id"], "voice_a")

    def test_approval_and_rights_enforced_before_provider(self):
        for endpoint, body in (
            ("/tts", {"text": "Hello", "voice_id": "voice_a"}),
            ("/transcribe", {"audio": AUDIO}),
            ("/align", {"audio": AUDIO, "text": "Hello"}),
        ):
            r = self.http.post(URI + endpoint, headers=AUTH, json=body)
            self.assertEqual(r.status_code, 403, r.text)
        self.assertEqual(self.fake.calls, [])

    def test_insufficient_credit_never_dispatches_paid_action(self):
        self.fake.balance = 0
        r = self.http.post(URI + "/transcribe",
            headers=AUTH, json=self.transcribe_payload())
        self.assertEqual(r.status_code, 402, r.text)
        self.assertEqual(self.fake.calls, [("credits", None)])

    def test_rejects_url_internal_and_invalid_locale(self):
        for body in (
            self.transcribe_payload(audio={"url": "http://localhost/audio.mp3"}),
            self.transcribe_payload(audio={"url": "https://127.0.0.1/audio.mp3"}),
            self.transcribe_payload(audio={"inline_data": {"mime_type": "audio/mpeg",
                                                          "data": "not base64"}}),
        ):
            r = self.http.post(URI + "/transcribe", headers=AUTH, json=body)
            self.assertEqual(r.status_code, 422, r.text)
        r = self.http.post(URI + "/tts", headers=AUTH, json={
            "text": "Hello", "voice_id": "voice_a", "locale": "javascript:",
            "confirmed_voice_rights": True,
            "approved_for_paid_generation": True,
        })
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.fake.calls, [])

    def test_auth_required_for_valid_requests(self):
        r = self.http.post(URI + "/transcribe", json=self.transcribe_payload())
        self.assertEqual(r.status_code, 401)
        self.assertEqual(self.fake.calls, [])

    def test_transcribe_and_align_no_automatic_retry(self):
        for endpoint, body in (
            ("/align", self.transcribe_payload(text="Hello")),
            ("/transcribe", self.transcribe_payload()),
        ):
            r = self.http.post(URI + endpoint, headers=AUTH, json=body)
            self.assertEqual(r.status_code, 200)
            self.assertFalse(r.json()["retry_after_timeout"])


if __name__ == "__main__":
    unittest.main()
