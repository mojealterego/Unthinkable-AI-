"""Authenticated, read-only virtual-number tools.

Public DID availability, SIP calling, SMS and caller-ID presentation are NOT
provided until a carrier contract and authorization checks exist.
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from services.ai_studio.omni_orchestrator import _auth
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
