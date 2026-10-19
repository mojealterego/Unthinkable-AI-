"""VisionStory Speech Studio: MP3 synthesis, SRT transcription, word alignment."""
from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, Field, model_validator

from services.ai_studio.omni_orchestrator import _auth
from .client import VisionStoryError, configured_client
from .router import MediaReference

router = APIRouter(prefix="/api/cinema/visionstory/speech", tags=["VisionStory Speech"])


class SourceApproval(BaseModel):
    audio: MediaReference
    confirmed_audio_rights: bool = False
    approved_for_paid_generation: bool = False


class TranscribeRequest(SourceApproval):
    diarize: bool = False
    srt: bool = False


class AlignRequest(SourceApproval):
    text: str = Field(min_length=1, max_length=15000)

    @model_validator(mode="after")
    def nonempty_text(self):
        if not self.text.strip():
            raise ValueError("Expected exact spoken text")
        return self


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    voice_id: str = Field(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9_-]+$")
    locale: str | None = Field(default=None, max_length=35)
    speech_rate: Literal["normal", "slow", "fast"] = "normal"
    confirmed_voice_rights: bool = False
    approved_for_paid_generation: bool = False

    @model_validator(mode="after")
    def validate_text(self):
        if not self.text.strip():
            raise ValueError("TTS text cannot be blank")
        if self.locale is not None and not re.fullmatch(
            r"[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){0,3}", self.locale
        ):
            raise ValueError("Invalid BCP-47 locale")
        return self


def _preflight(rights: bool, approval: bool):
    if not rights:
        raise HTTPException(status_code=403, detail="Confirm rights to the audio or voice")
    if not approval:
        raise HTTPException(status_code=403, detail="Explicit credit-cost approval is required")
    try:
        provider = configured_client()
        remaining = provider.credits().get("remaining")
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    if type(remaining) is not int:
        raise HTTPException(status_code=424, detail="Unable to verify provider credits")
    if remaining <= 0:
        raise HTTPException(status_code=402, detail="Insufficient VisionStory credits")
    return provider


@router.post("/transcribe")
def transcribe(req: TranscribeRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    provider = _preflight(req.confirmed_audio_rights, req.approved_for_paid_generation)
    try:
        result = provider.transcribe_audio({
            "audio": req.audio.model_dump(exclude_none=True),
            "diarize": req.diarize, "srt": req.srt,
        })
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    if not isinstance(result.get("text"), str) or not isinstance(result.get("words"), list):
        raise HTTPException(status_code=502, detail="Invalid transcription response")
    if req.srt and not isinstance(result.get("srt"), str):
        raise HTTPException(status_code=502, detail="Provider did not return requested subtitles")
    return {
        "text": result["text"], "language": result.get("language"),
        "words": result["words"], "srt": result.get("srt") if req.srt else None,
        "duration_sec": result.get("duration_sec"),
        "cost_credit": result.get("cost_credit"), "retry_after_timeout": False,
    }


@router.post("/align")
def align(req: AlignRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    provider = _preflight(req.confirmed_audio_rights, req.approved_for_paid_generation)
    try:
        result = provider.align_audio({
            "audio": req.audio.model_dump(exclude_none=True), "text": req.text,
        })
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    if not isinstance(result.get("words"), list):
        raise HTTPException(status_code=502, detail="Invalid word-alignment response")
    return {"words": result["words"], "duration_sec": result.get("duration_sec"),
            "cost_credit": result.get("cost_credit"), "retry_after_timeout": False}


@router.post("/tts")
def tts(req: TtsRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    provider = _preflight(req.confirmed_voice_rights, req.approved_for_paid_generation)
    try:
        audio, stats = provider.synthesize_mp3({
            "text": req.text, "voice_id": req.voice_id,
            "speech_rate": req.speech_rate,
            **({"locale": req.locale} if req.locale else {}),
        })
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    if not isinstance(audio, bytes) or len(audio) > 20_000_000 or not (
        audio.startswith(b"ID3") or
        (len(audio) >= 2 and audio[0] == 255 and audio[1] & 0xE0 == 0xE0)
    ):
        raise HTTPException(status_code=502, detail="Invalid MP3 response")
    return Response(audio, media_type="audio/mpeg", headers={
        "Content-Disposition": 'attachment; filename="visionstory-speech.mp3"',
        "Cache-Control": "private, no-store",
        "X-Cost-Credit": str(stats["cost_credit"]),
        "X-Usage-Characters": str(stats["usage_characters"]),
        "X-Audio-Duration-Sec": str(stats["duration_sec"]),
    })
