import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.gateway.app import app
from services.web.scraper import (
    ScrapeBlocked, canonical_url, extract_html, make_api_wrapper,
    scrape_pages,
)


class ScraperUnitTests(unittest.TestCase):
    def test_blocks_ip_private_and_unallowlisted_hosts_without_network(self):
        host = {"example.com"}
        for raw in ("http://example.com/", "https://127.0.0.1/",
                    "https://example.com:444/", "https://username:pw@example.com/",
                    "https://example.com/?token=a", "https://example.com/#fragment",
                    "https://bad.example/"):
            with self.assertRaises(ScrapeBlocked, msg=raw):
                canonical_url(raw, host)
        self.assertEqual(canonical_url("https://example.com/abc", host),
                         "https://example.com/abc")

    def test_html_extraction_never_exports_scripts_or_form_secrets(self):
        html = '<title>Moja witryna</title><meta name="description" content="Demo">' \
               '<h1>Nowa strona</h1><a href="/about">About</a>' \
               '<script>const secret="dont_expose";</script>' \
               '<form><input type="password" value="private_value"></form>' \
               '<img src="/pic.jpg" alt="Foto">'
        result = extract_html(html, "https://example.com/")
        self.assertEqual(result["title"], "Moja witryna")
        self.assertEqual(result["headings"][0]["text"], "Nowa strona")
        self.assertEqual(result["form_count"], 1)
        self.assertNotIn("private_value", str(result))
        self.assertNotIn("dont_expose", str(result))
        self.assertFalse(result["backend_extracted"] if "backend_extracted" in result else result["private_backend_extracted"])

    def test_admin_host_allowlist_required(self):
        with self.assertRaises(ScrapeBlocked):
            scrape_pages("https://example.com/", set())

    def test_html_wrapper_is_structured_and_read_only(self):
        structured = extract_html("<title>Demo</title><h1>Headline</h1>",
                                  "https://example.com/")
        wrapped = make_api_wrapper({
            "format": "unthinkable-authorized-site-wrapper-v1",
            "source_url": "https://example.com/",
            "pages": [structured],
        })
        self.assertEqual(wrapped["pages"][0]["title"], "Demo")
        self.assertFalse(wrapped["backend_logic_cloned"])
        self.assertTrue(wrapped["read_only"])


class ScraperAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer unit-key"}

    def test_auth_and_ownership_gate(self):
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "unit-key"):
            self.assertEqual(self.client.get("/api/web/capabilities").status_code, 401)
            reply = self.client.post("/api/web/scrape", headers=self.headers,
                                     json={"url": "https://example.com"})
            self.assertEqual(reply.status_code, 403)
            with patch.dict("os.environ", {"WEB_SCRAPER_ALLOWED_HOSTS": ""}):
                reply = self.client.post("/api/web/scrape", headers=self.headers,
                                         json={"url": "https://example.com", "confirm_ownership": True})
                self.assertEqual(reply.status_code, 422)

    def test_extract_and_wrapper_endpoints(self):
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "unit-key"):
            result = self.client.post("/api/web/extract", headers=self.headers,
                                      json={"html": "<h1>Moja własna witryna</h1>"})
            self.assertEqual(result.status_code, 200, result.text)
            document = {
                "format": "unthinkable-authorized-site-wrapper-v1",
                "source_url": "https://example.com/",
                "pages": [result.json()],
            }
            wrapped = self.client.post("/api/web/wrapper", headers=self.headers,
                                       json={"snapshot": document})
            self.assertEqual(wrapped.status_code, 200, wrapped.text)
            self.assertEqual(len(wrapped.json()["pages"]), 1)


if __name__ == "__main__":
    unittest.main()
