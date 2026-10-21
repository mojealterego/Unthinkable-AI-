"""Official VisionStory REST adapter (backend only).

No subprocess, credentials in URL, provider key in mobile builds, or deletes.
The provider API is https://openapi.visionstory.ai and uses X-API-Key.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

VISIONSTORY_API_BASE = "https://openapi.visionstory.ai"
_MAX_RESPONSE = 2_097_152


class VisionStoryError(RuntimeError):
    """Public-safe error with optional upstream status."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class VisionStoryRest:
    def __init__(
        self,
        api_key: str,
        *,
        transport: Callable[[str, str, dict[str, Any] | None], dict] | None = None,
    ) -> None:
        if not api_key or "\r" in api_key or "\n" in api_key:
            raise VisionStoryError("VisionStory API key is not configured", 503)
        self._api_key = api_key
        self._transport = transport

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        allowed = {
            ("GET", "/api/v1/billing/credits"),
            ("GET", "/api/v1/models"),
            ("GET", "/api/v1/ai_video/models"),
            ("GET", "/api/v1/ai_videos"),
            ("GET", "/api/v1/image/models"),
            ("GET", "/api/v1/videos"),
            ("GET", "/api/v1/avatars"),
            ("GET", "/api/v1/voices"),
            ("GET", "/api/v1/video"),
            ("POST", "/api/v1/video"),
            ("POST", "/api/v1/media/understand"),
            ("POST", "/api/v1/audio/transcribe"),
            ("POST", "/api/v1/audio/align"),
            ("GET", "/api/v1/ai_video/cost"),
            ("GET", "/api/v1/ai_video"),
            ("POST", "/api/v1/ai_video"),
            ("GET", "/api/v1/assets"),
            ("POST", "/api/v1/asset"),
            ("POST", "/api/v1/avatar"),
            ("POST", "/api/v1/avatar/framing"),
            ("POST", "/api/v1/voice"),
            ("POST", "/api/v1/image"),
        }
        url_path = path.split("?", 1)[0]
        if (method, url_path) not in allowed:
            raise ValueError("Unsupported VisionStory API operation")
        if self._transport is not None:
            response = self._transport(method, path, payload)
        else:
            url = VISIONSTORY_API_BASE + path
            headers = {
                "X-API-Key": self._api_key,
                "Accept": "application/json",
                "User-Agent": "Unthinkable-AI-Cinema/1.0",
            }
            body = None
            if payload is not None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                headers["Content-Type"] = "application/json"
            request = urllib.request.Request(url, data=body, headers=headers, method=method)
            opener = urllib.request.build_opener(NoRedirect())
            try:
                with opener.open(request, timeout=(190 if path in ("/api/v1/media/understand", "/api/v1/audio/transcribe", "/api/v1/audio/align", "/api/v1/image") else 20)) as stream:
                    raw = stream.read(_MAX_RESPONSE + 1)
                if len(raw) > _MAX_RESPONSE:
                    raise VisionStoryError("VisionStory response exceeded the safety limit")
                response = json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 400 and path == "/api/v1/avatar/framing":
                    # Preserve the provider's safe, actionable crop limit.
                    # Never surface arbitrary upstream HTML or secret-bearing data.
                    message = "Avatar framing rejected; check image dimensions"
                    try:
                        body = json.loads(exc.read(16_384).decode("utf-8"))
                        err = body.get("error", {}) if isinstance(body, dict) else {}
                        details = err.get("details") if isinstance(err, dict) else None
                        if isinstance(details, str):
                            details = json.loads(details)
                        if isinstance(details, dict) and "max_zoom" in details:
                            limit = details["max_zoom"]
                            if limit is None:
                                message = ("Framing unavailable for this aspect ratio; "
                                           "upload a larger portrait")
                            elif type(limit) in (int, float) and (
                                1 <= limit <= 10000
                            ):
                                message = f"Avatar crop exceeds max_zoom={limit:g}"
                    except (ValueError, UnicodeError, TypeError, AttributeError):
                        pass
                    raise VisionStoryError(message, 422) from exc
                if exc.code in (401, 403):
                    raise VisionStoryError("VisionStory rejected the server-side API credentials", 424) from exc
                if exc.code == 429:
                    # Vendor concurrency errors contain details as an object OR
                    # JSON-encoded string, while generic rate-limit errors may omit it.
                    message = "VisionStory rate limit reached; do not auto-retry paid submissions"
                    try:
                        body = json.loads(exc.read(16_384).decode("utf-8"))
                        err = body.get("error", {}) if isinstance(body, dict) else {}
                        details = err.get("details") if isinstance(err, dict) else None
                        if isinstance(details, str):
                            details = json.loads(details)
                        if isinstance(details, dict):
                            limit = details.get("limit")
                            active = details.get("in_flight")
                            if (type(limit) is int and 0 < limit < 100_000 and
                                type(active) is int and 0 <= active < 100_000):
                                message = ("VisionStory concurrency limit reached: "
                                           f"{active} in flight, limit {limit}. "
                                           "Retry only with the same client_request_id")
                    except (ValueError, UnicodeError, TypeError, AttributeError):
                        pass
                    raise VisionStoryError(message, 429) from exc
                raise VisionStoryError("VisionStory API returned an error", 502) from exc
            except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, ValueError) as exc:
                raise VisionStoryError("VisionStory API is unavailable or returned invalid JSON") from exc
        if not isinstance(response, dict) or not isinstance(response.get("data"), dict):
            raise VisionStoryError("VisionStory API response does not include a valid data object")
        return response["data"]

    def credits(self) -> dict:
        return self.request("GET", "/api/v1/billing/credits")

    def models(self) -> dict:
        return self.request("GET", "/api/v1/models")

    def ai_video_models(self) -> dict:
        return self.request("GET", "/api/v1/ai_video/models")

    def image_models(self) -> dict:
        return self.request("GET", "/api/v1/image/models")

    def recent_videos(self) -> dict:
        return self.request("GET", "/api/v1/videos")

    def list_avatars(self, *, is_public: bool = False,
                     limit: int = 20, cursor: int | None = None) -> dict:
        if type(is_public) is not bool or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid avatar visibility or page size")
        if cursor is not None and (type(cursor) is not int or cursor < 1):
            raise ValueError("Avatar cursor must be a positive integer")
        query = {"is_public": "true" if is_public else "false", "limit": limit}
        if cursor is not None:
            query["cursor"] = cursor
        return self.request("GET", "/api/v1/avatars?" + urllib.parse.urlencode(query))

    def public_avatars(self) -> dict:
        return self.request("GET", "/api/v1/avatars?is_public=true")

    def avatars(self) -> dict:
        return self.request("GET", "/api/v1/avatars")

    def voices(self) -> dict:
        return self.request("GET", "/api/v1/voices")
    def list_voices(
        self, *, locale: str | None = None, provider: str | None = None,
        limit: int | None = None, cursor: int = 0,
    ) -> dict:
        """Voice filters and BCP-47 locale, with paginated public catalog."""
        import re
        if locale is not None and not re.fullmatch(
            r"[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){0,3}", locale
        ):
            raise ValueError("Invalid BCP 47 voice locale")
        if provider is not None:
            provider = provider.lower()
            if provider not in {"elevenlabs", "seed", "gemini", "minimax"}:
                raise ValueError("Unknown voice provider")
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 500):
            raise ValueError("Voice page size must be 1..500")
        if type(cursor) is not int or cursor < 0 or (cursor and limit is None):
            raise ValueError("Voice cursor requires pagination")
        query = {}
        if locale is not None:
            query["locale"] = locale
        if provider is not None:
            query["provider"] = provider
        if limit is not None:
            query["limit"] = limit
            query["cursor"] = cursor
        if not query:
            return self.voices()
        return self.request("GET", "/api/v1/voices?" + urllib.parse.urlencode(query))

    def list_ai_videos(
        self, *, status: str | None = None, limit: int = 20, cursor: int = 0,
    ) -> dict:
        """Read-only paginated AI video jobs, optionally filtered by status."""
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("AI video page size must be 1..100")
        if type(cursor) is not int or cursor < 0:
            raise ValueError("AI video cursor cannot be negative")
        if status is not None:
            parts = status.split(",")
            if not parts or len(parts) > 4 or any(
                part not in {"queued", "creating", "created", "failed"} for part in parts
            ) or len(parts) != len(set(parts)):
                raise ValueError("Invalid AI video status filter")
        query = {"limit": limit, "cursor": cursor}
        if status is not None:
            query["status"] = status
        return self.request("GET", "/api/v1/ai_videos?" + urllib.parse.urlencode(query))


    def transcribe_audio(self, payload: dict) -> dict:
        """Synchronous chargeable STT; no automatic replay on timeout."""
        return self.request("POST", "/api/v1/audio/transcribe", payload)

    def align_audio(self, payload: dict) -> dict:
        """Synchronous chargeable forced audio alignment."""
        return self.request("POST", "/api/v1/audio/align", payload)

    def ai_video_cost(
        self, *, model_id: str, duration_sec: int,
        resolution: str | None = None, generate_audio: bool = True,
    ) -> dict:
        query = {
            "model_id": model_id, "duration_sec": duration_sec,
            "generate_audio": str(generate_audio).lower(),
        }
        if resolution is not None:
            query["resolution"] = resolution
        return self.request("GET", "/api/v1/ai_video/cost?" +
                            urllib.parse.urlencode(query))

    def create_ai_video(self, payload: dict) -> dict:
        return self.request("POST", "/api/v1/ai_video", payload)

    def ai_video_status(self, video_id: str) -> dict:
        return self.request("GET", "/api/v1/ai_video?video_id=" +
                            urllib.parse.quote(video_id, safe=""))

    def ai_video_batch_status(self, video_ids: list[str]) -> dict:
        """Read at most 20 jobs per request; the provider returns data.videos."""
        import re
        if (not isinstance(video_ids, list) or not 1 <= len(video_ids) <= 20 or
            any(not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,160}", v)
                for v in video_ids) or len(set(video_ids)) != len(video_ids)):
            raise ValueError("Provide 1–20 distinct, valid VisionStory video IDs")
        return self.request("GET", "/api/v1/ai_video?" +
                            urllib.parse.urlencode({"video_ids": ",".join(video_ids)}))

    def synthesize_mp3(self, payload: dict) -> tuple[bytes, dict]:
        """Vendor TTS is binary audio/mpeg, NOT a JSON envelope.

        Never retry automatically: a timeout can still consume provider credits.
        """
        request = urllib.request.Request(
            VISIONSTORY_API_BASE + "/api/v1/tts",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "X-API-Key": self._api_key,
                "Content-Type": "application/json", "Accept": "audio/mpeg",
                "User-Agent": "Unthinkable-AI-Speech/1.0",
            },
            method="POST",
        )
        try:
            opener = urllib.request.build_opener(NoRedirect())
            with opener.open(request, timeout=190) as stream:
                mime = (stream.headers.get("Content-Type", "") or "").split(";")[0].lower()
                audio = stream.read(20_000_001)
                headers = {key: stream.headers.get(key) for key in
                           ("X-Cost-Credit", "X-Usage-Characters", "X-Audio-Duration-Sec")}
        except urllib.error.HTTPError as exc:
            status = 424 if exc.code in (401, 403) else 429 if exc.code == 429 else 502
            raise VisionStoryError("TTS was rejected by the provider", status) from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise VisionStoryError("TTS failed; do not retry the charge automatically") from exc
        if mime != "audio/mpeg" or not 4 <= len(audio) <= 20_000_000 or not (
            audio.startswith(b"ID3") or (audio[0] == 255 and (audio[1] & 0xE0) == 0xE0)
        ):
            raise VisionStoryError("Provider did not return a valid bounded MP3")
        if not (headers["X-Cost-Credit"] or "").isdigit() or not (
            headers["X-Usage-Characters"] or ""
        ).isdigit():
            raise VisionStoryError("Missing verified TTS usage headers")
        try:
            duration = float(headers["X-Audio-Duration-Sec"] or 0)
        except ValueError as exc:
            raise VisionStoryError("Invalid TTS duration header") from exc
        return audio, {
            "cost_credit": int(headers["X-Cost-Credit"]),
            "usage_characters": int(headers["X-Usage-Characters"]),
            "duration_sec": duration,
        }

    def understand_media(self, payload: dict) -> dict:
        """Synchronous and potentially billable. No automatic retry on timeout."""
        return self.request("POST", "/api/v1/media/understand", payload)

    def create_talking_video(self, payload: dict) -> dict:
        return self.request("POST", "/api/v1/video", payload)

    def video_status(self, video_id: str) -> dict:
        return self.request("GET", "/api/v1/video?video_id=" + urllib.parse.quote(video_id, safe=""))


def configured_client() -> VisionStoryRest:
    key = os.environ.get("VISIONSTORY_API_KEY", "").strip()
    if not key:
        raise VisionStoryError(
            "Configure VISIONSTORY_API_KEY on the private server; do not paste it into chat",
            503,
        )
    return VisionStoryRest(key)
