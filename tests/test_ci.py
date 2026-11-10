import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import SLUGS  # noqa: E402
import check  # noqa: E402

WORKFLOWS = ROOT / ".github" / "workflows"
JOB_KEY = re.compile(r"^  ([a-z0-9-]+):$", re.MULTILINE)


def jobs() -> dict[str, str]:
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    parts = JOB_KEY.split(text.split("\njobs:\n", 1)[1])
    return dict(zip(parts[1::2], parts[2::2]))


class CiTests(unittest.TestCase):
    def test_every_app_has_a_job(self):
        self.assertLessEqual({"validate", "smoke", *SLUGS}, set(jobs()))

    def test_app_jobs_run_inside_their_folder(self):
        found = jobs()
        for slug in SLUGS:
            with self.subTest(slug=slug):
                self.assertIn(f"working-directory: {slug}", found[slug])
        self.assertIn("working-directory: visual-studio", found["visual-studio-windows"])

    def test_validate_covers_three_platforms(self):
        self.assertIn("ubuntu-latest, macos-latest, windows-latest", jobs()["validate"])

    def test_smoke_requires_installed_apps(self):
        self.assertIn('APOLLO_SMOKE_REQUIRED: "1"', jobs()["smoke"])

    def test_firefox_job_dry_runs_release(self):
        self.assertIn("firefox_release.py --dry-run firefox-v", jobs()["firefox"].replace('"', ""))

    def test_no_nested_github_directories(self):
        self.assertEqual([], sorted(ROOT.glob("*/.github")))

    def test_firefox_release_triggers_on_prefixed_tags(self):
        self.assertIn('"firefox-v*"', (WORKFLOWS / "firefox-release.yml").read_text(encoding="utf-8"))

    def test_vscode_package_points_at_monorepo(self):
        package = json.loads((ROOT / "vscode" / "package.json").read_text(encoding="utf-8"))
        script = package["scripts"]["package"]
        self.assertIn("--baseContentUrl https://github.com/apollo-theme/apollo-theme/blob/main/vscode", script)
        self.assertIn("--baseImagesUrl https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/vscode", script)

    def test_layout_rejects_nested_github(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for slug in SLUGS:
                (root / slug).mkdir()
            (root / "vim" / ".github").mkdir()
            with mock.patch.object(check, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "vim: nested .github is not allowed"):
                    check.check_layout()


if __name__ == "__main__":
    unittest.main()
