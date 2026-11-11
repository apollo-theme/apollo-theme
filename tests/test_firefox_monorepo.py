"""Monorepo-level checks for firefox/: standalone test boundary and root release wiring."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIREFOX = ROOT / "firefox"
WORKFLOWS = ROOT / ".github" / "workflows"
sys.path.insert(0, str(ROOT / "scripts"))

import firefox_release as release  # noqa: E402


def firefox_ci_job() -> str:
    """Return the `firefox:` job block from the root CI workflow."""
    ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^  firefox:\n(.*?)(?=^  [\w-]+:\n|\Z)", ci)
    if match is None:
        raise AssertionError("root ci.yml has no firefox job")
    return match.group(1)


class FirefoxStandaloneTests(unittest.TestCase):
    def test_firefox_folder_tests_pass_in_isolation(self):
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch) / "firefox"
            shutil.copytree(FIREFOX, copy, ignore=shutil.ignore_patterns("node_modules", "web-ext-artifacts", "__pycache__"))
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                cwd=copy, capture_output=True, text=True,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class FirefoxReleaseWiringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = (WORKFLOWS / "firefox-release.yml").read_text(encoding="utf-8")
        self.ci_job = firefox_ci_job()
        self.version = json.loads((FIREFOX / "package.json").read_text(encoding="utf-8"))["version"]

    def test_release_workflow_uses_target_qualified_name(self) -> None:
        self.assertIn('tags: ["firefox-v*"]', self.workflow)
        self.assertIn("working-directory: firefox", self.workflow)
        self.assertIn('name: "Apollo Themes for Firefox ${{ env.TAG }}"', self.workflow)
        # Release notes need tag history that shallow CI checkouts lack, so pin the heading template.
        script = (ROOT / "scripts" / "firefox_release.py").read_text(encoding="utf-8")
        self.assertIn('f"## Apollo Themes for Firefox {tag}"', script)

    def test_release_and_ci_cover_both_static_themes(self) -> None:
        self.assertEqual(
            {
                Path("manifest.json"): "humble-apollo@d0n9x1n",
                Path("variants/light/manifest.json"): "apollo-light@d0n9x1n",
            },
            release.GECKO_IDS,
        )
        for manifest_path, archive_name in (
            ("manifest.json", "apollo-theme.zip"),
            ("variants/light/manifest.json", "apollo-light-theme.zip"),
        ):
            with self.subTest(manifest_path=manifest_path):
                self.assertIn(Path(manifest_path), release.GECKO_IDS)
                self.assertIn(archive_name, release.ARTIFACTS)
                self.assertIn(f"firefox/web-ext-artifacts/{archive_name}", self.workflow)
                self.assertIn(f"firefox/web-ext-artifacts/{archive_name}", self.ci_job)
        for command in ("npm ci", "npm run check", "npm test", "npm run lint"):
            with self.subTest(command=command):
                self.assertIn(command, self.workflow)
                self.assertIn(f"- run: {command}", self.ci_job)
        self.assertIn("scripts/firefox_release.py --dry-run", self.workflow)
        self.assertIn("scripts/firefox_release.py --dry-run", self.ci_job)

    def test_release_rejects_tag_that_disagrees_with_either_manifest(self) -> None:
        version = self.version
        self.assertEqual(version, release.version_from_tag(f"firefox-v{version}"))
        release.check_versions(FIREFOX, version)
        release.check_gecko_ids(FIREFOX)
        for bad_tag in (f"v{version}", f"firefox-v{version}-rc1", "firefox-v1.1"):
            with self.subTest(bad_tag=bad_tag):
                with self.assertRaises(ValueError):
                    release.version_from_tag(bad_tag)
        with self.assertRaises(ValueError) as caught:
            release.check_versions(FIREFOX, "0.0.0")
        self.assertIn("light manifest", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
