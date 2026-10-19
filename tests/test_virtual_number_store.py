import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.gateway.app import app
from services.virtual_number.store import ClaimConflict, OnNetAliasStore


class OnNetReservationTests(unittest.TestCase):
    def test_owner_claim_is_persistent_idempotent_and_expires(self):
        with tempfile.TemporaryDirectory() as base:
            file = str(Path(base) / "alias.sqlite3")
            store = OnNetAliasStore(file)
            first = store.claim("111111111", owner_scope="owner-a", ttl_seconds=180, now=1000)
            second = OnNetAliasStore(file).claim(
                "111111111", owner_scope="owner-a", ttl_seconds=200, now=1010
            )
            self.assertEqual(first["expires_at_unix"], second["expires_at_unix"])
            self.assertFalse(first["publicly_routable"])
            self.assertEqual(len(store.list_claims(owner_scope="owner-a", now=1010)), 1)
            with self.assertRaises(ClaimConflict):
                store.claim("111111111", owner_scope="owner-b", now=1010)
            self.assertEqual(store.list_claims(owner_scope="owner-a", now=1181), [])
            owner_b = store.claim("111111111", owner_scope="owner-b", now=1181)
            self.assertEqual(owner_b["state"], "reserved_on_net")
            self.assertFalse(store.release("111111111", owner_scope="owner-a"))
            self.assertTrue(store.release("111111111", owner_scope="owner-b"))

    def test_atomic_competing_alias_claims(self):
        with tempfile.TemporaryDirectory() as base:
            store = OnNetAliasStore(str(Path(base) / "onnet.db"))
            def action(owner):
                try:
                    store.claim("000999000", owner_scope=owner)
                    return "OK"
                except ClaimConflict:
                    return "CONFLICT"
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(action, ("alpha", "beta")))
            self.assertEqual(sorted(results), ["CONFLICT", "OK"])

    def test_onnet_http_requires_auth_and_explicit_database(self):
        api = TestClient(app)
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "test-secret"):
            self.assertEqual(api.post("/api/virtual-number/on-net/claim", json={
                "identifier": "111111111"
            }).status_code, 401)
            with patch.dict(os.environ, {"VIRTUAL_ALIAS_DB_PATH": ""}):
                self.assertEqual(api.post("/api/virtual-number/on-net/claim", json={
                    "identifier": "111111111"
                }, headers={"Authorization": "Bearer test-secret"}).status_code, 503)
            with tempfile.TemporaryDirectory() as base:
                with patch.dict(os.environ, {"VIRTUAL_ALIAS_DB_PATH": str(Path(base) / "x.db")}):
                    headers = {"Authorization": "Bearer test-secret"}
                    req = {"identifier": "000777000", "ttl_seconds": 120}
                    response = api.post("/api/virtual-number/on-net/claim",
                                        json=req, headers=headers)
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["state"], "reserved_on_net")
                    self.assertFalse(response.json()["publicly_routable"])
                    listing = api.get("/api/virtual-number/on-net/claims", headers=headers)
                    self.assertEqual(listing.status_code, 200)
                    self.assertEqual(len(listing.json()["claims"]), 1)
                    deleted = api.delete("/api/virtual-number/on-net/claims/000777000",
                                         headers=headers)
                    self.assertEqual(deleted.status_code, 200)
                    self.assertTrue(deleted.json()["released"])


if __name__ == "__main__":
    unittest.main()
