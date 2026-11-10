import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import firefox_release  # noqa: E402
from firefox_release import build, check_gecko_ids, check_versions, main, release_notes, version_from_tag  # noqa: E402

FIREFOX = ROOT / "firefox"


def git(*args: str, cwd: Path) -> str:
    command = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false", *args]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_file(repo: Path, relative: str, message: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(message + "\n", encoding="utf-8")
    git("add", relative, cwd=repo)
    git("commit", "-q", "-m", message, cwd=repo)


def tag_exists(tag: str) -> bool:
    return subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], cwd=ROOT, capture_output=True).returncode == 0


class TagTests(unittest.TestCase):
    def test_version_from_tag(self):
        self.assertEqual("1.1.1", version_from_tag("firefox-v1.1.1"))

    def test_bad_tags_rejected(self):
        for tag in ("v1.1.1", "firefox-v1.1"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, r"^tag must look like firefox-vX\.Y\.Z$"):
                version_from_tag(tag)


class VersionTests(unittest.TestCase):
    def test_current_versions_match(self):
        check_versions(FIREFOX, "1.1.1")

    def test_mismatch_names_every_source(self):
        with self.assertRaises(ValueError) as caught:
            check_versions(FIREFOX, "9.9.9")
        message = str(caught.exception)
        for name in ("dark manifest", "light manifest", "package"):
            self.assertIn(name, message)


class GeckoIdTests(unittest.TestCase):
    def test_current_ids_pass(self):
        check_gecko_ids(FIREFOX)

    def test_changed_light_id_fails(self):
        with tempfile.TemporaryDirectory() as t:
            copy = Path(t) / "firefox"
            (copy / "variants" / "light").mkdir(parents=True)
            shutil.copy(FIREFOX / "manifest.json", copy / "manifest.json")
            light = json.loads((FIREFOX / "variants" / "light" / "manifest.json").read_text(encoding="utf-8"))
            light["browser_specific_settings"]["gecko"]["id"] = "changed@example.com"
            (copy / "variants" / "light" / "manifest.json").write_text(json.dumps(light), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "gecko id changed"):
                check_gecko_ids(copy)


class BuildTests(unittest.TestCase):
    def test_build_runs_npm_and_returns_both_zips(self):
        calls = []

        def fake(args, **kwargs):
            calls.append((args, kwargs.get("cwd")))

        with tempfile.TemporaryDirectory() as t:
            directory = Path(t)
            paths = build(directory, run=fake)
        self.assertEqual([(["npm", "run", "build"], directory)], calls)
        self.assertEqual(
            [directory / "web-ext-artifacts" / "apollo-theme.zip", directory / "web-ext-artifacts" / "apollo-light-theme.zip"],
            paths,
        )


class ReleaseNotesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git("init", "-q", cwd=self.repo)

    def tearDown(self):
        self._tmp.cleanup()

    def test_monorepo_notes_only_list_firefox_commits(self):
        commit_file(self.repo, "firefox/a.txt", "First Firefox change")
        git("tag", "firefox-v1.0.0", cwd=self.repo)
        git("tag", "other-v1.0.0", cwd=self.repo)
        commit_file(self.repo, "vscode/b.txt", "Unrelated VS Code change")
        commit_file(self.repo, "firefox/c.txt", "Second Firefox change")
        git("tag", "other-v2.0.0", cwd=self.repo)
        git("tag", "firefox-v1.0.1", cwd=self.repo)
        notes = release_notes("firefox-v1.0.1", root=self.repo)
        self.assertIn("## Apollo Themes for Firefox firefox-v1.0.1", notes)
        self.assertIn("### Commits since firefox-v1.0.0", notes)
        self.assertIn("- Second Firefox change (", notes)
        self.assertIn(") — Test", notes)
        self.assertNotIn("Unrelated VS Code change", notes)
        self.assertNotIn("First Firefox change", notes)
        self.assertIn(
            "**Full Changelog**: https://github.com/apollo-theme/apollo-theme/compare/firefox-v1.0.0...firefox-v1.0.1",
            notes,
        )

    def test_first_tag_has_no_previous_or_compare_link(self):
        commit_file(self.repo, "firefox/a.txt", "Initial Firefox theme")
        git("tag", "firefox-v0.1.0", cwd=self.repo)
        notes = release_notes("firefox-v0.1.0", root=self.repo)
        self.assertIn("### Commits\n", notes)
        self.assertIn("- Initial Firefox theme (", notes)
        self.assertNotIn("Full Changelog", notes)

    def test_imported_standalone_tag_lists_root_level_commits(self):
        commit_file(self.repo, "manifest.json", "Standalone start")
        git("tag", "firefox-v1.0.0", cwd=self.repo)
        commit_file(self.repo, "manifest.json", "Standalone fix")
        git("tag", "firefox-v1.0.1", cwd=self.repo)
        notes = release_notes("firefox-v1.0.1", root=self.repo)
        self.assertIn("- Standalone fix (", notes)
        self.assertNotIn("Standalone start", notes)

    def test_previous_imported_annotated_tag_is_found_by_ref_name(self):
        commit_file(self.repo, "firefox/a.txt", "Imported release")
        git("tag", "-a", "v1.1.1", "-m", "x", cwd=self.repo)
        git("update-ref", "refs/tags/firefox-v1.1.1", git("rev-parse", "v1.1.1", cwd=self.repo), cwd=self.repo)
        git("tag", "-d", "v1.1.1", cwd=self.repo)
        commit_file(self.repo, "firefox/b.txt", "First monorepo change")
        commit_file(self.repo, "firefox/c.txt", "Second monorepo change")
        git("tag", "firefox-v1.1.3", cwd=self.repo)
        notes = release_notes("firefox-v1.1.3", root=self.repo)
        self.assertIn("### Commits since firefox-v1.1.1\n", notes)
        self.assertIn("- First monorepo change (", notes)
        self.assertIn("- Second monorepo change (", notes)
        self.assertNotIn("Imported release", notes)
        self.assertIn(
            "**Full Changelog**: https://github.com/apollo-theme/apollo-theme/compare/firefox-v1.1.1...firefox-v1.1.3",
            notes,
        )

    @unittest.skipUnless(tag_exists("firefox-v1.1.1") and tag_exists("firefox-v1.1.0"), "imported Firefox tags not fetched")
    def test_imported_tag_in_this_repository(self):
        notes = release_notes("firefox-v1.1.1")
        self.assertIn("### Commits since firefox-v1.1.0", notes)
        self.assertRegex(notes, r"\n- .+ \([0-9a-f]+\) — ")


class MainTests(unittest.TestCase):
    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_mismatched_tag_fails(self):
        code, _, err = self.run_main(["--dry-run", "firefox-v9.9.9", "--skip-build"])
        self.assertEqual(1, code)
        self.assertIn("dark manifest", err)

    def test_malformed_tag_fails(self):
        code, _, err = self.run_main(["--dry-run", "v1.1.1", "--skip-build"])
        self.assertEqual(1, code)
        self.assertIn("tag must look like firefox-vX.Y.Z", err)

    def test_current_tag_passes(self):
        code, out, _ = self.run_main(["--dry-run", "firefox-v1.1.1", "--skip-build"])
        self.assertEqual(0, code)
        self.assertIn("attachments:", out)

    def test_missing_attachment_after_build_fails(self):
        original = firefox_release.build

        def no_output_build(directory, run=subprocess.run):
            return [Path(directory) / "web-ext-artifacts" / "missing-dark.zip", Path(directory) / "web-ext-artifacts" / "missing-light.zip"]

        firefox_release.build = no_output_build
        try:
            code, _, err = self.run_main(["--dry-run", "firefox-v1.1.1"])
        finally:
            firefox_release.build = original
        self.assertEqual(1, code)
        self.assertIn("missing-dark.zip", err)

    def test_dry_run_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["--skip-build"])


class WorkflowTests(unittest.TestCase):
    def test_workflow_never_calls_gh_and_uses_script(self):
        text = (ROOT / ".github" / "workflows" / "firefox-release.yml").read_text(encoding="utf-8")
        self.assertIn('tags: ["firefox-v*"]', text)
        self.assertIn('python3 ../scripts/firefox_release.py --dry-run "$GITHUB_REF_NAME" --notes-out RELEASE_NOTES.md', text)
        self.assertIn("firefox/web-ext-artifacts/apollo-theme.zip", text)
        self.assertIn("firefox/web-ext-artifacts/apollo-light-theme.zip", text)
        self.assertNotIn("gh release", text)


if __name__ == "__main__":
    unittest.main()
