"""Safe NoCode website previews, ZIP export and snapshot-to-draft import."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from services.ai_studio.omni_orchestrator import _auth
from .builder import Site, render_page, export_site_zip, site_from_snapshot

router = APIRouter(prefix="/api/web/nocode", tags=["NoCode Website Creator"])
_PREVIEW_CSP = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; object-src 'none'; frame-ancestors 'none'"


class PreviewRequest(BaseModel):
    site: Site
    slug: str = Field(default="index", max_length=48)


@router.post("/preview", response_class=HTMLResponse)
def preview_site(request: PreviewRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        html = render_page(request.site, request.slug)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return HTMLResponse(html, headers={
        "Content-Security-Policy": _PREVIEW_CSP,
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
    })


@router.post("/export")
def download_site(site: Site, authorization: str | None = Header(default=None)):
    _auth(authorization)
    archive = export_site_zip(site)
    return Response(
        archive, media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="unthinkable-website.zip"',
                 "Cache-Control": "no-store"},
    )


class ImportSnapshotRequest(BaseModel):
    wrapper: dict


@router.post("/import-snapshot")
def import_snapshot(request: ImportSnapshotRequest, authorization: str | None = Header(default=None)):
    _auth(authorization)
    try:
        return site_from_snapshot(request.wrapper).model_dump()
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/templates")
def template_catalog(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {"themes": [
        {"id": "midnight", "label": "Ciemny fiolet"},
        {"id": "gold", "label": "Unthinkable Gold"},
        {"id": "light", "label": "Jasny minimalistyczny"},
    ], "sections": ["hero", "text", "features", "cta", "contact"],
        "export": ["html", "zip", "json"], "website_hosting_active": False,
        "backend_recreated": False}
