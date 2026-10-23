"""First-party Unthinkable Cinema: local media ingestion and FFmpeg edit/render.

Does not call VisionStory or any other media generation API.
Owned media is referenced by opaque IDs, not user-supplied paths/URLs.
This is a real cut/concat + soundtrack render worker, NOT a full NLE or AI model.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from services.ai_studio.omni_orchestrator import _auth

router = APIRouter(prefix="/api/cinema/owned", tags=["Unthinkable Cinema - owned"])
_ID = re.compile(r"^[A-Za-z0-9_-]{5,96}$")
_VIDEO = ("mp4", "mov")
_AUDIO = ("mp3", "wav", "m4a")
_TYPES = {
    "mp4": "video/mp4", "mov": "video/quicktime",
    "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
}
_MAX_ASSET = 512 * 1024 * 1024
_MAX_PROJECT_MS = 12 * 60 * 60 * 1000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _root() -> Path:
    raw = os.environ.get("UNTHINKABLE_CINEMA_MEDIA_DIR", "").strip()
    if not raw or not os.path.isabs(raw):
        raise HTTPException(503, "Configure a private absolute UNTHINKABLE_CINEMA_MEDIA_DIR")
    root = Path(raw)
    if root.is_symlink():
        raise HTTPException(503, "The cinema media root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name in ("assets", "jobs", "renders"):
        folder = root / name
        if folder.is_symlink():
            raise HTTPException(503, "Media storage cannot use symlink directories")
        folder.mkdir(exist_ok=True, mode=0o700)
    return root


def _asset(root: Path, asset_id: str, *, extensions: tuple[str, ...]) -> Path:
    if not _ID.fullmatch(asset_id):
        raise HTTPException(422, "Invalid owned asset identifier")
    available = [root / "assets" / (asset_id + "." + ext) for ext in extensions]
    matches = [p for p in available if p.is_file() and not p.is_symlink()]
    if len(matches) != 1:
        raise HTTPException(422, "Asset missing or ambiguous in the owned media library")
    return matches[0]


class EditClip(BaseModel):
    asset_id: str = Field(min_length=5, max_length=96, pattern=_ID.pattern)
    trim_start_ms: int = Field(ge=0, le=_MAX_PROJECT_MS)
    duration_ms: int = Field(gt=0, le=3_600_000)


class EditProject(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    clips: list[EditClip] = Field(min_length=1, max_length=2000)
    soundtrack_asset_id: str | None = Field(
        default=None, min_length=5, max_length=96, pattern=_ID.pattern
    )
    width: int = 1280
    height: int = 720
    fps: int = 25

    @model_validator(mode="after")
    def validate_timeline(self):
        if (self.width, self.height) not in {
            (1280, 720), (720, 1280), (1920, 1080), (1080, 1920)
        } or self.fps not in (24, 25, 30):
            raise ValueError("Unsupported output dimensions or FPS")
        if sum(c.duration_ms for c in self.clips) > _MAX_PROJECT_MS:
            raise ValueError("Timeline exceeds the 12-hour edit limit")
        return self

    @property
    def total_ms(self) -> int:
        return sum(c.duration_ms for c in self.clips)


class RenderRequest(BaseModel):
    project: EditProject
    request_id: str = Field(min_length=8, max_length=96, pattern=r"^[A-Za-z0-9_-]+$")
    approved_for_local_render: bool = False
    confirmed_media_rights: bool = False


def _json_atomic(path: Path, data: dict) -> None:
    temp = path.parent / ("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _job(root: Path, request_id: str) -> Path:
    if not _ID.fullmatch(request_id):
        raise HTTPException(422, "Invalid render identifier")
    return root / "jobs" / (request_id + ".json")


def _inputs(root: Path, project: EditProject) -> tuple[list[Path], Path | None]:
    clips = [_asset(root, item.asset_id, extensions=_VIDEO) for item in project.clips]
    audio = (
        _asset(root, project.soundtrack_asset_id, extensions=_AUDIO)
        if project.soundtrack_asset_id is not None else None
    )
    return clips, audio


def ffmpeg_arguments(
    project: EditProject, clip_paths: list[Path], soundtrack: Path | None,
    output_path: Path, *, binary: str = "ffmpeg",
) -> list[str]:
    """Exact argv (no shell, no dynamic user filter expressions)."""
    if len(clip_paths) != len(project.clips):
        raise ValueError("Clip inputs do not match the edit timeline")
    args = [binary, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
    for path in clip_paths:
        args += ["-protocol_whitelist", "file,pipe", "-i", str(path)]
    if soundtrack is not None:
        args += ["-protocol_whitelist", "file,pipe", "-i", str(soundtrack)]
    filters = []
    inputs = []
    for index, clip in enumerate(project.clips):
        start = clip.trim_start_ms / 1000
        duration = clip.duration_ms / 1000
        filters.append(
            f"[{index}:v:0]trim=start={start:.3f}:duration={duration:.3f},"
            f"setpts=PTS-STARTPTS,fps={project.fps},"
            f"scale={project.width}:{project.height}:force_original_aspect_ratio=decrease,"
            f"pad={project.width}:{project.height}:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,format=yuv420p[v{index}]"
        )
        inputs.append(f"[v{index}]")
    filters.append("".join(inputs) + f"concat=n={len(inputs)}:v=1:a=0[vout]")
    if soundtrack is not None:
        index = len(clip_paths)
        filters.append(
            f"[{index}:a:0]atrim=duration={project.total_ms / 1000:.3f},"
            "asetpts=PTS-STARTPTS,"
            f"apad=pad_dur={project.total_ms / 1000:.3f}[aout]"
        )
    args += [
        "-filter_complex", ";".join(filters), "-map", "[vout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ]
    if soundtrack is not None:
        args += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    else:
        args += ["-an"]
    args += ["-t", f"{project.total_ms / 1000:.3f}", str(output_path)]
    return args


def _execute(root: Path, render_id: str, project: EditProject) -> None:
    job_path = _job(root, render_id)
    lock_file = root / "worker.lock"
    temp_output = root / "renders" / ("." + render_id + ".partial.mp4")
    final_output = root / "renders" / (render_id + ".mp4")
    with lock_file.open("a+b") as worker_lock:
        try:
            fcntl.flock(worker_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            info = json.loads(job_path.read_text(encoding="utf-8"))
            info.update(status="blocked", detail="Render worker is occupied", updated_at=_now())
            _json_atomic(job_path, info)
            return
        info = json.loads(job_path.read_text(encoding="utf-8"))
        try:
            info.update(status="running", updated_at=_now())
            _json_atomic(job_path, info)
            ffmpeg = shutil.which("ffmpeg")
            if ffmpeg is None:
                raise RuntimeError("FFmpeg binary is not installed in the owned media worker")
            clips, soundtrack = _inputs(root, project)
            argv = ffmpeg_arguments(project, clips, soundtrack, temp_output, binary=ffmpeg)
            # FFmpeg is isolated to explicitly referenced, local assets.
            completed = subprocess.run(
                argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, timeout=3600, check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError("FFmpeg rendering failed; check source codecs and trim limits")
            if not temp_output.is_file() or temp_output.stat().st_size < 12:
                raise RuntimeError("FFmpeg produced no valid output")
            with temp_output.open("rb") as stream:
                if stream.read(12)[4:8] != b"ftyp":
                    raise RuntimeError("Result is not an MP4 container")
            os.replace(temp_output, final_output)
            info.update(
                status="completed", updated_at=_now(),
                duration_ms=project.total_ms, output_bytes=final_output.stat().st_size,
                download_path=f"/api/cinema/owned/renders/{render_id}/file",
            )
        except (RuntimeError, OSError, subprocess.TimeoutExpired, HTTPException):
            info.update(status="failed", detail="Local render failed; inspect media worker logs",
                        updated_at=_now())
        finally:
            _json_atomic(job_path, info)
            temp_output.unlink(missing_ok=True)
            fcntl.flock(worker_lock.fileno(), fcntl.LOCK_UN)


@router.get("/capabilities")
def capabilities(authorization: str | None = Header(default=None)):
    _auth(authorization)
    return {
        "product": "Unthinkable Cinema",
        "primary": True,
        "provider": "self_hosted_ffmpeg",
        "external_provider_required": False,
        "external_api_keys_required": False,
        "features": ["local_asset_ingest", "cut", "concatenate",
                     "resize_and_pad", "soundtrack_mp3_wav_m4a", "mp4_export"],
        "video_model_inference": False,
        "advanced_multitrack_nle": False,
        "gpu_worker": False,
        "render_requires_explicit_approval": True,
    }


@router.put("/assets/{asset_id}")
async def upload_asset(
    asset_id: str, request: Request, extension: str,
    authorization: str | None = Header(default=None),
):
    _auth(authorization)
    root = _root()
    if not _ID.fullmatch(asset_id) or extension not in _TYPES:
        raise HTTPException(422, "Unsupported media asset identifier or type")
    expected = _TYPES[extension]
    mime = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if mime != expected:
        raise HTTPException(415, "Media MIME does not match the file extension")
    target = root / "assets" / f"{asset_id}.{extension}"
    if target.exists() or target.is_symlink():
        raise HTTPException(409, "Asset already exists; use a new asset ID")
    temp = root / "assets" / ("." + uuid.uuid4().hex + ".upload")
    total = 0
    digest = hashlib.sha256()
    try:
        with temp.open("xb") as output:
            async for part in request.stream():
                total += len(part)
                if total > _MAX_ASSET:
                    raise HTTPException(413, "Asset exceeds 512 MiB upload limit")
                digest.update(part)
                output.write(part)
        if total < 12:
            raise HTTPException(422, "Media file is empty or incomplete")
        with temp.open("rb") as f:
            header = f.read(12)
        if extension in ("mp4", "mov", "m4a") and header[4:8] != b"ftyp":
            raise HTTPException(422, "Media is not a supported ISO BMFF container")
        if extension == "wav" and (header[:4] != b"RIFF" or header[8:12] != b"WAVE"):
            raise HTTPException(422, "Media is not a RIFF/WAVE file")
        if extension == "mp3" and (
            header[:3] != b"ID3" and (header[0] != 0xFF or (header[1] & 0xE0) != 0xE0)
        ):
            raise HTTPException(422, "Media does not have an MP3 signature")
        # Atomic create, never replace a media file supplied earlier.
        try:
            os.link(temp, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise HTTPException(409, "Asset ID was registered concurrently") from exc
        return {"asset_id": asset_id, "extension": extension,
                "bytes": total, "sha256": digest.hexdigest(), "source": "user_owned"}
    finally:
        temp.unlink(missing_ok=True)


@router.post("/renders")
def start_render(req: RenderRequest, background: BackgroundTasks,
                 authorization: str | None = Header(default=None)):
    _auth(authorization)
    if not req.confirmed_media_rights or not req.approved_for_local_render:
        raise HTTPException(403, "Confirm asset rights and explicitly approve local compute")
    root = _root()
    _inputs(root, req.project)
    path = _job(root, req.request_id)
    fingerprint = hashlib.sha256(
        json.dumps(req.project.model_dump(), sort_keys=True).encode("utf-8")
    ).hexdigest()
    if path.is_file():
        current = json.loads(path.read_text(encoding="utf-8"))
        if current.get("fingerprint") != fingerprint:
            raise HTTPException(409, "Render ID already belongs to another timeline")
        return {"render_id": req.request_id, "status": current.get("status"),
                "reused": True, "provider": "self_hosted_ffmpeg"}
    record = {
        "render_id": req.request_id, "status": "queued", "created_at": _now(),
        "updated_at": _now(), "fingerprint": fingerprint,
        "duration_ms": req.project.total_ms, "provider": "self_hosted_ffmpeg",
    }
    # Exclusive creation prevents duplicate submissions without database dependency.
    try:
        with path.open("x", encoding="utf-8") as stream:
            json.dump(record, stream)
    except FileExistsError:
        return {"render_id": req.request_id, "status": "queued", "reused": True,
                "provider": "self_hosted_ffmpeg"}
    background.add_task(_execute, root, req.request_id, req.project)
    return {"render_id": req.request_id, "status": "queued", "reused": False,
            "duration_ms": req.project.total_ms, "provider": "self_hosted_ffmpeg"}


@router.get("/renders/{render_id}")
def render_status(render_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    path = _job(_root(), render_id)
    if not path.is_file():
        raise HTTPException(404, "Local render job does not exist")
    record = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in record.items() if key != "fingerprint"}


@router.get("/renders/{render_id}/file")
def render_file(render_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    root = _root()
    status = render_status(render_id, authorization)
    if status.get("status") != "completed":
        raise HTTPException(409, "Local render has not completed")
    path = root / "renders" / (render_id + ".mp4")
    if path.is_symlink() or not path.is_file():
        raise HTTPException(404, "Rendered MP4 file is missing")
    return FileResponse(
        path, media_type="video/mp4", filename=render_id + ".mp4",
        headers={"Cache-Control": "private, no-store"},
    )
