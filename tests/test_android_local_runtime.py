"""Ensure BYOM localhost transport is enabled without global cleartext traffic."""
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.configure_android_local_runtime import configure

MANIFEST = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:label="unthinkable_ai" />
</manifest>"""


class AndroidLocalRuntimeConfigTests(unittest.TestCase):
    def test_idempotent_loopback_only_network_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "android/app/src/main/AndroidManifest.xml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(MANIFEST, encoding="utf-8")
            configure(root)
            configure(root)
            result = manifest.read_text()
            self.assertEqual(result.count("android.permission.INTERNET"), 1)
            self.assertEqual(result.count("android:networkSecurityConfig"), 1)
            xml = (manifest.parent / "res/xml/network_security_config.xml").read_text()
            self.assertIn('cleartextTrafficPermitted="false"', xml)
            self.assertIn("<domain>127.0.0.1</domain>", xml)
            self.assertIn("<domain>localhost</domain>", xml)
            self.assertNotIn('usesCleartextTraffic="true"', result)
            self.assertNotIn('<domain>example.com</domain>', xml)


if __name__ == "__main__":
    unittest.main()
