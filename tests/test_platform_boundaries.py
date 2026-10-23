"""Product regression: Unthinkable AI must remain first-party and modular.

Run in a clean process with UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY=0.
No external network calls, vendor keys, paid jobs or GPU are needed.
"""
import os
import re
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

# Must be set before gateway routes are imported.
os.environ["UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY"] = "0"
from services.gateway.app import app  # noqa: E402


class FirstPartyPlatformBoundaries(unittest.TestCase):
    def test_owned_cinema_and_film_studio_are_registered(self):
        # Verify the actual HTTP contract. FastAPI may hold routers as
        # _IncludedRouter objects, which do not expose a .path attribute.
        client = TestClient(app)
        for url in (
            "/api/film-studio/capabilities",
            "/api/cinema/owned/capabilities",
        ):
            with self.subTest(url=url):
                self.assertNotEqual(client.get(url).status_code, 404)
        # GET on a POST-only rendering path must be 405 when registered.
        self.assertEqual(
            client.get("/api/film-studio/timeline/render").status_code,
            405,
        )

    def test_legacy_provider_is_not_a_core_route(self):
        client = TestClient(app)
        # Probe a known vendor route instead of depending on router internals.
        self.assertEqual(
            client.get("/api/cinema/visionstory/models").status_code,
            404,
            "Vendor adapter must never be enabled on the default gateway",
        )

    def test_film_capabilities_explicitly_do_not_claim_video_inference(self):
        from unittest.mock import patch
        client = TestClient(app)
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "test-owned-key"):
            r = client.get(
                "/api/cinema/owned/capabilities",
                headers={"Authorization": "Bearer test-owned-key"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["primary"])
        self.assertFalse(r.json()["external_api_keys_required"])
        self.assertFalse(r.json()["video_model_inference"])

    def test_film_is_one_of_all_27_requirement_domains(self):
        root = Path(__file__).resolve().parents[1]
        dart = (root / "lib" / "main.dart").read_text(encoding="utf-8")
        entries = re.findall(
            r"FeatureDomain\('([A-Z]+)',\s*'[^']*',\s*'[^']*',\s*(\d+),",
            dart,
        )
        ids = [code for code, _ in entries]
        self.assertEqual(len(entries), 27)
        self.assertEqual(len(set(ids)), 27)
        self.assertEqual(sum(int(count) for _, count in entries), 339)
        for domain in (
            "VIDEO", "IMAGE", "AUDIO", "MODELS", "AGENTS",
            "WEB", "GAME", "APPS", "MARKET", "PAY", "OWNER", "DGM",
        ):
            self.assertIn(domain, ids)


if __name__ == "__main__":
    unittest.main()
