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


class TalkingVideoInput(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$")
    voice_id: str = Field(min_length=1, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$")
    model_id: str = Field(min_length=1, max_length=160, pattern=r"^[a-zA-Z0-9_.-]+$")
    text: str = Field(min_length=1, max_length=5000)
    aspect_ratio: Literal["9:16", "16:9", "1:1"] = "9:16"
    resolution: Literal["720p", "1080p", "2k"] = "720p"
    speech_rate: Literal["slow", "normal", "fast"] = "normal"
    client_request_id: str = Field(
        min_length=8, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    approved_for_paid_generation: bool = False

    @model_validator(mode="after")
    def accept_script(self):
        if not self.text.strip():
            raise ValueError("Video speech cannot be blank")
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

        voices = client.voices()
        found_voice = any(
            v.get("voice_id") == req.voice_id
            for group in ("public_voices", "my_voices", "voices")
            for v in voices.get(group, [])
            if isinstance(v, dict)
        )
        if not found_voice:
            raise VisionStoryError("Voice is missing from currently accessible provider catalog", 422)

        result = client.create_talking_video({
            "model_id": req.model_id,
            "avatar_id": req.avatar_id,
            "client_request_id": req.client_request_id,
            "text_script": {
                "text": req.text,
                "voice_id": req.voice_id,
                "speech_rate": req.speech_rate,
            },
            "aspect_ratio": req.aspect_ratio,
            "resolution": req.resolution,
        })
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
