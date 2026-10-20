#!/usr/bin/env python3
"""Safe VisionStory CLI / local MCP preflight for Unthinkable AI operators.

No installation, implicit network calls, paid creation, secret exposure, or deletion.
The optional --verify-access performs only the vendor's read-only credits command.
Use on an operator-controlled Linux/macOS/WSL host, not in the Android APK.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Callable


def checked_command(
    argv: list[str], *,
    runner: Callable = subprocess.run,
    timeout: int = 20,
) -> bool:
    environment = os.environ.copy()
    environment["VISIONSTORY_UPDATE_CHECK"] = "0"
    try:
        outcome = runner(
            argv, capture_output=True, text=True, timeout=timeout,
            check=False, env=environment,
        )
    except (OSError, TimeoutError, subprocess.TimeoutExpired):
        return False
    # Never print vendor output, stderr, credential, API URL, JSON or env content.
    return outcome.returncode == 0


def inspect(
    *, verify_access: bool = False,
    which: Callable = shutil.which,
    runner: Callable = subprocess.run,
) -> dict:
    binary = which("visionstory")
    mcp = which("visionstory-mcp")
    result = {
        "provider": "visionstory",
        "cli_installed": bool(binary),
        "cli_doctor": "unavailable",
        "cli_contract": "unavailable",
        "credits_read_only": "not_requested",
        "local_mcp_installed": bool(mcp),
        "local_mcp_check": "unavailable",
        "paid_operations_run": 0,
        "operations_deleted": 0,
        "provider_key_disclosed": False,
    }
    if binary:
        result["cli_doctor"] = "ok" if checked_command(
            [binary, "doctor"], runner=runner
        ) else "failed"
        result["cli_contract"] = "ok" if checked_command(
            [binary, "contract"], runner=runner
        ) else "failed"
        if verify_access:
            # A custom base URL can be dangerous; never send a key there by default.
            base = os.environ.get("VISIONSTORY_API_BASE", "").strip()
            if base and base.rstrip("/") != "https://openapi.visionstory.ai":
                result["credits_read_only"] = "blocked_custom_api_base"
            elif result["cli_doctor"] != "ok":
                result["credits_read_only"] = "blocked_doctor_failed"
            else:
                result["credits_read_only"] = "ok" if checked_command(
                    [binary, "credits"], runner=runner, timeout=30,
                ) else "failed"
    if mcp:
        # Only inspect an already installed executable. Running uvx may download
        # packages and is therefore never triggered by this diagnostic.
        result["local_mcp_check"] = "ok" if checked_command(
            [mcp, "--check"], runner=runner
        ) else "failed"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-access", action="store_true",
        help="Explicitly run a read-only credits request (may use your locally stored key)",
    )
    args = parser.parse_args(argv)
    report = inspect(verify_access=args.verify_access)
    print(json.dumps(report, sort_keys=True))
    if not report["cli_installed"] or report["cli_doctor"] != "ok":
        return 1
    if args.verify_access and report["credits_read_only"] != "ok":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
