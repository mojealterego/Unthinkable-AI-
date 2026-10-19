"""Safe operator-configured MP4 archiving for completed VisionStory jobs.

The provider's video_url is NOT trusted input: outbound fetches require an
exact administrator-approved HTTPS hostname and a public, DNS-pinned IP.
No cookies or provider API key are sent to the download host.
"""
from __future__ import annotations

import http.client
import ipaddress
import os
from pathlib import Path
import re
import socket
import ssl
import tempfile
from urllib.parse import urlsplit

from .client import VisionStoryError

MAX_MP4_BYTES = 120 * 1024 * 1024
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{3,160}$")


def archive_root() -> Path:
    raw = os.getenv("VISIONSTORY_MEDIA_DIR", "").strip()
    if not raw or not os.path.isabs(raw):
        raise VisionStoryError("Configure an absolute private media archive path", 503)
    path = Path(raw)
    if path.is_symlink():
        raise VisionStoryError("Archive root must not be a symlink", 503)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir():
        raise VisionStoryError("Media archive is unavailable", 503)
    return path


def mp4_path(video_id: str) -> Path:
    if not _VIDEO_ID.fullmatch(video_id):
        raise ValueError("Invalid video id")
    return archive_root() / (video_id + ".mp4")


def validate_download_url(url: str, allowed_hosts: set[str]) -> tuple[str, str]:
    if not isinstance(url, str) or len(url) > 4096 or any(c in url for c in "\r\n\t"):
        raise VisionStoryError("Invalid provider media URL", 422)
    try:
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.port not in (None, 443):
            raise ValueError
    except ValueError as exc:
        raise VisionStoryError("Provider media URL must be HTTPS port 443", 422) from exc
    if parts.username or parts.password or parts.fragment:
        raise VisionStoryError("Provider media URL includes prohibited components", 422)
    host = parts.hostname.lower().rstrip(".")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]", host) or ".." in host:
        raise VisionStoryError("Invalid download hostname", 422)
    if host not in allowed_hosts or not allowed_hosts:
        raise VisionStoryError("Media download hostname is not operator approved", 403)
    return host, parts.path + (("?" + parts.query) if parts.query else "") or "/"


def approved_download_hosts() -> set[str]:
    return {
        host.strip().lower().rstrip(".")
        for host in os.getenv("VISIONSTORY_MEDIA_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    }


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, ip: str):
        super().__init__(
            host, port=443, timeout=30, context=ssl.create_default_context()
        )
        self._ip = ip

    def connect(self):
        plain = socket.create_connection((self._ip, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(plain, server_hostname=self.host)
        except BaseException:
            plain.close()
            raise


def _resolve_public_ip(host: str) -> str:
    try:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise VisionStoryError("Could not resolve approved media hostname") from exc
    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise VisionStoryError("Approved media hostname did not resolve")
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        mapped = getattr(parsed, "ipv4_mapped", None)
        if mapped:
            parsed = mapped
        if not parsed.is_global:
            raise VisionStoryError("Media hostname resolves to non-public IP", 403)
    return addresses[0]


def save_completed_mp4(video_id: str, video_url: str) -> tuple[str, int]:
    """Return file name and bytes after a bounded, verified, atomic download."""
    if not _VIDEO_ID.fullmatch(video_id):
        raise VisionStoryError("Invalid video id", 422)
    host, remote_path = validate_download_url(video_url, approved_download_hosts())
    ip = _resolve_public_ip(host)
    folder = archive_root()
    connection = PinnedHTTPS(host, ip)
    temp_path: Path | None = None
    try:
        connection.request(
            "GET", remote_path,
            headers={
                "Host": host,
                "Accept": "video/mp4,application/octet-stream",
                "Accept-Encoding": "identity",
                "User-Agent": "Unthinkable-AI-Media-Archive/1.0",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise VisionStoryError("Provider media download did not succeed")
        mime = (response.getheader("Content-Type", "") or "").lower().split(";")[0].strip()
        if mime not in ("video/mp4", "application/octet-stream", ""):
            raise VisionStoryError("Provider media is not an MP4 file")
        length = response.getheader("Content-Length")
        if length and (not length.isdigit() or int(length) > MAX_MP4_BYTES):
            raise VisionStoryError("Media file exceeds per-file archive limit", 413)
        total = 0
        with tempfile.NamedTemporaryFile(
            prefix=".visionstory-", suffix=".tmp", dir=folder, delete=False
        ) as output:
            temp_path = Path(output.name)
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_MP4_BYTES:
                    raise VisionStoryError("Media download exceeded the 120 MiB limit", 413)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        with temp_path.open("rb") as input_file:
            header = input_file.read(12)
        if len(header) < 12 or header[4:8] != b"ftyp":
            raise VisionStoryError("Downloaded bytes do not have an MP4 container header")
        filename = video_id + ".mp4"
        os.replace(temp_path, folder / filename)
        temp_path = None
        return filename, total
    except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
        raise VisionStoryError("Provider media download failed") from exc
    finally:
        connection.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
