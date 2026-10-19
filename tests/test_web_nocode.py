import io
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from fastapi.testclient import TestClient
from pydantic import ValidationError
from services.gateway.app import app
from services.web.builder import (
    Page, Section, Site, export_site_zip, render_page, site_from_snapshot,
)


def demo_site():
    return Site(
        name="Studio Alfa", tagline="Nasza własna witryna", theme="gold",
        pages=[
            Page(slug="index", title="Start", sections=[
                Section(type="hero", heading="Witamy", body="Budujemy strony bez kodu"),
                Section(type="features", heading="Zalety", items=["Szybko", "Bezpiecznie"]),
                Section(type="cta", heading="Kontakt", button_label="Napisz",
                        button_url="mailto:hello@example.org"),
            ]),
            Page(slug="kontakt", title="Kontakt", sections=[
                Section(type="contact", heading="Dane kontaktowe", body="Przykład"),
            ]),
        ],
    )


class NoCodeBuilderTests(unittest.TestCase):
    def test_static_zip_contains_all_pages_without_backend_or_scripts(self):
        output = export_site_zip(demo_site())
        with ZipFile(io.BytesIO(output)) as archive:
            self.assertEqual(set(archive.namelist()),
                             {"index.html", "kontakt.html", "site.json", "README.txt"})
            html = archive.read("index.html").decode("utf-8")
            self.assertIn("Witamy", html)
            self.assertIn('href="kontakt.html"', html)
            self.assertNotIn("<script", html)
            self.assertNotIn("api_key", html.lower())

    def test_html_is_escaped_and_unsafe_links_rejected(self):
        site = Site(name='<script>alert(1)</script>', pages=[
            Page(slug="index", title="Start", sections=[
                Section(type="text", heading="<img src=x onerror=alert(1)>",
                        body='Hi & <script>alert("a")</script>')])])
        html = render_page(site, "index")
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn('<script>alert(1)</script>', html)
        for href in ("javascript:alert(1)", "data:text/html;base64,x", "//evil.example"):
            with self.assertRaises(ValidationError):
                Section(type="cta", heading="Link", button_label="Open", button_url=href)

    def test_validates_page_slugs_and_uniqueness(self):
        with self.assertRaises(ValidationError):
            Site(name="X", pages=[
                Page(slug="index", title="A", sections=[Section(type="hero", heading="A")]),
                Page(slug="index", title="B", sections=[Section(type="hero", heading="B")]),
            ])
        with self.assertRaises(ValidationError):
            Page(slug="../foo", title="Unsafe", sections=[Section(type="hero", heading="X")])

    def test_wrapper_to_editable_site_draft(self):
        draft = site_from_snapshot({
            "format": "unthinkable-nocode-data-wrapper-v1",
            "pages": [{"title": "Źródło", "description": "Przykład",
                       "headings": [{"text": "O nas"}]}],
        })
        self.assertEqual(draft.pages[0].slug, "index")
        self.assertEqual(len(draft.pages[0].sections), 2)


class NoCodeAPITests(unittest.TestCase):
    def test_all_endpoints_authorized_and_preview_sandboxed(self):
        client = TestClient(app)
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "unit-key"):
            self.assertEqual(client.get("/api/web/nocode/templates").status_code, 401)
            headers = {"Authorization": "Bearer unit-key"}
            self.assertEqual(client.get("/api/web/nocode/templates",
                                        headers=headers).status_code, 200)
            doc = demo_site().model_dump()
            reply = client.post("/api/web/nocode/preview", headers=headers,
                                json={"site": doc, "slug": "index"})
            self.assertEqual(reply.status_code, 200, reply.text)
            self.assertEqual(reply.headers["cache-control"], "no-store")
            self.assertIn("default-src 'none'", reply.headers["content-security-policy"])
            package = client.post("/api/web/nocode/export", headers=headers, json=doc)
            self.assertEqual(package.status_code, 200, package.text)
            self.assertTrue(package.content.startswith(b"PK"))
            self.assertEqual(package.headers["content-type"], "application/zip")
            missing = client.post("/api/web/nocode/preview", headers=headers,
                                  json={"site": doc, "slug": "nonexistent"})
            self.assertEqual(missing.status_code, 422)


if __name__ == "__main__":
    unittest.main()
