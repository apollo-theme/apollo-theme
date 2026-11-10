import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from migration import migrated_body  # noqa: E402
from restore_releases import Plan, apply, main, plan_releases  # noqa: E402
from verify_migration import ROOT_RELEASE_TAGS, check_releases  # noqa: E402

ASSET_BYTES = b"<plist>apollo</plist>\n"
ASSET_SHA = hashlib.sha256(ASSET_BYTES).hexdigest()


def git(*args: str, cwd: Path) -> str:
    command = [
        "git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "init.defaultBranch=main", *args,
    ]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def write_release(backup: Path, repo: str, tag: str, name: str, body: str, assets: dict[str, bytes]) -> None:
    directory = backup / "releases" / repo
    directory.mkdir(parents=True, exist_ok=True)
    records = [
        {"name": asset, "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "id": "RA_x", "downloadCount": 3}
        for asset, data in assets.items()
    ]
    (directory / f"{tag}.json").write_text(json.dumps({"tagName": tag, "name": name, "body": body, "assets": records}), encoding="utf-8")
    if assets:
        (directory / tag).mkdir()
        for asset, data in assets.items():
            (directory / tag / asset).write_bytes(data)


def rest(tag: str, name: str, body: str, assets: dict[str, bytes]) -> dict:
    return {
        "tag_name": tag,
        "name": name,
        "body": body,
        "id": 1,
        "assets": [
            {"name": asset, "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "download_count": 9}
            for asset, data in assets.items()
        ],
    }


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.backup = Path(self.directory.name)
        write_release(self.backup, "bat-apollo-theme", "v0.1.0", "v0.1.0", "b", {"Apollo.tmTheme": ASSET_BYTES})

    def tearDown(self):
        self.directory.cleanup()

    def asset(self) -> Path:
        return self.backup / "releases" / "bat-apollo-theme" / "v0.1.0" / "Apollo.tmTheme"

    def test_plan_maps_tag_title_body_and_assets(self):
        self.assertEqual(
            plan_releases(self.backup),
            [Plan(tag="bat-v0.1.0", title="bat v0.1.0", body=migrated_body("b", "bat-apollo-theme"), assets=[self.asset()])],
        )

    def test_title_keeps_original_name_when_it_differs_from_tag(self):
        write_release(self.backup, "bat-apollo-theme", "v0.2.0", "Apollo Dark + Light v0.2.0", "c", {})
        plans = plan_releases(self.backup)
        self.assertEqual([plan.title for plan in plans], ["bat v0.1.0", "Apollo Dark + Light v0.2.0"])
        self.assertEqual(plans[1].assets, [])

    def test_assets_without_asset_dir_raise(self):
        self.asset().unlink()
        self.asset().parent.rmdir()
        with self.assertRaises(FileNotFoundError):
            plan_releases(self.backup)

    def test_local_asset_sha_mismatch_raises(self):
        self.asset().write_bytes(ASSET_BYTES.replace(b"apollo", b"apolla"))
        with self.assertRaises(ValueError):
            plan_releases(self.backup)

    def test_root_site_org_profile_and_non_app_repos_are_excluded(self):
        for repo in ("apollo-theme", "apollo-theme.github.io", ".github", "demo-repository"):
            write_release(self.backup, repo, "v1.0.0", "v1.0.0", "x", {})
        self.assertEqual([plan.tag for plan in plan_releases(self.backup)], ["bat-v0.1.0"])

    def test_plans_sort_by_app_then_version(self):
        write_release(self.backup, "bat-apollo-theme", "v0.10.0", "v0.10.0", "x", {})
        write_release(self.backup, "bat-apollo-theme", "v0.2.0", "v0.2.0", "x", {})
        write_release(self.backup, "eza-apollo-theme", "v0.1.0", "v0.1.0", "x", {})
        self.assertEqual([plan.tag for plan in plan_releases(self.backup)], ["bat-v0.1.0", "bat-v0.2.0", "bat-v0.10.0", "eza-v0.1.0"])

    def test_apply_skips_existing_and_creates_the_rest_not_latest(self):
        existing = Plan(tag="bat-v0.1.0", title="bat v0.1.0", body="one\n", assets=[self.asset()])
        new = Plan(tag="bat-v0.2.0", title="bat v0.2.0", body="two\n", assets=[])
        calls, notes = [], []

        def run(command, **kwargs):
            calls.append(command)
            if command[:3] == ["gh", "release", "view"]:
                return subprocess.CompletedProcess(command, 0 if command[3] == "bat-v0.1.0" else 1, "", "")
            notes.append(Path(command[command.index("--notes-file") + 1]).read_text(encoding="utf-8"))
            return subprocess.CompletedProcess(command, 0, "", "")

        self.assertEqual(apply([existing, new], run=run), ["bat-v0.2.0"])
        creates = [command for command in calls if command[:3] == ["gh", "release", "create"]]
        self.assertEqual(len(creates), 1)
        create = creates[0]
        self.assertEqual(create[3], "bat-v0.2.0")
        for flag in ("--verify-tag", "--latest=false"):
            self.assertIn(flag, create)
        self.assertEqual(create[create.index("--repo") + 1], "apollo-theme/apollo-theme")
        self.assertEqual(create[create.index("--title") + 1], "bat v0.2.0")
        self.assertEqual(notes, ["two\n"])
        self.assertIn(["gh", "release", "view", "bat-v0.1.0", "--repo", "apollo-theme/apollo-theme"], calls)

    def test_apply_create_failure_raises(self):
        plan = Plan(tag="bat-v0.2.0", title="bat v0.2.0", body="two\n", assets=[])

        def run(command, **kwargs):
            code = 1
            return subprocess.CompletedProcess(command, code, "", "boom")

        with self.assertRaises(subprocess.CalledProcessError):
            apply([plan], run=run)

    def test_cli_without_apply_prints_plans_only(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--backup", str(self.backup)])
        self.assertEqual(code, 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[-1], "1 plans")
        self.assertIn("bat-v0.1.0", lines[0])
        self.assertIn("Apollo.tmTheme", lines[0])


class CheckReleasesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.backup = base / "backup"
        write_release(self.backup, "bat-apollo-theme", "v0.1.0", "v0.1.0", "b", {"Apollo.tmTheme": ASSET_BYTES})
        self.root = base / "root"
        self.root.mkdir()
        git("init", "-q", cwd=self.root)
        for tag in ROOT_RELEASE_TAGS:
            (self.root / "f.txt").write_text(tag, encoding="utf-8")
            git("add", "f.txt", cwd=self.root)
            git("commit", "-q", "-m", tag, cwd=self.root)
            git("tag", "-a", tag, "-m", tag, cwd=self.root) if tag == "v0.3.1" else git("tag", tag, cwd=self.root)
            write_release(self.backup, "apollo-theme", tag, f"Apollo Theme {tag}", f"root {tag}\r\n", {})
        git("bundle", "create", "-q", str(self.backup / "apollo-theme.bundle"), "--all", cwd=self.root)
        self.remote_tags = {f"refs/tags/{tag}": git("rev-parse", f"{tag}^{{commit}}", cwd=self.root) for tag in ROOT_RELEASE_TAGS}
        self.releases = [rest("bat-v0.1.0", "bat v0.1.0", migrated_body("b", "bat-apollo-theme"), {"Apollo.tmTheme": ASSET_BYTES})]
        self.releases += [rest(tag, f"Apollo Theme {tag}", f"root {tag}", {}) for tag in ROOT_RELEASE_TAGS]
        self.downloads = []

    def tearDown(self):
        self.directory.cleanup()

    def download(self, data=ASSET_BYTES):
        def fake(tag, name):
            self.downloads.append((tag, name))
            return data
        return fake

    def check(self, releases=None, download=None, remote_tags=None, **kwargs):
        return check_releases(
            self.backup,
            api=lambda path: self.releases if releases is None else releases,
            download=download or self.download(),
            root=self.root,
            remote_tags=self.remote_tags if remote_tags is None else remote_tags,
            **kwargs,
        )

    def release(self, tag):
        return next(release for release in self.releases if release["tag_name"] == tag)

    def test_matching_data_passes(self):
        self.assertEqual(self.check(), [])

    def test_api_path(self):
        paths = []
        check_releases(self.backup, api=lambda path: paths.append(path) or self.releases, download=self.download(), root=self.root, remote_tags=self.remote_tags)
        self.assertEqual(paths, ["repos/apollo-theme/apollo-theme/releases"])

    def test_body_differs(self):
        self.release("bat-v0.1.0")["body"] = "b"
        self.assertEqual(self.check(), ["bat-v0.1.0: body differs"])

    def test_title_differs(self):
        self.release("bat-v0.1.0")["name"] = "v0.1.0"
        self.assertEqual(self.check(), ["bat-v0.1.0: title differs"])

    def test_asset_sha256_differs_by_digest(self):
        self.release("bat-v0.1.0")["assets"][0]["digest"] = "sha256:" + "0" * 64
        self.assertEqual(self.check(), ["bat-v0.1.0: Apollo.tmTheme sha256 differs"])

    def test_asset_sha256_differs_by_download_when_digest_missing(self):
        del self.release("bat-v0.1.0")["assets"][0]["digest"]
        self.assertEqual(self.check(), [])
        self.assertEqual(self.downloads, [("bat-v0.1.0", "Apollo.tmTheme")])
        self.assertEqual(self.check(download=self.download(b"tampered")), ["bat-v0.1.0: Apollo.tmTheme sha256 differs"])

    def test_asset_size_missing_and_extra(self):
        assets = self.release("bat-v0.1.0")["assets"]
        assets[0]["size"] += 1
        self.assertEqual(self.check(), ["bat-v0.1.0: Apollo.tmTheme size differs"])
        assets.append(dict(assets[0], name="extra.zip", size=len(ASSET_BYTES)))
        assets.pop(0)
        self.assertEqual(self.check(), ["bat-v0.1.0: Apollo.tmTheme missing", "bat-v0.1.0: extra.zip unexpected"])

    def test_restored_release_missing(self):
        releases = [release for release in self.releases if release["tag_name"] != "bat-v0.1.0"]
        self.assertEqual(self.check(releases=releases), ["bat-v0.1.0: release missing"])

    def test_root_release_changed(self):
        for field in ("body", "name"):
            with self.subTest(field=field):
                original = self.release("v0.3.1")[field]
                self.release("v0.3.1")[field] = "edited"
                self.assertEqual(self.check(), ["v0.3.1: release changed"])
                self.release("v0.3.1")[field] = original

    def test_root_release_missing(self):
        releases = [release for release in self.releases if release["tag_name"] != "v0.1.0"]
        self.assertEqual(self.check(releases=releases), ["v0.1.0: release missing"])

    def test_root_tag_commit_changed_locally_or_on_origin(self):
        moved = dict(self.remote_tags, **{"refs/tags/v0.3.1": "0" * 40})
        self.assertEqual(self.check(remote_tags=moved), ["v0.3.1: tag commit changed on origin"])
        git("tag", "-f", "v0.3.1", "v0.1.0", cwd=self.root)
        self.assertEqual(self.check(), ["v0.3.1: tag commit changed locally"])

    def test_local_backup_asset_must_match_json_digest(self):
        asset = self.backup / "releases" / "bat-apollo-theme" / "v0.1.0" / "Apollo.tmTheme"
        asset.write_bytes(ASSET_BYTES.replace(b"apollo", b"apolla"))
        self.assertEqual(self.check(), ["bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme sha256 differs from JSON"])

    def test_failures_fail_closed(self):
        def broken(path):
            raise subprocess.CalledProcessError(1, ["gh", "api", path])

        errors = check_releases(self.backup, api=broken, download=self.download(), root=self.root, remote_tags=self.remote_tags)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("releases: "), errors)

        (self.backup / "apollo-theme.bundle").unlink()
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertIn("apollo-theme.bundle", errors[0])

    def test_missing_root_backup_json_fails(self):
        (self.backup / "releases" / "apollo-theme" / "v0.2.0.json").unlink()
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("v0.2.0: "), errors)

    def test_slugs_filter_checks_only_those_apps_and_skips_root(self):
        write_release(self.backup, "eza-apollo-theme", "v0.1.0", "v0.1.0", "e", {})
        self.assertEqual(self.check(slugs=["bat"], releases=self.releases[:1]), [])
        self.assertEqual(self.check(slugs=["eza"], releases=self.releases[:1]), ["eza-v0.1.0: release missing"])

    def test_requested_app_without_backup_fails_and_retired_apps_are_skipped(self):
        errors = self.check(slugs=["vim"], releases=self.releases[:1])
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("vim: missing release backup"), errors)
        self.assertEqual(self.check(slugs=["wezterm"], releases=[]), [])

    def test_include_root_with_explicit_slugs(self):
        self.assertEqual(self.check(slugs=["bat"], include_root=True), [])
        releases = [release for release in self.releases if release["tag_name"] != "v0.3.0"]
        self.assertEqual(self.check(slugs=["bat"], include_root=True, releases=releases), ["v0.3.0: release missing"])


if __name__ == "__main__":
    unittest.main()
