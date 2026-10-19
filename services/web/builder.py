"""NoCode static multipage website builder: structured sections -> escaped HTML/ZIP.

No arbitrary user CSS, JavaScript, HTML, iframes, forms or server-side code.
Assets and deployment require an explicit subsequent owner action.
"""
from __future__ import annotations

from html import escape
import io
import json
from pathlib import PurePosixPath
import re
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

from pydantic import BaseModel, Field, model_validator
from typing import Literal


Slug = str
SLUG = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
THEMES = {
    "midnight": {"bg": "#0b0b12", "surface": "#181827", "text": "#f3f2fd", "accent": "#9678fa"},
    "gold": {"bg": "#0b0b0c", "surface": "#1c1a17", "text": "#faf7ed", "accent": "#dfb956"},
    "light": {"bg": "#f8f9fc", "surface": "#ffffff", "text": "#1f2430", "accent": "#5546bd"},
}
SectionKind = Literal["hero", "text", "features", "cta", "contact"]


class Section(BaseModel):
    type: SectionKind
    heading: str = Field(min_length=1, max_length=150)
    body: str = Field(default="", max_length=3500)
    items: list[str] = Field(default_factory=list, max_length=12)
    button_label: str = Field(default="", max_length=80)
    button_url: str = Field(default="", max_length=1024)

    @model_validator(mode="after")
    def validate_link(self):
        if self.button_url:
            parts = urlsplit(self.button_url)
            if parts.scheme == "https":
                if not parts.hostname or parts.username or parts.password:
                    raise ValueError("CTA links must not contain credentials")
            elif self.button_url.startswith("/"):
                if self.button_url.startswith("//") or "\\" in self.button_url:
                    raise ValueError("Ambiguous relative link")
            elif parts.scheme == "mailto":
                if not re.fullmatch(r"mailto:[A-Za-z0-9.+_-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,20}",
                                    self.button_url):
                    raise ValueError("Invalid mailto URL")
            else:
                raise ValueError("Only HTTPS, site-relative or mailto links are allowed")
        return self


class Page(BaseModel):
    slug: str = Field(min_length=1, max_length=48)
    title: str = Field(min_length=1, max_length=120)
    sections: list[Section] = Field(min_length=1, max_length=35)

    @model_validator(mode="after")
    def validate_slug(self):
        if self.slug != "index" and not SLUG.fullmatch(self.slug):
            raise ValueError("Page slug must be lowercase ASCII and URL-safe")
        return self


class Site(BaseModel):
    format: Literal["unthinkable-nocode-website-v1"] = "unthinkable-nocode-website-v1"
    name: str = Field(min_length=1, max_length=100)
    tagline: str = Field(default="", max_length=200)
    theme: Literal["midnight", "gold", "light"] = "midnight"
    pages: list[Page] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_pages(self):
        paths = [page.slug for page in self.pages]
        if "index" not in paths or len(paths) != len(set(paths)):
            raise ValueError("Pages require one index and unique slugs")
        return self


def _link(label: str, url: str) -> str:
    if not label or not url:
        return ""
    return '<a class="action" href="' + escape(url, quote=True) + '">' + escape(label) + "</a>"


def _section(section: Section) -> str:
    heading = "<h1>" if section.type == "hero" else "<h2>"
    closing = "</h1>" if section.type == "hero" else "</h2>"
    body = "<p>" + escape(section.body).replace("\n", "<br>") + "</p>" if section.body else ""
    cards = ""
    if section.type == "features" and section.items:
        cards = '<ul class="features">' + "".join(
            "<li>" + escape(item) + "</li>" for item in section.items
        ) + "</ul>"
    return ('<section class="section section-' + section.type + '"><div class="container">' +
            heading + escape(section.heading) + closing + body + cards +
            _link(section.button_label, section.button_url) +
            "</div></section>")


def render_page(site: Site, slug: str) -> str:
    page = next((item for item in site.pages if item.slug == slug), None)
    if page is None:
        raise ValueError("Page not found")
    colors = THEMES[site.theme]
    css = (
        ":root{color-scheme:" + ("light" if site.theme == "light" else "dark") +
        ";--bg:" + colors["bg"] + ";--surface:" + colors["surface"] +
        ";--text:" + colors["text"] + ";--accent:" + colors["accent"] +
        "}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);"
        "font:16px/1.65 system-ui,sans-serif}a{color:inherit}.container{width:min(100% - 36px,1040px);"
        "margin:auto}.navbar{display:flex;align-items:center;gap:20px;flex-wrap:wrap;padding:20px 0}"
        ".brand{font-size:21px;font-weight:800;margin-right:auto}.navlinks{display:flex;gap:18px;flex-wrap:wrap}"
        ".section{padding:70px 0;border-bottom:1px solid color-mix(in srgb,var(--text) 10%,transparent)}"
        ".section-hero{padding:100px 0;background:linear-gradient(110deg,var(--surface),var(--bg))}"
        "h1,h2{line-height:1.15;letter-spacing:-.025em}h1{font-size:clamp(34px,7vw,66px)}"
        "h2{font-size:clamp(26px,4vw,44px)}p{max-width:70ch;white-space:normal}"
        ".features{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));"
        "gap:12px;padding:0;list-style:none}.features li{padding:20px;border-radius:14px;"
        "background:var(--surface)}.action{display:inline-block;background:var(--accent);"
        "color:var(--bg);padding:12px 20px;text-decoration:none;font-weight:700;"
        "border-radius:10px}.footer{padding:40px 0;opacity:.85}"
    )
    nav = "".join(
        '<a href="' + ("index.html" if p.slug == "index" else p.slug + ".html") +
        '">' + escape(p.title) + "</a>" for p in site.pages
    )
    return ("<!doctype html><html lang=\"pl\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<meta name=\"referrer\" content=\"no-referrer\">"
            "<title>" + escape(page.title) + " | " + escape(site.name) + "</title>"
            "<meta name=\"description\" content=\"" + escape(site.tagline, quote=True) + "\">"
            "<style>" + css + "</style></head><body>"
            "<header class=\"container navbar\"><span class=\"brand\">" + escape(site.name) +
            "</span><nav class=\"navlinks\" aria-label=\"Nawigacja\">" + nav + "</nav></header>"
            "<main>" + "".join(_section(s) for s in page.sections) + "</main>"
            "<footer class=\"container footer\">" + escape(site.name) +
            " — wygenerowano lokalnie w Unthinkable AI</footer></body></html>")


def export_site_zip(site: Site) -> bytes:
    out = io.BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED, compresslevel=7) as archive:
        for page in site.pages:
            path = "index.html" if page.slug == "index" else page.slug + ".html"
            archive.writestr(path, render_page(site, page.slug))
        archive.writestr("site.json", site.model_dump_json(indent=2))
        archive.writestr("README.txt",
                         "Static site exported from Unthinkable AI.\n"
                         "No server, credentials, database, backend or deployment is included.\n"
                         "Upload the HTML files to your own static hosting provider.\n")
    return out.getvalue()


def site_from_snapshot(snapshot: dict) -> Site:
    if snapshot.get("format") != "unthinkable-nocode-data-wrapper-v1":
        raise ValueError("Unsupported wrapper format")
    originals = snapshot.get("pages", [])
    if not isinstance(originals, list) or not 1 <= len(originals) <= 12:
        raise ValueError("Expected 1..12 pages in wrapper")
    pages = []
    for idx, original in enumerate(originals):
        if not isinstance(original, dict):
            raise ValueError("Invalid wrapper page")
        title = str(original.get("title") or f"Strona {idx+1}")[:120]
        sections = [Section(type="hero", heading=title,
                            body=str(original.get("description", ""))[:3500])]
        for heading in (original.get("headings") or [])[:12]:
            if isinstance(heading, dict) and heading.get("text"):
                sections.append(Section(type="text", heading=str(heading["text"])[:150]))
        pages.append(Page(slug="index" if idx == 0 else f"page-{idx+1}",
                          title=title, sections=sections))
    return Site(name=pages[0].title, pages=pages)
