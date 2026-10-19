"""Declarative NoCode website renderer. Every user-controlled value is escaped.

There is no arbitrary JavaScript injection, command execution, network fetch,
untrusted HTML insertion, backend or database extraction.
"""
from __future__ import annotations

from html import escape
import io
import json
import re
import zipfile
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, model_validator
from typing import Literal

BlockKind = Literal["heading", "paragraph", "feature", "button"]
_HEX = r"^#[a-fA-F0-9]{6}$"


class SiteBlock(BaseModel):
    kind: BlockKind
    text: str = Field(min_length=1, max_length=1200)
    subtitle: str = Field(default="", max_length=500)
    link: str = Field(default="", max_length=2048)

    @model_validator(mode="after")
    def validate_link(self):
        if self.kind != "button" and self.link:
            raise ValueError("Only button blocks accept links")
        if self.kind == "button":
            if not self.link:
                raise ValueError("Buttons must link somewhere")
            value = urlsplit(self.link)
            valid_path = self.link.startswith("/") and not self.link.startswith("//") \
                         and not self.link.startswith("/\\")
            valid_https = value.scheme == "https" and bool(value.hostname) and \
                          not value.username and not value.password
            if not (valid_path or valid_https) or any(c in self.link for c in ('"', "'", "<", ">", "\n", "\r")):
                raise ValueError("Buttons require safe local paths or HTTPS URLs")
        return self


class SiteDesign(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=320)
    accent: str = Field(default="#876BFF", pattern=_HEX)
    background: str = Field(default="#0B0A11", pattern=_HEX)
    blocks: list[SiteBlock] = Field(min_length=1, max_length=60)
    footer: str = Field(default="Created with Unthinkable AI", max_length=300)


def render_html(design: SiteDesign) -> str:
    name, desc, footer = (escape(x, quote=True) for x in
                          (design.name, design.description, design.footer))
    sections = []
    for item in design.blocks:
        title = escape(item.text, quote=True)
        subtitle = escape(item.subtitle, quote=True)
        if item.kind == "heading":
            section = f"<h1>{title}</h1>"
        elif item.kind == "paragraph":
            section = f"<p>{title}</p>"
        elif item.kind == "feature":
            section = f'<article class="feature"><h2>{title}</h2><p>{subtitle}</p></article>'
        else:
            link = escape(item.link, quote=True)
            section = f'<a class="button" href="{link}" rel="noopener noreferrer">{title}</a>'
        sections.append(section)
    content = "\n".join(sections)
    return f"""<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; object-src 'none'; form-action 'none'; style-src 'unsafe-inline'; img-src 'none';">
<title>{name}</title>
<style>
:root {{color-scheme:dark;--bg:{design.background};--accent:{design.accent};}}
* {{box-sizing:border-box}}
body {{margin:0;font:17px/1.6 system-ui,sans-serif;background:var(--bg);color:#f8f7ff}}
main {{margin:auto;max-width:960px;padding:clamp(24px,8vw,100px) 24px}}
h1 {{font-size:clamp(34px,7vw,74px);line-height:1.08;letter-spacing:-.04em}}
h2 {{font-size:25px}}p {{color:#cecbd7}}
.feature {{border:1px solid #ffffff24;padding:24px;border-radius:20px;margin:18px 0}}
.button {{display:inline-block;margin:20px 0;padding:15px 25px;background:var(--accent);color:#080808;text-decoration:none;border-radius:12px;font-weight:700}}
.button:focus-visible {{outline:3px solid white;outline-offset:4px}}
footer {{padding:40px 24px;text-align:center;border-top:1px solid #ffffff20;color:#aaa}}
</style></head><body><main><header><strong>{name}</strong></header>
{content}
</main><footer>{footer}</footer></body></html>"""


def export_zip(design: SiteDesign) -> bytes:
    html = render_html(design)
    manifest = {
        "format": "unthinkable-web-nocode-v1",
        "design": design.model_dump(mode="json"),
        "generated_assets": ["index.html", "site.json"],
        "backend_included": False,
        "deployment_performed": False,
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("index.html", html)
        archive.writestr("site.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return out.getvalue()
