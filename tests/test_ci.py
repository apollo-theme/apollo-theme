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


def actions_glob(pattern: str, ref: str) -> bool:
    """GitHub Actions filter globbing: `*` stops at `/`, `**` crosses it."""
    regex = ""
    i = 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            regex, i = regex + ".*", i + 2
        elif pattern[i] == "*":
            regex, i = regex + "[^/]*", i + 1
        else:
            regex, i = regex + re.escape(pattern[i]), i + 1
    return re.fullmatch(regex, ref) is not None


def tag_triggers(text: str, tag: str) -> bool:
    match = re.search(r"tags: \[([^\]]*)\]", text)
    if not match:
        return False
    included = False
    for pattern in re.findall(r'"([^"]+)"', match.group(1)):
        if pattern.startswith("!"):
            included = included and not actions_glob(pattern[1:], tag)
        else:
            included = included or actions_glob(pattern, tag)
    return included


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

    def test_smoke_uses_preinstalled_pwsh(self):
        smoke = jobs()["smoke"]
        self.assertNotIn("--cask powershell", smoke)
        self.assertIn("pwsh --version", smoke)

    def test_firefox_job_dry_runs_release(self):
        self.assertIn("firefox_release.py --dry-run firefox-v", jobs()["firefox"].replace('"', ""))

    def test_no_nested_github_directories(self):
        self.assertEqual([], sorted(ROOT.glob("*/.github")))

    def test_firefox_release_triggers_on_prefixed_tags(self):
        self.assertIn('"firefox-v*"', (WORKFLOWS / "firefox-release.yml").read_text(encoding="utf-8"))

    def test_release_job_builds_every_app(self):
        self.assertIn("app_release.py --check-all", jobs()["release"])

    def test_app_release_covers_every_tag_but_firefox(self):
        text = (WORKFLOWS / "app-release.yml").read_text(encoding="utf-8")
        self.assertIn('tags: ["**", "!firefox-v*"]', text)
        self.assertIn('app_release.py --dry-run "$TAG"', text)
        self.assertIn("fail_on_unmatched_files: true", text)
        self.assertNotIn("gh release", text)
        self.assertIn("permissions: { contents: write }", text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn("body_path: RELEASE_NOTES.md", text)
        self.assertIn('files: "release-assets/*"', text)
        self.assertIn("${{ env.APP_NAME }}", text)

    def test_every_tag_push_runs_exactly_one_release_workflow(self):
        workflows = {path.name: path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml")}
        expected = {f"{slug}-v1.2.3": "firefox-release.yml" if slug == "firefox" else "app-release.yml" for slug in SLUGS}
        for tag in ("v1.2.3", "not-an-app", "release/v1.2.3", "a/b/c", "firefox-v1.2", "firefox-vX"):
            expected[tag] = "firefox-release.yml" if tag.startswith("firefox-v") else "app-release.yml"
        for tag, workflow in expected.items():
            with self.subTest(tag=tag):
                self.assertEqual([workflow], [name for name, text in workflows.items() if tag_triggers(text, tag)])

    def test_tag_glob_follows_actions_semantics(self):
        self.assertFalse(actions_glob("*", "release/v1"))
        self.assertTrue(actions_glob("**", "release/v1"))
        self.assertTrue(actions_glob("firefox-v*", "firefox-v1.2.3"))
        self.assertFalse(actions_glob("firefox-v*", "x/firefox-v1"))

    def test_every_release_attaches_checksums(self):
        self.assertIn("release-assets/*", (WORKFLOWS / "app-release.yml").read_text(encoding="utf-8"))
        self.assertIn("firefox/web-ext-artifacts/SHA256SUMS", (WORKFLOWS / "firefox-release.yml").read_text(encoding="utf-8"))

    def test_release_workflows_check_tag_first(self):
        app = (WORKFLOWS / "app-release.yml").read_text(encoding="utf-8")
        firefox = (WORKFLOWS / "firefox-release.yml").read_text(encoding="utf-8")
        app_check = app.index('app_release.py --check-tag "$TAG" --github-env "$GITHUB_ENV"')
        self.assertLess(app_check, app.index("generate.py --check"))
        firefox_check = firefox.index('firefox_release.py --dry-run "$TAG" --skip-build')
        self.assertLess(firefox_check, firefox.index("npm ci"))

    def test_missed_tags_can_be_released_through_ci(self):
        for name in ("app-release.yml", "firefox-release.yml"):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("workflow_dispatch:", text)
                self.assertIn('TAG: "${{ inputs.tag || github.ref_name }}"', text)
                self.assertIn('ref: "${{ env.TAG }}"', text)
                self.assertIn('tag_name: "${{ env.TAG }}"', text)
                self.assertNotIn("GITHUB_REF_NAME", text)

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
