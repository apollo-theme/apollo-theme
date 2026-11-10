import contextlib
import hashlib
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

from migration import inventory_problems, load_inventory, migrated_body  # noqa: E402
from restore_releases import Plan, apply, main, plan_releases  # noqa: E402
from verify_migration import ROOT_RELEASE_TAGS, check_releases  # noqa: E402

ASSET_BYTES = b"<plist>apollo</plist>\n"
ASSET_SHA = hashlib.sha256(ASSET_BYTES).hexdigest()
REAL_BACKUP = ROOT.parent / "org-backup-2026-11-09"


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


def rest(tag: str, name: str, body: str, assets: dict[str, bytes], draft: bool = False) -> dict:
    return {
        "tag_name": tag,
        "name": name,
        "body": body,
        "draft": draft,
        "prerelease": False,
        "id": 1,
        "assets": [
            {"name": asset, "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "state": "uploaded", "download_count": 9}
            for asset, data in assets.items()
        ],
    }


class ShippedInventoryTests(unittest.TestCase):
    def test_inventory_covers_13_apps_and_root(self):
        inventory = load_inventory()
        apps = {repo: tags for repo, tags in inventory.items() if repo != "apollo-theme"}
        self.assertEqual(len(apps), 13)
        self.assertEqual(sum(len(tags) for tags in apps.values()), 33)
        self.assertEqual(tuple(sorted(inventory["apollo-theme"])), ROOT_RELEASE_TAGS)
        self.assertEqual(sum(len(assets) for tags in inventory.values() for assets in tags.values()), 24)
        self.assertEqual(inventory["firefox-apollo-theme"]["v1.1.1"], ["apollo-light-theme.zip", "apollo-theme.zip"])

    @unittest.skipUnless((REAL_BACKUP / "releases").is_dir(), "org backup not present")
    def test_real_backup_matches_inventory(self):
        self.assertEqual(inventory_problems(REAL_BACKUP, load_inventory()), [])
        self.assertEqual(len(plan_releases(REAL_BACKUP)), 33)

    def test_malformed_inventory_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            for bad in ({}, {"releases": []}, {"releases": {"x": {"v1": "a.zip"}}}):
                path.write_text(json.dumps(bad), encoding="utf-8")
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    load_inventory(path)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.backup = Path(self.directory.name)
        write_release(self.backup, "bat-apollo-theme", "v0.1.0", "v0.1.0", "b", {"Apollo.tmTheme": ASSET_BYTES})
        self.inventory = {"bat-apollo-theme": {"v0.1.0": ["Apollo.tmTheme"]}}

    def tearDown(self):
        self.directory.cleanup()

    def plan(self):
        return plan_releases(self.backup, inventory=self.inventory)

    def add(self, repo, tag, name="x", body="x", assets=None):
        write_release(self.backup, repo, tag, name, body, assets or {})
        self.inventory.setdefault(repo, {})[tag] = sorted(assets or {})

    def asset(self) -> Path:
        return self.backup / "releases" / "bat-apollo-theme" / "v0.1.0" / "Apollo.tmTheme"

    def test_plan_maps_tag_title_body_and_assets(self):
        self.assertEqual(
            self.plan(),
            [Plan(tag="bat-v0.1.0", title="bat v0.1.0", body=migrated_body("b", "bat-apollo-theme"), assets=[self.asset()])],
        )

    def test_title_keeps_original_name_when_it_differs_from_tag(self):
        self.add("bat-apollo-theme", "v0.2.0", "Apollo Dark + Light v0.2.0", "c")
        plans = self.plan()
        self.assertEqual([plan.title for plan in plans], ["bat v0.1.0", "Apollo Dark + Light v0.2.0"])
        self.assertEqual(plans[1].assets, [])

    def test_local_asset_sha_mismatch_raises(self):
        self.asset().write_bytes(ASSET_BYTES.replace(b"apollo", b"apolla"))
        with self.assertRaises(ValueError):
            self.plan()

    def test_root_site_org_profile_and_non_app_repos_are_excluded(self):
        for repo in ("apollo-theme", "apollo-theme.github.io", ".github", "demo-repository"):
            write_release(self.backup, repo, "v1.0.0", "v1.0.0", "x", {})
        self.inventory["apollo-theme"] = {"v1.0.0": []}
        self.assertEqual([plan.tag for plan in self.plan()], ["bat-v0.1.0"])

    def test_plans_sort_by_app_then_version(self):
        self.add("bat-apollo-theme", "v0.10.0")
        self.add("bat-apollo-theme", "v0.2.0")
        self.add("eza-apollo-theme", "v0.1.0")
        self.assertEqual([plan.tag for plan in self.plan()], ["bat-v0.1.0", "bat-v0.2.0", "bat-v0.10.0", "eza-v0.1.0"])

    # Inventory completeness: planning fails closed.

    def test_missing_json_raises(self):
        (self.backup / "releases" / "bat-apollo-theme" / "v0.1.0.json").unlink()
        with self.assertRaises(FileNotFoundError) as caught:
            self.plan()
        self.assertIn("v0.1.0.json missing", str(caught.exception))

    def test_missing_tag_asset_dir_raises(self):
        shutil.rmtree(self.asset().parent)
        with self.assertRaises(FileNotFoundError) as caught:
            self.plan()
        self.assertIn("backup asset v0.1.0/Apollo.tmTheme missing", str(caught.exception))

    def test_missing_repo_release_dir_raises(self):
        shutil.rmtree(self.backup / "releases" / "bat-apollo-theme")
        with self.assertRaises(FileNotFoundError) as caught:
            self.plan()
        self.assertIn("bat-apollo-theme: missing release backup", str(caught.exception))

    def test_missing_asset_raises(self):
        self.asset().unlink()
        with self.assertRaises(FileNotFoundError):
            self.plan()

    def test_asset_names_differ_from_inventory_raises(self):
        self.inventory["bat-apollo-theme"]["v0.1.0"] = ["Apollo.tmTheme", "Apollo Light.tmTheme"]
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("bat-apollo-theme: backup v0.1.0 assets differ from inventory", str(caught.exception))

    def test_backup_tag_not_in_inventory_raises(self):
        write_release(self.backup, "bat-apollo-theme", "v0.9.0", "v0.9.0", "x", {})
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("bat-apollo-theme: backup v0.9.0.json not in inventory", str(caught.exception))

    def test_backup_app_dir_not_in_inventory_raises(self):
        write_release(self.backup, "eza-apollo-theme", "v0.1.0", "v0.1.0", "x", {})
        with self.assertRaises(ValueError) as caught:
            self.plan()
        self.assertIn("eza-apollo-theme: release backup not in inventory", str(caught.exception))

    def test_cli_without_apply_prints_plans_only(self):
        inventory = self.backup / "inventory.json"
        inventory.write_text(json.dumps({"releases": self.inventory}), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--backup", str(self.backup), "--inventory", str(inventory)])
        self.assertEqual(code, 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[-1], "1 plans")
        self.assertIn("bat-v0.1.0", lines[0])
        self.assertIn("Apollo.tmTheme", lines[0])

    def test_cli_planning_failure_exits_nonzero(self):
        self.asset().unlink()
        inventory = self.backup / "inventory.json"
        inventory.write_text(json.dumps({"releases": self.inventory}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            code = main(["--backup", str(self.backup), "--inventory", str(inventory)])
        self.assertEqual(code, 1)
        self.assertIn("Apollo.tmTheme missing", err.getvalue())


class FakeGitHub:
    """Stateful stand-in for the gh commands apply() runs against apollo-theme/apollo-theme."""

    def __init__(self, releases=None):
        self.releases = {release["tag_name"]: release for release in (releases or [])}
        self.calls = []
        self.fail_upload_after = None  # number of successful asset uploads before failing
        self.ignore_edits = False
        self.uploads = 0
        self.listing_lag = 0  # listings that still omit a just-created release
        self._hidden = {}

    @property
    def writes(self):
        return [call for call in self.calls if call[:3] != ["gh", "api", "repos/apollo-theme/apollo-theme/releases"]]

    def _ok(self, command, stdout=""):
        return subprocess.CompletedProcess(command, 0, stdout, "")

    def _upload(self, release, path: Path) -> bool:
        if self.fail_upload_after is not None and self.uploads >= self.fail_upload_after:
            return False
        self.uploads += 1
        data = path.read_bytes()
        release["assets"] = [asset for asset in release["assets"] if asset["name"] != path.name]
        release["assets"].append({"name": path.name, "size": len(data), "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "state": "uploaded"})
        return True

    @staticmethod
    def _option(command, flag):
        return command[command.index(flag) + 1]

    def __call__(self, command, **kwargs):
        self.calls.append(list(command))
        assert command[0] == "gh", command
        if command[1] == "api":
            assert command[2:] == ["repos/apollo-theme/apollo-theme/releases", "--paginate", "--slurp"], command
            visible = [release for tag, release in self.releases.items() if self._hidden.get(tag, 0) <= 0]
            self._hidden = {tag: left - 1 for tag, left in self._hidden.items()}
            return self._ok(command, json.dumps([visible]))
        action, tag = command[2], command[3]
        assert self._option(command, "--repo") == "apollo-theme/apollo-theme", command
        if action == "create":
            assert "--verify-tag" in command and "--latest=false" in command, command
            if tag in self.releases:
                return subprocess.CompletedProcess(command, 1, "", "a release with the same tag name already exists")
            release = {
                "tag_name": tag, "name": self._option(command, "--title"),
                "body": Path(self._option(command, "--notes-file")).read_text(encoding="utf-8"),
                "draft": True, "prerelease": "--prerelease" in command, "assets": [],
            }
            self.releases[tag] = release
            self._hidden[tag] = self.listing_lag
            valued = {"--repo", "--title", "--notes-file"}
            paths, skip = [], False
            for argument in command[4:]:
                if skip:
                    skip = False
                elif argument in valued:
                    skip = True
                elif not argument.startswith("--"):
                    paths.append(Path(argument))
            for path in paths:
                if not self._upload(release, path):
                    return subprocess.CompletedProcess(command, 1, "", "upload failed")
            release["draft"] = False
            return self._ok(command)
        release = self.releases[tag]
        if action == "upload":
            assert "--clobber" in command, command
            for argument in command[4:]:
                if not argument.startswith("--") and argument != "apollo-theme/apollo-theme":
                    if not self._upload(release, Path(argument)):
                        return subprocess.CompletedProcess(command, 1, "", "upload failed")
            return self._ok(command)
        if action == "edit":
            assert "--draft=false" in command and "--latest=false" in command, command
            if not self.ignore_edits:
                release["name"] = self._option(command, "--title")
                release["body"] = Path(self._option(command, "--notes-file")).read_text(encoding="utf-8")
                release["draft"] = False
                release["prerelease"] = "--prerelease=true" in command
            return self._ok(command)
        raise AssertionError(f"unexpected command {command}")


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.a = base / "a.zip"
        self.b = base / "b.zip"
        self.a.write_bytes(b"alpha")
        self.b.write_bytes(b"bravo")
        self.plan = Plan(tag="bat-v0.1.0", title="bat v0.1.0", body="notes\n\n_migrated_\n", assets=[self.a, self.b])

    def tearDown(self):
        self.directory.cleanup()

    def complete(self, draft=False):
        return rest("bat-v0.1.0", "bat v0.1.0", "notes\n\n_migrated_\n", {"a.zip": b"alpha", "b.zip": b"bravo"}, draft=draft)

    def test_new_release_is_created_with_verify_tag_and_not_latest(self):
        fake = FakeGitHub()
        self.assertEqual(apply([self.plan], run=fake), [("bat-v0.1.0", "created")])
        create = fake.writes[0]
        self.assertEqual(create[:4], ["gh", "release", "create", "bat-v0.1.0"])
        self.assertEqual(fake._option(create, "--title"), "bat v0.1.0")
        self.assertEqual(len(fake.writes), 1)
        self.assertFalse(fake.releases["bat-v0.1.0"]["draft"])

    def test_listing_lag_after_create_is_retried(self):
        fake = FakeGitHub()
        fake.listing_lag = 2
        self.assertEqual(apply([self.plan], run=fake, sleep=lambda seconds: None), [("bat-v0.1.0", "created")])
        self.assertEqual(len(fake.writes), 1)

    def test_listing_lag_beyond_retries_raises(self):
        fake = FakeGitHub()
        fake.listing_lag = 99
        with self.assertRaisesRegex(RuntimeError, "not found after created"):
            apply([self.plan], run=fake, sleep=lambda seconds: None)

    def test_rerun_while_listing_is_stale_does_not_create_twice(self):
        fake = FakeGitHub()
        fake.listing_lag = 99
        with self.assertRaises(RuntimeError):
            apply([self.plan], run=fake, sleep=lambda seconds: None)
        fake.listing_lag = 0
        fake._hidden = {"bat-v0.1.0": 1}
        fake.calls.clear()
        self.assertEqual(apply([self.plan], run=fake, sleep=lambda seconds: None), [("bat-v0.1.0", "created")])
        self.assertEqual(1, sum(1 for tag in fake.releases if tag == "bat-v0.1.0"))
        self.assertFalse(any(call[2] in {"upload", "edit"} for call in fake.writes))

    def test_create_upload_failure_then_second_run_repairs(self):
        fake = FakeGitHub()
        fake.fail_upload_after = 1
        with self.assertRaises(subprocess.CalledProcessError):
            apply([self.plan], run=fake)
        left = fake.releases["bat-v0.1.0"]
        self.assertTrue(left["draft"])
        self.assertEqual([asset["name"] for asset in left["assets"]], ["a.zip"])

        fake.fail_upload_after = None
        fake.calls.clear()
        self.assertEqual(apply([self.plan], run=fake), [("bat-v0.1.0", "repaired")])
        upload, edit = fake.writes
        self.assertEqual(upload[:4], ["gh", "release", "upload", "bat-v0.1.0"])
        self.assertIn(str(self.b), upload)
        self.assertNotIn(str(self.a), upload)
        self.assertEqual(edit[:4], ["gh", "release", "edit", "bat-v0.1.0"])
        self.assertFalse(fake.releases["bat-v0.1.0"]["draft"])

    def test_draft_left_behind_is_published(self):
        fake = FakeGitHub([self.complete(draft=True)])
        self.assertEqual(apply([self.plan], run=fake), [("bat-v0.1.0", "repaired")])
        self.assertEqual([write[2] for write in fake.writes], ["edit"])
        self.assertFalse(fake.releases["bat-v0.1.0"]["draft"])

    def test_complete_release_makes_no_writes(self):
        fake = FakeGitHub([self.complete()])
        self.assertEqual(apply([self.plan], run=fake), [("bat-v0.1.0", "complete")])
        self.assertEqual(fake.writes, [])

    def test_wrong_title_or_body_is_edited(self):
        for field in ("name", "body"):
            with self.subTest(field=field):
                release = self.complete()
                release[field] = "stale"
                fake = FakeGitHub([release])
                self.assertEqual(apply([self.plan], run=fake), [("bat-v0.1.0", "repaired")])
                self.assertEqual([write[2] for write in fake.writes], ["edit"])

    def test_mismatched_or_failed_asset_is_reuploaded_alone(self):
        for change in (lambda asset: asset.update(digest="sha256:" + "0" * 64), lambda asset: asset.update(state="starter")):
            with self.subTest():
                release = self.complete()
                change(release["assets"][1])
                fake = FakeGitHub([release])
                self.assertEqual(apply([self.plan], run=fake), [("bat-v0.1.0", "repaired")])
                self.assertEqual(len(fake.writes), 1)
                self.assertEqual(fake.writes[0][2], "upload")
                self.assertIn(str(self.b), fake.writes[0])
                self.assertNotIn(str(self.a), fake.writes[0])

    def test_unexpected_live_asset_raises_without_writes(self):
        release = self.complete()
        release["assets"].append({"name": "stray.zip", "size": 1, "digest": "sha256:" + "0" * 64, "state": "uploaded"})
        fake = FakeGitHub([release])
        with self.assertRaises(RuntimeError) as caught:
            apply([self.plan], run=fake)
        self.assertIn("stray.zip", str(caught.exception))
        self.assertEqual(fake.writes, [])

    def test_repair_that_does_not_stick_raises(self):
        fake = FakeGitHub([self.complete(draft=True)])
        fake.ignore_edits = True
        with self.assertRaises(RuntimeError) as caught:
            apply([self.plan], run=fake)
        self.assertIn("bat-v0.1.0", str(caught.exception))
        self.assertIn("draft", str(caught.exception))

    def test_duplicate_live_releases_for_a_tag_raise(self):
        fake = FakeGitHub()
        fake.releases = {"one": self.complete(), "two": self.complete(draft=True)}
        with self.assertRaises(RuntimeError):
            apply([self.plan], run=fake)
        self.assertEqual(fake.writes, [])

    def test_listing_failure_raises(self):
        def broken(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "HTTP 502")

        with self.assertRaises(subprocess.CalledProcessError):
            apply([self.plan], run=broken)


class CheckReleasesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.backup = base / "backup"
        write_release(self.backup, "bat-apollo-theme", "v0.1.0", "v0.1.0", "b", {"Apollo.tmTheme": ASSET_BYTES})
        self.inventory = {"bat-apollo-theme": {"v0.1.0": ["Apollo.tmTheme"]}, "apollo-theme": {}}
        self.root = base / "root"
        self.root.mkdir()
        git("init", "-q", cwd=self.root)
        for tag in ROOT_RELEASE_TAGS:
            (self.root / "f.txt").write_text(tag, encoding="utf-8")
            git("add", "f.txt", cwd=self.root)
            git("commit", "-q", "-m", tag, cwd=self.root)
            git("tag", "-a", tag, "-m", tag, cwd=self.root) if tag == "v0.3.1" else git("tag", tag, cwd=self.root)
            write_release(self.backup, "apollo-theme", tag, f"Apollo Theme {tag}", f"root {tag}\r\n", {})
            self.inventory["apollo-theme"][tag] = []
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
            inventory=kwargs.pop("inventory", self.inventory),
            **kwargs,
        )

    def release(self, tag):
        return next(release for release in self.releases if release["tag_name"] == tag)

    def asset(self) -> Path:
        return self.backup / "releases" / "bat-apollo-theme" / "v0.1.0" / "Apollo.tmTheme"

    def test_matching_data_passes(self):
        self.assertEqual(self.check(), [])

    def test_api_path(self):
        paths = []
        check_releases(
            self.backup, api=lambda path: paths.append(path) or self.releases, download=self.download(),
            root=self.root, remote_tags=self.remote_tags, inventory=self.inventory,
        )
        self.assertEqual(paths, ["repos/apollo-theme/apollo-theme/releases"])

    def test_body_differs(self):
        self.release("bat-v0.1.0")["body"] = "b"
        self.assertEqual(self.check(), ["bat-v0.1.0: body differs"])

    def test_title_differs(self):
        self.release("bat-v0.1.0")["name"] = "v0.1.0"
        self.assertEqual(self.check(), ["bat-v0.1.0: title differs"])

    def test_draft_release_fails(self):
        self.release("bat-v0.1.0")["draft"] = True
        self.assertEqual(self.check(), ["bat-v0.1.0: release is a draft"])
        del self.release("bat-v0.1.0")["draft"]
        self.assertEqual(self.check(), ["bat-v0.1.0: release is a draft"])

    def test_prerelease_must_match_backup(self):
        self.release("bat-v0.1.0")["prerelease"] = True
        self.assertEqual(self.check(), ["bat-v0.1.0: prerelease differs"])
        path = self.backup / "releases" / "bat-apollo-theme" / "v0.1.0.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(dict(data, isPrerelease=True)), encoding="utf-8")
        self.assertEqual(self.check(), [])

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
        self.asset().write_bytes(ASSET_BYTES.replace(b"apollo", b"apolla"))
        self.assertEqual(self.check(), ["bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme sha256 differs from JSON"])

    def test_failures_fail_closed(self):
        def broken(path):
            raise subprocess.CalledProcessError(1, ["gh", "api", path])

        errors = check_releases(
            self.backup, api=broken, download=self.download(), root=self.root, remote_tags=self.remote_tags, inventory=self.inventory
        )
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("releases: "), errors)

        (self.backup / "apollo-theme.bundle").unlink()
        errors = self.check()
        self.assertEqual(len(errors), 1)
        self.assertIn("apollo-theme.bundle", errors[0])

    def test_slugs_filter_checks_only_those_apps_and_skips_root(self):
        write_release(self.backup, "eza-apollo-theme", "v0.1.0", "v0.1.0", "e", {})
        self.inventory["eza-apollo-theme"] = {"v0.1.0": []}
        self.assertEqual(self.check(slugs=["bat"], releases=self.releases[:1]), [])
        self.assertEqual(self.check(slugs=["eza"], releases=self.releases[:1]), ["eza-v0.1.0: release missing"])

    def test_requested_app_not_in_inventory_or_backup_fails_and_retired_apps_are_skipped(self):
        self.assertEqual(self.check(slugs=["vim"], releases=self.releases[:1]), ["vim: not in release inventory"])
        self.inventory["vim-apollo-theme"] = {"v0.1.0": []}
        errors = self.check(slugs=["vim"], releases=self.releases[:1])
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(errors[0].startswith("vim-apollo-theme: missing release backup"), errors)
        self.assertEqual(errors[1], "vim-v0.1.0: release missing")
        self.assertEqual(self.check(slugs=["wezterm"], releases=[]), [])

    def test_include_root_with_explicit_slugs(self):
        self.assertEqual(self.check(slugs=["bat"], include_root=True), [])
        releases = [release for release in self.releases if release["tag_name"] != "v0.3.0"]
        self.assertEqual(self.check(slugs=["bat"], include_root=True, releases=releases), ["v0.3.0: release missing"])

    # Inventory completeness: verification reports every gap once.

    def test_missing_app_json_is_reported(self):
        (self.backup / "releases" / "bat-apollo-theme" / "v0.1.0.json").unlink()
        self.assertEqual(self.check(), ["bat-apollo-theme: backup v0.1.0.json missing"])

    def test_missing_root_backup_json_is_reported(self):
        (self.backup / "releases" / "apollo-theme" / "v0.2.0.json").unlink()
        self.assertEqual(self.check(), ["apollo-theme: backup v0.2.0.json missing"])

    def test_missing_tag_asset_dir_is_reported(self):
        shutil.rmtree(self.asset().parent)
        self.assertEqual(self.check(), ["bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme missing"])

    def test_missing_repo_release_dir_is_reported(self):
        shutil.rmtree(self.backup / "releases" / "bat-apollo-theme")
        errors = self.check()
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].startswith("bat-apollo-theme: missing release backup"), errors)

    def test_missing_asset_is_reported(self):
        self.asset().unlink()
        self.assertEqual(self.check(), ["bat-apollo-theme: backup asset v0.1.0/Apollo.tmTheme missing"])

    def test_backup_tag_or_app_not_in_inventory_is_reported(self):
        write_release(self.backup, "bat-apollo-theme", "v0.9.0", "v0.9.0", "x", {})
        self.assertEqual(self.check(), ["bat-apollo-theme: backup v0.9.0.json not in inventory"])
        (self.backup / "releases" / "bat-apollo-theme" / "v0.9.0.json").unlink()
        write_release(self.backup, "eza-apollo-theme", "v0.1.0", "v0.1.0", "x", {})
        self.assertEqual(self.check(), ["eza-apollo-theme: release backup not in inventory"])

    def test_root_inventory_must_be_the_five_root_tags(self):
        del self.inventory["apollo-theme"]["v0.1.1"]
        (self.backup / "releases" / "apollo-theme" / "v0.1.1.json").unlink()
        self.assertEqual(self.check(), ["apollo-theme: inventory tags differ from v0.1.0..v0.3.1"])


if __name__ == "__main__":
    unittest.main()
