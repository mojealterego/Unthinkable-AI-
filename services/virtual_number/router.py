"""Authenticated, read-only virtual-number tools.

Public DID availability, SIP calling, SMS and caller-ID presentation are NOT
provided until a carrier contract and authorization checks exist.
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from services.ai_studio.omni_orchestrator import _auth
from services.virtual_number.store import ClaimConflict, configured_alias_store
from services.virtual_number.vanity import (
    classify_alias, suggest_internal_aliases,
)

router = APIRouter(prefix="/api/virtual-number", tags=["Virtual Number"])


class ScoreRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=40)


class SuggestRequest(BaseModel):
    prefix: str = Field(default="", max_length=15)
    length: int = Field(default=9, ge=4, le=18)
    style: Literal["random", "repeated", "pairs", "sequence"] = "repeated"
    count: int = Field(default=10, ge=1, le=30)


@router.get("/capabilities")
def capabilities(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {
        "engine": "on_net_alias_preview_v1",
        "on_net_alias_generation": True,
        "score_heuristic": True,
        "public_did_inventory_connected": False,
        "public_number_reservation": False,
        "outbound_pstn_enabled": False,
        "sms_mms_enabled": False,
        "caller_id_unverified_allowed": False,
    }


@router.post("/score")
def score(req: ScoreRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        return classify_alias(req.identifier).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/suggest")
def suggest(req: SuggestRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        candidates = suggest_internal_aliases(
            prefix=req.prefix, length=req.length, style=req.style, count=req.count
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "candidates": [item.to_dict() for item in candidates],
        "scope": "on_net_only",
        "carrier_checked": False,
        "numbers_reserved": False,
    }

class ClaimRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=30)
    ttl_seconds: int = Field(default=3600, ge=60, le=86400)


def _store():
    try:
        return configured_alias_store()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="On-net reservation storage not configured") from exc


@router.post("/on-net/claim")
def claim_onnet(req: ClaimRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    store, owner = _store()
    try:
        return store.claim(req.identifier, owner_scope=owner, ttl_seconds=req.ttl_seconds)
    except ClaimConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/on-net/claims")
def onnet_claims(authorization: str | None = Header(default=None)):
    _auth(authorization)
    store, owner = _store()
    return {"claims": store.list_claims(owner_scope=owner), "scope": "on_net_only"}


@router.delete("/on-net/claims/{identifier}")
def release_onnet(identifier: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    store, owner = _store()
    try:
        return {"released": store.release(identifier, owner_scope=owner)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
