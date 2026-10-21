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
    # The vendor, not this app, determines max_zoom based on source dimensions.
    zoom: float = Field(ge=1, allow_inf_nan=False)
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


def _image_quote(provider, req: GenerateImageInput) -> tuple[int, str, str]:
    """Live provider catalog is the single authority on output price and options."""
    models = provider.image_models().get("models")
    if not isinstance(models, list):
        raise VisionStoryError("Provider image model catalog cannot be verified", 424)
    model = next((
        item for item in models
        if isinstance(item, dict) and item.get("model_id") == req.model_id
    ), None)
    if model is None:
        raise VisionStoryError("Image model is not available to this account", 422)
    params = model.get("params")
    if not isinstance(params, dict):
        raise VisionStoryError("Incomplete provider model limits", 424)

    def options(name: str) -> tuple[list, str | None]:
        section = params.get(name)
        if not isinstance(section, dict) or not isinstance(section.get("values"), list):
            raise VisionStoryError("Model lacks " + name + " limits", 424)
        return section["values"], section.get("default")

    resolutions, default_resolution = options("resolution")
    ratios, default_ratio = options("aspect_ratio")
    resolution = req.resolution if req.resolution is not None else default_resolution
    aspect_ratio = req.aspect_ratio if req.aspect_ratio is not None else default_ratio
    if not isinstance(resolution, str) or resolution not in resolutions:
        raise VisionStoryError("Unsupported image resolution", 422)
    if not isinstance(aspect_ratio, str) or aspect_ratio not in ratios:
        raise VisionStoryError("Unsupported image aspect ratio", 422)
    prompt_conf = params.get("prompt")
    length_cap = prompt_conf.get("max_length") if isinstance(prompt_conf, dict) else None
    if type(length_cap) is not int or len(req.prompt) > length_cap:
        raise VisionStoryError("Image prompt exceeds model limit", 422)
    refs_conf = params.get("refs")
    max_refs = refs_conf.get("max") if isinstance(refs_conf, dict) else None
    if req.refs and (type(max_refs) is not int or len(req.refs) > max_refs):
        raise VisionStoryError("Too many reference images", 422)

    price_by_resolution = model.get("credit_by_resolution")
    if isinstance(price_by_resolution, dict):
        price = price_by_resolution.get(resolution)
    elif resolution == default_resolution:
        price = model.get("credit_per_image")
    else:
        price = None
    if type(price) is not int or price <= 0:
        raise VisionStoryError("Exact resolution price not available", 424)
    return price, resolution, aspect_ratio


@router.post("/images/estimate")
def image_estimate(
    req: GenerateImageInput,
    authorization: str | None = Header(default=None),
):
    """No paid image generation: fresh model configuration and price only."""
    _auth(authorization)

    def quote():
        price, resolution, ratio = _image_quote(configured_client(), req)
        return {
            "provider": "visionstory", "model_id": req.model_id,
            "resolution": resolution, "aspect_ratio": ratio,
            "credits_estimated": price, "generation_submitted": False,
            "based_on_live_model_catalog": True,
        }
    return _call(quote)


@router.post("/images/generate")
def generate_image(
    req: GenerateImageInput,
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    _confirm(req.confirmed_reference_rights, req.approved_for_paid_generation)

    def create():
        provider = configured_client()
        price, resolution, aspect_ratio = _image_quote(provider, req)
        if price > req.max_approved_credits:
            raise VisionStoryError("Image price exceeds approved credit cap", 409)
        balance = provider.credits().get("remaining")
        if type(balance) is not int or balance < price:
            raise VisionStoryError("Provider credits insufficient or unverified", 402)
        payload = {
            "model_id": req.model_id,
            "prompt": req.prompt,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
        }
        if req.refs:
            payload["refs"] = [
                reference.model_dump(exclude_none=True) for reference in req.refs
            ]
        # Paid synchronous provider operation. Never retry on timeout.
        response = provider.request("POST", "/api/v1/image", payload)
        url = response.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise VisionStoryError("No valid image URL returned by provider")
        return {
            "provider": "visionstory", "url": url,
            "cost_credit": response.get("cost_credit"),
            "approved_credit_cap": req.max_approved_credits,
            "model_id": req.model_id,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "automatic_retry": False, "stored_as_asset": False,
        }
    return _call(create)
