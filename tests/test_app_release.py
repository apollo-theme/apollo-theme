import contextlib
import hashlib
import io
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import app_release  # noqa: E402
from app_release import RAW_ASSETS, build_assets, build_zip, check_version, main, parse_tag, release_notes  # noqa: E402
from common import APPS, SLUGS  # noqa: E402

RELEASED = tuple(slug for slug in SLUGS if slug != "firefox")
DEV_PARTS = {"scripts", "tests", "palette", ".github", "CLAUDE.md", ".gitignore", ".gitattributes", ".vscodeignore", "package-lock.json"}


def git(*args: str, cwd: Path) -> str:
    command = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "-c", "commit.gpgsign=false", *args]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_file(repo: Path, relative: str, message: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(message + "\n", encoding="utf-8")
    git("add", relative, cwd=repo)
    git("commit", "-q", "-m", message, cwd=repo)


class TagTests(unittest.TestCase):
    def test_parses_every_released_slug(self):
        for slug in RELEASED:
            with self.subTest(slug=slug):
                self.assertEqual((slug, "1.2.3"), parse_tag(f"{slug}-v1.2.3"))

    def test_bad_tags_rejected(self):
        for tag in ("v1.2.3", "vim-v1.2", "vim-1.2.3", "emacs-v1.2.3", "vim-v1.2.3-rc1"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "tag must look like"):
                parse_tag(tag)

    def test_firefox_points_at_its_own_release(self):
        with self.assertRaisesRegex(ValueError, "firefox_release.py"):
            parse_tag("firefox-v1.1.1")


class RawAssetTests(unittest.TestCase):
    def test_every_released_app_is_mapped(self):
        self.assertEqual(set(RELEASED), set(RAW_ASSETS))

    def test_sources_exist_and_names_are_release_safe(self):
        for slug, mapping in RAW_ASSETS.items():
            names = list(mapping.values())
            self.assertEqual(len(names), len(set(names)), slug)
            for source, name in mapping.items():
                with self.subTest(slug=slug, source=source):
                    self.assertTrue((ROOT / slug / source).is_file())
                    self.assertRegex(name, r"^[A-Za-z0-9._-]+$")

    def test_filename_named_light_themes_stay_in_zip_only(self):
        for slug, source in (("iterm2", "Apollo Light.itermcolors"), ("xcode", "Apollo Light.xccolortheme"), ("bat", "Apollo Light.tmTheme"), ("eza", "light/theme.yml")):
            with self.subTest(slug=slug):
                self.assertNotIn(source, RAW_ASSETS[slug])

    def test_existing_consumer_names_are_stable(self):
        self.assertEqual("apollo.toml", RAW_ASSETS["sonicterm"]["apollo.toml"])
        self.assertEqual("apollo-rmux.conf", RAW_ASSETS["rmux"]["apollo-rmux.conf"])
        self.assertEqual("apollo.tmux", RAW_ASSETS["tmux"]["apollo.tmux"])
        self.assertEqual("theme.yml", RAW_ASSETS["eza"]["theme.yml"])


class VersionTests(unittest.TestCase):
    def test_declared_versions_match_current(self):
        check_version("vscode", "0.2.0")
        check_version("powershell", "0.2.0")

    def test_mismatch_names_source(self):
        for slug, source in (("vscode", "package.json"), ("powershell", "ApolloTheme.psd1")):
            with self.subTest(slug=slug), self.assertRaisesRegex(ValueError, source):
                check_version(slug, "9.9.9")

    def test_unversioned_apps_accept_any_version(self):
        check_version("vim", "9.9.9")


class ZipTests(unittest.TestCase):
    def test_zip_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            a = build_zip("iterm2", "1.0.0", Path(first)).read_bytes()
            b = build_zip("iterm2", "1.0.0", Path(second)).read_bytes()
        self.assertEqual(a, b)

    def test_zip_bytes_do_not_depend_on_build_platform(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            with mock.patch.object(zipfile.sys, "platform", "win32"):
                a = build_zip("vim", "1.0.0", Path(first)).read_bytes()
            with mock.patch.object(zipfile.sys, "platform", "darwin"):
                b = build_zip("vim", "1.0.0", Path(second)).read_bytes()
        self.assertEqual(a, b)

    def test_dot_paths_are_never_shipped(self):
        listed = b"vim/.editorconfig\0vim/.cache/file\0vim/colors/apollo.vim\0"
        result = subprocess.CompletedProcess([], 0, stdout=listed)
        with mock.patch.object(app_release.subprocess, "run", return_value=result):
            self.assertEqual(["colors/apollo.vim"], app_release.shippable_files("vim"))

    def test_every_zip_holds_shippable_files_only(self):
        with tempfile.TemporaryDirectory() as out:
            for slug in RELEASED:
                with self.subTest(slug=slug):
                    path = build_zip(slug, "1.0.0", Path(out))
                    self.assertEqual(f"apollo-{slug}-1.0.0.zip", path.name)
                    names = zipfile.ZipFile(path).namelist()
                    prefix = f"apollo-{slug}-1.0.0/"
                    self.assertTrue(all(name.startswith(prefix) for name in names))
                    inner = {name[len(prefix):] for name in names}
                    self.assertLessEqual({"README.md", "LICENSE", APPS[slug]["light_artifact"]}, inner)
                    for name in inner:
                        self.assertFalse(DEV_PARTS & set(Path(name).parts), name)
                    with zipfile.ZipFile(path) as archive:
                        light = archive.read(prefix + APPS[slug]["light_artifact"])
                    self.assertEqual((ROOT / slug / APPS[slug]["light_artifact"]).read_bytes(), light)


class AssetTests(unittest.TestCase):
    def test_assets_and_checksums(self):
        with tempfile.TemporaryDirectory() as out:
            paths = build_assets("apple-terminal", "1.0.0", Path(out))
            names = sorted(path.name for path in paths)
            self.assertEqual(sorted(["Apollo.terminal", "Apollo-Light.terminal", "apollo-apple-terminal-1.0.0.zip", "SHA256SUMS"]), names)
            self.assertEqual((ROOT / "apple-terminal" / "Apollo Light.terminal").read_bytes(), (Path(out) / "Apollo-Light.terminal").read_bytes())
            sums = (Path(out) / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
            self.assertEqual(3, len(sums))
            for line in sums:
                digest, name = line.split("  ", 1)
                self.assertEqual(hashlib.sha256((Path(out) / name).read_bytes()).hexdigest(), digest)

    def test_vscode_attaches_vsix(self):
        calls = []

        def fake_run(command, cwd, check):
            calls.append((command, cwd))
            (cwd / "dist").mkdir(exist_ok=True)
            (cwd / "dist" / "apollo-theme.vsix").write_bytes(b"vsix")

        with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as package_dir:
            names = [path.name for path in build_assets("vscode", "0.2.0", Path(out), run=fake_run, vsix_dir=Path(package_dir))]
        self.assertEqual(["apollo-vscode-0.2.0.zip", "apollo-theme-0.2.0.vsix", "SHA256SUMS"], names)
        self.assertEqual(["npm", "run", "package"], calls[-1][0])

    def test_non_empty_output_rejected(self):
        with tempfile.TemporaryDirectory() as out:
            (Path(out) / "stale.zip").write_bytes(b"old")
            with self.assertRaisesRegex(ValueError, "must be empty"):
                build_assets("vim", "1.0.0", Path(out))

    def test_missing_asset_rejected(self):
        with tempfile.TemporaryDirectory() as out:
            build_assets("vim", "1.0.0", Path(out) / "a")
            (Path(out) / "a" / "apollo.vim").unlink()
            with self.assertRaisesRegex(ValueError, "must be exactly"):
                app_release.check_assets(Path(out) / "a", app_release.expected_assets("vim", "1.0.0"))

    def test_vscode_without_vsix_output_fails(self):
        with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as fake_root:
            with self.assertRaisesRegex(ValueError, "apollo-theme.vsix"):
                build_assets("vscode", "0.2.0", Path(out), run=lambda command, cwd, check: None, vsix_dir=Path(fake_root))


class NotesTests(unittest.TestCase):
    def test_notes_scope_commits_to_app_since_previous_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git("init", "-q", cwd=repo)
            commit_file(repo, "vim/a.txt", "Old vim change")
            git("tag", "vim-v1.0.0", cwd=repo)
            commit_file(repo, "tmux/a.txt", "Unrelated tmux change")
            commit_file(repo, "vim/b.txt", "New vim change")
            git("tag", "vim-v1.1.0", cwd=repo)
            notes = release_notes("vim-v1.1.0", root=repo)
        self.assertIn("## Apollo Themes for Vim vim-v1.1.0", notes)
        self.assertIn("New vim change", notes)
        self.assertNotIn("Old vim change", notes)
        self.assertNotIn("Unrelated tmux change", notes)
        self.assertIn("compare/vim-v1.0.0...vim-v1.1.0", notes)

    def test_previous_tag_on_same_commit_is_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git("init", "-q", cwd=repo)
            commit_file(repo, "vim/a.txt", "First vim change")
            git("tag", "vim-v1.0.0", cwd=repo)
            commit_file(repo, "vim/b.txt", "Second vim change")
            git("tag", "vim-v1.1.0", cwd=repo)
            git("tag", "vim-v1.1.1", cwd=repo)
            notes = release_notes("vim-v1.1.1", root=repo)
            older = release_notes("vim-v1.1.0", root=repo)
        self.assertIn("Commits since vim-v1.1.0", notes)
        self.assertNotIn("Second vim change", notes)
        self.assertIn("Commits since vim-v1.0.0", older)

    def test_imported_tags_without_folder_list_root_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git("init", "-q", cwd=repo)
            commit_file(repo, "Apollo.itermcolors", "Imported root change")
            git("tag", "iterm2-v0.1.0", cwd=repo)
            notes = release_notes("iterm2-v0.1.0", root=repo)
        self.assertIn("Imported root change", notes)


class MainTests(unittest.TestCase):
    def test_dry_run_writes_assets_and_notes(self):
        with tempfile.TemporaryDirectory() as out:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main(["--dry-run", "tmux-v9.9.9", "--out", out])
            self.assertEqual(0, code)
            self.assertTrue((Path(out) / "apollo.tmux").is_file())
            self.assertIn("apollo-tmux-9.9.9.zip", stdout.getvalue())

    def test_bad_tag_exits_nonzero(self):
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as out, contextlib.redirect_stderr(stderr):
            self.assertEqual(1, main(["--dry-run", "firefox-v1.1.1", "--out", out]))
        self.assertIn("error:", stderr.getvalue())

    def test_check_all_builds_every_released_app(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(0, main(["--check-all"]))
        for slug in RELEASED:
            self.assertIn(f"apollo-{slug}-", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
