#!/usr/bin/env python3
"""Fail-closed deletion of the 15 consolidated apollo-theme repositories.

Gates, in order, each aborting the whole run on any failure:
  a. validate the ledger and reconcile it with GitHub
  b. the CI-green marker equals live apollo-theme main
  c. the live site lists 17 apps and links only to the three kept repositories
  d. every target bundle restores into a clean repository (fsck --strict, every ref present)
  e. every TODO target's issues, PRs, reviews, comments, and timelines are archived locally
  f. archive every TODO target (reversible)                          [--execute only]
  g. full online verify_migration.py                                  [--execute only]
  h. per target: verify live == backup, write-ahead pending, delete, confirm 404, mark deleted
  i. the organization lists exactly the three kept repositories

``--dry-run`` (the default) runs a-e and prints the plan; it writes local metadata backups only.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from common import ROOT
from migration import DEFAULT_BACKUP

ORG = "apollo-theme"
KEEPERS = ("apollo-palette", "apollo-theme", "apollo-theme.github.io")
TARGETS = (
    "sonicterm-apollo-theme", "windows-terminal-apollo-theme", "firefox-apollo-theme", "vscode-apollo-theme",
    "visual-studio-apollo-theme", "vim-apollo-theme", "nvim-apollo-theme", "xcode-apollo-theme",
    "tmux-apollo-theme", "rmux-apollo-theme", "powershell-apollo-theme", "bat-apollo-theme",
    "eza-apollo-theme", ".github", "demo-repository",
)
SITE_URL = "https://apollo-theme.github.io/"
SITE_PORTS = 17
DEFAULT_LEDGER = DEFAULT_BACKUP.parent / "deletion-ledger.json"
DEFAULT_CI_MARKER = DEFAULT_BACKUP.parent / "ci-green-sha"
VERIFY = ROOT / "scripts" / "verify_migration.py"
STATES = ("pending", "deleted")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ORG_LINK = re.compile(r"(?:github\.com|raw\.githubusercontent\.com)/apollo-theme/([A-Za-z0-9_.-]+)", re.I)


class AbortError(Exception):
    pass


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str
    stderr: str


class Runner:
    """The only door to the outside world; tests substitute a fake with the same two methods."""

    def run(self, argv, cwd=None) -> Result:
        done = subprocess.run(list(argv), cwd=cwd, capture_output=True, text=True)
        return Result(done.returncode, done.stdout, done.stderr)

    def fetch(self, url, headers) -> tuple[int, str]:
        request = urllib.request.Request(url, headers=dict(headers))
        try:
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed site URL
                return response.status, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            return error.code, ""
        except (urllib.error.URLError, OSError) as error:
            raise AbortError(f"site: fetch failed: {error}") from error


# Ledger -------------------------------------------------------------------


def _check_entries(entries) -> list[dict]:
    if not isinstance(entries, list):
        raise AbortError("ledger: entries is not a list")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"repo", "state", "at"}:
            raise AbortError(f"ledger: entry {entry!r} must have exactly repo, state, at")
        repo, state, at = entry["repo"], entry["state"], entry["at"]
        if repo not in TARGETS:
            raise AbortError(f"ledger: {repo!r} is not a deletion target")
        if repo in seen:
            raise AbortError(f"ledger: duplicate entry for {repo}")
        seen.add(repo)
        if state not in STATES:
            raise AbortError(f"ledger: {repo} has unknown state {state!r}")
        try:
            moment = datetime.datetime.fromisoformat(at) if isinstance(at, str) else None
        except ValueError:
            moment = None
        if moment is None or moment.tzinfo is None:
            raise AbortError(f"ledger: {repo} has invalid timestamp {at!r}")
    return entries


def load_ledger(path: Path) -> list[dict]:
    """Parse and fully validate the ledger. Only a nonexistent file means empty; any other failure aborts."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as error:
        raise AbortError(f"ledger: cannot read {path}: {error}") from error
    try:
        data = json.loads(text)
    except ValueError as error:
        raise AbortError(f"ledger: {path} is not JSON: {error}") from error
    if not isinstance(data, dict) or set(data) != {"version", "entries"}:
        raise AbortError("ledger: top level must be exactly {version, entries}")
    if type(data["version"]) is not int or data["version"] != 1:
        raise AbortError(f"ledger: unsupported version {data['version']!r}")
    return _check_entries(data["entries"])


def _fsync_dir(directory: Path) -> None:
    # Directory fsync makes the rename durable on POSIX; Windows cannot open a directory and its
    # replace is already metadata-journaled, so there is nothing to sync there.
    if os.name == "nt":
        return
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path: Path, data: bytes) -> None:
    """Temp file in the same directory, fsync, rename over the target, fsync the directory."""
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass
        raise
    _fsync_dir(path.parent)


def write_ledger(path: Path, entries: list[dict]) -> None:
    entries = _check_entries(entries)
    text = json.dumps({"version": 1, "entries": entries}, indent=2) + "\n"
    atomic_write(Path(path), text.encode("utf-8"))


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# Site ---------------------------------------------------------------------


def check_site(html: str) -> list[str]:
    errors = []
    ports = html.count('class="app-port"')
    if ports != SITE_PORTS:
        errors.append(f"site: {ports} app ports, expected {SITE_PORTS}")
    for match in ORG_LINK.finditer(html):
        name = match.group(1).lower()
        if name.endswith(".git"):
            name = name[:-4]
        if name not in KEEPERS:
            errors.append(f"site: link to {match.group(0)} (not a kept repository)")
    return list(dict.fromkeys(errors))


# Bundles ------------------------------------------------------------------


def bundle_path(backup: Path, repo: str) -> Path:
    return Path(backup) / ("dot-github.bundle" if repo == ".github" else f"{repo}.bundle")


def check_bundle(runner, bundle: Path) -> list[str]:
    """Restore the bundle into an isolated repository and prove every advertised ref is a present commit."""
    bundle = Path(bundle)
    label = bundle.name
    if not bundle.is_file():
        return [f"{label}: missing"]
    with tempfile.TemporaryDirectory() as directory:
        repo = str(Path(directory) / "restore.git")

        def git(*args):
            return runner.run(["git", "-C", repo, *args])

        init = runner.run(["git", "init", "-q", "--bare", repo])
        if init.returncode != 0:
            return [f"{label}: git init failed: {init.stderr.strip()}"]
        heads = runner.run(["git", "bundle", "list-heads", str(bundle)])
        if heads.returncode != 0:
            return [f"{label}: list-heads failed: {heads.stderr.strip()}"]
        advertised: dict[str, str] = {}
        for line in heads.stdout.splitlines():
            parts = line.split()
            if len(parts) != 2 or not HEX40.match(parts[0]):
                return [f"{label}: unparseable list-heads line {line!r}"]
            advertised[parts[1]] = parts[0]
        refs = {ref: sha for ref, sha in advertised.items() if ref.startswith("refs/")}
        if not refs:
            return [f"{label}: advertises no refs"]
        verify = git("bundle", "verify", "-q", str(bundle))
        if verify.returncode != 0:
            return [f"{label}: bundle verify failed: {verify.stderr.strip()}"]
        fetch = git("fetch", "-q", "--no-tags", str(bundle), "+refs/*:refs/*")
        if fetch.returncode != 0:
            return [f"{label}: fetch failed: {fetch.stderr.strip()}"]
        if "refs/heads/main" in refs:
            git("symbolic-ref", "HEAD", "refs/heads/main")
        fsck = git("fsck", "--full", "--strict", "--no-progress", "--no-dangling")
        if fsck.returncode != 0 or re.search(r"\b(missing|broken|error|corrupt)\b", fsck.stdout + fsck.stderr, re.I):
            return [f"{label}: fsck failed: {(fsck.stderr or fsck.stdout).strip()}"]
        listed = git("for-each-ref", "--format=%(objectname) %(refname)")
        restored = dict(reversed(line.split(" ", 1)) for line in listed.stdout.splitlines() if line.strip())
        errors = []
        if restored != refs:
            errors.append(f"{label}: restored refs differ from advertised refs")
        for ref, sha in sorted(advertised.items()):
            kind = git("cat-file", "-t", sha)
            commit = git("rev-parse", "--verify", "-q", f"{sha}^{{commit}}")
            if kind.returncode != 0 or commit.returncode != 0:
                errors.append(f"{label}: {ref} {sha} does not resolve to a commit")
        if "HEAD" in advertised and advertised["HEAD"] not in refs.values():
            errors.append(f"{label}: HEAD {advertised['HEAD']} is not an advertised ref")
        return errors


# Metadata -----------------------------------------------------------------


def _api_json(runner, path: str, paginate: bool):
    argv = ["gh", "api", "--paginate", "--slurp", path] if paginate else ["gh", "api", path]
    result = runner.run(argv)
    if result.returncode != 0:
        raise AbortError(f"metadata: gh api {path} failed: {result.stderr.strip() or result.returncode}")
    try:
        data = json.loads(result.stdout)
    except ValueError as error:
        raise AbortError(f"metadata: gh api {path} returned invalid JSON: {error}") from error
    if paginate:
        if not isinstance(data, list) or not all(isinstance(page, list) for page in data):
            raise AbortError(f"metadata: gh api {path} did not return a list of pages")
        return [item for page in data for item in page]
    return data


def _dump(data) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def export_metadata(runner, backup: Path, repo: str) -> dict:
    """Export repo settings, topics, and every issue/PR with its comments, reviews, and timeline.

    Everything is fetched and checked in memory before the first byte is written, so a failing call
    leaves the previous export intact. Output is deterministic, so a rerun on unchanged data is a no-op.
    """
    base = f"repos/{ORG}/{repo}"
    files: dict[str, bytes] = {}
    counts = dict.fromkeys(("issues", "pull_requests", "issue_comments", "reviews", "review_comments", "timeline_events"), 0)
    repo_json = _api_json(runner, base, paginate=False)
    if isinstance(repo_json, dict):
        repo_json.pop("temp_clone_token", None)  # per-request credential: not metadata, breaks idempotency
    files["repo.json"] = _dump(repo_json)
    files["topics.json"] = _dump(_api_json(runner, f"{base}/topics", paginate=False))
    items = _api_json(runner, f"{base}/issues?state=all&per_page=100", paginate=True)
    numbers = [item.get("number") if isinstance(item, dict) else None for item in items]
    if any(type(n) is not int for n in numbers) or len(set(numbers)) != len(numbers):
        raise AbortError(f"metadata: {repo} issue list is incomplete (bad or duplicate numbers)")
    files["issues.json"] = _dump(sorted(items, key=lambda item: item["number"]))
    for item in sorted(items, key=lambda item: item["number"]):
        n = item["number"]
        comments = _api_json(runner, f"{base}/issues/{n}/comments?per_page=100", paginate=True)
        timeline = _api_json(runner, f"{base}/issues/{n}/timeline?per_page=100", paginate=True)
        if len(comments) != item.get("comments"):
            raise AbortError(f"metadata: {repo} #{n} export incomplete: {len(comments)} comments, issue reports {item.get('comments')}")
        files[f"issues/{n}/comments.json"] = _dump(comments)
        files[f"issues/{n}/timeline.json"] = _dump(timeline)
        counts["issue_comments"] += len(comments)
        counts["timeline_events"] += len(timeline)
        if "pull_request" not in item:
            counts["issues"] += 1
            continue
        counts["pull_requests"] += 1
        pull = _api_json(runner, f"{base}/pulls/{n}", paginate=False)
        reviews = _api_json(runner, f"{base}/pulls/{n}/reviews?per_page=100", paginate=True)
        review_comments = _api_json(runner, f"{base}/pulls/{n}/comments?per_page=100", paginate=True)
        if not isinstance(pull, dict) or pull.get("number") != n:
            raise AbortError(f"metadata: {repo} PR #{n} export incomplete: pull JSON does not match")
        if len(review_comments) != pull.get("review_comments"):
            raise AbortError(
                f"metadata: {repo} PR #{n} export incomplete: {len(review_comments)} review comments, PR reports {pull.get('review_comments')}"
            )
        files[f"pulls/{n}/pull.json"] = _dump(pull)
        files[f"pulls/{n}/reviews.json"] = _dump(reviews)
        files[f"pulls/{n}/review_comments.json"] = _dump(review_comments)
        counts["reviews"] += len(reviews)
        counts["review_comments"] += len(review_comments)

    manifest = {
        "version": 1,
        "repo": f"{ORG}/{repo}",
        "counts": counts,
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
    }
    directory = Path(backup) / "metadata" / repo
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in sorted(files.items()):
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_bytes() != data:
            atomic_write(target, data)
    for stale in sorted(directory.rglob("*"), reverse=True):
        relative = stale.relative_to(directory).as_posix()
        if stale.is_file() and relative != "manifest.json" and relative not in files:
            stale.unlink()
        elif stale.is_dir() and not any(stale.iterdir()):
            stale.rmdir()
    manifest_bytes = _dump(manifest)
    if not (directory / "manifest.json").is_file() or (directory / "manifest.json").read_bytes() != manifest_bytes:
        atomic_write(directory / "manifest.json", manifest_bytes)
    verify_metadata(directory, manifest)
    return manifest


def verify_metadata(directory: Path, manifest: dict) -> None:
    """Re-read the export: manifest round-trips and every file matches its recorded SHA-256, nothing extra."""
    try:
        on_disk = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise AbortError(f"metadata: {directory} manifest unreadable: {error}") from error
    if on_disk != manifest:
        raise AbortError(f"metadata: {directory} manifest differs after write")
    present = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()} - {"manifest.json"}
    if present != set(manifest["files"]):
        raise AbortError(f"metadata: {directory} files differ from manifest")
    for name, digest in manifest["files"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise AbortError(f"metadata: {directory / name} hash differs from manifest")


# Deletion -----------------------------------------------------------------


class Deleter:
    def __init__(self, runner, backup=DEFAULT_BACKUP, ledger=DEFAULT_LEDGER, ci_marker=DEFAULT_CI_MARKER,
                 execute=False, targets=TARGETS, out=print, sleep=None, retries=6, skip_site_gate=False):
        targets = list(targets)
        for repo in targets:
            if repo in KEEPERS:
                raise AbortError(f"refusing to target kept repository {repo}")
            if repo not in TARGETS:
                raise AbortError(f"unknown deletion target {repo}")
        if len(set(targets)) != len(targets):
            raise AbortError("duplicate deletion target")
        if execute and skip_site_gate:
            raise AbortError("--skip-site-gate is only allowed with --dry-run")
        self.runner, self.backup, self.ledger_path = runner, Path(backup), Path(ledger)
        self.ci_marker, self.execute, self.targets, self.out = Path(ci_marker), execute, targets, out
        self.sleep = sleep if sleep is not None else (lambda seconds: time.sleep(seconds))
        self.retries, self.skip_site_gate = retries, skip_site_gate
        self.entries: dict[str, dict] = {}

    # a. ledger + reconcile
    def _record(self, repo: str, state: str) -> None:
        self.entries[repo] = {"repo": repo, "state": state, "at": _now()}
        write_ledger(self.ledger_path, list(self.entries.values()))

    def status(self, repo: str) -> tuple[int, dict | None]:
        result = self.runner.run(["gh", "api", "-i", f"repos/{ORG}/{repo}"])
        head, _, body = result.stdout.replace("\r\n", "\n").partition("\n\n")
        match = re.match(r"HTTP/[\d.]+ (\d{3})", head)
        if not match:
            raise AbortError(f"{repo}: cannot determine HTTP status: {(result.stderr or result.stdout).strip()[:200]}")
        code = int(match.group(1))
        if code != 200:
            return code, None
        try:
            data = json.loads(body)
        except ValueError as error:
            raise AbortError(f"{repo}: HTTP 200 with invalid JSON: {error}") from error
        if not isinstance(data, dict) or data.get("full_name") != f"{ORG}/{repo}":
            raise AbortError(f"{repo}: HTTP 200 resolves to {data.get('full_name') if isinstance(data, dict) else data!r}, not {ORG}/{repo}")
        return code, data

    def reconcile(self) -> list[str]:
        todo = []
        for repo in self.targets:
            code, _ = self.status(repo)
            if code not in (200, 404):
                raise AbortError(f"{repo}: unexpected HTTP {code}")
            entry = self.entries.get(repo)
            state = entry["state"] if entry else None
            if state == "deleted":
                if code != 404:
                    raise AbortError(f"{repo}: ledger says deleted but GitHub returns HTTP {code}")
                self.out(f"  {repo}: deleted (ledger, confirmed 404)")
            elif code == 404:
                if state != "pending":
                    raise AbortError(f"{repo}: GitHub returns 404 but it is not in the ledger")
                if self.execute:
                    self._record(repo, "deleted")
                    self.out(f"  {repo}: pending + 404 -> marked deleted")
                else:
                    self.out(f"  {repo}: pending + 404 -> would mark deleted")
            else:
                todo.append(repo)
                self.out(f"  {repo}: live (HTTP 200){'; pending in ledger, will re-verify' if state == 'pending' else ''}")
        return todo

    # b. CI marker
    def check_ci(self) -> None:
        try:
            marker = self.ci_marker.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise AbortError(f"CI marker unreadable: {error}") from error
        if not HEX40.match(marker):
            raise AbortError(f"CI marker {marker!r} is not a 40-hex SHA")
        result = self.runner.run(["git", "ls-remote", f"https://github.com/{ORG}/apollo-theme", "refs/heads/main"])
        lines = [line.split("\t") for line in result.stdout.splitlines() if line.strip()]
        if result.returncode != 0 or len(lines) != 1 or lines[0][1:] != ["refs/heads/main"]:
            raise AbortError(f"CI gate: ls-remote failed: {result.stderr.strip() or result.stdout.strip()}")
        if lines[0][0] != marker:
            raise AbortError(f"CI gate: marker {marker} is not live main {lines[0][0]}")
        self.out(f"  CI-green marker equals live main {marker}")

    # c. site
    def check_site(self) -> None:
        url = f"{SITE_URL}?nocache={int(time.time() * 1000)}"
        code, html = self.runner.fetch(url, {"Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
        if code != 200:
            raise AbortError(f"site gate: {url} returned HTTP {code}")
        errors = check_site(html)
        if errors:
            raise AbortError("site gate failed:\n  " + "\n  ".join(errors))
        self.out(f"  live site: {SITE_PORTS} app ports, only kept repositories linked")

    # d. bundles
    def check_bundles(self, repos) -> None:
        errors = []
        for repo in repos:
            problems = check_bundle(self.runner, bundle_path(self.backup, repo))
            errors += problems
            if not problems:
                self.out(f"  {bundle_path(self.backup, repo).name}: restored, fsck --strict clean, all refs present")
        if errors:
            raise AbortError("bundle gate failed:\n  " + "\n  ".join(errors))

    # e. metadata
    def export(self, repos) -> None:
        for repo in repos:
            manifest = export_metadata(self.runner, self.backup, repo)
            c = manifest["counts"]
            self.out(f"  {repo}: wrote metadata/{repo}/ ({len(manifest['files'])} files; {c['issues']} issues, "
                     f"{c['pull_requests']} PRs, {c['issue_comments']} comments, {c['reviews']} reviews, "
                     f"{c['review_comments']} review comments, {c['timeline_events']} timeline events)")

    # f. archive
    def archive(self, repos) -> None:
        for repo in repos:
            code, data = self.status(repo)
            if code != 200:
                raise AbortError(f"{repo}: HTTP {code} before archive")
            if not data.get("archived"):
                result = self.runner.run(["gh", "api", "-X", "PATCH", f"repos/{ORG}/{repo}", "-F", "archived=true"])
                if result.returncode != 0:
                    raise AbortError(f"{repo}: archive failed: {result.stderr.strip()}")
                code, data = self.status(repo)
                if code != 200 or not data.get("archived"):
                    raise AbortError(f"{repo}: not archived after PATCH")
            self.out(f"  {repo}: archived")

    # g/h. verify
    def verify(self, *args: str) -> None:
        argv = [sys.executable, str(VERIFY), "--backup", str(self.backup), *args]
        result = self.runner.run(argv, cwd=str(ROOT))
        if result.returncode != 0:
            raise AbortError(f"verify_migration.py {' '.join(args)} failed:\n{result.stdout}{result.stderr}")
        self.out(f"  verify_migration.py {' '.join(args)}: ok")

    def delete(self, repo: str) -> None:
        if repo in KEEPERS or repo not in TARGETS:
            raise AbortError(f"refusing to delete {repo}")
        code, _ = self.status(repo)
        if code != 200:
            raise AbortError(f"{repo}: HTTP {code} before delete")
        args = ["--live-source", repo]
        if repo.endswith("-apollo-theme"):
            args += ["--app", repo.removesuffix("-apollo-theme")]
        self.verify(*args)
        self._record(repo, "pending")
        result = self.runner.run(["gh", "repo", "delete", f"{ORG}/{repo}", "--yes"])
        for attempt in range(self.retries):
            code, _ = self.status(repo)
            if code == 404:
                self._record(repo, "deleted")
                self.out(f"  {repo}: deleted (confirmed 404)")
                return
            if code != 200:
                raise AbortError(f"{repo}: unexpected HTTP {code} after delete; ledger left pending")
            self.sleep(min(2 ** attempt, 30))
        detail = f": {result.stderr.strip()}" if result.returncode != 0 else ""
        raise AbortError(f"{repo}: still HTTP 200 after delete{detail}; ledger left pending, rerun to reconcile")

    # i. final
    def check_final(self) -> None:
        result = self.runner.run(["gh", "repo", "list", ORG, "--limit", "100", "--json", "name"])
        if result.returncode != 0:
            raise AbortError(f"final: gh repo list failed: {result.stderr.strip()}")
        try:
            names = sorted(item["name"] for item in json.loads(result.stdout))
        except (ValueError, KeyError, TypeError) as error:
            raise AbortError(f"final: unparseable repo list: {error}") from error
        if names != sorted(KEEPERS):
            raise AbortError(f"final: organization lists {names}, expected exactly {sorted(KEEPERS)}")
        self.out(f"  organization lists exactly {', '.join(names)}")

    def run(self) -> None:
        mode = "EXECUTE" if self.execute else "DRY RUN (no GitHub writes)"
        self.out(f"delete_repos: {mode}; ledger {self.ledger_path}; backup {self.backup}")
        self.out("a. ledger + reconcile")
        self.entries = {entry["repo"]: entry for entry in load_ledger(self.ledger_path)}
        todo = self.reconcile()
        self.out("b. CI gate")
        self.check_ci()
        self.out("c. live-site gate")
        if self.skip_site_gate:
            self.out("  SKIPPED (--skip-site-gate): this run cannot authorize --execute")
        else:
            self.check_site()
        self.out("d. bundle recoverability")
        self.check_bundles(todo)
        self.out(f"e. metadata archive (writes local backup files under {self.backup / 'metadata'})")
        self.export(todo)
        if not self.execute:
            self.out("plan (dry run; nothing archived or deleted, ledger untouched):")
            for repo in todo:
                self.out(f"  would archive, verify --live-source, then would delete apollo-theme/{repo}")
            if not todo:
                self.out("  nothing to delete")
            return
        self.out("f. archive")
        self.archive(todo)
        self.out("g. full verify")
        self.verify()
        self.out("h. delete")
        for repo in todo:
            self.delete(repo)
        self.out("i. final repository list")
        self.check_final()


def main(argv=None, runner=None, out=print) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="run gates a-e and print the plan (default)")
    mode.add_argument("--execute", action="store_true", help="archive and permanently delete the targets")
    parser.add_argument("--skip-site-gate", action="store_true", help="dry run only: skip gate c; exits 3")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--ci-marker", type=Path, default=DEFAULT_CI_MARKER)
    args = parser.parse_args(argv)
    if args.execute and args.skip_site_gate:
        parser.error("--skip-site-gate is only allowed with --dry-run")
    try:
        Deleter(runner or Runner(), backup=args.backup, ledger=args.ledger, ci_marker=args.ci_marker,
                execute=args.execute, out=out, skip_site_gate=args.skip_site_gate).run()
    except (AbortError, OSError) as error:
        out(f"ABORT: {error}")
        return 1
    if args.skip_site_gate:
        out("NOT CLEARED: the live-site gate was skipped")
        return 3
    out("done" if args.execute else "dry run passed every gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
