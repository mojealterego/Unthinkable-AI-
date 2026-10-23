"""First-party Unthinkable Film Studio. No VisionStory, cloud account or credits.

Authenticated uploads and an FFmpeg-only timeline composer. Runs on the
operator's own host, optional offline. AI model inference (Wan/LTX/ODYN),
face-swap, beat alignment and 3-D avatars are separate workers, NOT claimed
by this module. Each job renders actual MP4 when FFmpeg is installed.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ASSET_LIMIT = 160 * 1024 * 1024
SUFFIXES = {
    "video/mp4": (".mp4", "video"),
    "image/jpeg": (".jpg", "image"),
    "image/png": (".png", "image"),
    "audio/mpeg": (".mp3", "audio"),
    "audio/wav": (".wav", "audio"),
}
_UUID = __import__("re").compile(r"^[a-f0-9]{32}$")
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="own-film-render")
_DB_LOCK = threading.RLock()


class FilmEngineError(Exception):
    def __init__(self, detail: str, status: int = 422):
        super().__init__(detail)
        self.status = status


class Shot(BaseModel):
    asset_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    duration_seconds: int = Field(ge=1, le=3600)
    name: str = Field(min_length=1, max_length=200)
    reference_asset_ids: list[str] = Field(default_factory=list, max_length=16)


class Timeline(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    shots: list[Shot] = Field(min_length=1, max_length=2000)
    soundtrack_asset_id: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{32}$"
    )
    output_width: Literal[640, 1280, 1920] = 1280
    fps: Literal[24, 25, 30] = 24
    confirm_media_rights: bool = False

    @model_validator(mode="after")
    def validate_timeline(self):
        if sum(s.duration_seconds for s in self.shots) > 43200:
            raise ValueError("Timeline cannot exceed 12 hours")
        for s in self.shots:
            if any(not _UUID.fullmatch(a) for a in s.reference_asset_ids):
                raise ValueError("Invalid reference asset identifier")
        return self


def root_dir() -> Path:
    raw = os.environ.get("UNTHINKABLE_FILM_ROOT", "").strip()
    if not raw or not os.path.isabs(raw):
        raise FilmEngineError("Set UNTHINKABLE_FILM_ROOT to a private absolute path", 503)
    path = Path(raw)
    if path.is_symlink():
        raise FilmEngineError("Film root must not be a symlink", 503)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    for sub in ("assets", "jobs"):
        folder = path / sub
        if folder.is_symlink():
            raise FilmEngineError("Film storage directory must not be a symlink", 503)
        folder.mkdir(exist_ok=True, mode=0o700)
    return path


def _connect(base: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(base / "film_studio.sqlite3"), timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY, filename TEXT NOT NULL, kind TEXT NOT NULL,
        size_bytes INTEGER NOT NULL, created_at REAL NOT NULL
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, status TEXT NOT NULL,
        title TEXT NOT NULL, output_file TEXT,
        error TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL
    )""")
    connection.commit()
    return connection


def _check_magic(path: Path, mime: str) -> None:
    with path.open("rb") as stream:
        start = stream.read(16)
    valid = {
        "video/mp4": len(start) >= 12 and start[4:8] == b"ftyp",
        "image/jpeg": start.startswith(b"\xff\xd8\xff"),
        "image/png": start.startswith(b"\x89PNG\r\n\x1a\n"),
        "audio/mpeg": start.startswith(b"ID3") or (
            len(start) >= 2 and start[0] == 0xff and start[1] & 0xe0 == 0xe0
        ),
        "audio/wav": start.startswith(b"RIFF") and start[8:12] == b"WAVE",
    }.get(mime, False)
    if not valid:
        raise FilmEngineError("Uploaded content does not match selected media type")


def register_asset(base: Path, temporary_file: Path, mime: str, count: int) -> dict:
    if mime not in SUFFIXES or count < 12 or count > ASSET_LIMIT:
        raise FilmEngineError("Invalid media type or size")
    _check_magic(temporary_file, mime)
    asset_id = uuid.uuid4().hex
    suffix, kind = SUFFIXES[mime]
    destination = base / "assets" / (asset_id + suffix)
    with _DB_LOCK:
        temporary_file.replace(destination)
        try:
            with _connect(base) as db:
                db.execute("INSERT INTO assets VALUES (?,?,?,?,?)",
                           (asset_id, destination.name, kind, count, time.time()))
        except Exception:
            destination.unlink(missing_ok=True)
            raise
    return {"asset_id": asset_id, "kind": kind, "bytes": count,
            "filename": destination.name}


def list_assets(base: Path) -> list[dict]:
    with _connect(base) as db:
        return [dict(row) for row in db.execute(
            "SELECT id, kind, size_bytes, created_at FROM assets ORDER BY created_at DESC LIMIT 500"
        )]


def _asset(base: Path, asset_id: str, kinds: set[str]) -> Path:
    if not _UUID.fullmatch(asset_id):
        raise FilmEngineError("Invalid asset ID")
    with _connect(base) as db:
        row = db.execute(
            "SELECT filename,kind FROM assets WHERE id=?", (asset_id,)
        ).fetchone()
    if row is None or row["kind"] not in kinds:
        raise FilmEngineError("Media asset is missing or incompatible")
    p = base / "assets" / row["filename"]
    if p.is_symlink() or not p.is_file():
        raise FilmEngineError("Media asset is not accessible")
    return p


def verify_timeline(base: Path, timeline: Timeline) -> dict:
    for shot in timeline.shots:
        _asset(base, shot.asset_id, {"video", "image"})
        for asset in shot.reference_asset_ids:
            _asset(base, asset, {"image"})
    if timeline.soundtrack_asset_id is not None:
        _asset(base, timeline.soundtrack_asset_id, {"audio"})
    return {"duration_seconds": sum(s.duration_seconds for s in timeline.shots),
            "shots": len(timeline.shots), "soundtrack": bool(timeline.soundtrack_asset_id)}


def _run_ffmpeg(ffmpeg: str, args: list[str], *, timeout: int) -> None:
    command = [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y"] + args
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FilmEngineError("Own FFmpeg worker failed or timed out", 503) from exc
    if result.returncode != 0:
        raise FilmEngineError("FFmpeg could not render this clip; check codecs and source assets")


def render_timeline(base: Path, timeline: Timeline, target: Path,
                    *, ffmpeg: str | None = None) -> None:
    """Actual CPU timeline compositor: normalize, concatenate, mux MP3/WAV."""
    binary = ffmpeg or shutil.which("ffmpeg")
    if not binary:
        raise FilmEngineError("FFmpeg is not installed on this own media worker", 503)
    verify_timeline(base, timeline)
    width = timeline.output_width
    height = width * 9 // 16
    with tempfile.TemporaryDirectory(dir=base / "jobs", prefix="render-") as work:
        workdir = Path(work)
        normalized: list[Path] = []
        for index, shot in enumerate(timeline.shots):
            source = _asset(base, shot.asset_id, {"video", "image"})
            is_image = source.suffix.lower() in (".jpg", ".png")
            out = workdir / ("shot_%04d.mp4" % index)
            input_args = (["-loop", "1", "-framerate", str(timeline.fps)] if is_image
                          else ["-stream_loop", "-1"]) + ["-i", str(source)]
            filter_chain = (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"fps={timeline.fps},format=yuv420p"
            )
            _run_ffmpeg(binary, input_args + [
                "-map", "0:v:0", "-t", str(shot.duration_seconds), "-an",
                "-vf", filter_chain, "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "24", "-pix_fmt", "yuv420p", str(out),
            ], timeout=max(180, shot.duration_seconds * 15))
            normalized.append(out)
        listing = workdir / "clips.ffconcat"
        listing.write_text(
            "ffconcat version 1.0\n" +
            "".join("file '" + p.name + "'\n" for p in normalized),
            encoding="utf-8",
        )
        joined = workdir / "joined.mp4"
        _run_ffmpeg(binary, [
            "-safe", "0", "-f", "concat", "-i", str(listing),
            "-c", "copy", "-movflags", "+faststart", str(joined),
        ], timeout=max(180, sum(s.duration_seconds for s in timeline.shots) * 2))
        if timeline.soundtrack_asset_id:
            audio = _asset(base, timeline.soundtrack_asset_id, {"audio"})
            final = workdir / "with_sound.mp4"
            _run_ffmpeg(binary, [
                "-i", str(joined), "-stream_loop", "-1", "-i", str(audio),
                "-map", "0:v:0", "-map", "1:a:0", "-t",
                str(sum(s.duration_seconds for s in timeline.shots)),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", str(final),
            ], timeout=max(180, sum(s.duration_seconds for s in timeline.shots) * 2))
            final.replace(target)
        else:
            joined.replace(target)


def enqueue(base: Path, timeline: Timeline) -> dict:
    if not shutil.which("ffmpeg"):
        raise FilmEngineError("This server has no first-party FFmpeg renderer", 503)
    verification = verify_timeline(base, timeline)
    with _DB_LOCK:
        with _connect(base) as db:
            pending = db.execute(
                "SELECT count(*) FROM jobs WHERE status IN ('queued','rendering')"
            ).fetchone()[0]
            if pending >= 10:
                raise FilmEngineError("Local rendering queue is full", 429)
            job_id = uuid.uuid4().hex
            now = time.time()
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?)",
                       (job_id, "queued", timeline.title, None, None, now, now))
    _EXECUTOR.submit(_run_job, base, job_id, timeline)
    return {"job_id": job_id, "status": "queued",
            "render_engine": "own_ffmpeg",
            "provider": None, **verification}


def _status(base: Path, job_id: str, status: str,
            output_file: str | None = None, error: str | None = None) -> None:
    with _DB_LOCK:
        with _connect(base) as db:
            db.execute(
                "UPDATE jobs SET status=?, output_file=?, error=?, updated_at=? WHERE id=?",
                (status, output_file, error, time.time(), job_id),
            )


def _run_job(base: Path, job_id: str, timeline: Timeline) -> None:
    target = base / "jobs" / (job_id + ".mp4")
    _status(base, job_id, "rendering")
    try:
        render_timeline(base, timeline, target)
    except Exception:
        target.unlink(missing_ok=True)
        _status(base, job_id, "failed", error="Render failed; inspect server-side logs")
    else:
        _status(base, job_id, "completed", output_file=target.name)


def get_job(base: Path, job_id: str) -> dict:
    if not _UUID.fullmatch(job_id):
        raise FilmEngineError("Invalid film render job")
    with _connect(base) as db:
        record = db.execute("SELECT id,title,status,output_file,error,created_at,updated_at "
                            "FROM jobs WHERE id=?", (job_id,)).fetchone()
    if record is None:
        raise FilmEngineError("Unknown film render job", 404)
    result = dict(record)
    if result["status"] == "completed":
        result["download_path"] = "/api/film-studio/jobs/" + job_id + "/file"
    return result
