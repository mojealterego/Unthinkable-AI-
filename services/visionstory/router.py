"""Read-only discovery + explicit-cost-gated VisionStory speaking video jobs.

This adapter does not install CLI, expose upstream key, delete anything,
automatically render a full film or proxy arbitrary media URLs.
"""
from __future__ import annotations

import re
import uuid
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from services.ai_studio.omni_orchestrator import _auth
from .client import VisionStoryError, configured_client

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
        "inline_audio_max_bytes": 8_000_000,
        "emotion_and_chroma_key": True,
        "talking_avatar_submit": True,
        "video_status": True,
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
def avatars(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().avatars())


@router.get("/avatars/public")
def public_avatars(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().public_avatars())


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
def voices(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _remote(lambda: _client().voices())


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
        result = client.create_talking_video(payload)
        video_id = result.get("video_id")
        if not isinstance(video_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{3,160}", video_id):
            raise VisionStoryError("Provider did not return a valid video_id")
        return {
            "provider": "visionstory",
            "video_id": video_id,
            "mode": "remote_provider_job",
            "locally_generated": False,
            "client_request_id": req.client_request_id,
            "poll_after_seconds": 5,
            "requires_status_check": True,
        }

    return _remote(submit)


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
