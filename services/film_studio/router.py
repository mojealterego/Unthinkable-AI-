"""First-party Film Studio routes, independent of third-party video providers."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import FileResponse

from services.ai_studio.omni_orchestrator import _auth
from .engine import (
    ASSET_LIMIT, SUFFIXES, FilmEngineError, Timeline, enqueue, get_job,
    list_assets, register_asset, root_dir, verify_timeline,
)

router = APIRouter(prefix="/api/film-studio", tags=["Own Film Studio"])


def _handle(action):
    try:
        return action()
    except FilmEngineError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc


@router.get("/capabilities")
def capabilities(authorization: str | None = Header(default=None)):
    _auth(authorization)
    ffmpeg = shutil.which("ffmpeg") is not None
    try:
        root_dir()
        storage = True
    except FilmEngineError:
        storage = False
    return {
        "provider": "unthinkable_self_hosted",
        "external_accounts_required": False,
        "third_party_credits": False,
        "local_media_import": True,
        "timeline_editing": ffmpeg and storage,
        "mp3_music_video_assembly": ffmpeg and storage,
        "reference_images_as_stills": ffmpeg and storage,
        "local_ffmpeg_ready": ffmpeg,
        "private_storage_ready": storage,
        "native_wan_ai_inference": False,
        "avatar_identity_model": False,
        "face_swap_model": False,
        "long_film_assembly": ffmpeg and storage,
        "max_duration_seconds": 43200,
        "per_asset_size_limit_bytes": ASSET_LIMIT,
    }


@router.post("/assets", status_code=201)
async def upload_asset(request: Request, authorization: str | None = Header(default=None)):
    _auth(authorization)
    mime = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if mime not in SUFFIXES:
        raise HTTPException(status_code=415, detail="Supported: MP4, MP3, WAV, JPEG, PNG")
    try:
        base = root_dir()
    except FilmEngineError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc)) from exc
    count = 0
    with tempfile.NamedTemporaryFile(dir=base / "assets",
                                    prefix=".upload-", suffix=".partial",
                                    delete=False) as handle:
        pending = Path(handle.name)
        try:
            async for chunk in request.stream():
                count += len(chunk)
                if count > ASSET_LIMIT:
                    raise HTTPException(status_code=413, detail="Media upload exceeds 160 MiB")
                handle.write(chunk)
            handle.flush()
            return _handle(lambda: register_asset(base, pending, mime, count))
        finally:
            pending.unlink(missing_ok=True)


@router.get("/assets")
def get_assets(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _handle(lambda: {"assets": list_assets(root_dir())})


@router.post("/timeline/validate")
def validate_timeline(timeline: Timeline, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not timeline.confirm_media_rights:
        raise HTTPException(status_code=403, detail="Media rights and permissions must be confirmed")
    return _handle(lambda: {"status": "valid", **verify_timeline(root_dir(), timeline)})


@router.post("/timeline/render", status_code=202)
def start_render(timeline: Timeline, authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not timeline.confirm_media_rights:
        raise HTTPException(status_code=403, detail="Media rights and permissions must be confirmed")
    return _handle(lambda: enqueue(root_dir(), timeline))


@router.get("/jobs/{job_id}")
def job_status(job_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _handle(lambda: get_job(root_dir(), job_id))


@router.get("/jobs/{job_id}/file")
def job_file(job_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    base = _handle(root_dir)
    job = _handle(lambda: get_job(base, job_id))
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Film is not completed")
    path = base / "jobs" / job["output_file"]
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=404, detail="Film MP4 unavailable")
    return FileResponse(path, media_type="video/mp4",
                        filename="unthinkable-" + job_id + ".mp4",
                        headers={"Cache-Control": "private, no-store"})
