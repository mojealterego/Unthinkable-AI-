"""Durable, single-owner paid-job idempotency ledger for VisionStory.

A request that may have reached the provider is NEVER automatically retried.
Stores a SHA-256 digest, not the prompt, user media or credentials. This is not
multi-tenant storage; global gateway API_KEY cannot isolate end users.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Any

from .client import VisionStoryError

_VALID = re.compile(r"^[a-zA-Z0-9_-]{8,128}$")
_NAMESPACES = frozenset(("avatar_video", "ai_video"))
_STATES = frozenset(("sending", "ambiguous", "submitted", "created", "failed"))


class JobLedger:
    def __init__(self, path: str):
        if not path or not os.path.isabs(path) or path == ":memory:":
            raise ValueError("Job database must be an absolute persistent path")
        self.path = Path(path)
        if self.path.is_symlink():
            raise ValueError("Symlink database paths are not permitted")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self._conn() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS visionstory_jobs (
                    namespace TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL,
                    video_id TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    PRIMARY KEY (namespace, request_id)
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS visionstory_jobs_recent
                ON visionstory_jobs(updated_at DESC)
            """)

    @contextmanager
    def _conn(self):
        db = sqlite3.connect(self.path, timeout=7.0, isolation_level=None)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA busy_timeout=7000")
            yield db
        finally:
            db.close()

    @staticmethod
    def _digest(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
        return sha256(raw).hexdigest()

    def begin(self, namespace: str, request_id: str, payload: dict) -> str | None:
        """Return existing video_id or None if reserved by this call.

        Conflict means the same ID changed payload, or outcome is uncertain.
        """
        if namespace not in _NAMESPACES or not _VALID.fullmatch(request_id):
            raise ValueError("Invalid job namespace or request id")
        digest = self._digest(payload)
        now = int(time.time())
        with self._conn() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT payload_sha256,state,video_id FROM visionstory_jobs "
                    "WHERE namespace=? AND request_id=?",
                    (namespace, request_id),
                ).fetchone()
                if row is None:
                    db.execute(
                        "INSERT INTO visionstory_jobs "
                        "(namespace,request_id,payload_sha256,state,created_at,updated_at)"
                        " VALUES(?,?,?,?,?,?)",
                        (namespace, request_id, digest, "sending", now, now),
                    )
                    db.commit()
                    return None
                if row["payload_sha256"] != digest:
                    raise VisionStoryError(
                        "This request ID was already used with different inputs", 409
                    )
                if row["video_id"] and row["state"] in ("submitted", "created", "failed"):
                    db.commit()
                    return row["video_id"]
                raise VisionStoryError(
                    "The earlier request outcome is uncertain; manually reconcile "
                    "the provider job before a new paid submission", 409
                )
            except Exception:
                db.rollback()
                raise

    def mark_ambiguous(self, namespace: str, request_id: str):
        self._transition(namespace, request_id, "ambiguous", None)

    def finish(self, namespace: str, request_id: str, video_id: str):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{3,160}", video_id):
            raise ValueError("Provider returned an invalid video ID")
        self._transition(namespace, request_id, "submitted", video_id)

    def _transition(self, namespace: str, request_id: str, state: str,
                    video_id: str | None):
        if namespace not in _NAMESPACES or state not in _STATES:
            raise ValueError("Invalid job transition")
        with self._conn() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT state FROM visionstory_jobs WHERE namespace=? AND request_id=?",
                    (namespace, request_id)
                ).fetchone()
                if row is None or row["state"] != "sending":
                    raise VisionStoryError("Job transition rejected: no active submission", 409)
                db.execute(
                    "UPDATE visionstory_jobs SET state=?, video_id=?, updated_at=? "
                    "WHERE namespace=? AND request_id=?",
                    (state, video_id, int(time.time()), namespace, request_id)
                )
                db.commit()
            except Exception:
                db.rollback()
                raise

    def list_jobs(self, limit: int = 100) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Jobs page limit must be 1..200")
        with self._conn() as db:
            rows = db.execute(
                "SELECT namespace,request_id,state,video_id,created_at,updated_at "
                "FROM visionstory_jobs ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]


def configured_ledger() -> JobLedger | None:
    path = os.getenv("VISIONSTORY_JOB_DB_PATH", "").strip()
    required = os.getenv("VISIONSTORY_REQUIRE_DURABLE_JOBS", "0").strip() == "1"
    if not path:
        if required:
            raise VisionStoryError("Durable VisionStory job database is required", 503)
        return None
    try:
        return JobLedger(path)
    except (ValueError, OSError, sqlite3.Error) as exc:
        raise VisionStoryError("VisionStory durable job database is unavailable", 503) from exc
