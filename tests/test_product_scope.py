"""Guard the product scope: 27 domains and a first-party Film Studio default."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {
    "FOUND", "MODELS", "REASON", "AGENTS", "EXT", "DEEP", "DGM", "GITHUB",
    "IMAGE", "VIDEO", "AUDIO", "GAME", "APPS", "PUBLISH", "CHAT",
    "BROWSER", "ANDROID", "WEB", "OWNER", "MATH", "MARKET", "PAY",
    "INFRA", "FORMAL", "LEGAL", "OPTION", "REUSE",
}


class ProductScopeTests(unittest.TestCase):
    def test_full_app_navigation_not_just_film(self):
        main = (ROOT / "lib/main.dart").read_text(encoding="utf-8")
        domains = re.findall(r"FeatureDomain\('([A-Z]+)',", main)
        self.assertEqual(len(domains), 27)
        self.assertEqual(set(domains), EXPECTED)
        self.assertEqual(len(domains), len(set(domains)))
        self.assertIn("const OwnFilmStudioScreen()", main)
        for domain in ("VIDEO", "MODELS", "WEB", "CHAT", "AUDIO"):
            self.assertIn("domain.code == '" + domain + "'", main)
        self.assertNotIn("VisionStoryScreen(", main)

    def test_default_gateway_uses_our_studio_without_visionstory_routes(self):
        code = (
            "import json\n"
            "from services.gateway.app import app\n"
            "paths = {route.path for route in app.routes}\n"
            "print(json.dumps({\n"
            " 'film': '/api/film-studio/capabilities' in paths,\n"
            " 'cinema': '/api/cinema/owned/capabilities' in paths,\n"
            " 'web': '/api/web-studio/capabilities' in paths,\n"
            " 'visionstory': '/api/cinema/visionstory/credits' in paths,\n"
            "}))\n"
        )
        env = os.environ.copy()
        env["UNTHINKABLE_ENABLE_LEGACY_VISIONSTORY"] = "0"
        r = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr[-1500:])
        self.assertEqual(json.loads(r.stdout), {
            "film": True, "cinema": True, "web": True,
            "visionstory": False,
        })

    def test_documentation_distinguishes_reference_from_own_engine(self):
        scope = (ROOT / "docs/PRODUCT_SYSTEM_SCOPE.md").read_text(encoding="utf-8")
        for term in ("27 obszarów", "własnym sprzęcie", "Studio Filmowe jest tylko jednym"):
            self.assertIn(term, scope)


if __name__ == "__main__":
    unittest.main()
