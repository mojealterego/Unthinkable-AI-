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
                with opener.open(request, timeout=(190 if path == "/api/v1/media/understand" else 20)) as stream:
                    raw = stream.read(_MAX_RESPONSE + 1)
                if len(raw) > _MAX_RESPONSE:
                    raise VisionStoryError("VisionStory response exceeded the safety limit")
                response = json.loads(raw.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise VisionStoryError("VisionStory rejected the server-side API credentials", 424) from exc
                if exc.code == 429:
                    raise VisionStoryError("VisionStory rate limit reached", 429) from exc
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
