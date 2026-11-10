#!/usr/bin/env python3
"""Verify that every app folder still matches the repository it was migrated from.

Fail-closed: every subprocess error, missing bundle/backup file, or missing release is
reported as an error string; nothing is skipped.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from common import ROOT, SLUGS
from migration import (
    DEFAULT_BACKUP,
    DEFAULT_RETIRED,
    RETIRED,
    MigrationError,
    Source,
    bundle_source,
    app_release_dirs,
    migrated_body,
    release_title,
    source_for,
    version_key,
)
from sync_palette import PALETTE_FILES, PALETTE_REPOSITORY

ORG = "apollo-theme"
MONOREPO = f"{ORG}/apollo-theme"
ROOT_RELEASE_TAGS = ("v0.1.0", "v0.1.1", "v0.2.0", "v0.3.0", "v0.3.1")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")



def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def _failure(slug: str, result: subprocess.CompletedProcess, args: tuple) -> str:
    return f"{slug}: git {' '.join(args)} failed: {result.stderr.strip() or result.returncode}"


# Offline checks -----------------------------------------------------------


def check_tree(root: Path, source: Source) -> list[str]:
    args = ("diff", "--no-renames", "--name-only", f"{source.rev}^{{tree}}", f"HEAD:{source.slug}")
    result = _git(root, *args)
    if result.returncode != 0:
        return [_failure(source.slug, result, args)]
    return [
        f"{source.slug}: {path} differs from source"
        for path in result.stdout.splitlines()
        if path and not any(fnmatch.fnmatch(path, pattern) for pattern in source.allow)
    ]


def check_history(root: Path, source: Source) -> list[str]:
    args = ("merge-base", "--is-ancestor", source.rev, "HEAD")
    result = _git(root, *args)
    if result.returncode == 0:
        return []
    if result.returncode == 1:
        return [f"{source.slug}: source {source.rev} is not an ancestor of HEAD"]
    return [_failure(source.slug, result, args)]


def check_tags(root: Path | None, source: Source, remote_tags: dict | None = None) -> list[str]:
    """Compare tag commits. Offline reads ``<slug>-<tag>^{commit}``; online uses peeled ls-remote refs."""
    errors = []
    for tag, expected in sorted(source.tags.items()):
        name = f"{source.slug}-{tag}"
        if remote_tags is None:
            result = _git(root, "rev-parse", "--verify", "-q", f"refs/tags/{name}^{{commit}}")
            actual = result.stdout.strip() if result.returncode == 0 else None
        else:
            actual = remote_tags.get(f"refs/tags/{name}")
        if actual is None:
            errors.append(f"{source.slug}: tag {name} missing")
        elif actual != expected:
            errors.append(f"{source.slug}: tag {name} not on {expected}")
    return errors


# Online checks ------------------------------------------------------------


def run_ls_remote(*args: str) -> str:
    return subprocess.run(["git", "ls-remote", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def gh_api(path: str):
    """GET a GitHub API path; paginated list endpoints are flattened into one list."""
    output = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", path], check=True, capture_output=True, text=True
    ).stdout
    pages = json.loads(output)
    if all(isinstance(page, list) for page in pages):
        return [item for page in pages for item in page]
    return pages[0] if len(pages) == 1 else pages


def gh_raw(path: str) -> bytes:
    return subprocess.run(
        ["gh", "api", path, "-H", "Accept: application/vnd.github.raw"], check=True, capture_output=True
    ).stdout


def download_asset(asset: dict) -> bytes:
    url = asset.get("browser_download_url") or asset["url"]
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - fixed GitHub release URL
        return response.read()


def parse_ls_remote(text: str, peel: bool = False) -> dict[str, str]:
    """Map ref -> sha. With ``peel``, an annotated tag's ``^{}`` line wins; otherwise ``^{}`` lines are dropped."""
    refs: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        sha, ref = line.split("\t", 1)
        if ref.endswith("^{}"):
            peeled[ref[:-3]] = sha
        else:
            refs[ref] = sha
    if peel:
        refs.update(peeled)
    return refs


def check_pushed(root: Path, ls_remote=run_ls_remote) -> list[str]:
    try:
        remote = parse_ls_remote(ls_remote("origin", "refs/heads/main")).get("refs/heads/main")
    except (subprocess.CalledProcessError, OSError) as error:
        return [f"origin/main: ls-remote failed: {error}"]
    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return [f"HEAD: rev-parse failed: {head.stderr.strip()}"]
    return [] if remote == head.stdout.strip() else ["origin/main is not HEAD"]


def _pin_shape_problem(pin) -> str | None:
    """Reject a pin that would let check_pin verify less than both palettes at an exact commit."""
    if not isinstance(pin, dict):
        return "is not an object"
    if pin.get("repository") != PALETTE_REPOSITORY:
        return f"repository is not {PALETTE_REPOSITORY}"
    if not isinstance(pin.get("commit"), str) or not HEX40.match(pin["commit"]):
        return "commit is not a 40-hex SHA"
    digests = pin.get("sha256")
    if not isinstance(digests, dict) or set(digests) != set(PALETTE_FILES):
        return f"sha256 keys are not exactly {', '.join(PALETTE_FILES)}"
    for name in PALETTE_FILES:
        if not isinstance(digests[name], str) or not HEX64.match(digests[name]):
            return f"sha256 for {name} is not 64-hex"
    return None


def check_pin(root: Path, fetch_raw=gh_raw) -> list[str]:
    try:
        pin = json.loads((Path(root) / "palette" / "SOURCE.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"palette/SOURCE.json unreadable: {error}"]
    problem = _pin_shape_problem(pin)
    if problem:
        return [f"palette/SOURCE.json {problem}"]
    commit, digests = pin["commit"], pin["sha256"]
    errors = []
    for name, expected in sorted(digests.items()):
        try:
            data = fetch_raw(f"repos/{ORG}/apollo-palette/contents/palette/{name}?ref={commit}")
        except (subprocess.CalledProcessError, OSError) as error:
            errors.append(f"palette/{name}: fetch at {commit} failed: {error}")
            continue
        if hashlib.sha256(data).hexdigest() != expected:
            errors.append(f"palette/{name}: apollo-palette@{commit} does not match SOURCE.json")
    return errors


def normalize(release: dict, download=None) -> dict:
    """Comparable view of a release from either ``gh release view`` JSON or the REST API."""
    assets = []
    for asset in release.get("assets", []):
        digest = asset.get("digest")
        if digest:
            sha256 = digest.removeprefix("sha256:")
        elif download is not None:
            sha256 = hashlib.sha256(download(asset)).hexdigest()
        else:
            raise ValueError(f"asset {asset.get('name')} has no digest and no downloader")
        assets.append((asset["name"], asset["size"], sha256))
    body = (release.get("body") or "").replace("\r\n", "\n").rstrip()
    return {
        "tag": release["tagName"] if "tagName" in release else release["tag_name"],
        "name": release.get("name") or "",
        "body": body,
        "assets": sorted(assets),
    }


def _bundle_path(backup: Path, repo: str) -> Path:
    return Path(backup) / ("dot-github.bundle" if repo == ".github" else f"{repo}.bundle")


def _local_asset(directory: Path):
    def read(asset: dict) -> bytes:
        return (directory / asset["name"]).read_bytes()
    return read


def check_backup_assets(repo: str, tag: str, release: dict, directory: Path) -> list[str]:
    """Every asset in a backup release JSON exists locally with the recorded size and SHA-256."""
    errors = []
    for asset in release.get("assets", []):
        label = f"{repo}: backup asset {tag}/{asset.get('name')}"
        path = directory / str(asset.get("name"))
        if not path.is_file():
            errors.append(f"{label} missing")
            continue
        data = path.read_bytes()
        if asset.get("size") != len(data):
            errors.append(f"{label} size differs from JSON")
        digest = asset.get("digest")
        if digest and digest.removeprefix("sha256:") != hashlib.sha256(data).hexdigest():
            errors.append(f"{label} sha256 differs from JSON")
    return errors


def check_live_source(repo: str, backup: Path, ls_remote=run_ls_remote, api=gh_api, download=download_asset) -> list[str]:
    """The live org repository still matches its backup bundle and release JSON."""
    backup = Path(backup)
    bundle = _bundle_path(backup, repo)
    if not bundle.is_file():
        return [f"{repo}: missing bundle {bundle}"]
    releases_dir = backup / "releases" / repo
    if not releases_dir.is_dir():
        return [f"{repo}: missing release backup {releases_dir}"]
    errors: list[str] = []
    try:
        heads = subprocess.run(
            ["git", "bundle", "list-heads", str(bundle)], check=True, capture_output=True, text=True
        ).stdout
        expected_refs = {
            ref: sha
            for sha, ref in (line.split(" ", 1) for line in heads.splitlines() if line.strip())
            if ref.startswith(("refs/heads/", "refs/tags/"))
        }
        live_refs = parse_ls_remote(ls_remote("--heads", "--tags", f"https://github.com/{ORG}/{repo}"))
        live_releases = api(f"repos/{ORG}/{repo}/releases")
        backup_releases = {
            path.stem: json.loads(path.read_text(encoding="utf-8")) for path in sorted(releases_dir.glob("*.json"))
        }
        for tag, release in backup_releases.items():
            errors += check_backup_assets(repo, tag, release, releases_dir / tag)
        expected = {
            tag: normalize(release, _local_asset(releases_dir / tag)) for tag, release in backup_releases.items()
        }
        live = {}
        for release in live_releases:
            view = normalize(release, download)
            live[view["tag"]] = view
    except (subprocess.CalledProcessError, OSError, ValueError, KeyError, TypeError) as error:
        return errors + [f"{repo}: {type(error).__name__}: {error}"]

    if live_refs != expected_refs:
        errors.append(f"{repo}: refs differ from bundle")
    for tag in sorted(expected):
        if tag not in live:
            errors.append(f"{repo}: release {tag} missing")
        elif live[tag] != expected[tag]:
            errors.append(f"{repo}: release {tag} differs from backup")
    for tag in sorted(set(live) - set(expected)):
        errors.append(f"{repo}: release {tag} not in backup")
    return errors


# Restored releases --------------------------------------------------------


def gh_release_asset(tag: str, name: str) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            ["gh", "release", "download", tag, "--repo", MONOREPO, "-p", name, "-D", directory],
            check=True, capture_output=True, text=True,
        )
        return (Path(directory) / name).read_bytes()


def _check_restored(slug: str, directory: Path, tag: str, live: dict, download) -> list[str]:
    """One backed-up app release against its restored ``<slug>-<tag>`` monorepo release."""
    path = directory / f"{tag}.json"
    release = json.loads(path.read_text(encoding="utf-8"))
    restored = f"{slug}-{tag}"
    errors = check_backup_assets(directory.name, tag, release, directory / tag)
    if restored not in live:
        return errors + [f"{restored}: release missing"]
    expected = normalize(
        dict(release, tagName=restored, name=release_title(slug, tag, release.get("name") or ""),
             body=migrated_body(release.get("body") or "", directory.name)),
        _local_asset(directory / tag),
    )
    actual = normalize(live[restored], lambda asset: download(restored, asset["name"]))
    if actual == expected:
        return errors
    if actual["name"] != expected["name"]:
        errors.append(f"{restored}: title differs")
    if actual["body"] != expected["body"]:
        errors.append(f"{restored}: body differs")
    want = {name: (size, sha) for name, size, sha in expected["assets"]}
    have = {name: (size, sha) for name, size, sha in actual["assets"]}
    for name in sorted(want):
        if name not in have:
            errors.append(f"{restored}: {name} missing")
            continue
        if have[name][0] != want[name][0]:
            errors.append(f"{restored}: {name} size differs")
        if have[name][1] != want[name][1]:
            errors.append(f"{restored}: {name} sha256 differs")
    errors += [f"{restored}: {name} unexpected" for name in sorted(set(have) - set(want))]
    return errors


def _check_root_releases(backup: Path, live: dict, root: Path, remote_tags: dict) -> list[str]:
    """apollo-theme v0.1.0..v0.3.1 keep their backed-up name, body, and tag commit."""
    errors = []
    try:
        bundle_tags = bundle_source("apollo-theme", backup / "apollo-theme.bundle").tags
    except MigrationError as error:
        errors.append(f"apollo-theme: {error}")
        bundle_tags = None
    for tag in ROOT_RELEASE_TAGS:
        path = backup / "releases" / "apollo-theme" / f"{tag}.json"
        try:
            original = normalize(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, KeyError) as error:
            errors.append(f"{tag}: backup unreadable: {error}")
            continue
        if tag not in live:
            errors.append(f"{tag}: release missing")
        else:
            current = normalize(dict(live[tag], assets=[]))
            if (current["name"], current["body"]) != (original["name"], original["body"]):
                errors.append(f"{tag}: release changed")
        if bundle_tags is None:
            continue
        expected = bundle_tags.get(tag)
        if expected is None:
            errors.append(f"{tag}: tag not in apollo-theme.bundle")
            continue
        local = _git(root, "rev-parse", "--verify", "-q", f"refs/tags/{tag}^{{commit}}")
        if local.returncode != 0 or local.stdout.strip() != expected:
            errors.append(f"{tag}: tag commit changed locally")
        if remote_tags.get(f"refs/tags/{tag}") != expected:
            errors.append(f"{tag}: tag commit changed on origin")
    return errors


def check_releases(
    backup: Path,
    api=gh_api,
    download=gh_release_asset,
    root: Path = ROOT,
    remote_tags: dict | None = None,
    slugs: list[str] | None = None,
    include_root: bool | None = None,
) -> list[str]:
    """Restored app releases match the backup; the monorepo's own v0.1.0..v0.3.1 are unchanged.

    ``slugs=None`` checks every backed-up app and, by default, the root releases. Retired apps are skipped.
    """
    backup = Path(backup)
    include_root = slugs is None if include_root is None else include_root
    errors: list[str] = []
    try:
        live = {}
        for release in api(f"repos/{MONOREPO}/releases"):
            live[release["tag_name"]] = release
    except (subprocess.CalledProcessError, OSError, ValueError, KeyError, TypeError) as error:
        return [f"releases: {type(error).__name__}: {error}"]

    if slugs is None:
        try:
            apps = app_release_dirs(backup)
        except (OSError, ValueError) as error:
            return [f"releases: {error}"]
    else:
        apps = []
        for slug in slugs:
            directory = backup / "releases" / f"{slug}-apollo-theme"
            if slug in RETIRED:
                continue
            if not directory.is_dir():
                errors.append(f"{slug}: missing release backup {directory}")
                continue
            apps.append((slug, directory))
    for slug, directory in apps:
        if slug in RETIRED:
            continue
        for path in sorted(directory.glob("*.json"), key=lambda p: version_key(p.stem)):
            try:
                errors += _check_restored(slug, directory, path.stem, live, download)
            except (subprocess.CalledProcessError, OSError, ValueError, KeyError, TypeError) as error:
                errors.append(f"{slug}-{path.stem}: {type(error).__name__}: {error}")

    if include_root:
        if remote_tags is None:
            try:
                remote_tags = parse_ls_remote(run_ls_remote("--tags", "origin"), peel=True)
            except (subprocess.CalledProcessError, OSError) as error:
                errors.append(f"origin: ls-remote --tags failed: {error}")
                remote_tags = {}
        errors += _check_root_releases(backup, live, Path(root), remote_tags)
    return errors


# CLI ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the consolidated app folders against their source repositories")
    parser.add_argument("--app", choices=SLUGS, help="verify one app folder only")
    parser.add_argument("--offline", action="store_true", help="skip every network check")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help="org backup directory with bundles and releases")
    parser.add_argument("--retired", type=Path, default=DEFAULT_RETIRED, help="directory of retired <slug>-apollo-theme clones")
    parser.add_argument("--live-source", metavar="REPO", help="check a live org repository against its backup (online)")
    args = parser.parse_args(argv)
    if args.offline and args.live_source:
        parser.error("--live-source needs network access; drop --offline")

    errors: list[str] = []
    slugs = [args.app] if args.app else ([] if args.live_source else list(SLUGS))
    remote_tags = None
    if slugs and not args.offline:
        try:
            remote_tags = parse_ls_remote(run_ls_remote("--tags", "origin"), peel=True)
        except (subprocess.CalledProcessError, OSError) as error:
            errors.append(f"origin: ls-remote --tags failed: {error}")
            remote_tags = {}
    for slug in slugs:
        try:
            source = source_for(slug, args.backup, args.retired)
        except MigrationError as error:
            errors.append(f"{slug}: {error}")
            continue
        errors += check_tree(ROOT, source)
        errors += check_history(ROOT, source)
        errors += check_tags(ROOT, source, remote_tags=remote_tags)
    if slugs and not args.offline:
        errors += check_pushed(ROOT)
        errors += check_pin(ROOT)
        errors += check_releases(args.backup, remote_tags=remote_tags, slugs=[args.app] if args.app else None)
    if args.live_source:
        errors += check_live_source(args.live_source, args.backup)

    for error in errors:
        print(error)
    if errors:
        return 1
    if slugs:
        print(f"verified {len(slugs)} apps")
    if args.live_source:
        print(f"verified live source {args.live_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
