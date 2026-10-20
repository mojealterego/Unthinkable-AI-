"""Configure Flutter Android shell for BYOM loopback inference only.

Run after flutter create, and on every rebuilt Android native project. No
global usesCleartextTraffic=true. No vendor account or remote plaintext hosts.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PERMISSION = '<uses-permission android:name="android.permission.INTERNET" />'
CONFIG = """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
  <base-config cleartextTrafficPermitted="false" />
  <domain-config cleartextTrafficPermitted="true">
    <domain>localhost</domain>
    <domain>127.0.0.1</domain>
  </domain-config>
</network-security-config>
"""


def configure(project: Path) -> None:
    manifest = project / "android/app/src/main/AndroidManifest.xml"
    if not manifest.exists():
        raise FileNotFoundError("Run flutter create --platforms android first")
    xml = manifest.read_text(encoding="utf-8")
    if "xmlns:android" not in xml or not re.search(r"<application\b", xml):
        raise ValueError("Unexpected Android manifest")
    if "android.permission.INTERNET" not in xml:
        xml = xml.replace("<application", "  " + PERMISSION + "\n    <application", 1)
    if 'android:networkSecurityConfig=' not in xml:
        xml = xml.replace(
            "<application",
            '<application android:networkSecurityConfig="@xml/network_security_config"',
            1,
        )
    # Invalid or surprising manifest changes fail rather than being silently saved.
    ET.fromstring(xml)
    manifest.write_text(xml, encoding="utf-8")
    folder = project / "android/app/src/main/res/xml"
    folder.mkdir(parents=True, exist_ok=True)
    resource = folder / "network_security_config.xml"
    resource.write_text(CONFIG, encoding="utf-8")
    ET.fromstring(resource.read_text(encoding="utf-8"))
    print("BYOM Android: INTERNET permission + loopback-only cleartext config verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".", type=Path)
    args = parser.parse_args()
    configure(args.project)
