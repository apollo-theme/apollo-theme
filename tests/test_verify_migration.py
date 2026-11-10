import contextlib
import copy
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

from migration import MIGRATION_LINE, Source, bundle_source, migrated_body, retired_source  # noqa: E402
from verify_migration import (  # noqa: E402
    check_history,
    check_live_source,
    check_pin,
    check_pushed,
    check_tags,
    check_tree,
    main,
    normalize,
    parse_ls_remote,
)

FIXTURES = ROOT / "tests" / "fixtures" / "releases"
BACKUP_JSON = FIXTURES / "bat-v0.1.0.backup.json"
REST_JSON = FIXTURES / "bat-v0.1.0.rest.json"
ASSET = FIXTURES / "bat-v0.1.0" / "Apollo.tmTheme"
ASSET_SHA256 = "f9d7c4af10571f4f587481e49dd5410a7203d0b4a7d972a6b17dbe8f4860d65b"
REAL_BACKUP = ROOT.parent / "org-backup-2026-11-09"

# Real Firefox v1.1.1: annotated tag object 66a5737 peels to commit c4bc29f.
FIREFOX_TAG_OBJECT = "66a5737f6101e6d6bf55fbd8b26b8c8dae828941"
FIREFOX_TAG_COMMIT = "c4bc29fbe8fc4bcb48ec8f8dd124c134c37f2108"


def git(*args: str, cwd: Path) -> str:
    command = [
        "git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "init.defaultBranch=main", *args,
    ]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_file(repo: Path, relative: str, text: str) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git("add", relative, cwd=repo)
    git("commit", "-q", "-m", f"edit {relative}", cwd=repo)


def make_source_repo(base: Path) -> Path:
    src = base / "src"
    src.mkdir()
    git("init", "-q", cwd=src)
    (src / "README.md").write_text("readme\n", encoding="utf-8")
    (src / "a.txt").write_text("a\n", encoding="utf-8")
    git("add", ".", cwd=src)
    git("commit", "-q", "-m", "initial", cwd=src)
    git("tag", "v0.1.0", cwd=src)
    return src


def make_mono(base: Path, bundle: Path) -> Path:
    mono = base / "mono"
    mono.mkdir()
    git("init", "-q", cwd=mono)
    commit_file(mono, "root.txt", "root\n")
    git("subtree", "add", "-q", "--prefix=x", str(bundle), "main", cwd=mono)
    git("fetch", "-q", "--no-tags", str(bundle), "refs/tags/*:refs/tags/x-*", cwd=mono)
    return mono


class MigrationFactsTests(unittest.TestCase):
    def test_migrated_body_appends_line_once(self):
        body = migrated_body("Notes\r\n\n", "bat-apollo-theme")
        self.assertEqual(body, "Notes\r\n\n" + MIGRATION_LINE.format(repo="bat-apollo-theme") + "\n")
        self.assertEqual(migrated_body("Notes", "x"), "Notes\n\n" + MIGRATION_LINE.format(repo="x") + "\n")

    def test_bundle_source_peels_lightweight_and_annotated_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            src = make_source_repo(base)
            git("tag", "-a", "v1.1.1", "-m", "annotated", cwd=src)
            bundle = base / "x-apollo-theme.bundle"
            git("bundle", "create", "-q", str(bundle), "--all", cwd=src)
            source = bundle_source("x", bundle)
            head = git("rev-parse", "main", cwd=src)
            self.assertEqual(source.rev, head)
            self.assertEqual(source.tags, {"v0.1.0": head, "v1.1.1": head})
            self.assertNotEqual(git("rev-parse", "v1.1.1", cwd=src), head)

    def test_bundle_source_missing_bundle_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Exception) as caught:
                bundle_source("x", Path(directory) / "missing.bundle")
            self.assertIn("missing.bundle", str(caught.exception))

    def test_retired_source_resolves_short_rev_and_peeled_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            src = make_source_repo(Path(directory))
            git("tag", "-a", "v0.2.0", "-m", "annotated", cwd=src)
            head = git("rev-parse", "HEAD", cwd=src)
            source = retired_source("x", src, head[:7])
            self.assertEqual(source.rev, head)
            self.assertEqual(source.tags, {"v0.1.0": head, "v0.2.0": head})

    @unittest.skipUnless((REAL_BACKUP / "firefox-apollo-theme.bundle").exists(), "org backup not present")
    def test_real_firefox_annotated_tag_peels_to_commit(self):
        source = bundle_source("firefox", REAL_BACKUP / "firefox-apollo-theme.bundle")
        self.assertEqual(source.tags["v1.1.1"], FIREFOX_TAG_COMMIT)


class OfflineCheckTests(unittest.TestCase):
    def test_tree_history_and_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            src = make_source_repo(base)
            bundle = base / "src.bundle"
            git("bundle", "create", "-q", str(bundle), "--all", cwd=src)
            mono = make_mono(base, bundle)
            rev = git("rev-parse", "main", cwd=src)
            sha = git("rev-parse", "v0.1.0^{commit}", cwd=src)
            source = Source(slug="x", rev=rev, tags={"v0.1.0": sha}, allow=("README.md",))

            self.assertEqual(check_tree(mono, source), [])
            self.assertEqual(check_history(mono, source), [])
            self.assertEqual(check_tags(mono, source), [])

            commit_file(mono, "x/README.md", "edited readme\n")
            self.assertEqual(check_tree(mono, source), [])

            commit_file(mono, "x/a.txt", "edited\n")
            self.assertEqual(check_tree(mono, source), ["x: a.txt differs from source"])
            self.assertEqual(check_history(mono, source), [])

            git("tag", "-f", "x-v0.1.0", "HEAD", cwd=mono)
            self.assertEqual(check_tags(mono, source), [f"x: tag x-v0.1.0 not on {sha}"])

    def test_common_allow_covers_nested_github_and_deletions(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            src = make_source_repo(base)
            commit_file(src, ".github/workflows/ci.yml", "on: push\n")
            bundle = base / "src.bundle"
            git("bundle", "create", "-q", str(bundle), "--all", cwd=src)
            mono = make_mono(base, bundle)
            source = Source(slug="x", rev=git("rev-parse", "main", cwd=src), tags={}, allow=("README.md", ".github/*"))
            git("rm", "-q", "-r", "x/.github", cwd=mono)
            git("commit", "-q", "-m", "drop workflows", cwd=mono)
            self.assertEqual(check_tree(mono, source), [])
            git("rm", "-q", "x/a.txt", cwd=mono)
            git("commit", "-q", "-m", "drop a", cwd=mono)
            self.assertEqual(check_tree(mono, source), ["x: a.txt differs from source"])

    def test_rename_into_allowlisted_directory_reports_original_path(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            src = make_source_repo(base)
            bundle = base / "src.bundle"
            git("bundle", "create", "-q", str(bundle), "--all", cwd=src)
            mono = make_mono(base, bundle)
            source = Source(slug="x", rev=git("rev-parse", "main", cwd=src), tags={}, allow=("README.md", ".github/*"))
            (mono / "x" / ".github").mkdir()
            git("mv", "x/a.txt", "x/.github/a.txt", cwd=mono)
            git("commit", "-q", "-m", "hide a", cwd=mono)
            self.assertEqual(check_tree(mono, source), ["x: a.txt differs from source"])

    def test_missing_tag_and_unrelated_history_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            src = make_source_repo(base)
            bundle = base / "src.bundle"
            git("bundle", "create", "-q", str(bundle), "--all", cwd=src)
            mono = make_mono(base, bundle)
            git("checkout", "-q", "-b", "side", cwd=mono)
            commit_file(mono, "side.txt", "side\n")
            side = git("rev-parse", "HEAD", cwd=mono)
            git("checkout", "-q", "main", cwd=mono)
            source = Source(slug="x", rev=side, tags={"v9.9.9": side}, allow=())
            self.assertEqual(check_history(mono, source), [f"x: source {side} is not an ancestor of HEAD"])
            self.assertEqual(check_tags(mono, source), ["x: tag x-v9.9.9 missing"])

    def test_git_failure_becomes_error_string(self):
        with tempfile.TemporaryDirectory() as directory:
            mono = Path(directory)
            source = Source(slug="x", rev="0" * 40, tags={}, allow=())
            for check in (check_tree, check_history):
                errors = check(mono, source)
                self.assertEqual(len(errors), 1)
                self.assertTrue(errors[0].startswith("x: "), errors[0])


class OnlineTagTests(unittest.TestCase):
    LS_REMOTE = (
        f"{FIREFOX_TAG_OBJECT}\trefs/tags/firefox-v1.1.1\n"
        f"{FIREFOX_TAG_COMMIT}\trefs/tags/firefox-v1.1.1^{{}}\n"
        "3b1cffb3605c7a4ae3aa1ae163675f8364828a9d\trefs/tags/bat-v0.1.0\n"
    )

    def test_parse_ls_remote_prefers_peeled_lines(self):
        self.assertEqual(
            parse_ls_remote(self.LS_REMOTE, peel=True),
            {
                "refs/tags/firefox-v1.1.1": FIREFOX_TAG_COMMIT,
                "refs/tags/bat-v0.1.0": "3b1cffb3605c7a4ae3aa1ae163675f8364828a9d",
            },
        )
        self.assertEqual(parse_ls_remote(self.LS_REMOTE)["refs/tags/firefox-v1.1.1"], FIREFOX_TAG_OBJECT)

    def test_annotated_and_lightweight_remote_tags_pass_moved_tag_fails(self):
        remote = parse_ls_remote(self.LS_REMOTE, peel=True)
        firefox = Source(slug="firefox", rev="", tags={"v1.1.1": FIREFOX_TAG_COMMIT}, allow=())
        bat = Source(slug="bat", rev="", tags={"v0.1.0": "3b1cffb3605c7a4ae3aa1ae163675f8364828a9d"}, allow=())
        self.assertEqual(check_tags(None, firefox, remote_tags=remote), [])
        self.assertEqual(check_tags(None, bat, remote_tags=remote), [])
        moved = Source(slug="bat", rev="", tags={"v0.1.0": "f" * 40}, allow=())
        self.assertEqual(check_tags(None, moved, remote_tags=remote), [f"bat: tag bat-v0.1.0 not on {'f' * 40}"])


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.backup = json.loads(BACKUP_JSON.read_text(encoding="utf-8"))
        self.rest = json.loads(REST_JSON.read_text(encoding="utf-8"))

    def test_backup_and_rest_shapes_agree(self):
        expected = {
            "tag": "v0.1.0",
            "name": "Apollo Theme for bat v0.1.0",
            "body": self.backup["body"],
            "assets": [("Apollo.tmTheme", 5610, ASSET_SHA256)],
        }
        self.assertEqual(normalize(self.backup), expected)
        self.assertEqual(normalize(self.rest), expected)

    def test_missing_digest_is_downloaded_and_hashed(self):
        rest = copy.deepcopy(self.rest)
        for asset in rest["assets"]:
            asset.pop("digest", None)
        calls = []

        def download(asset):
            calls.append(asset["name"])
            return ASSET.read_bytes()

        self.assertEqual(normalize(rest, download=download), normalize(self.backup))
        self.assertEqual(calls, ["Apollo.tmTheme"])

    def test_missing_digest_without_downloader_raises(self):
        rest = copy.deepcopy(self.rest)
        rest["assets"][0].pop("digest", None)
        with self.assertRaises(Exception):
            normalize(rest)

    def test_crlf_and_trailing_whitespace_in_body_ignored(self):
        rest = copy.deepcopy(self.rest)
        rest["body"] = rest["body"].replace("\n", "\r\n") + "\r\n  \n"
        self.assertEqual(normalize(rest), normalize(self.backup))

    def test_changed_size_or_body_differs(self):
        for field, change in (("size", lambda r: r["assets"][0].update(size=5611)), ("body", lambda r: r.update(body="Edited"))):
            with self.subTest(field=field):
                rest = copy.deepcopy(self.rest)
                change(rest)
                self.assertNotEqual(normalize(rest), normalize(self.backup))

    def test_ids_urls_and_download_counts_ignored(self):
        rest = copy.deepcopy(self.rest)
        rest.update(id=1, node_id="n", url="u")
        rest["assets"][0].update(id=2, node_id="m", url="v", download_count=999)
        self.assertEqual(normalize(rest), normalize(self.backup))


class LiveSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        src = make_source_repo(base)
        git("tag", "-a", "v0.2.0", "-m", "annotated", cwd=src)
        self.backup = base / "backup"
        self.backup.mkdir()
        self.bundle = self.backup / "bat-apollo-theme.bundle"
        git("bundle", "create", "-q", str(self.bundle), "--all", cwd=src)
        releases = self.backup / "releases" / "bat-apollo-theme"
        (releases / "v0.1.0").mkdir(parents=True)
        shutil.copy(BACKUP_JSON, releases / "v0.1.0.json")
        shutil.copy(ASSET, releases / "v0.1.0" / "Apollo.tmTheme")
        self.remote_text = "".join(
            f"{sha}\t{ref}\n"
            for sha, ref in (line.split(" ", 1) for line in git("bundle", "list-heads", str(self.bundle), cwd=base).splitlines())
            if ref.startswith(("refs/heads/", "refs/tags/"))
        )
        tag_object = git("rev-parse", "v0.2.0", cwd=src)
        self.assertIn(tag_object, self.remote_text)
        self.remote_text += f"{git('rev-parse', 'HEAD', cwd=src)}\trefs/tags/v0.2.0^{{}}\n"
        self.rest = json.loads(REST_JSON.read_text(encoding="utf-8"))
        self.calls = []

    def tearDown(self):
        self.directory.cleanup()

    def ls_remote(self, text=None):
        def fake(*args):
            self.calls.append(args)
            return self.remote_text if text is None else text
        return fake

    def api(self, releases):
        def fake(path):
            self.calls.append(path)
            return releases
        return fake

    def test_matching_refs_and_releases_pass(self):
        errors = check_live_source("bat-apollo-theme", self.backup, ls_remote=self.ls_remote(), api=self.api([self.rest]))
        self.assertEqual(errors, [])
        self.assertIn(("--heads", "--tags", "https://github.com/apollo-theme/bat-apollo-theme"), self.calls)
        self.assertIn("repos/apollo-theme/bat-apollo-theme/releases", self.calls)

    def test_moved_ref_fails(self):
        first_sha = self.remote_text.split("\t", 1)[0]
        moved = self.remote_text.replace(first_sha, "0" * 40, 1)
        errors = check_live_source("bat-apollo-theme", self.backup, ls_remote=self.ls_remote(moved), api=self.api([self.rest]))
        self.assertEqual(errors, ["bat-apollo-theme: refs differ from bundle"])

    def test_edited_body_or_digest_fails(self):
        edits = (
            lambda r: r.update(body="Edited"),
            lambda r: r["assets"][0].update(digest="sha256:" + "0" * 64),
        )
        for edit in edits:
            rest = copy.deepcopy(self.rest)
            edit(rest)
            errors = check_live_source("bat-apollo-theme", self.backup, ls_remote=self.ls_remote(), api=self.api([rest]))
            self.assertEqual(errors, ["bat-apollo-theme: release v0.1.0 differs from backup"])

    def test_missing_and_extra_releases_fail(self):
        errors = check_live_source("bat-apollo-theme", self.backup, ls_remote=self.ls_remote(), api=self.api([]))
        self.assertEqual(errors, ["bat-apollo-theme: release v0.1.0 missing"])
        extra = dict(copy.deepcopy(self.rest), tag_name="v9.9.9")
        errors = check_live_source("bat-apollo-theme", self.backup, ls_remote=self.ls_remote(), api=self.api([self.rest, extra]))
        self.assertEqual(errors, ["bat-apollo-theme: release v9.9.9 not in backup"])

    def test_failures_fail_closed(self):
        def broken(*args):
            raise subprocess.CalledProcessError(128, "git ls-remote")

        errors = check_live_source("bat-apollo-theme", self.backup, ls_remote=broken, api=self.api([self.rest]))
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("bat-apollo-theme: "), errors)
        errors = check_live_source("vim-apollo-theme", self.backup, ls_remote=self.ls_remote(), api=self.api([]))
        self.assertEqual(len(errors), 1)
        self.assertIn("vim-apollo-theme.bundle", errors[0])

    def test_dot_github_uses_dot_github_bundle(self):
        shutil.copy(self.bundle, self.backup / "dot-github.bundle")
        errors = check_live_source(".github", self.backup, ls_remote=self.ls_remote(), api=self.api([]))
        self.assertEqual(len(errors), 1)
        self.assertIn("missing release backup", errors[0])
        (self.backup / "releases" / ".github").mkdir()
        errors = check_live_source(".github", self.backup, ls_remote=self.ls_remote(), api=self.api([]))
        self.assertEqual(errors, [])
        self.assertIn(("--heads", "--tags", "https://github.com/apollo-theme/.github"), self.calls)

    def local_asset(self):
        return self.backup / "releases" / "bat-apollo-theme" / "v0.1.0" / "Apollo.tmTheme"

    def check(self):
        return check_live_source("bat-apollo-theme", self.backup, ls_remote=self.ls_remote(), api=self.api([self.rest]))

    def test_missing_backup_asset_fails(self):
        self.local_asset().unlink()
        self.assertEqual(self.check(), ["bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme missing"])

    def test_corrupt_backup_asset_fails(self):
        data = bytearray(self.local_asset().read_bytes())
        data[0] ^= 0xFF
        self.local_asset().write_bytes(bytes(data))
        self.assertEqual(self.check(), ["bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme sha256 differs from JSON"])

    def test_backup_asset_size_mismatch_fails(self):
        self.local_asset().write_bytes(self.local_asset().read_bytes() + b"\n")
        self.assertEqual(
            self.check(),
            [
                "bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme size differs from JSON",
                "bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme sha256 differs from JSON",
            ],
        )


def write_pin(root: Path, pin: dict) -> None:
    (root / "palette").mkdir(parents=True, exist_ok=True)
    (root / "palette" / "SOURCE.json").write_text(json.dumps(pin), encoding="utf-8")


class OnlineRootChecksTests(unittest.TestCase):
    def test_check_pushed(self):
        with tempfile.TemporaryDirectory() as directory:
            mono = Path(directory)
            git("init", "-q", cwd=mono)
            commit_file(mono, "f", "f\n")
            head = git("rev-parse", "HEAD", cwd=mono)
            self.assertEqual(check_pushed(mono, ls_remote=lambda *a: f"{head}\trefs/heads/main\n"), [])
            self.assertEqual(check_pushed(mono, ls_remote=lambda *a: f"{'0' * 40}\trefs/heads/main\n"), ["origin/main is not HEAD"])

    def test_check_pin(self):
        source = json.loads((ROOT / "palette" / "SOURCE.json").read_text(encoding="utf-8"))
        files = {name: (ROOT / "palette" / name).read_bytes() for name in source["sha256"]}
        paths = []

        def fetch(path):
            paths.append(path)
            return files[path.split("/")[-1].split("?")[0]]

        self.assertEqual(check_pin(ROOT, fetch_raw=fetch), [])
        self.assertIn(f"repos/apollo-theme/apollo-palette/contents/palette/apollo.json?ref={source['commit']}", paths)
        errors = check_pin(ROOT, fetch_raw=lambda path: b"tampered")
        self.assertEqual(len(errors), len(source["sha256"]))

    def test_check_pin_rejects_malformed_pin_before_fetching(self):
        good = json.loads((ROOT / "palette" / "SOURCE.json").read_text(encoding="utf-8"))
        cases = {
            "empty sha256": dict(good, sha256={}),
            "one key missing": dict(good, sha256={"apollo.json": good["sha256"]["apollo.json"]}),
            "extra key": dict(good, sha256=dict(good["sha256"], **{"other.json": "0" * 64})),
            "non-hex value": dict(good, sha256=dict(good["sha256"], **{"apollo.json": "z" * 64})),
            "short value": dict(good, sha256=dict(good["sha256"], **{"apollo.json": "0" * 63})),
            "bad commit": dict(good, commit="24f6b2e"),
            "wrong repository": dict(good, repository="https://github.com/someone/apollo-palette"),
            "missing commit": {k: v for k, v in good.items() if k != "commit"},
        }

        def fetch(path):
            raise AssertionError(f"fetched {path} for a malformed pin")

        for label, pin in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as directory:
                write_pin(Path(directory), pin)
                errors = check_pin(Path(directory), fetch_raw=fetch)
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(errors[0].startswith("palette/SOURCE.json"), errors)


class CliTests(unittest.TestCase):
    def test_missing_backup_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(["--offline", "--app", "bat", "--backup", directory, "--retired", directory])
            self.assertEqual(code, 1)
            self.assertIn("bat-apollo-theme.bundle", out.getvalue())
            self.assertNotIn("verified", out.getvalue())


if __name__ == "__main__":
    unittest.main()
