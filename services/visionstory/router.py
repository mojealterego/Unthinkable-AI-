"""Read-only discovery + explicit-cost-gated VisionStory speaking video jobs.

This adapter does not install CLI, expose upstream key, delete anything,
automatically render a full film or proxy arbitrary media URLs.
"""
from __future__ import annotations

import re
import uuid
import base64
import binascii
import json
import ipaddress
from urllib.parse import urlsplit
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse
from .archive import save_completed_mp4, mp4_path, archive_root
from pydantic import BaseModel, Field, model_validator

from services.ai_studio.omni_orchestrator import _auth
from .client import VisionStoryError, configured_client
from .jobs import configured_ledger

router = APIRouter(prefix="/api/cinema/visionstory", tags=["Cinema VisionStory"])


_MIME_AUDIO = {"audio/avi", "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a", "audio/wav"}


class InlineAudio(BaseModel):
    mime_type: Literal[
        "audio/avi", "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a", "audio/wav"
    ]
    data: str = Field(min_length=4, max_length=11_200_000)

    @model_validator(mode="after")
    def check_base64(self):
        import base64
        import binascii
        try:
            decoded = base64.b64decode(self.data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Audio must be raw valid base64, without a data URI") from exc
        if not decoded or len(decoded) > 8_000_000:
            raise ValueError("Inline audio must be 1..8,000,000 bytes")
        return self


class AudioScriptInput(BaseModel):
    audio_url: str | None = Field(default=None, max_length=2048)
    inline_data: InlineAudio | None = None
    denoise: bool = False
    voice_change: bool = False
    voice_id: str | None = Field(
        default=None, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$"
    )

    @model_validator(mode="after")
    def check_source(self):
        if (self.audio_url is None) == (self.inline_data is None):
            raise ValueError("Provide exactly one of audio_url or inline_data")
        if self.voice_change and not self.voice_id:
            raise ValueError("Voice conversion requires a selected voice_id")
        if self.audio_url is not None:
            import ipaddress
            from urllib.parse import urlsplit
            url = urlsplit(self.audio_url)
            if (url.scheme != "https" or not url.hostname or url.username or
                url.password or url.port not in (None, 443) or url.fragment or
                any(c in self.audio_url for c in "\r\n\t")):
                raise ValueError("Audio URL must be public HTTPS without credentials")
            host = url.hostname.lower().rstrip(".")
            if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
                raise ValueError("Internal audio host is forbidden")
            try:
                ip = ipaddress.ip_address(host)
            except ValueError:
                pass
            else:
                if not ip.is_global:
                    raise ValueError("Non-public IP address is forbidden")
        return self


class TalkingVideoInput(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$")
    model_id: str = Field(min_length=1, max_length=160, pattern=r"^[a-zA-Z0-9_.-]+$")
    # Legacy top-level text/voice_id remain supported for the existing Android contract.
    text: str | None = Field(default=None, max_length=5000)
    voice_id: str | None = Field(
        default=None, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    audio_script: AudioScriptInput | None = None
    confirmed_audio_rights: bool = False
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    resolution: Literal["720p", "1080p", "2k"] = "720p"
    speech_rate: Literal["slow", "normal", "fast"] = "normal"
    emotion: Literal["cheerful", "angry", "marketing", "news", "singing"] = "cheerful"
    background_color: str = Field(
        default="", max_length=7, pattern=r"^(?:|#[0-9a-fA-F]{6})$"
    )
    client_request_id: str = Field(
        min_length=8, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    approved_for_paid_generation: bool = False

    @model_validator(mode="after")
    def check_exclusive_script(self):
        has_text = self.text is not None
        has_audio = self.audio_script is not None
        if has_text == has_audio:
            raise ValueError("Provide exactly one text script or recorded audio_script")
        if has_text and (not self.text or not self.text.strip() or not self.voice_id):
            raise ValueError("Text-to-speech requires both text and voice_id")
        if has_audio and not self.confirmed_audio_rights:
            raise ValueError("The audio rights/permission confirmation is required")
        return self


class VideoId(BaseModel):
    video_id: str = Field(min_length=3, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$")


def _remote(action):
    try:
        return action()
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


def _client():
    return configured_client()


@router.get("/capabilities")
def capabilities(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {
        "provider": "visionstory",
        "integration": "remote_rest_backend",
        "credential_location": "private_server",  # do not expose provider key or readiness
        "read_only_discovery": True,
        "ai_video_model_discovery": True,
        "image_model_discovery": True,
        "recorded_audio_script": True,
        "avatar_cursor_pagination": True,
        "media_understanding_structured": True,
        "media_understanding_requires_paid_approval": True,
        "inline_audio_max_bytes": 8_000_000,
        "emotion_and_chroma_key": True,
        "talking_avatar_submit": True,
        "video_status": True,
        "operator_managed_mp4_archive": True,
        "mp4_archive_requires_approved_cdn_host": True,
        "voice_locale_provider_pagination": True,
        "ai_video_status_filters": True,
        "mp4_download_in_cli": True,
        "local_rendering": False,
        "automatic_voice_cloning": False,
        "delete_supported": False,
        "generation_requires_user_approval": True,
    }


@router.get("/credits")
def credits(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().credits())


@router.get("/models")
def models(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().models())


@router.get("/avatars")
def avatars(
    authorization: str | None = Header(default=None),
    limit: int = 20,
    cursor: int | None = None,
):
    _auth(authorization)
    if not 1 <= limit <= 100 or (cursor is not None and cursor < 1):
        raise HTTPException(status_code=422, detail="Invalid avatar pagination values")
    if limit == 20 and cursor is None:  # backward compatibility
        return _remote(lambda: _client().avatars())
    return _remote(lambda: _client().list_avatars(limit=limit, cursor=cursor))


@router.get("/avatars/public")
def public_avatars(
    authorization: str | None = Header(default=None),
    limit: int = 20,
    cursor: int | None = None,
):
    _auth(authorization)
    if not 1 <= limit <= 100 or (cursor is not None and cursor < 1):
        raise HTTPException(status_code=422, detail="Invalid avatar pagination values")
    if limit == 20 and cursor is None:  # backward compatibility
        return _remote(lambda: _client().public_avatars())
    return _remote(lambda: _client().list_avatars(
        is_public=True, limit=limit, cursor=cursor
    ))


@router.get("/models/ai-video")
def ai_video_models(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().ai_video_models())


@router.get("/models/image")
def image_models(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().image_models())


@router.get("/videos/recent")
def recent_videos(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().recent_videos())


@router.get("/voices")
def voices(
    authorization: str | None = Header(default=None),
    locale: str | None = None,
    provider: str | None = None,
    limit: int | None = None,
    cursor: int = 0,
):
    _auth(authorization)
    try:
        return _remote(lambda: _client().list_voices(
            locale=locale, provider=provider, limit=limit, cursor=cursor
        ))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/ai-videos")
def ai_videos(
    authorization: str | None = Header(default=None),
    status: str | None = None, limit: int = 20, cursor: int = 0,
):
    _auth(authorization)
    try:
        return _remote(lambda: _client().list_ai_videos(
            status=status, limit=limit, cursor=cursor
        ))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/talking-video")
def talking_video(req: TalkingVideoInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not req.approved_for_paid_generation:
        raise HTTPException(
            status_code=403, detail="Explicit approval for potentially billable rendering is required"
        )

    def submit():
        client = _client()
        balance = client.credits()
        if isinstance(balance.get("remaining"), bool) or not isinstance(balance.get("remaining"), int):
            raise VisionStoryError("Cannot verify a numeric VisionStory credit balance", 424)
        if balance["remaining"] <= 0:
            raise VisionStoryError("VisionStory account has no remaining credits", 402)

        discovered = client.models().get("models", [])
        if not isinstance(discovered, list):
            raise VisionStoryError("Cannot validate provider model catalog")
        model = next((m for m in discovered if isinstance(m, dict) and
                      m.get("model_id") == req.model_id), None)
        if model is None:
            raise VisionStoryError("Requested model is not in the live provider catalog", 422)
        if req.aspect_ratio not in model.get("aspect_ratios", []):
            raise VisionStoryError("Model does not support requested aspect ratio", 422)
        if req.resolution not in model.get("resolutions", []):
            raise VisionStoryError("Model does not support requested resolution", 422)

        catalog = client.avatars()
        found_avatar = any(
            a.get("avatar_id") == req.avatar_id
            for group in ("avatars", "my_avatars", "public_avatars")
            for a in catalog.get(group, [])
            if isinstance(a, dict)
        )
        if not found_avatar:
            raise VisionStoryError("Avatar is missing from currently accessible provider catalog", 422)

        voice_to_check = req.voice_id if req.audio_script is None else (
            req.audio_script.voice_id if req.audio_script.voice_change else None
        )
        if voice_to_check is not None:
            voices = client.voices()
            found_voice = any(
                v.get("voice_id") == voice_to_check
                for group in ("public_voices", "my_voices", "voices")
                for v in voices.get(group, [])
                if isinstance(v, dict)
            )
            if not found_voice:
                raise VisionStoryError("Voice is missing from currently accessible provider catalog", 422)

        script = (
            {"text_script": {"text": req.text, "voice_id": req.voice_id,
                             "speech_rate": req.speech_rate}}
            if req.audio_script is None else
            {"audio_script": req.audio_script.model_dump(exclude_none=True)}
        )
        payload = {
            "model_id": req.model_id,
            "avatar_id": req.avatar_id,
            "client_request_id": req.client_request_id,
            "aspect_ratio": req.aspect_ratio,
            "resolution": req.resolution,
            "emotion": req.emotion,
            "background_color": req.background_color,
            **script,
        }
        ledger = configured_ledger()
        existing = ledger.begin("avatar_video", req.client_request_id, payload) if ledger else None
        if existing is not None:
            return {
                "provider": "visionstory", "video_id": existing,
                "client_request_id": req.client_request_id,
                "mode": "remote_provider_job", "locally_generated": False,
                "poll_after_seconds": 5, "requires_status_check": True,
                "reused_existing_job": True, "durable_job_ledger": True,
            }
        try:
            result = client.create_talking_video(payload)
            video_id = result.get("video_id")
            if not isinstance(video_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{3,160}", video_id):
                raise VisionStoryError("Provider did not return a valid video_id")
        except Exception:
            if ledger:
                ledger.mark_ambiguous("avatar_video", req.client_request_id)
            raise
        if ledger:
            ledger.finish("avatar_video", req.client_request_id, video_id)
        return {
            "provider": "visionstory",
            "video_id": video_id,
            "mode": "remote_provider_job",
            "locally_generated": False,
            "client_request_id": req.client_request_id,
            "poll_after_seconds": 5,
            "requires_status_check": True,
            "durable_job_ledger": ledger is not None,
        }

    return _remote(submit)


@router.post("/talking-video/{video_id}/archive")
def archive_talking_video(video_id: str, authorization: str | None = Header(default=None)):
    """Download finished provider MP4 to explicitly configured private server storage."""
    _auth(authorization)
    try:
        video = VideoId(video_id=video_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid video id") from exc

    def archive():
        data = _client().video_status(video.video_id)
        if data.get("status") not in ("created", "success"):
            raise VisionStoryError("Video job is not completed", 409)
        url = data.get("video_url")
        if not isinstance(url, str) or not url:
            raise VisionStoryError("Completed job does not have an MP4 download URL", 409)
        filename, size = save_completed_mp4(video.video_id, url)
        return {
            "archived": True,
            "video_id": video.video_id,
            "filename": filename,
            "bytes": size,
            "content_type": "video/mp4",
            "download_path": (
                "/api/cinema/visionstory/talking-video/"
                + video.video_id + "/file"
            ),
        }

    return _remote(archive)


@router.get("/talking-video/{video_id}/file")
def download_archived_video(video_id: str, authorization: str | None = Header(default=None)):
    """Serve only an existing, locally archived MP4 after gateway authentication."""
    _auth(authorization)
    try:
        path = mp4_path(VideoId(video_id=video_id).video_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid video id") from exc
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=404, detail="No archived MP4 exists for this video id")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=path.name,
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("/talking-video/{video_id}")
def talking_video_status(video_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        validated = VideoId(video_id=video_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid video identifier") from exc

    def load():
        result = _client().video_status(validated.video_id)
        status = result.get("status")
        # The provider status enum is documented as created, although an older
        # example uses success. Normalize that completed state in the gateway.
        if status == "success":
            status = "created"
        if status not in {"queued", "creating", "created", "failed"}:
            raise VisionStoryError("Unrecognized video job status; check provider contract")
        url = result.get("video_url")
        if url and (not isinstance(url, str) or not url.startswith("https://")):
            raise VisionStoryError("Provider returned a non-HTTPS download link")
        return {
            "provider": "visionstory",
            "video_id": validated.video_id,
            "status": status,
            "video_url": url if status == "created" else None,
            "cost_credit": result.get("cost_credit"),
            "download_retention_days": 7,
            "local_file_saved": False,
        }

    return _remote(load)


_MEDIA_TYPES = frozenset((
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp",
    "image/tiff", "image/gif", "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3", "video/mp4", "video/quicktime", "video/mov",
))
_SCHEMA_PRIMITIVES = frozenset(("object", "array", "string", "number", "integer", "boolean", "null"))


def _media_public_url(value: str) -> str:
    if len(value) > 2048 or any(c in value for c in "\r\n\t"):
        raise ValueError("Media URL is malformed")
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password or (
        url.port not in (None, 443)
    ) or url.fragment:
        raise ValueError("Media URL must be public HTTPS without credentials")
    host = url.hostname.rstrip(".").lower()
    if host in ("localhost",) or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Internal media host not permitted")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host):
            raise ValueError("Invalid public media hostname")
    else:
        if not ip.is_global:
            raise ValueError("Non-public IP in media URL")
    return value


class MediaInline(BaseModel):
    mime_type: Literal[
        "image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp",
        "image/tiff", "image/gif", "audio/wav", "audio/x-wav", "audio/wave",
        "audio/mpeg", "audio/mp3", "video/mp4", "video/quicktime", "video/mov",
    ]
    data: str = Field(min_length=4, max_length=18_700_000)

    @model_validator(mode="after")
    def validate_encoded_data(self):
        try:
            raw = base64.b64decode(self.data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Media inline_data must be raw base64") from exc
        if not raw or len(raw) > 14_000_000:
            raise ValueError("Individual inline media exceeds size budget")
        return self


class MediaReference(BaseModel):
    asset_id: str | None = Field(
        default=None, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    url: str | None = Field(default=None, max_length=2048)
    inline_data: MediaInline | None = None

    @model_validator(mode="after")
    def validate_exactly_one_source(self):
        if sum(x is not None for x in (
            self.asset_id, self.url, self.inline_data,
        )) != 1:
            raise ValueError("Select exactly one media reference per input")
        if self.url is not None:
            _media_public_url(self.url)
        return self


def _validate_output_schema(schema: dict[str, Any]) -> None:
    # A compact, bounded JSON Schema subset. Forbid remote refs and network lookups.
    if len(json.dumps(schema, ensure_ascii=False).encode("utf-8")) > 20_000:
        raise ValueError("Schema exceeds 20 KB")
    if schema.get("type") != "object" or not isinstance(
        schema.get("properties"), dict
    ) or not schema["properties"]:
        raise ValueError("Root schema needs type=object and nonempty properties")
    def check(node: Any, level: int) -> None:
        if level > 8:
            raise ValueError("Schema nesting is too deep")
        if isinstance(node, dict):
            if "$ref" in node:  # conservative policy: not even local references
                raise ValueError("Schema references are not accepted by this gateway")
            if "type" in node and node["type"] not in _SCHEMA_PRIMITIVES:
                raise ValueError("Unknown JSON Schema type")
            for key, value in node.items():
                if not isinstance(key, str) or len(key) > 100:
                    raise ValueError("Invalid JSON Schema property name")
                check(value, level + 1)
        elif isinstance(node, list):
            if len(node) > 150:
                raise ValueError("Schema array is too long")
            for child in node:
                check(child, level + 1)
        elif not isinstance(node, (str, int, float, bool, type(None))):
            raise ValueError("Invalid JSON Schema property value")
    check(schema, 0)


class MediaUnderstandInput(BaseModel):
    prompt: str = Field(min_length=1, max_length=5000)
    inputs: list[MediaReference] = Field(min_length=1, max_length=8)
    schema_: dict[str, Any] = Field(alias="schema")
    confirmed_media_rights: bool = False
    approved_for_paid_generation: bool = False

    @model_validator(mode="after")
    def validate_scope(self):
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be blank")
        _validate_output_schema(self.schema_)
        inline_bytes = 0
        for media in self.inputs:
            if media.inline_data is not None:
                inline_bytes += len(base64.b64decode(media.inline_data.data))
        if inline_bytes > 14_000_000:
            raise ValueError("Combined inline media exceeds 14 MB")
        return self


@router.post("/media/understand")
def understand_media(
    req: MediaUnderstandInput,
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    if not req.confirmed_media_rights:
        raise HTTPException(status_code=403, detail="Media usage rights must be confirmed")
    if not req.approved_for_paid_generation:
        raise HTTPException(status_code=403, detail="Explicit credit approval required")

    def submit():
        client = _client()
        credits = client.credits()
        remaining = credits.get("remaining")
        if type(remaining) is not int:
            raise VisionStoryError("Cannot verify a numeric VisionStory credit balance", 424)
        if remaining <= 0:
            raise VisionStoryError("Paid VisionStory credits are insufficient", 402)
        data = client.understand_media({
            "prompt": req.prompt, "inputs": [m.model_dump(exclude_none=True) for m in req.inputs],
            "schema": req.schema_,
        })
        output = data.get("output")
        usage = data.get("usage")
        cost = data.get("cost_credit")
        if not isinstance(output, dict) or not isinstance(usage, dict) or (
            type(cost) is not int or cost < 0
        ):
            raise VisionStoryError("VisionStory returned invalid structured media results")
        return {
            "output": output,
            "usage": usage,
            "cost_credit": cost,
            "provider": "visionstory",
            "operation": "media_understanding",
            "retry_after_timeout": False,
            "local_file_saved": False,
        }

    # Synchronous call can complete at provider after client times out.
    # Never automatically retry: each successful completion consumes credits.
    return _remote(submit)


@router.get("/jobs")
def durable_jobs(authorization: str | None = Header(default=None), limit: int = 100):
    """Single-owner list; never returns prompts or provider credentials."""
    _auth(authorization)
    ledger = configured_ledger()
    if ledger is None:
        raise HTTPException(status_code=503, detail="Job ledger is not configured")
    try:
        return {"scope": "single_owner", "jobs": ledger.list_jobs(limit)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
