"""Vendor CLI/MCP diagnostics without subprocess execution or network traffic."""
import os
import subprocess
import unittest
from unittest.mock import patch, Mock
from tools.visionstory_cli_preflight import inspect


class VisionStoryCLIPreflightTest(unittest.TestCase):
    def test_no_cli_means_no_execution(self):
        called = []
        report = inspect(which=lambda name: None,
                         runner=lambda *args, **kwargs: called.append(args))
        self.assertEqual(report["cli_doctor"], "unavailable")
        self.assertEqual(report["credits_read_only"], "not_requested")
        self.assertEqual(called, [])

    def test_only_whitelisted_read_only_commands(self):
        commands = []
        def run(argv, **kwargs):
            commands.append(argv)
            self.assertEqual(kwargs["env"]["VISIONSTORY_UPDATE_CHECK"], "0")
            return Mock(returncode=0, stdout="SECRET", stderr="SECRET")
        report = inspect(
            which=lambda name: "/usr/bin/" + name, runner=run,
            verify_access=True,
        )
        self.assertEqual(report["cli_doctor"], "ok")
        self.assertEqual(report["cli_contract"], "ok")
        self.assertEqual(report["credits_read_only"], "ok")
        self.assertEqual(report["local_mcp_check"], "ok")
        self.assertEqual(commands, [
            ["/usr/bin/visionstory", "doctor"],
            ["/usr/bin/visionstory", "contract"],
            ["/usr/bin/visionstory", "credits"],
            ["/usr/bin/visionstory-mcp", "--check"],
        ])
        self.assertFalse(report["provider_key_disclosed"])
        self.assertEqual(report["paid_operations_run"], 0)

    def test_custom_api_host_prevents_use_of_vendor_secret(self):
        cmds = []
        def run(argv, **kwargs):
            cmds.append(argv)
            return Mock(returncode=0)
        with patch.dict(os.environ, {"VISIONSTORY_API_BASE": "https://untrusted.example"}):
            report = inspect(which=lambda n: "/bin/visionstory" if n == "visionstory" else None,
                             runner=run, verify_access=True)
        self.assertEqual(report["credits_read_only"], "blocked_custom_api_base")
        self.assertFalse(any("credits" in parts for parts in cmds))

    def test_doctor_failure_blocks_credits_request(self):
        cmds = []
        def run(argv, **kwargs):
            cmds.append(argv)
            return Mock(returncode=1 if "doctor" in argv else 0)
        report = inspect(which=lambda n: "/bin/visionstory" if n == "visionstory" else None,
                         runner=run, verify_access=True)
        self.assertEqual(report["credits_read_only"], "blocked_doctor_failed")
        self.assertFalse(any("credits" in parts for parts in cmds))

    def test_process_timeouts_cannot_create_paid_jobs(self):
        def timeout(argv, **kwargs):
            raise subprocess.TimeoutExpired(cmd=argv, timeout=1)
        report = inspect(which=lambda n: "/bin/visionstory" if n == "visionstory" else None,
                         runner=timeout, verify_access=True)
        self.assertEqual(report["credits_read_only"], "blocked_doctor_failed")
        self.assertEqual(report["paid_operations_run"], 0)


if __name__ == "__main__":
    unittest.main()
