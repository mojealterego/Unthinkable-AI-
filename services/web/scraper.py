"""Read-only, owned-host HTML extraction and structured API wrapper.

Safety: explicit administrator allowlist, public IP verification *and* connection
pinning, HTTPS-only, no redirects/proxies/cookies/credentials, robots.txt,
bounded requests and body sizes. Executes no JavaScript, crawls no forms.
"""
from __future__ import annotations

from html.parser import HTMLParser
import http.client
import ipaddress
import os
import re
import socket
import ssl
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

MAX_BODY = 1_500_000
USER_AGENT = "UnthinkableAuthorizedWebsiteAudit/1.0"
_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?$")


class ScrapeBlocked(ValueError):
    pass


def canonical_url(url: str, allowed_hosts: set[str]) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise ScrapeBlocked("Invalid or oversized URL")
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.port not in (None, 443):
        raise ScrapeBlocked("Only credential-free HTTPS:443 targets are permitted")
    host = parts.hostname.lower().rstrip(".")
    if not _HOST.fullmatch(host) or ".." in host or host not in allowed_hosts:
        raise ScrapeBlocked("Host is not on the administrator allowlist")
    if parts.fragment or parts.query or "\\" in parts.path:
        raise ScrapeBlocked("Fragments, query parameters and backslashes are prohibited")
    path = parts.path or "/"
    if "//" in path or any(p in {".", ".."} for p in path.split("/")):
        raise ScrapeBlocked("Ambiguous path")
    return urlunsplit(("https", host, path, "", ""))


def allowed_hosts_from_environment() -> set[str]:
    value = os.getenv("WEB_SCRAPER_ALLOWED_HOSTS", "")
    hosts = {name.strip().lower() for name in value.split(",") if name.strip()}
    return {h for h in hosts if _HOST.fullmatch(h) and ".." not in h}


def _public_addresses(host: str) -> list[str]:
    ips: list[str] = []
    try:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ScrapeBlocked("DNS lookup failed") from exc
    for record in records:
        addr = record[4][0]
        if not ipaddress.ip_address(addr).is_global:
            raise ScrapeBlocked("Private, reserved or local DNS addresses are refused")
        if addr not in ips:
            ips.append(addr)
    if not ips:
        raise ScrapeBlocked("No resolved global IP addresses")
    return ips


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, ip: str):
        super().__init__(host, port=443, timeout=8, context=ssl.create_default_context())
        self.ip = ip

    def connect(self):
        # Connects only to the validated literal IP; TLS SNI and certificate match host.
        plain = socket.create_connection((self.ip, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(plain, server_hostname=self.host)
        except BaseException:
            plain.close()
            raise


def _read_https(url: str, allowed_hosts: set[str], *, robots: bool = False) -> tuple[int, str, bytes]:
    safe = canonical_url(url, allowed_hosts)
    parts = urlsplit(safe)
    addr = _public_addresses(parts.hostname)
    connection = _PinnedHTTPS(parts.hostname, addr[0])
    try:
        connection.request("GET", parts.path, headers={
            "Host": parts.hostname, "User-Agent": USER_AGENT,
            "Accept": "text/html" if not robots else "text/plain",
            "Accept-Encoding": "identity", "Connection": "close",
        })
        response = connection.getresponse()
        if response.status in (301, 302, 303, 307, 308):
            raise ScrapeBlocked("Redirects are not followed")
        if response.status == 404 and robots:
            return 404, "text/plain", b""
        if response.status != 200:
            raise ScrapeBlocked(f"Source returned HTTP {response.status}")
        declared = response.getheader("Content-Length")
        if declared and (not declared.isdigit() or int(declared) > MAX_BODY):
            raise ScrapeBlocked("Source body exceeds size limit")
        content_type = response.getheader("Content-Type", "").lower()
        if robots:
            if "text/plain" not in content_type and "text/" not in content_type:
                raise ScrapeBlocked("Invalid robots response type")
        elif "text/html" not in content_type:
            raise ScrapeBlocked("Source is not HTML")
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise ScrapeBlocked("HTML response exceeds size limit")
        return response.status, content_type, body
    except (OSError, ssl.SSLError, http.client.HTTPException, TimeoutError) as exc:
        raise ScrapeBlocked("HTTPS connection or response failed") from exc
    finally:
        connection.close()


class PageExtractor(HTMLParser):
    """Extracts public presentation facts, not credentials, scripts or hidden inputs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_description = ""
        self.headings: list[dict] = []
        self.links: list[dict] = []
        self.images: list[dict] = []
        self.forms: int = 0
        self._capture: str | None = None
        self._heading_level = ""
        self._buffer: list[str] = []
        self._excluded = 0

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag in {"script", "style", "noscript", "template"}:
            self._excluded += 1
            return
        if self._excluded:
            return
        if tag == "title" or (tag in {"h1", "h2", "h3"} and len(self.headings) < 100):
            self._capture = tag
            self._buffer = []
        if tag == "meta" and props.get("name", "").lower() == "description":
            self.meta_description = (props.get("content") or "")[:500]
        if tag == "a" and len(self.links) < 300 and props.get("href"):
            self.links.append({"href": props["href"][:1024], "text": ""})
        if tag == "img" and len(self.images) < 100:
            self.images.append({"src": (props.get("src") or "")[:1024],
                                "alt": (props.get("alt") or "")[:250]})
        if tag == "form":
            self.forms += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "template"}:
            self._excluded = max(0, self._excluded - 1)
            return
        if self._capture == tag:
            value = " ".join("".join(self._buffer).split())[:300]
            if tag == "title":
                self.title = value
            elif value:
                self.headings.append({"level": tag, "text": value})
            self._capture = None
            self._buffer = []

    def handle_data(self, data):
        if not self._excluded and self._capture:
            self._buffer.append(data[:1000])

    def public_structure(self, url: str) -> dict:
        return {
            "url": url, "title": self.title,
            "description": self.meta_description,
            "headings": self.headings, "links": self.links,
            "images": self.images, "form_count": self.forms,
            "raw_html_exported": False, "script_executed": False,
            "private_backend_extracted": False,
        }


def extract_html(html: str, url: str) -> dict:
    if len(html.encode("utf-8")) > MAX_BODY:
        raise ScrapeBlocked("HTML input too large")
    parser = PageExtractor()
    parser.feed(html)
    parser.close()
    return parser.public_structure(url)


def _check_robots(url: str, hosts: set[str]) -> None:
    parts = urlsplit(url)
    robots_url = "https://" + parts.hostname + "/robots.txt"
    status, _, body = _read_https(robots_url, hosts, robots=True)
    if status == 404:
        return
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(body.decode("utf-8", "replace").splitlines())
    if not parser.can_fetch(USER_AGENT, url):
        raise ScrapeBlocked("Robots policy does not permit this path")


def scrape_pages(url: str, allowed_hosts: set[str], *, max_pages: int = 3) -> dict:
    if not allowed_hosts:
        raise ScrapeBlocked("No administrator-approved hosts configured")
    if not 1 <= max_pages <= 5:
        raise ScrapeBlocked("Page limit must be 1..5")
    root = canonical_url(url, allowed_hosts)
    root_host = urlsplit(root).hostname
    queue: list[str] = [root]
    visited: set[str] = set()
    pages: list[dict] = []
    while queue and len(pages) < max_pages:
        target = queue.pop(0)
        if target in visited:
            continue
        visited.add(target)
        _check_robots(target, allowed_hosts)
        _, _, html = _read_https(target, allowed_hosts)
        page = extract_html(html.decode("utf-8", "replace"), target)
        pages.append(page)
        for link in page["links"]:
            try:
                candidate = canonical_url(urljoin(target, link["href"]), allowed_hosts)
            except (ScrapeBlocked, ValueError):
                continue
            if urlsplit(candidate).hostname == root_host and candidate not in visited and candidate not in queue:
                queue.append(candidate)
    return {
        "format": "unthinkable-authorized-site-wrapper-v1",
        "mode": "read_only_html",
        "source_url": root,
        "pages": pages,
        "pages_scanned": len(pages),
        "scripts_executed": False,
        "backend_extracted": False,
        "database_extracted": False,
    }


def make_api_wrapper(snapshot: dict) -> dict:
    """Structured site-data wrapper for the NoCode builder, not arbitrary API proxy."""
    if snapshot.get("format") != "unthinkable-authorized-site-wrapper-v1":
        raise ValueError("Unsupported snapshot format")
    pages = snapshot.get("pages", [])
    if not isinstance(pages, list) or len(pages) > 5:
        raise ValueError("Invalid pages list")
    return {
        "format": "unthinkable-nocode-data-wrapper-v1",
        "read_only": True,
        "source_url": snapshot.get("source_url", ""),
        "pages": [
            {
                "path": urlsplit(p.get("url", "")).path,
                "title": str(p.get("title", ""))[:250],
                "description": str(p.get("description", ""))[:500],
                "headings": (p.get("headings") or [])[:100],
            } for p in pages if isinstance(p, dict)
        ],
        "upstream_credentials_copied": False,
        "backend_logic_cloned": False,
    }
