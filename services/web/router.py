"""HTTP adapter for authorized, bounded web extraction and safe data wrappers."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from services.ai_studio.omni_orchestrator import _auth
from .scraper import (
    ScrapeBlocked, allowed_hosts_from_environment, extract_html,
    scrape_pages, make_api_wrapper,
)

router = APIRouter(prefix="/api/web", tags=["Website Studio"])


class SiteScanRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    max_pages: int = Field(default=3, ge=1, le=5)
    confirm_ownership: bool = False


@router.get("/capabilities")
def web_capabilities(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {
        "authorized_scraper": True,
        "html_structure_parser": True,
        "data_wrapper": True,
        "frontend_reconstruction": "structured_reference_only",
        "private_backend_extraction": False,
        "credential_extraction": False,
        "allowed_hosts_configured": bool(allowed_hosts_from_environment()),
    }


@router.post("/scrape")
def web_scrape(request: SiteScanRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not request.confirm_ownership:
        raise HTTPException(status_code=403, detail="Explicit ownership/permission acknowledgment required")
    try:
        return scrape_pages(request.url, allowed_hosts_from_environment(), max_pages=request.max_pages)
    except ScrapeBlocked as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ExtractRequest(BaseModel):
    html: str = Field(min_length=1, max_length=1_500_000)
    source_label: str = Field(default="user_supplied_document", max_length=256)


@router.post("/extract")
def web_extract(request: ExtractRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    return extract_html(request.html, request.source_label)


class WrapperRequest(BaseModel):
    snapshot: dict


@router.post("/wrapper")
def web_wrapper(request: WrapperRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        return make_api_wrapper(request.snapshot)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
