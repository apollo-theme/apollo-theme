import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import delete_repos  # noqa: E402
from delete_repos import (  # noqa: E402
    KEEPERS,
    TARGETS,
    AbortError,
    Deleter,
    Result,
    check_bundle,
    check_site,
    export_metadata,
    load_ledger,
    main,
    write_ledger,
)

SHA = "a" * 40
TWO = ["bat-apollo-theme", ".github"]
AT = "2026-11-10T00:00:00+00:00"


def git(*args: str, cwd: Path) -> str:
    command = [
        "git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
        "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", "-c", "init.defaultBranch=main", *args,
    ]
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def site(ports: int = 17, extra: str = "") -> str:
    links = (
        '<a href="https://github.com/apollo-theme/apollo-theme/tree/main/bat">bat</a>'
        '<a href="https://github.com/apollo-theme/apollo-palette">palette</a>'
        '<img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/bat.svg">'
    )
    return "<html>" + '<li class="app-port">x</li>' * ports + links + extra + "</html>"


def is_write(call) -> bool:
    if not isinstance(call, list) or not call or call[0] not in ("gh", "git"):
        return False
    if call[0] == "git":
        return len(call) > 1 and call[1] == "push"
    if call[1:3] in (["repo", "delete"], ["repo", "edit"], ["repo", "archive"], ["repo", "create"], ["repo", "rename"]):
        return True
    for flag in ("-X", "--method"):
        if flag in call and call[call.index(flag) + 1].upper() != "GET":
            return True
    return False



def rmtree(path):
    """shutil.rmtree that also clears read-only bits, which git sets on object files (Windows refuses to unlink them)."""
    def retry(function, target, _info):
        os.chmod(target, stat.S_IWRITE)
        function(target)
    shutil.rmtree(path, onerror=retry)

class Crash(BaseException):
    """Simulates the process dying (kill -9, power loss) right after GitHub accepted the delete."""


class FakeGitHub:
    def __init__(self, repos, ci_sha=SHA, html=None, ledger=None):
        self.repos = {name: {"status": 200, "archived": False, "issues": [], "pulls": {}, "lists": {}, "lag": 0} for name in repos}
        self.calls: list = []
        self.ci_sha = ci_sha
        self.html = site() if html is None else html
        self.fail_paths: set = set()
        self.verify_rc: dict = {}
        self.crash_on_delete = None
        self.delete_lag = 0
        self.ledger = ledger
        self.ledger_at_delete: dict = {}
        self.extra_listed: list = []
        self.before_archive = None  # callable(repo) run just before a repo is archived

    @property
    def writes(self):
        return [call for call in self.calls if is_write(call)]

    def deletes(self, repo=None):
        return [c for c in self.calls if isinstance(c, list) and c[1:3] == ["repo", "delete"] and (repo is None or c[3] == f"apollo-theme/{repo}")]

    def fetch(self, url, headers):
        self.calls.append(("fetch", url, dict(headers)))
        return 200, self.html

    def run(self, argv, cwd=None):
        argv = list(argv)
        self.calls.append(argv)
        if argv[:2] == ["git", "ls-remote"]:
            return Result(0, f"{self.ci_sha}\trefs/heads/main\n", "")
        if argv[0] == "git":
            done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
            return Result(done.returncode, done.stdout, done.stderr)
        if argv[0] == sys.executable and argv[1].endswith("verify_migration.py"):
            key = argv[argv.index("--live-source") + 1] if "--live-source" in argv else "full"
            rc = self.verify_rc.get(key, 0)
            return Result(rc, "verified\n" if rc == 0 else "BAD\n", "")
        if argv[:3] == ["gh", "repo", "delete"]:
            repo = argv[3].split("/", 1)[1]
            if self.ledger is not None:
                entries = json.loads(Path(self.ledger).read_text())["entries"]
                self.ledger_at_delete[repo] = {e["repo"]: e["state"] for e in entries}.get(repo)
            state = self.repos[repo]
            state["status"], state["lag"] = 404, self.delete_lag
            if self.crash_on_delete == repo:
                raise Crash(repo)
            return Result(0, "", "")
        if argv[:3] == ["gh", "repo", "list"]:
            names = [r for r, s in self.repos.items() if s["status"] == 200] + list(KEEPERS) + self.extra_listed
            return Result(0, json.dumps([{"name": n} for n in names]), "")
        if argv[:2] == ["gh", "api"]:
            return self.api(argv[2:])
        raise AssertionError(f"unexpected command {argv}")

    def repo_json(self, repo):
        return {"name": repo, "full_name": f"apollo-theme/{repo}", "archived": self.repos[repo]["archived"], "description": "d", "homepage": ""}

    def api(self, args):
        path = next(a for a in args if a.startswith("repos/"))
        parts = path.split("?")[0].split("/")
        repo, rest = parts[2], parts[3:]
        state = self.repos.get(repo)
        live = state is not None and (state["status"] == 200 or state["lag"] > 0)
        if "-i" in args:
            if state is not None and state["lag"] > 0:
                state["lag"] -= 1
                code = 200
            else:
                code = state["status"] if state else 404
            body = json.dumps(self.repo_json(repo)) if code == 200 else json.dumps({"message": "Not Found"})
            reason = {200: "OK", 404: "Not Found"}.get(code, "Error")
            return Result(0 if code == 200 else 1, f"HTTP/2.0 {code} {reason}\nContent-Type: application/json\n\n{body}", "")
        if not live:
            return Result(1, "", "gh: Not Found (HTTP 404)")
        if path.split("?")[0] in self.fail_paths:
            return Result(1, "", "gh: Bad Gateway (HTTP 502)")
        if "-X" in args:
            assert args[args.index("-X") + 1] == "PATCH" and "archived=true" in args
            if self.before_archive is not None:
                self.before_archive(repo)
            state["archived"] = True
            return Result(0, json.dumps(self.repo_json(repo)), "")
        if not rest:
            data = self.repo_json(repo)
        elif rest == ["topics"]:
            data = {"names": ["theme"]}
        elif rest == ["issues"]:
            data = state["issues"]
        elif rest[0] == "issues" and rest[2] == "comments":
            data = state["lists"].get(("comments", int(rest[1])), [])
        elif rest[0] == "issues" and rest[2] == "timeline":
            data = state["lists"].get(("timeline", int(rest[1])), [])
        elif rest[0] == "pulls" and len(rest) == 2:
            data = state["pulls"][int(rest[1])]
        elif rest[0] == "pulls" and rest[2] == "reviews":
            data = state["lists"].get(("reviews", int(rest[1])), [])
        elif rest[0] == "pulls" and rest[2] == "comments":
            data = state["lists"].get(("review_comments", int(rest[1])), [])
        else:
            raise AssertionError(f"unexpected api path {path}")
        if "--paginate" in args:
            return Result(0, json.dumps([data]), "")
        return Result(0, json.dumps(data), "")

    def add_pr(self, repo, number=1):
        state = self.repos[repo]
        state["issues"].append({"number": number, "title": "Profile", "comments": 1, "pull_request": {"url": "u"}})
        state["pulls"][number] = {"number": number, "comments": 1, "review_comments": 1, "merged": True}
        state["lists"][("comments", number)] = [{"id": 10, "body": "c"}]
        state["lists"][("reviews", number)] = [{"id": 20, "state": "APPROVED"}]
        state["lists"][("review_comments", number)] = [{"id": 30, "body": "rc"}]
        state["lists"][("timeline", number)] = [{"event": "merged"}, {"event": "closed"}]

    def add_issue(self, repo, number=2, comments=0):
        self.repos[repo]["issues"].append({"number": number, "title": "Bug", "comments": comments})


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(tempfile.mkdtemp())
        src = cls.fixture / "src"
        src.mkdir()
        git("init", "-q", cwd=src)
        for i in range(3):
            (src / "f.txt").write_text("line %d\n" % i * 200, encoding="utf-8")
            git("add", ".", cwd=src)
            git("commit", "-q", "-m", f"c{i}", cwd=src)
        git("tag", "-a", "v0.1.0", "-m", "v0.1.0", cwd=src)
        cls.good = cls.fixture / "good.bundle"
        git("bundle", "create", "-q", str(cls.good), "--all", cwd=src)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.fixture)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.backup = self.tmp / "backup"
        self.backup.mkdir()
        for repo in TARGETS:
            name = "dot-github.bundle" if repo == ".github" else f"{repo}.bundle"
            shutil.copy(self.good, self.backup / name)
        self.ledger = self.tmp / "deletion-ledger.json"
        self.marker = self.tmp / "ci-green-sha"
        self.marker.write_text(SHA + "\n", encoding="utf-8")
        self.out: list[str] = []

    def tearDown(self):
        rmtree(self.tmp)

    def fake(self, repos=TWO, **kwargs):
        fake = FakeGitHub(repos, ledger=self.ledger, **kwargs)
        if ".github" in repos:
            fake.add_pr(".github")
        return fake

    def deleter(self, fake, execute=True, targets=TWO, **kwargs):
        kwargs.setdefault("sleep", lambda seconds: None)
        return Deleter(fake, backup=self.backup, ledger=self.ledger, ci_marker=self.marker,
                       execute=execute, targets=targets, out=self.out.append, **kwargs)

    def write_raw_ledger(self, entries):
        self.ledger.write_text(json.dumps({"version": 1, "entries": entries}), encoding="utf-8")

    def states(self):
        return {e["repo"]: e["state"] for e in json.loads(self.ledger.read_text())["entries"]}


class TargetTests(Base):
    def test_target_set_is_exactly_fifteen_without_keepers(self):
        self.assertEqual(15, len(set(TARGETS)))
        self.assertEqual(set(), set(TARGETS) & set(KEEPERS))
        self.assertEqual(("apollo-palette", "apollo-theme", "apollo-theme.github.io"), tuple(sorted(KEEPERS)))

    def test_keeper_passed_as_target_aborts_before_any_call(self):
        fake = self.fake()
        for keeper in KEEPERS:
            with self.assertRaisesRegex(AbortError, keeper):
                self.deleter(fake, targets=TWO + [keeper])
        with self.assertRaisesRegex(AbortError, "unknown"):
            self.deleter(fake, targets=["stray-repo"])
        self.assertEqual([], fake.calls)

    def test_full_run_never_writes_to_keepers(self):
        fake = self.fake()
        self.deleter(fake).run()
        touched = {c[3].split("/", 1)[1] if c[1] == "repo" else c[4].split("/")[2] for c in fake.writes}
        self.assertEqual(set(TWO), touched)


class LedgerTests(Base):
    def test_malformed_ledgers_abort(self):
        bad = [
            "not json",
            json.dumps([]),
            json.dumps({"version": 2, "entries": []}),
            json.dumps({"version": 1}),
            json.dumps({"version": 1, "entries": [], "extra": 1}),
            json.dumps({"version": 1, "entries": [{"repo": "bat-apollo-theme", "state": "gone", "at": AT}]}),
            json.dumps({"version": 1, "entries": [{"repo": "bat-apollo-theme", "state": "deleted"}]}),
            json.dumps({"version": 1, "entries": [{"repo": "bat-apollo-theme", "state": "deleted", "at": "yesterday"}]}),
            json.dumps({"version": 1, "entries": [{"repo": "bat-apollo-theme", "state": "deleted", "at": "2026-11-10T00:00:00"}]}),
            json.dumps({"version": 1, "entries": [{"repo": "bat-apollo-theme", "state": "deleted", "at": AT, "x": 1}]}),
            json.dumps({"version": 1, "entries": [{"repo": "bat-apollo-theme", "state": "deleted", "at": AT}] * 2}),
            json.dumps({"version": 1, "entries": [{"repo": "stray-repo", "state": "deleted", "at": AT}]}),
            json.dumps({"version": 1, "entries": [{"repo": "apollo-theme", "state": "pending", "at": AT}]}),
        ]
        for text in bad:
            with self.subTest(text=text):
                self.ledger.write_text(text, encoding="utf-8")
                with self.assertRaises(AbortError):
                    load_ledger(self.ledger)

    def test_missing_ledger_is_empty_but_unreadable_ledger_aborts(self):
        self.assertEqual([], load_ledger(self.ledger))
        self.ledger.mkdir()
        with self.assertRaises(AbortError):
            load_ledger(self.ledger)

    def test_malformed_ledger_aborts_before_any_external_call(self):
        self.ledger.write_text("{", encoding="utf-8")
        fake = self.fake()
        with self.assertRaisesRegex(AbortError, "ledger"):
            self.deleter(fake).run()
        self.assertEqual([], fake.calls)

    def test_unknown_repo_in_ledger_aborts_before_any_external_call(self):
        self.write_raw_ledger([{"repo": "humble-apollo", "state": "deleted", "at": AT}])
        fake = self.fake()
        with self.assertRaisesRegex(AbortError, "humble-apollo"):
            self.deleter(fake).run()
        self.assertEqual([], fake.calls)

    def test_write_is_atomic_when_replace_fails(self):
        write_ledger(self.ledger, [{"repo": "bat-apollo-theme", "state": "pending", "at": AT}])
        before = self.ledger.read_bytes()
        with mock.patch("delete_repos.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                write_ledger(self.ledger, [{"repo": "bat-apollo-theme", "state": "deleted", "at": AT}])
        self.assertEqual(before, self.ledger.read_bytes())
        self.assertEqual({"backup", "ci-green-sha", "deletion-ledger.json"}, {p.name for p in self.tmp.iterdir()})

    def test_write_is_atomic_when_fsync_fails(self):
        write_ledger(self.ledger, [{"repo": "bat-apollo-theme", "state": "pending", "at": AT}])
        before = self.ledger.read_bytes()
        with mock.patch("delete_repos.os.fsync", side_effect=OSError("io error")):
            with self.assertRaises(OSError):
                write_ledger(self.ledger, [{"repo": "bat-apollo-theme", "state": "deleted", "at": AT}])
        self.assertEqual(before, self.ledger.read_bytes())
        self.assertEqual({"backup", "ci-green-sha", "deletion-ledger.json"}, {p.name for p in self.tmp.iterdir()})

    def test_write_fsyncs_file_and_directory(self):
        with mock.patch("delete_repos.os.fsync", wraps=delete_repos.os.fsync) as fsync:
            write_ledger(self.ledger, [])
        self.assertGreaterEqual(fsync.call_count, 1 if os.name == "nt" else 2)
        self.assertEqual({"version": 1, "entries": []}, json.loads(self.ledger.read_text()))


class ReconcileTests(Base):
    def test_unrecorded_404_aborts_without_writes(self):
        fake = self.fake()
        fake.repos[".github"]["status"] = 404
        with self.assertRaisesRegex(AbortError, r"\.github.*404.*not in the ledger"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)

    def test_deleted_entry_that_still_exists_aborts(self):
        self.write_raw_ledger([{"repo": "bat-apollo-theme", "state": "deleted", "at": AT}])
        fake = self.fake()
        with self.assertRaisesRegex(AbortError, "bat-apollo-theme"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)

    def test_unexpected_status_aborts(self):
        fake = self.fake()
        fake.repos["bat-apollo-theme"]["status"] = 500
        with self.assertRaisesRegex(AbortError, "500"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)

    def test_pending_and_404_reconciles_to_deleted_without_delete(self):
        self.write_raw_ledger([{"repo": "bat-apollo-theme", "state": "pending", "at": AT}])
        fake = self.fake()
        fake.repos["bat-apollo-theme"]["status"] = 404
        self.deleter(fake).run()
        self.assertEqual({"bat-apollo-theme": "deleted", ".github": "deleted"}, self.states())
        self.assertEqual([], fake.deletes("bat-apollo-theme"))
        self.assertEqual(1, len(fake.deletes(".github")))

    def test_pending_and_200_reverifies_and_deletes(self):
        self.write_raw_ledger([{"repo": "bat-apollo-theme", "state": "pending", "at": AT}])
        fake = self.fake()
        self.deleter(fake).run()
        verify = [c for c in fake.calls if isinstance(c, list) and c[0] == sys.executable and "bat-apollo-theme" in c]
        self.assertEqual([[sys.executable, str(ROOT / "scripts" / "verify_migration.py"), "--backup", str(self.backup),
                           "--live-source", "bat-apollo-theme", "--app", "bat"]], verify)
        self.assertEqual(1, len(fake.deletes("bat-apollo-theme")))
        self.assertEqual({"bat-apollo-theme": "deleted", ".github": "deleted"}, self.states())

    def test_crash_after_delete_then_rerun_reconciles_without_second_delete(self):
        fake = self.fake()
        fake.crash_on_delete = "bat-apollo-theme"
        with self.assertRaises(Crash):
            self.deleter(fake).run()
        self.assertEqual({"bat-apollo-theme": "pending"}, self.states())
        fake.crash_on_delete = None
        self.deleter(fake).run()
        self.assertEqual(1, len(fake.deletes("bat-apollo-theme")))
        self.assertEqual(1, len(fake.deletes(".github")))
        self.assertEqual({"bat-apollo-theme": "deleted", ".github": "deleted"}, self.states())


class DeletionTests(Base):
    def test_pending_is_written_before_each_delete(self):
        fake = self.fake()
        self.deleter(fake).run()
        self.assertEqual({"bat-apollo-theme": "pending", ".github": "pending"}, fake.ledger_at_delete)

    def test_order_archive_then_full_verify_then_per_repo(self):
        fake = self.fake()
        self.deleter(fake).run()
        steps = []
        for c in fake.calls:
            if not isinstance(c, list):
                continue
            if "-X" in c:
                steps.append(("archive", c[4].split("/")[2]))
            elif c[0] == sys.executable:
                steps.append(("verify", c[c.index("--live-source") + 1] if "--live-source" in c else "full"))
            elif c[1:3] == ["repo", "delete"]:
                steps.append(("delete", c[3].split("/")[1]))
        self.assertEqual([
            ("archive", "bat-apollo-theme"), ("archive", ".github"), ("verify", "full"),
            ("verify", "bat-apollo-theme"), ("delete", "bat-apollo-theme"),
            ("verify", ".github"), ("delete", ".github"),
        ], steps)
        dot = [c for c in fake.calls if isinstance(c, list) and c[0] == sys.executable and ".github" in c][0]
        self.assertNotIn("--app", dot)

    def test_propagation_lag_is_retried(self):
        fake = self.fake()
        fake.delete_lag = 2
        self.deleter(fake, retries=5).run()
        self.assertEqual({"bat-apollo-theme": "deleted", ".github": "deleted"}, self.states())

    def test_delete_not_confirmed_aborts_and_stays_pending(self):
        fake = self.fake()
        fake.delete_lag = 99
        with self.assertRaisesRegex(AbortError, "bat-apollo-theme"):
            self.deleter(fake, retries=3).run()
        self.assertEqual({"bat-apollo-theme": "pending"}, self.states())
        self.assertEqual([], fake.deletes(".github"))

    def test_failed_live_source_verify_blocks_delete(self):
        fake = self.fake()
        fake.verify_rc[".github"] = 1
        with self.assertRaisesRegex(AbortError, r"\.github"):
            self.deleter(fake).run()
        self.assertEqual([], fake.deletes(".github"))
        self.assertNotIn(".github", self.states())

    def test_failed_full_verify_blocks_every_delete(self):
        fake = self.fake()
        fake.verify_rc["full"] = 1
        with self.assertRaisesRegex(AbortError, "verify_migration"):
            self.deleter(fake).run()
        self.assertEqual([], fake.deletes())

    def test_ci_marker_mismatch_aborts_without_writes(self):
        fake = self.fake(ci_sha="b" * 40)
        with self.assertRaisesRegex(AbortError, "CI"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)

    def test_missing_ci_marker_aborts(self):
        self.marker.unlink()
        fake = self.fake()
        with self.assertRaisesRegex(AbortError, "CI"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)

    def test_final_repo_list_mismatch_aborts(self):
        fake = self.fake()
        fake.extra_listed = ["stray"]
        with self.assertRaisesRegex(AbortError, "stray"):
            self.deleter(fake).run()

    def test_main_exits_nonzero_on_final_repo_list_mismatch(self):
        fake = self.fake(repos=list(TARGETS))
        fake.extra_listed = ["stray"]
        argv = ["--execute", "--backup", str(self.backup), "--ledger", str(self.ledger), "--ci-marker", str(self.marker)]
        with mock.patch("delete_repos.time.sleep"):
            self.assertEqual(1, main(argv, runner=fake, out=self.out.append))
        self.assertEqual(15, len(fake.deletes()))
        self.assertTrue(any("stray" in line for line in self.out))

    def test_main_rejects_skip_site_gate_with_execute(self):
        fake = self.fake()
        with self.assertRaises(SystemExit):
            main(["--execute", "--skip-site-gate"], runner=fake, out=self.out.append)
        self.assertEqual([], fake.calls)


class DryRunTests(Base):
    def test_dry_run_performs_zero_github_writes(self):
        self.write_raw_ledger([{"repo": "bat-apollo-theme", "state": "pending", "at": AT}])
        before = self.ledger.read_bytes()
        fake = self.fake()
        fake.repos["bat-apollo-theme"]["status"] = 404
        self.deleter(fake, execute=False).run()
        self.assertEqual([], fake.writes)
        self.assertEqual(before, self.ledger.read_bytes())
        self.assertFalse(any(isinstance(c, list) and c[0] == sys.executable for c in fake.calls))
        self.assertTrue((self.backup / "metadata" / ".github" / "manifest.json").is_file())
        text = "\n".join(self.out)
        self.assertIn("would delete apollo-theme/.github", text)
        self.assertIn("metadata", text)

    def test_dry_run_leaves_no_ledger(self):
        fake = self.fake()
        self.deleter(fake, execute=False).run()
        self.assertFalse(self.ledger.exists())

    def test_main_dry_run_is_default_and_skip_site_gate_exits_nonzero(self):
        fake = self.fake(repos=list(TARGETS), html=site(13))
        argv = ["--backup", str(self.backup), "--ledger", str(self.ledger), "--ci-marker", str(self.marker)]
        self.assertEqual(1, main(argv, runner=fake, out=self.out.append))
        self.assertEqual(3, main(argv + ["--skip-site-gate"], runner=fake, out=self.out.append))
        self.assertEqual([], fake.writes)


class SiteTests(Base):
    def test_good_site_passes(self):
        self.assertEqual([], check_site(site()))

    def test_thirteen_ports_rejected(self):
        self.assertTrue(any("13" in e for e in check_site(site(13))))

    def test_dead_links_rejected(self):
        for link in (
            '<a href="https://github.com/apollo-theme/bat-apollo-theme">x</a>',
            '<a href="https://github.com/apollo-theme/.github">x</a>',
            '<img src="https://raw.githubusercontent.com/apollo-theme/vim-apollo-theme/main/x.png">',
            '<a href="https://GitHub.com/Apollo-Theme/demo-repository.git">x</a>',
        ):
            with self.subTest(link=link):
                self.assertTrue(check_site(site(17, link)))

    def test_site_gate_blocks_run_and_bypasses_cache(self):
        fake = self.fake(html=site(13))
        with self.assertRaisesRegex(AbortError, "site"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)
        fetch = [c for c in fake.calls if isinstance(c, tuple)][0]
        self.assertIn("?", fetch[1])
        self.assertIn("no-cache", fetch[2].get("Cache-Control", ""))


class BundleTests(Base):
    def run_git(self):
        fake = FakeGitHub([])
        return fake

    def test_good_bundle_passes(self):
        self.assertEqual([], check_bundle(self.run_git(), self.good))

    def test_truncated_bundle_fails(self):
        data = self.good.read_bytes()
        bad = self.tmp / "bad.bundle"
        bad.write_bytes(data[: len(data) - 40])
        self.assertTrue(check_bundle(self.run_git(), bad))

    def test_missing_bundle_fails(self):
        self.assertTrue(check_bundle(self.run_git(), self.tmp / "absent.bundle"))

    def test_truncated_bundle_blocks_run(self):
        data = self.good.read_bytes()
        (self.backup / "dot-github.bundle").write_bytes(data[: len(data) // 2])
        fake = self.fake()
        with self.assertRaisesRegex(AbortError, "dot-github"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)


class MetadataTests(Base):
    def test_export_writes_manifest_with_counts_and_hashes(self):
        fake = self.fake()
        fake.add_issue(".github", 2, comments=0)
        manifest = export_metadata(fake, self.backup, ".github")
        directory = self.backup / "metadata" / ".github"
        self.assertEqual(manifest, json.loads((directory / "manifest.json").read_text()))
        self.assertEqual({"issues": 1, "pull_requests": 1, "issue_comments": 1, "reviews": 1,
                          "review_comments": 1, "timeline_events": 2}, manifest["counts"])
        on_disk = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()} - {"manifest.json"}
        self.assertEqual(set(manifest["files"]), on_disk)
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), digest)
        for required in ("repo.json", "topics.json", "issues.json", "pulls/1/pull.json", "pulls/1/reviews.json",
                         "pulls/1/review_comments.json", "issues/1/comments.json", "issues/1/timeline.json",
                         "issues/2/comments.json", "issues/2/timeline.json"):
            self.assertIn(required, manifest["files"])

    def test_export_is_idempotent(self):
        fake = self.fake()
        export_metadata(fake, self.backup, ".github")
        directory = self.backup / "metadata" / ".github"
        first = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        export_metadata(fake, self.backup, ".github")
        second = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        self.assertEqual(first, second)

    def test_manifest_paths_ignore_platform_separator(self):
        # On Windows str(relative_to()) uses backslashes; the manifest keys use "/".
        fake = self.fake()
        export_metadata(fake, self.backup, ".github")
        directory = self.backup / "metadata" / ".github"
        nested = sorted(p for p in directory.rglob("*") if p.is_file() and p.parent != directory)
        self.assertTrue(nested, "fixture must export nested files")
        real = Path.relative_to
        with mock.patch.object(Path, "relative_to", lambda self, *a, **k: PureWindowsPath(real(self, *a, **k).as_posix())):
            export_metadata(fake, self.backup, ".github")
        self.assertEqual(nested, sorted(p for p in directory.rglob("*") if p.is_file() and p.parent != directory))

    def test_export_drops_per_request_clone_token(self):
        fake = self.fake()
        plain, tokens = fake.repo_json, iter(range(1000))
        fake.repo_json = lambda repo: dict(plain(repo), temp_clone_token=f"TOKEN{next(tokens)}")
        export_metadata(fake, self.backup, ".github")
        directory = self.backup / "metadata" / ".github"
        first = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        export_metadata(fake, self.backup, ".github")
        self.assertEqual(first, {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()})
        self.assertNotIn("temp_clone_token", (directory / "repo.json").read_text())

    def test_failing_pr_sub_call_aborts_and_keeps_previous_export(self):
        fake = self.fake()
        export_metadata(fake, self.backup, ".github")
        directory = self.backup / "metadata" / ".github"
        before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
        fake.fail_paths.add("repos/apollo-theme/.github/pulls/1/reviews")
        with self.assertRaisesRegex(AbortError, "pulls/1/reviews"):
            export_metadata(fake, self.backup, ".github")
        self.assertEqual(before, {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()})

    def test_comment_count_mismatch_aborts(self):
        fake = self.fake()
        fake.repos[".github"]["lists"][("comments", 1)] = []
        with self.assertRaisesRegex(AbortError, "incomplete"):
            export_metadata(fake, self.backup, ".github")

    def test_failing_metadata_blocks_run(self):
        fake = self.fake()
        fake.fail_paths.add("repos/apollo-theme/.github/issues/1/timeline")
        with self.assertRaisesRegex(AbortError, "timeline"):
            self.deleter(fake).run()
        self.assertEqual([], fake.writes)

    def test_metadata_added_before_freeze_is_archived_before_any_delete(self):
        # Tech Lead race: an issue opened after the first export but before archival must not be lost.
        fake = self.fake()
        fake.before_archive = lambda repo: fake.add_issue(repo, number=7) if repo == "bat-apollo-theme" else None
        self.deleter(fake).run()
        issues = json.loads((self.backup / "metadata" / "bat-apollo-theme" / "issues.json").read_text(encoding="utf-8"))
        self.assertIn(7, [issue["number"] for issue in issues])
        refresh = [i for i, c in enumerate(fake.calls) if isinstance(c, list) and "repos/apollo-theme/bat-apollo-theme/issues?state=all&per_page=100" in c]
        first_delete = fake.calls.index(fake.deletes()[0])
        self.assertTrue(any(i < first_delete for i in refresh[1:]), "metadata must be re-exported after archive and before the first delete")

    def test_metadata_refresh_failure_after_freeze_blocks_every_delete(self):
        fake = self.fake()
        def fail_after_archive(repo):
            fake.fail_paths.add("repos/apollo-theme/.github/issues/1/timeline")
        fake.before_archive = fail_after_archive
        with self.assertRaisesRegex(AbortError, "timeline"):
            self.deleter(fake).run()
        self.assertEqual([], fake.deletes())


if __name__ == "__main__":
    unittest.main()
