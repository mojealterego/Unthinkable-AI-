"""Web Studio integration tests: safe scraping, wrapper validation and HTML export."""
import base64
from io import BytesIO
import os
import socket
import unittest
from unittest.mock import patch
import zipfile

from fastapi.testclient import TestClient
from pydantic import ValidationError

from services.gateway.app import app
from services.web_studio.scraper import (
    authorize_target, inspect_html, _safe_ip, fetch_authorized_page,
)
from services.web_studio.nocode import SiteBlock, SiteDesign, render_html, export_zip
from services.web_studio.wrapper import ApiOperation, WrapperDesign, build_openapi


class ScraperTests(unittest.TestCase):
    def test_extracted_public_structure_is_bounded_and_does_not_run_scripts(self):
        html = ('<html><head><title>Portfolio</title></head><body>'
                '<h1>Fotograf</h1><p>Moja strona</p>'
                '<script>window.evil=1; localStorage.getItem("secret")</script>'
                '<a href="/about">O mnie</a><img src="/pic.jpg">'
                '<form action="/login"><input type="password"></form></body></html>')
        r = inspect_html(html, base_url="https://gallery.example")
        self.assertEqual(r["title"], "Portfolio")
        self.assertEqual(r["headings"][0]["text"], "Fotograf")
        self.assertEqual(r["links"][0]["href"], "https://gallery.example/about")
        self.assertEqual(r["images"], ["https://gallery.example/pic.jpg"])
        self.assertEqual(r["forms_count"], 1)
        self.assertFalse(r["scripts_executed"])
        self.assertFalse(r["secrets_extracted"])
        self.assertNotIn("evil", repr(r))

    def test_rejects_unsanctioned_and_private_network_targets(self):
        allow = {"gallery.example"}
        for url in ("http://gallery.example", "https://user:pw@gallery.example",
                    "https://gallery.example:8443", "https://gallery.example?q=api_key",
                    "https://gallery.example/#fragment",
                    "https://127.0.0.1/", "https://gallery.example.evil.com"):
            with self.assertRaises((ValueError, PermissionError)):
                authorize_target(url, allow)
        self.assertEqual(authorize_target("https://gallery.example/gallery", allow)[0],
                         "gallery.example")
        for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "192.168.0.1",
                        "::1", "fd00::1", "::ffff:127.0.0.1"):
            with self.assertRaises(ValueError):
                _safe_ip(address)
        self.assertEqual(_safe_ip("1.1.1.1"), "1.1.1.1")

    def test_live_scraper_pins_validated_dns_and_respects_robots(self):
        entries = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with patch("services.web_studio.scraper.socket.getaddrinfo", return_value=entries), \
             patch("services.web_studio.scraper._request", side_effect=[
                 (200, "text/plain", b"User-agent: *\nAllow: /"),
                 (200, "text/html", b"<h1>Authorized page</h1>"),
             ]) as mocked:
            content = fetch_authorized_page("https://gallery.example/", {"gallery.example"})
            self.assertIn("Authorized", content)
            self.assertEqual(mocked.call_count, 2)
            self.assertEqual(mocked.call_args.args[1], "1.1.1.1")
        with patch("services.web_studio.scraper.socket.getaddrinfo", return_value=entries), \
             patch("services.web_studio.scraper._request", return_value=(
                 200, "text/plain", b"User-agent: *\nDisallow: /private"
             )) as mocked:
            with self.assertRaises(PermissionError):
                fetch_authorized_page("https://gallery.example/private", {"gallery.example"})
            self.assertEqual(mocked.call_count, 1)

    def test_private_dns_rebinding_address_prevents_http_request(self):
        entries = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch("services.web_studio.scraper.socket.getaddrinfo", return_value=entries), \
             patch("services.web_studio.scraper._request") as req:
            with self.assertRaises(ValueError):
                fetch_authorized_page("https://gallery.example/", {"gallery.example"})
            req.assert_not_called()


class CreatorTests(unittest.TestCase):
    def test_site_is_real_static_html_and_escapes_html_and_urls(self):
        site = SiteDesign(name='<img src=x onerror=alert(1)>', blocks=[
            SiteBlock(kind="heading", text="<script>alert('X')</script>"),
            SiteBlock(kind="feature", text="Własna firma", subtitle="Portfolio"),
            SiteBlock(kind="button", text="Kontakt", link="https://example.com/contact"),
        ])
        html = render_html(site)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("<!doctype html>", html)
        self.assertIn('Content-Security-Policy', html)
        archive = zipfile.ZipFile(BytesIO(export_zip(site)))
        self.assertEqual(set(archive.namelist()), {"index.html", "site.json"})
        self.assertEqual(archive.read("index.html").decode(), html)

    def test_rejects_javascript_links_and_html_injection(self):
        with self.assertRaises(ValidationError):
            SiteBlock(kind="button", text="Click", link="javascript:alert(1)")
        with self.assertRaises(ValidationError):
            SiteBlock(kind="button", text="Click", link="https://example.com/\" onmouseover=\"a")
        with self.assertRaises(ValidationError):
            SiteDesign(name="No content", blocks=[])


class WrapperTests(unittest.TestCase):
    def test_generated_openapi_contains_real_operations_but_no_proxy(self):
        spec = WrapperDesign(title="My API", operations=[
            ApiOperation(operation_id="list_projects", method="GET",
                         path="/projects", summary="List projects"),
            ApiOperation(operation_id="create_project", method="POST",
                         path="/projects", summary="Add project",
                         request_fields=["name", "description"]),
        ])
        data = build_openapi(spec)
        self.assertEqual(data["openapi"], "3.1.0")
        self.assertEqual(len(data["paths"]["/projects"]), 2)
        self.assertEqual(data["paths"]["/projects"]["post"]["operationId"], "create_project")
        self.assertFalse(data["x-unthinkable-capabilities"]["proxy_started"])

    def test_duplicate_routes_and_unsafe_paths_rejected(self):
        with self.assertRaises(ValidationError):
            ApiOperation(operation_id="bad", method="GET", path="//127.0.0.1", summary="x")
        with self.assertRaises(ValidationError):
            WrapperDesign(title="x", operations=[
                ApiOperation(operation_id="first", path="/items", summary="first"),
                ApiOperation(operation_id="second", path="/items", summary="second"),
            ])


class HttpApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer web-studio-testing-key"}

    def test_auth_and_nocode_and_wrapper(self):
        site = {"name": "Strona", "blocks": [
            {"kind": "heading", "text": "Witaj"},
            {"kind": "button", "text": "Dowiedz się", "link": "/kontakt"},
        ]}
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "web-studio-testing-key"):
            self.assertEqual(self.client.post("/api/web-studio/nocode/render",
                              json=site).status_code, 401)
            rendered = self.client.post("/api/web-studio/nocode/render",
                                       json=site, headers=self.headers)
            self.assertEqual(rendered.status_code, 200, rendered.text)
            data = rendered.json()
            self.assertTrue(data["html"].startswith("<!doctype html>"))
            self.assertFalse(data["published"])
            with zipfile.ZipFile(BytesIO(base64.b64decode(data["zip_base64"]))) as archive:
                self.assertIn("index.html", archive.namelist())
            spec = self.client.post("/api/web-studio/wrapper/build",
                  json={"title": "Owned API", "operations": [
                    {"operation_id": "hello", "method": "GET", "path": "/hello", "summary": "Hi"},
                  ]}, headers=self.headers)
            self.assertEqual(spec.status_code, 200)
            self.assertEqual(spec.json()["paths"]["/hello"]["get"]["operationId"], "hello")

    def test_no_fetch_with_empty_allowlist_or_invalid_host(self):
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "web-studio-testing-key"):
            with patch.dict(os.environ, {"WEB_STUDIO_ALLOWED_HOSTS": ""}):
                denied = self.client.post("/api/web-studio/scraper/fetch",
                    json={"url": "https://gallery.example/"}, headers=self.headers)
                self.assertEqual(denied.status_code, 403)
            local = self.client.post("/api/web-studio/scraper/inspect",
                json={"html": "<h1>Przykładowa strona</h1>"}, headers=self.headers)
            self.assertEqual(local.status_code, 200, local.text)
            self.assertEqual(local.json()["headings"][0]["text"], "Przykładowa strona")


if __name__ == "__main__":
    unittest.main()
