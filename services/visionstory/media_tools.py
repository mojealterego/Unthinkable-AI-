"""Licensed media import, portrait avatars, custom voices and AI image edits.

Never touches provider DELETE APIs. Inline input size is bounded more strictly
than some vendor maxima to prevent memory exhaustion at this gateway.
"""
from __future__ import annotations

import base64
import binascii
import re
from typing import Literal
from urllib.parse import urlencode

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from services.ai_studio.omni_orchestrator import _auth
from .client import VisionStoryError, configured_client
from .router import MediaReference, _media_public_url

router = APIRouter(prefix="/api/cinema/visionstory", tags=["VisionStory Media Tools"])


class UploadInline(BaseModel):
    mime_type: Literal[
        "image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic",
        "audio/mp3", "audio/mpeg", "audio/wav", "audio/m4a", "audio/mp4",
        "video/mp4",
    ]
    data: str = Field(min_length=4, max_length=18_700_000)

    @model_validator(mode="after")
    def bounded_base64(self):
        try:
            length = len(base64.b64decode(self.data, validate=True))
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Media must be raw valid base64") from exc
        if not 1 <= length <= 14_000_000:
            raise ValueError("Inline content may not exceed 14 MB")
        return self


class MediaUploadInput(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    inline_data: UploadInline | None = None
    confirmed_media_rights: bool = False
    approved_external_upload: bool = False

    @model_validator(mode="after")
    def validate_input(self):
        if (self.url is None) == (self.inline_data is None):
            raise ValueError("Exactly one media source is required")
        if self.url is not None:
            _media_public_url(self.url)
        return self


class PortraitAvatarInput(BaseModel):
    img_url: str | None = Field(default=None, max_length=2048)
    inline_data: UploadInline | None = None
    confirmed_image_rights: bool = False
    confirmed_subject_consent: bool = False
    approved_external_upload: bool = False

    @model_validator(mode="after")
    def image_only(self):
        if (self.img_url is None) == (self.inline_data is None):
            raise ValueError("Exactly one portrait image is required")
        if self.img_url is not None:
            _media_public_url(self.img_url)
        if self.inline_data is not None:
            if not self.inline_data.mime_type.startswith("image/"):
                raise ValueError("Avatar requires an image")
            if len(base64.b64decode(self.inline_data.data)) > 10_000_000:
                raise ValueError("Avatar portraits are limited to 10 MB")
        return self


class FrameInput(BaseModel):
    avatar_id: str = Field(min_length=3, max_length=160, pattern=r"^[a-zA-Z0-9_-]+$")
    aspect_ratio: Literal["9:16", "16:9", "1:1"]
    zoom: float = Field(ge=1, le=4)
    offset_x: float = Field(ge=-1, le=1)
    offset_y: float = Field(ge=-1, le=1)
    confirmed_framing_change: bool = False


class VoiceCloneInput(BaseModel):
    audio_url: str | None = Field(default=None, max_length=2048)
    inline_data: UploadInline | None = None
    preview_text: str | None = Field(default=None, max_length=500)
    confirmed_voice_owner_consent: bool = False
    approved_external_upload: bool = False

    @model_validator(mode="after")
    def voice_audio_only(self):
        if (self.audio_url is None) == (self.inline_data is None):
            raise ValueError("Exactly one voice sample is required")
        if self.audio_url is not None:
            _media_public_url(self.audio_url)
        if self.inline_data is not None and not self.inline_data.mime_type.startswith("audio/"):
            raise ValueError("Voice cloning requires audio")
        return self


class GenerateImageInput(BaseModel):
    model_id: str = Field(min_length=3, max_length=160, pattern=r"^[a-zA-Z0-9_.-]+$")
    prompt: str = Field(min_length=1, max_length=20000)
    aspect_ratio: str | None = Field(default=None, max_length=24)
    resolution: str | None = Field(default=None, max_length=20)
    refs: list[MediaReference] = Field(default_factory=list, max_length=14)
    confirmed_reference_rights: bool = False
    approved_for_paid_generation: bool = False
    max_approved_credits: int = Field(default=0, ge=0, le=100000)

    @model_validator(mode="after")
    def validate_refs(self):
        if not self.prompt.strip():
            raise ValueError("Image prompt cannot be blank")
        for ref in self.refs:
            if ref.inline_data is not None and not ref.inline_data.mime_type.startswith("image/"):
                raise ValueError("Image references must be images")
        return self


def _call(action):
    try:
        return action()
    except VisionStoryError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


def _confirm(rights: bool, permission: bool):
    if not rights:
        raise HTTPException(status_code=403, detail="Ownership and subject/media rights must be confirmed")
    if not permission:
        raise HTTPException(status_code=403, detail="Explicit approval required before provider transfer")


@router.get("/assets")
def assets(
    authorization: str | None = Header(default=None),
    kind: Literal["image", "audio", "video"] | None = None,
    limit: int = 20, cursor: int = 0,
):
    _auth(authorization)
    if not 1 <= limit <= 100 or cursor < 0:
        raise HTTPException(status_code=422, detail="Invalid asset pagination")
    query = {"limit": limit, "cursor": cursor}
    if kind is not None:
        query["kind"] = kind
    return _call(lambda: configured_client().request(
        "GET", "/api/v1/assets?" + urlencode(query)
    ))


@router.post("/assets/upload")
def upload_asset(req: MediaUploadInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    _confirm(req.confirmed_media_rights, req.approved_external_upload)
    payload = req.model_dump(exclude={
        "confirmed_media_rights", "approved_external_upload"
    }, exclude_none=True)

    def send():
        data = configured_client().request("POST", "/api/v1/asset", payload)
        if not isinstance(data.get("asset_id"), str):
            raise VisionStoryError("Provider did not return an asset ID")
        return {"asset_id": data["asset_id"], "provider": "visionstory"}
    return _call(send)


@router.post("/avatars/create")
def create_avatar(req: PortraitAvatarInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    _confirm(req.confirmed_image_rights and req.confirmed_subject_consent,
             req.approved_external_upload)
    payload = req.model_dump(exclude={
        "confirmed_image_rights", "confirmed_subject_consent", "approved_external_upload"
    }, exclude_none=True)

    def send():
        data = configured_client().request("POST", "/api/v1/avatar", payload)
        if not isinstance(data.get("avatar_id"), str):
            raise VisionStoryError("Provider did not return an avatar ID")
        return data
    return _call(send)


@router.post("/avatars/framing")
def change_avatar_framing(req: FrameInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not req.confirmed_framing_change:
        raise HTTPException(status_code=403, detail="Explicit framing modification approval required")

    def send():
        provider = configured_client()
        existing = provider.avatars()
        owned = existing.get("my_avatars")
        if owned is None:
            owned = existing.get("avatars")
        if not isinstance(owned, list) or not any(
            isinstance(row, dict) and row.get("avatar_id") == req.avatar_id
            for row in owned
        ):
            raise VisionStoryError("Avatar not found in owned-account catalog", 403)
        payload = req.model_dump(exclude={"confirmed_framing_change"})
        data = provider.request("POST", "/api/v1/avatar/framing", payload)
        if data.get("avatar_id") != req.avatar_id:
            raise VisionStoryError("Provider returned an unexpected avatar framing")
        return data
    return _call(send)


@router.post("/voices/clone")
def clone_voice(req: VoiceCloneInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    _confirm(req.confirmed_voice_owner_consent, req.approved_external_upload)
    payload = req.model_dump(exclude={
        "confirmed_voice_owner_consent", "approved_external_upload"
    }, exclude_none=True)

    def send():
        data = configured_client().request("POST", "/api/v1/voice", payload)
        if not isinstance(data.get("voice_id"), str):
            raise VisionStoryError("Provider did not return a cloned voice ID")
        return data
    return _call(send)


@router.post("/images/generate")
def generate_image(req: GenerateImageInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    _confirm(req.confirmed_reference_rights, req.approved_for_paid_generation)

    def create():
        provider = configured_client()
        models = provider.image_models().get("models")
        if not isinstance(models, list):
            raise VisionStoryError("Provider model catalog cannot be verified", 424)
        model = next((m for m in models if isinstance(m, dict) and
                      m.get("model_id") == req.model_id), None)
        if model is None:
            raise VisionStoryError("Requested image model not in live catalog", 422)
        params = model.get("params")
        params = params if isinstance(params, dict) else {}
        def allowed(field):
            entry = params.get(field)
            return entry.get("values") if isinstance(entry, dict) else None
        for field, value in (("aspect_ratio", req.aspect_ratio),
                             ("resolution", req.resolution)):
            if value is not None:
                options = allowed(field)
                if not isinstance(options, list) or value not in options:
                    raise VisionStoryError("Unsupported model parameter " + field, 422)
        allowed_prompt = params.get("prompt")
        max_prompt = allowed_prompt.get("max_length") if isinstance(allowed_prompt, dict) else None
        if type(max_prompt) is not int or len(req.prompt) > max_prompt:
            raise VisionStoryError("Unsupported prompt length", 422)
        ref_config = params.get("refs", {})
        max_refs = ref_config.get("max") if isinstance(ref_config, dict) else None
        if req.refs and (type(max_refs) is not int or len(req.refs) > max_refs):
            raise VisionStoryError("Reference count exceeds provider model limit", 422)
        prices = model.get("credit_by_resolution")
        price = prices.get(req.resolution) if req.resolution is not None and isinstance(prices, dict) else None
        if price is None and req.resolution is None:
            price = model.get("credit_per_image")
        if type(price) is not int or price <= 0:
            raise VisionStoryError("Cannot verify exact image price", 424)
        if price > req.max_approved_credits:
            raise VisionStoryError("Image price exceeds approved credit cap", 409)
        balance = provider.credits().get("remaining")
        if type(balance) is not int or balance < price:
            raise VisionStoryError("Provider credits insufficient or unverified", 402)
        payload = {
            "model_id": req.model_id, "prompt": req.prompt,
            **({"aspect_ratio": req.aspect_ratio} if req.aspect_ratio else {}),
            **({"resolution": req.resolution} if req.resolution else {}),
            **({"refs": [r.model_dump(exclude_none=True) for r in req.refs]}
                if req.refs else {}),
        }
        response = provider.request("POST", "/api/v1/image", payload)
        if not isinstance(response.get("url"), str) or not response["url"].startswith("https://"):
            raise VisionStoryError("No valid image URL returned by provider")
        return {
            "provider": "visionstory", "url": response["url"],
            "cost_credit": response.get("cost_credit"),
            "approved_credit_cap": req.max_approved_credits,
            "model_id": req.model_id,
            "automatic_retry": False, "stored_as_asset": False,
        }
    return _call(create)
