"""VisionStory production integrations: captioning, forced alignment, AI video.

All paid operations use server-only provider credentials, human cost approval,
live model discovery and (where supported) vendor cost quotes. No automatic
retries for synchronous paid audio operations. No media deletion endpoints.
"""
from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from services.ai_studio.omni_orchestrator import _auth
from .client import VisionStoryError, configured_client
from .jobs import configured_ledger
from .router import MediaReference

router = APIRouter(prefix="/api/cinema/visionstory", tags=["VisionStory Production"])

_ID = re.compile(r"^[a-zA-Z0-9_.-]{3,160}$")
_RATE = re.compile(r"^[a-zA-Z0-9_-]{8,128}$")
_STATUS = {"queued", "creating", "created", "failed"}


def _paid(fn):
    try:
        return fn()
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


def _check_credits(client, estimate: int) -> int:
    balance = client.credits().get("remaining")
    if type(balance) is not int or balance < 0:
        raise VisionStoryError("Cannot verify a numeric credit balance", 424)
    if balance < estimate:
        raise VisionStoryError("Not enough provider credits for this operation", 402)
    return balance


def _audio_reference(source: MediaReference) -> dict:
    """Restrict URL inputs to explicit media domains or own asset IDs."""
    if source.url is not None:
        raise ValueError("External audio URLs require prior upload to an owned asset_id")
    if source.inline_data is not None:
        if not source.inline_data.mime_type.startswith("audio/"):
            raise ValueError("Audio endpoint requires an audio media type")
    return source.model_dump(exclude_none=True)


class CaptionInput(BaseModel):
    audio: MediaReference
    diarize: bool = False
    srt: bool = False
    confirmed_audio_rights: bool = False
    approved_for_paid_processing: bool = False

    @model_validator(mode="after")
    def valid_media(self):
        _audio_reference(self.audio)
        return self


class AlignInput(BaseModel):
    audio: MediaReference
    text: str = Field(min_length=1, max_length=12000)
    confirmed_audio_rights: bool = False
    approved_for_paid_processing: bool = False

    @model_validator(mode="after")
    def valid_media(self):
        _audio_reference(self.audio)
        if not self.text.strip():
            raise ValueError("Alignment text cannot be blank")
        return self


def _audio_gate(rights: bool, approved: bool):
    if not rights:
        raise HTTPException(status_code=403, detail="Audio usage rights must be confirmed")
    if not approved:
        raise HTTPException(status_code=403, detail="Explicit paid processing approval required")


def _validate_words(data: dict, require_text: bool) -> dict:
    words = data.get("words")
    duration = data.get("duration_sec")
    credits = data.get("cost_credit")
    if (not isinstance(words, list) or type(credits) is not int or credits < 0 or
        type(duration) not in (int, float) or duration < 0):
        raise VisionStoryError("Invalid provider transcription metadata")
    if require_text and not isinstance(data.get("text"), str):
        raise VisionStoryError("Missing provider transcript text")
    for word in words:
        if not isinstance(word, dict) or type(word.get("start_sec")) not in (
            int, float
        ) or type(word.get("end_sec")) not in (int, float) or (
            word["end_sec"] < word["start_sec"]
        ) or not isinstance(word.get("text"), str):
            raise VisionStoryError("Invalid provider word timestamps")
    return data


@router.post("/audio/transcribe")
def transcribe_audio(req: CaptionInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    _audio_gate(req.confirmed_audio_rights, req.approved_for_paid_processing)

    def execute():
        client = configured_client()
        _check_credits(client, 1)
        result = client.transcribe_audio({
            "audio": _audio_reference(req.audio),
            "diarize": req.diarize,
            "srt": req.srt,
        })
        _validate_words(result, require_text=True)
        if req.srt and not isinstance(result.get("srt"), str):
            raise VisionStoryError("Requested SRT track missing")
        return {
            "text": result["text"],
            "words": result["words"],
            "srt": result.get("srt", ""),
            "language": result.get("language", ""),
            "duration_sec": result["duration_sec"],
            "cost_credit": result["cost_credit"],
            "diarization_requested": req.diarize,
            "srt_requested": req.srt,
            "automatic_retry": False,
        }

    return _paid(execute)


@router.post("/audio/align")
def align_audio(req: AlignInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    _audio_gate(req.confirmed_audio_rights, req.approved_for_paid_processing)

    def execute():
        client = configured_client()
        _check_credits(client, 1)
        result = client.align_audio({
            "audio": _audio_reference(req.audio), "text": req.text
        })
        _validate_words(result, require_text=False)
        return {
            "words": result["words"],
            "duration_sec": result["duration_sec"],
            "cost_credit": result["cost_credit"],
            "automatic_retry": False,
        }

    return _paid(execute)


class ClipInput(BaseModel):
    model_id: str = Field(min_length=3, max_length=160, pattern=r"^[a-zA-Z0-9_.-]+$")
    prompt: str = Field(min_length=1, max_length=20000)
    duration_sec: int = Field(ge=1, le=120)
    resolution: str = Field(min_length=3, max_length=12, pattern=r"^[a-zA-Z0-9]+$")
    aspect_ratio: str | None = Field(default=None, max_length=24)
    generate_audio: bool = True
    first_frame: MediaReference | None = None
    end_frame: MediaReference | None = None
    refs: list[MediaReference] = Field(default_factory=list, max_length=12)
    client_request_id: str = Field(min_length=8, max_length=128,
                                   pattern=r"^[a-zA-Z0-9_-]+$")
    confirmed_media_rights: bool = False
    approved_for_paid_generation: bool = False
    max_approved_credits: int = Field(default=0, ge=0, le=100000)

    @model_validator(mode="after")
    def check_exclusive_assets(self):
        if not self.prompt.strip():
            raise ValueError("Video prompt is blank")
        if self.first_frame is not None and self.refs:
            raise ValueError("Refs and first_frame cannot be combined")
        if self.end_frame is not None and self.first_frame is None:
            raise ValueError("end_frame requires first_frame")
        if self.aspect_ratio is not None and self.aspect_ratio not in (
            "9:16", "16:9", "1:1", "adaptive", "4:3", "3:4"
        ):
            raise ValueError("Unknown aspect ratio")
        all_refs = [
            x for x in (self.first_frame, self.end_frame) if x is not None
        ] + self.refs
        for ref in all_refs:
            if ref.url is not None:
                raise ValueError("Import reference URL to an owned asset_id first")
        return self


def _allowed_values(model: dict, key: str):
    params = model.get("params", {})
    entry = params.get(key, {}) if isinstance(params, dict) else {}
    values = entry.get("values") if isinstance(entry, dict) else None
    if values is None:
        values = model.get(key + "s")
    return values if isinstance(values, list) else None


def _validate_provider_model(client, req: ClipInput) -> None:
    catalog = client.ai_video_models().get("models")
    if not isinstance(catalog, list):
        raise VisionStoryError("Cannot verify the provider AI video model catalog", 424)
    model = next((
        item for item in catalog if isinstance(item, dict) and
        item.get("model_id") == req.model_id
    ), None)
    if model is None:
        raise VisionStoryError("AI video model is not available to the account", 422)
    for key, value in (
        ("duration_sec", req.duration_sec),
        ("resolution", req.resolution),
        ("aspect_ratio", req.aspect_ratio),
    ):
        if value is None:
            continue
        allowed = _allowed_values(model, key)
        if allowed is None or value not in allowed:
            raise VisionStoryError("Requested " + key + " is unsupported for this model", 422)
    params = model.get("params", {})
    max_prompt = (params.get("prompt", {}) or {}).get("max_length") if isinstance(params, dict) else None
    if type(max_prompt) is not int or len(req.prompt) > max_prompt:
        raise VisionStoryError("Prompt length not supported by model", 422)
    if req.refs:
        cap = (params.get("refs", {}) or {}) if isinstance(params, dict) else {}
        maximum = cap.get("max") if isinstance(cap, dict) else None
        if type(maximum) is not int or len(req.refs) > maximum:
            raise VisionStoryError("Reference quantity not supported by model", 422)

    # Model-specific restrictions documented by VisionStory. Validate before
    # estimating credits or initiating a paid provider operation.
    if req.model_id.startswith("wan-") and req.refs and req.aspect_ratio is not None:
        raise VisionStoryError("Wan refs cannot be combined with explicit aspect_ratio", 422)
    if req.model_id == "kling-3.0":
        if req.refs:
            raise VisionStoryError("Kling 3.0 does not accept refs", 422)
        if req.first_frame is not None and req.aspect_ratio is not None:
            raise VisionStoryError("Kling image-to-video forbids explicit aspect_ratio", 422)
    if req.model_id == "kling-3.0-omni":
        if req.first_frame is not None:
            raise VisionStoryError("Kling Omni cannot use first_frame", 422)
        if req.refs and req.generate_audio:
            # Provider forbids generate_audio when references include video.
            # Check directly identified inline video; asset_id kinds must be
            # verified using the owner's library rather than guessed.
            inline_video = any(
                x.inline_data is not None and
                x.inline_data.mime_type.startswith("video/") for x in req.refs
            )
            asset_ids = {
                x.asset_id for x in req.refs if x.asset_id is not None
            }
            found = {}
            if asset_ids:
                cursor = 0
                for _ in range(30):
                    query = "limit=100&cursor=" + str(cursor)
                    page = client.request("GET", "/api/v1/assets?" + query)
                    assets = page.get("assets")
                    if not isinstance(assets, list):
                        raise VisionStoryError("Cannot verify the reference asset kinds", 424)
                    for item in assets:
                        if isinstance(item, dict) and item.get("asset_id") in asset_ids:
                            found[item["asset_id"]] = item.get("kind")
                    if len(found) == len(asset_ids):
                        break
                    cursor = page.get("next_cursor", 0)
                    if type(cursor) is not int or cursor <= 0:
                        break
                if len(found) != len(asset_ids) or any(
                    k not in {"image", "video", "audio"} for k in found.values()
                ):
                    raise VisionStoryError("Unverified reference asset kinds", 422)
            if inline_video or "video" in found.values():
                raise VisionStoryError(
                    "Kling Omni video references require generate_audio=false", 422
                )
    if req.first_frame is not None:
        # A model may advertise no image-to-video support. Absent capability
        # metadata: fail closed rather than risk a paid provider rejection.
        image_to_video = model.get("image_to_video")
        if image_to_video is False:
            raise VisionStoryError("Selected model cannot accept first_frame", 422)


def _cost(client, req: ClipInput) -> int:
    quote = client.ai_video_cost(
        model_id=req.model_id, duration_sec=req.duration_sec,
        resolution=req.resolution, generate_audio=req.generate_audio,
    )
    credit = quote.get("credit")
    if type(credit) is not int or credit <= 0:
        raise VisionStoryError("Cannot determine a positive generation quote", 424)
    return credit


@router.post("/ai-video/estimate")
def estimate_video(req: ClipInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    def estimate():
        client = configured_client()
        _validate_provider_model(client, req)
        return {
            "model_id": req.model_id, "credits_estimated": _cost(client, req),
            "quoted_by": "visionstory", "generation_submitted": False,
        }
    return _paid(estimate)


@router.post("/ai-video")
def submit_video(req: ClipInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not req.confirmed_media_rights:
        raise HTTPException(status_code=403, detail="Media rights must be confirmed")
    if not req.approved_for_paid_generation:
        raise HTTPException(status_code=403, detail="Explicit paid generation approval required")

    def submit():
        client = configured_client()
        _validate_provider_model(client, req)
        estimated = _cost(client, req)
        if estimated > req.max_approved_credits:
            raise VisionStoryError("Quote exceeds approved credit budget", 409)
        _check_credits(client, estimated)
        payload = {
            "model_id": req.model_id, "prompt": req.prompt,
            "duration_sec": req.duration_sec, "resolution": req.resolution,
            "generate_audio": req.generate_audio,
            "client_request_id": req.client_request_id,
        }
        if req.aspect_ratio is not None:
            payload["aspect_ratio"] = req.aspect_ratio
        if req.first_frame is not None:
            payload["first_frame"] = req.first_frame.model_dump(exclude_none=True)
        if req.end_frame is not None:
            payload["end_frame"] = req.end_frame.model_dump(exclude_none=True)
        if req.refs:
            payload["refs"] = [r.model_dump(exclude_none=True) for r in req.refs]
        ledger = configured_ledger()
        existing = ledger.begin("ai_video", req.client_request_id, payload) if ledger else None
        if existing is not None:
            return {
                "video_id": existing, "status": "submitted",
                "client_request_id": req.client_request_id,
                "provider": "visionstory", "automatic_retry": False,
                "reused_existing_job": True, "durable_job_ledger": True,
            }
        try:
            result = client.create_ai_video(payload)
            video_id = result.get("video_id")
            if not isinstance(video_id, str) or not _ID.fullmatch(video_id):
                raise VisionStoryError("AI video provider omitted a valid video ID")
        except Exception:
            if ledger:
                ledger.mark_ambiguous("ai_video", req.client_request_id)
            raise
        if ledger:
            ledger.finish("ai_video", req.client_request_id, video_id)
        return {
            "video_id": video_id,
            "status": result.get("status", "queued"),
            "cost_credit": result.get("cost_credit"),
            "quoted_credit": estimated,
            "client_request_id": req.client_request_id,
            "provider": "visionstory",
            "automatic_retry": False,
            "requires_status_polling": True,
            "durable_job_ledger": ledger is not None,
        }
    return _paid(submit)


class VideoBatchRequest(BaseModel):
    video_ids: list[str] = Field(min_length=1, max_length=20)


@router.post("/ai-video/batch-status")
def ai_video_batch_status(
    req: VideoBatchRequest, authorization: str | None = Header(default=None)
):
    """Read-only batch polling. Up to twenty provider jobs per call."""
    _auth(authorization)
    if (any(not isinstance(v, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{3,160}", v) for v in req.video_ids) or
        len(set(req.video_ids)) != len(req.video_ids)):
        raise HTTPException(status_code=422, detail="Invalid or repeated video IDs")

    def query():
        result = configured_client().ai_video_batch_status(req.video_ids)
        videos = result.get("videos")
        if not isinstance(videos, list) or len(videos) > 20:
            raise VisionStoryError("Invalid batch status response from provider")
        cleaned = []
        expected = set(req.video_ids)
        for video in videos:
            if not isinstance(video, dict) or video.get("video_id") not in expected:
                raise VisionStoryError("Unexpected provider video ID in batch response")
            status = video.get("status")
            if status == "success":
                status = "created"
            if status not in _STATUS:
                raise VisionStoryError("Unexpected provider video job status")
            url = video.get("video_url")
            if url is not None and (
                not isinstance(url, str) or not url.startswith("https://")
            ):
                raise VisionStoryError("Invalid provider media URL")
            cleaned.append({
                "video_id": video["video_id"],
                "status": status,
                "video_url": url if status == "created" else None,
                "cost_credit": video.get("cost_credit"),
                "error": video.get("error") if status == "failed" else None,
            })
        return {"videos": cleaned, "poll_after_seconds": 5,
                "provider": "visionstory", "paid_generation_started": False}
    return _paid(query)


@router.get("/ai-video/{video_id}")
def ai_video_status(video_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not _ID.fullmatch(video_id):
        raise HTTPException(status_code=422, detail="Invalid AI video identifier")
    def status():
        data = configured_client().ai_video_status(video_id)
        state = data.get("status")
        if state == "success":
            state = "created"
        if state not in _STATUS:
            raise VisionStoryError("Unrecognized provider video status")
        url = data.get("video_url")
        if url is not None and (not isinstance(url, str) or not url.startswith("https://")):
            raise VisionStoryError("Invalid provider media URL")
        return {
            "video_id": video_id,
            "status": state,
            "video_url": url if state == "created" else None,
            "cost_credit": data.get("cost_credit"),
            "error": data.get("error") if state == "failed" else None,
            "poll_after_seconds": 5,
        }
    return _paid(status)
