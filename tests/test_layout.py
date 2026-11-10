import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import APPS, CLONE_APPS, MONOREPO, SLUGS, readme_blocks  # noqa: E402
import check  # noqa: E402


class LayoutTests(unittest.TestCase):
    def test_seventeen_slugs(self):
        self.assertEqual(17, len(SLUGS))
        self.assertEqual(SLUGS, tuple(APPS))

    def test_every_app_is_a_tracked_folder(self):
        modes = subprocess.run(["git", "ls-files", "-s"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertNotIn("160000", modes)
        check.check_layout()

    def test_source_pin_matches_palette_bytes(self):
        check.check_source_pin(ROOT)

    def test_bad_pin_fails(self):
        with tempfile.TemporaryDirectory() as t:
            shutil.copytree(ROOT / "palette", Path(t) / "palette")
            p = Path(t) / "palette" / "SOURCE.json"
            d = json.loads(p.read_text())
            d["sha256"]["apollo.json"] = "0" * 64
            p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError, "apollo.json"):
                check.check_source_pin(Path(t))

    def test_gecko_ids_unchanged(self):
        for f, gid in (
            ("firefox/manifest.json", "humble-apollo@d0n9x1n"),
            ("firefox/variants/light/manifest.json", "apollo-light@d0n9x1n"),
        ):
            self.assertEqual(gid, json.loads((ROOT / f).read_text())["browser_specific_settings"]["gecko"]["id"])

    def test_clone_apps_and_monorepo(self):
        self.assertEqual(("vim", "nvim", "tmux", "rmux", "powershell", "bat", "eza"), CLONE_APPS)
        self.assertTrue(set(CLONE_APPS) <= set(SLUGS))
        self.assertEqual("https://github.com/apollo-theme/apollo-theme", MONOREPO)

    def test_readme_blocks_returns_fenced_bodies_after_marker(self):
        text = (
            "intro\n<!-- smoke:install -->\n```sh\nmkdir -p a\ncp x a/\n```\n"
            "```sh\nunmarked\n```\n"
            "<!-- smoke:other -->\n```sh\nother\n```\n"
            "<!-- smoke:install -->\n\n~~~powershell\nImport-Module x\n~~~\n"
        )
        self.assertEqual(["mkdir -p a\ncp x a/\n", "Import-Module x\n"], readme_blocks(text, "install"))
        self.assertEqual(["other\n"], readme_blocks(text, "other"))
        self.assertEqual([], readme_blocks(text, "missing"))


if __name__ == "__main__":
    unittest.main()
