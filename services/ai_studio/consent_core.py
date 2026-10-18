"""Pure consent-policy primitives for AI Studio.

This module deliberately does not persist grants or execute jobs. Callers must
load a grant from trusted storage and invoke these checks immediately before
side effects. Missing/expired/revoked grants fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


class Access(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class Duration(str, Enum):
    ONCE = "once"
    SESSION = "session"
    TASK = "task"
    ALWAYS = "always"


class ConsentError(PermissionError):
    """Raised when requested authority is not explicitly granted."""


@dataclass(frozen=True)
class Grant:
    subject_id: str
    resource: str
    access: frozenset[Access]
    duration: Duration
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    session_id: str | None = None
    task_id: str | None = None

    def __post_init__(self) -> None:
        if not self.subject_id.strip() or not self.resource.strip():
            raise ValueError("subject_id and resource are required")
        for value in (self.created_at, self.expires_at, self.revoked_at):
            if value is not None and value.tzinfo is None:
                raise ValueError("timestamps must be timezone-aware")
        if self.duration == Duration.ONCE and (self.session_id is None or self.task_id is None):
            raise ValueError("once grants must be bound to a session and task")
        if self.duration == Duration.SESSION and self.session_id is None:
            raise ValueError("session grants must be bound to a session")
        if self.duration == Duration.TASK and self.task_id is None:
            raise ValueError("task grants must be bound to a task")


def authorize(
    grant: Grant | None,
    *,
    subject_id: str,
    resource: str,
    access: Access,
    now: datetime | None = None,
    session_id: str | None = None,
    task_id: str | None = None,
    consumed_once: bool = False,
) -> None:
    """Raise ConsentError unless this exact request is covered by the grant."""
    if grant is None:
        raise ConsentError("No consent grant")
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if grant.revoked_at is not None or (grant.expires_at is not None and instant >= grant.expires_at):
        raise ConsentError("Grant is revoked or expired")
    if grant.subject_id != subject_id or grant.resource != resource:
        raise ConsentError("Grant does not cover this subject and resource")
    if access not in grant.access:
        raise ConsentError("Requested access level is not granted")
    if grant.duration == Duration.ONCE:
        if consumed_once:
            raise ConsentError("Once grant has already been consumed")
        if grant.session_id != session_id or grant.task_id != task_id:
            raise ConsentError("Once grant is outside its session or task")
    elif grant.duration == Duration.SESSION and grant.session_id != session_id:
        raise ConsentError("Grant is outside its session")
    elif grant.duration == Duration.TASK and grant.task_id != task_id:
        raise ConsentError("Grant is outside its task")


def normalize_access(values: Iterable[str]) -> frozenset[Access]:
    """Parse explicit access labels; invalid values are rejected, never ignored."""
    try:
        parsed = frozenset(Access(value) for value in values)
    except ValueError as exc:
        raise ValueError("Unknown access level") from exc
    if not parsed:
        raise ValueError("At least one access level is required")
    return parsed
