"""Persistent, atomic on-net alias reservations (no PSTN provisioning).

This is a single-tenant prototype protected by the gateway API_KEY.
For multi-user service, replace this with independently authenticated
principal IDs, tenant isolation, quotas and transaction audit.
"""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import time
from .vanity import digits_only


class ClaimConflict(ValueError):
    pass


class OnNetAliasStore:
    def __init__(self, path: str):
        if not path or path == ":memory:":
            raise ValueError("A persistent absolute SQLite path is required")
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ValueError("Alias database path must be absolute")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS onnet_aliases (
                    identifier TEXT PRIMARY KEY,
                    owner_scope TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=7.0, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 7000")
        return db

    def claim(self, alias: str, *, owner_scope: str, ttl_seconds: int = 3600,
              now: int | None = None) -> dict:
        identifier = digits_only(alias)
        if not owner_scope or len(owner_scope) > 128:
            raise ValueError("Owner scope required")
        if type(ttl_seconds) is not int or not 60 <= ttl_seconds <= 86400:
            raise ValueError("TTL must be 60..86400 seconds")
        now = int(time.time()) if now is None else now
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("DELETE FROM onnet_aliases WHERE expires_at <= ?", (now,))
                current = db.execute(
                    "SELECT * FROM onnet_aliases WHERE identifier = ?", (identifier,)
                ).fetchone()
                if current:
                    if current["owner_scope"] != owner_scope:
                        raise ClaimConflict("This internal alias is already reserved")
                    expiration = current["expires_at"]  # Idempotent, no silent extension.
                else:
                    expiration = now + ttl_seconds
                    db.execute(
                        "INSERT INTO onnet_aliases (identifier, owner_scope, created_at, expires_at)"
                        " VALUES (?,?,?,?)", (identifier, owner_scope, now, expiration)
                    )
                db.commit()
            except Exception:
                db.rollback()
                raise
        return {
            "identifier": identifier, "expires_at_unix": expiration,
            "state": "reserved_on_net", "publicly_routable": False,
            "carrier_did_reserved": False,
        }

    def list_claims(self, *, owner_scope: str, now: int | None = None) -> list[dict]:
        now = int(time.time()) if now is None else now
        with self._connect() as db:
            rows = db.execute(
                "SELECT identifier,expires_at FROM onnet_aliases "
                "WHERE owner_scope = ? AND expires_at > ? "
                "ORDER BY expires_at DESC LIMIT 200", (owner_scope, now)
            ).fetchall()
        return [{
            "identifier": r["identifier"], "expires_at_unix": r["expires_at"],
            "state": "reserved_on_net", "publicly_routable": False,
        } for r in rows]

    def release(self, alias: str, *, owner_scope: str) -> bool:
        identifier = digits_only(alias)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                result = db.execute(
                    "DELETE FROM onnet_aliases WHERE identifier = ? AND owner_scope = ?",
                    (identifier, owner_scope)
                )
                db.commit()
                return result.rowcount == 1
            except Exception:
                db.rollback()
                raise


def configured_alias_store() -> tuple[OnNetAliasStore, str]:
    path = os.environ.get("VIRTUAL_ALIAS_DB_PATH", "").strip()
    scope = os.environ.get("VIRTUAL_ALIAS_OWNER_SCOPE", "single-owner").strip()
    if not path or not scope:
        raise RuntimeError("Internal alias reservations are not configured")
    return OnNetAliasStore(path), scope
