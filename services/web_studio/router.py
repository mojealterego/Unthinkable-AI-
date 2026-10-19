"""Web Studio API: scraper, NoCode site output, declarative API wrappers.

Requires existing gateway Bearer authentication. No implicit publishing.
"""
from __future__ import annotations

import base64
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from services.ai_studio.omni_orchestrator import _auth
from .scraper import inspect_html, fetch_authorized_page
from .nocode import SiteDesign, render_html, export_zip
from .wrapper import WrapperDesign, build_openapi

router = APIRouter(prefix="/api/web-studio", tags=["Web Studio"])


class HtmlInput(BaseModel):
    html: str = Field(min_length=1, max_length=1_048_576)
    base_url: str = Field(default="", max_length=2048)


class FetchInput(BaseModel):
    url: str = Field(min_length=12, max_length=2048)


@router.get("/capabilities")
def capabilities(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {
        "scraper": "admin_allowlisted_https_only",
        "html_inspection": True,
        "website_nocode": True,
        "site_zip_export": True,
        "api_wrapper_openapi": True,
        "database_cloning": False, "hidden_api_access": False,
        "automatic_deployment": False,
    }


@router.post("/scraper/inspect")
def inspect_uploaded_html(req: HtmlInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        return inspect_html(req.html, base_url=req.base_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/scraper/fetch")
def fetch_public_site(req: FetchInput, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        html = fetch_authorized_page(req.url)
        result = inspect_html(html, base_url=req.url)
        result["source_url"] = req.url
        result["fetch_mode"] = "allowlisted_https"
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (OSError, ValueError, TimeoutError) as exc:
        # Do not include raw server responses or URL credentials in errors.
        raise HTTPException(status_code=422, detail="Site cannot be fetched with current policy") from exc


@router.post("/wrapper/build")
def build_wrapper(req: WrapperDesign, authorization: str | None = Header(default=None)):
    _auth(authorization)
    return build_openapi(req)


@router.post("/nocode/render")
def render_site(req: SiteDesign, authorization: str | None = Header(default=None)):
    _auth(authorization)
    html = render_html(req)
    archive = export_zip(req)
    return {
        "format": "unthinkable-web-nocode-v1",
        "html": html,
        "zip_base64": base64.b64encode(archive).decode("ascii"),
        "site_name": req.name,
        "published": False,
        "includes_backend": False,
    }
