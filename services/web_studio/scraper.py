"""Authorized and explicitly allowlisted HTTPS page inspector (no cookies/auth).

Only publicly exposed page structure is extracted. This does not acquire
private source code, server credentials, database contents, or hidden APIs.
"""
from __future__ import annotations

from html.parser import HTMLParser
import http.client
import ipaddress
import os
import re
import socket
import ssl
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

MAX_BYTES = 1_048_576
USER_AGENT = "UnthinkableWebStudio/1.0 (+authorized-site-inspection)"
_TEXT_LIMIT = 220


def _safe_ip(value: str) -> str:
    parsed = ipaddress.ip_address(value)
    if getattr(parsed, "ipv4_mapped", None):
        parsed = parsed.ipv4_mapped
    if not parsed.is_global:
        raise ValueError("Address resolves outside public IP space")
    return value


def authorize_target(raw: str, allowed_hosts: set[str]) -> tuple[str, str, str]:
    if not isinstance(raw, str) or len(raw) > 2048 or any(c in raw for c in "\r\n\t"):
        raise ValueError("Invalid target URL")
    u = urlsplit(raw)
    if u.scheme != "https" or not u.hostname or u.username or u.password or \
            u.port not in (None, 443) or u.fragment:
        raise ValueError("Only HTTPS port 443 without credentials or fragments is supported")
    host = u.hostname.lower().rstrip(".")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,251}[a-z0-9]", host) or ".." in host:
        raise ValueError("Invalid public DNS hostname")
    if host not in allowed_hosts or not allowed_hosts:
        raise PermissionError("Host is not in the administrator allowlist")
    if u.query:
        raise ValueError("Query strings are not accepted (may contain credentials)")
    return host, u.path or "/", u.geturl()


def permitted_hosts() -> set[str]:
    return {s.lower().strip().rstrip(".") for s in
            os.getenv("WEB_STUDIO_ALLOWED_HOSTS", "").split(",") if s.strip()}


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, hostname: str, ip: str):
        super().__init__(hostname, port=443, timeout=8, context=ssl.create_default_context())
        self._pinned_ip = ip

    def connect(self) -> None:
        plain = socket.create_connection((self._pinned_ip, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(plain, server_hostname=self.host)
        except BaseException:
            plain.close()
            raise


def _request(host: str, ip: str, path: str, limit: int = MAX_BYTES) -> tuple[int, str, bytes]:
    connection = _PinnedHTTPS(host, ip)
    try:
        connection.request("GET", path, headers={
            "Host": host,
            "User-Agent": USER_AGENT,
            "Accept": "text/html, text/plain;q=0.2",
            "Accept-Encoding": "identity",
            "Cookie": "",
        })
        response = connection.getresponse()
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Remote document exceeded size limit")
        return response.status, response.getheader("Content-Type", ""), data
    finally:
        connection.close()


def fetch_authorized_page(url: str, allowed_hosts: set[str] | None = None) -> str:
    host, path, _ = authorize_target(url, permitted_hosts() if allowed_hosts is None else allowed_hosts)
    if not host.isascii():
        raise ValueError("IDN domain must be represented as punycode")
    resolved = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    ips = sorted(set(_safe_ip(item[4][0]) for item in resolved))
    if not ips:
        raise ValueError("No public IP addresses resolved")
    # Pin one validated address for both robots.txt and document retrieval.
    ip = ips[0]
    robots_status, _, robots_data = _request(host, ip, "/robots.txt", limit=65536)
    if robots_status == 200:
        robots = RobotFileParser()
        robots.parse(robots_data.decode("utf-8", errors="replace").splitlines())
        if not robots.can_fetch(USER_AGENT, path):
            raise PermissionError("robots.txt disallows this fetch")
    elif robots_status not in (404, 410):
        raise PermissionError("Cannot verify site scraping policy")
    status, mime, data = _request(host, ip, path)
    if not (200 <= status < 300):
        raise ValueError("Remote source did not return a successful HTML response")
    if not mime.lower().split(";")[0].strip() in ("text/html", "application/xhtml+xml"):
        raise ValueError("The remote document is not HTML")
    return data.decode("utf-8", errors="replace")


class PageInspector(HTMLParser):
    def __init__(self, *, base_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.headings: list[dict[str, str]] = []
        self.paragraphs: list[str] = []
        self.links: list[dict[str, str]] = []
        self.images: list[str] = []
        self.forms_count = 0
        self._stack: list[str] = []
        self._skip = 0
        self._link_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in ("script", "style", "noscript", "template", "svg"):
            self._skip += 1
        if self._skip:
            self._stack.append(tag)
            return
        data = dict(attrs)
        self._stack.append(tag)
        if tag == "form":
            self.forms_count += 1
        if tag == "a" and len(self.links) < 120:
            link = data.get("href", "") or ""
            resolved = urljoin(self.base_url, link) if self.base_url else link
            if resolved.startswith(("https://", "http://", "/")) and len(resolved) < 2048:
                self._link_url = resolved
                self.links.append({"href": resolved, "text": ""})
        if tag == "img" and len(self.images) < 80:
            src = data.get("src", "") or ""
            resolved = urljoin(self.base_url, src) if self.base_url else src
            if resolved.startswith(("https://", "http://", "/")) and len(resolved) < 2048:
                self.images.append(resolved)

    def handle_endtag(self, tag: str) -> None:
        if self._stack:
            self._stack.pop()
        if tag.lower() in ("script", "style", "noscript", "template", "svg"):
            self._skip = max(0, self._skip - 1)
        if tag.lower() == "a":
            self._link_url = None

    def handle_data(self, value: str) -> None:
        if self._skip:
            return
        stripped = " ".join(value.split())[:_TEXT_LIMIT]
        if not stripped or not self._stack:
            return
        tag = self._stack[-1]
        if tag == "title" and not self.title:
            self.title = stripped
        elif tag in ("h1", "h2", "h3", "h4") and len(self.headings) < 100:
            self.headings.append({"level": tag, "text": stripped})
        elif tag == "p" and len(self.paragraphs) < 100:
            self.paragraphs.append(stripped)
        elif tag == "a" and self._link_url and self.links:
            self.links[-1]["text"] = (self.links[-1]["text"] + " " + stripped).strip()[:120]


def inspect_html(content: str, *, base_url: str = "") -> dict:
    if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_BYTES:
        raise ValueError("HTML is too large")
    if base_url and (urlsplit(base_url).scheme not in ("https", "http")):
        raise ValueError("Base URL must use HTTP(S)")
    inspector = PageInspector(base_url=base_url)
    inspector.feed(content)
    return {
        "title": inspector.title, "headings": inspector.headings,
        "paragraphs": inspector.paragraphs, "links": inspector.links,
        "images": inspector.images, "forms_count": inspector.forms_count,
        "scripts_executed": False, "secrets_extracted": False,
        "server_code_retrieved": False,
    }
