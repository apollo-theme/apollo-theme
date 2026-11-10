#!/usr/bin/env python3
"""Recreate every backed-up app release on apollo-theme/apollo-theme under its imported ``<slug>-<tag>`` tag.

Without ``--apply`` this only prints the plans. ``--apply`` is resumable: a missing release is created
with ``--latest=false``; an existing one (published or a draft left by an interrupted run) is compared to
its plan and repaired in place by re-uploading only missing or mismatched assets and editing metadata.
Every release must be complete after the run, or the run raises.

The expected set comes from ``release_inventory.json`` (recorded from the live source repositories), so a
missing backup JSON, release directory, or asset fails planning instead of silently shrinking the set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from common import SLUGS
from migration import (
    APP_REPO,
    DEFAULT_BACKUP,
    INVENTORY,
    inventory_problems,
    load_inventory,
    migrated_body,
    normalize_body,
    release_title,
    version_key,
)

MONOREPO = "apollo-theme/apollo-theme"


@dataclass(frozen=True)
class Plan:
    tag: str
    title: str
    body: str
    assets: list = field(default_factory=list)
    prerelease: bool = False


def _verified_assets(release: dict, directory: Path) -> list[Path]:
    """Local backup files for ``release``; each must exist and match the JSON size and SHA-256."""
    paths = []
    for asset in release.get("assets", []):
        path = directory / asset["name"]
        if not path.is_file():
            raise FileNotFoundError(f"missing backup asset {path}")
        data = path.read_bytes()
        digest = (asset.get("digest") or "").removeprefix("sha256:")
        if not digest:
            raise ValueError(f"backup asset {path} has no recorded digest")
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"backup asset {path} sha256 differs from JSON")
        if asset.get("size") != len(data):
            raise ValueError(f"backup asset {path} size differs from JSON")
        paths.append(path)
    return paths


def plan_releases(backup: Path = DEFAULT_BACKUP, inventory: dict | None = None) -> list[Plan]:
    inventory = load_inventory() if inventory is None else inventory
    backup = Path(backup)
    problems = inventory_problems(backup, inventory)
    if problems:
        error = FileNotFoundError if all(problem.missing for problem in problems) else ValueError
        raise error("; ".join(problems))
    plans = []
    for repo in sorted(inventory):
        match = APP_REPO.match(repo)
        if not match:
            continue
        slug = match["slug"]
        if slug not in SLUGS:
            raise ValueError(f"{repo}: unknown app in release inventory")
        directory = backup / "releases" / repo
        for tag in sorted(inventory[repo], key=version_key):
            release = json.loads((directory / f"{tag}.json").read_text(encoding="utf-8"))
            plans.append(
                Plan(
                    tag=f"{slug}-{tag}",
                    title=release_title(slug, tag, release.get("name") or ""),
                    body=migrated_body(release.get("body") or "", repo),
                    assets=_verified_assets(release, directory / tag),
                    prerelease=bool(release.get("isPrerelease", False)),
                )
            )
    return plans


# Applying -------------------------------------------------------------------


def _gh(run, *args: str) -> str:
    command = ["gh", *args]
    result = run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
    return result.stdout


def _live_release(run, tag: str) -> dict | None:
    """The monorepo release for ``tag``, drafts included (the tag endpoint omits drafts)."""
    pages = json.loads(_gh(run, "api", f"repos/{MONOREPO}/releases", "--paginate", "--slurp"))
    matches = [release for page in pages for release in page if release.get("tag_name") == tag]
    if len(matches) > 1:
        raise RuntimeError(f"{tag}: {len(matches)} releases share this tag; delete the extra drafts by hand and rerun")
    return matches[0] if matches else None


def _gaps(plan: Plan, live: dict) -> tuple[list[Path], list[str], list[str]]:
    """``(assets to upload, metadata problems, unexpected live asset names)`` for an existing release."""
    by_name = {asset.get("name"): asset for asset in live.get("assets", [])}
    uploads = []
    for path in plan.assets:
        data = path.read_bytes()
        asset = by_name.get(path.name)
        if (
            asset is None
            or asset.get("state", "uploaded") != "uploaded"
            or asset.get("size") != len(data)
            or (asset.get("digest") or "").removeprefix("sha256:") != hashlib.sha256(data).hexdigest()
        ):
            uploads.append(path)
    metadata = []
    if (live.get("name") or "") != plan.title:
        metadata.append("title")
    if normalize_body(live.get("body")) != normalize_body(plan.body):
        metadata.append("body")
    if live.get("draft") is not False:
        metadata.append("draft")
    if bool(live.get("prerelease")) != plan.prerelease:
        metadata.append("prerelease")
    unexpected = sorted(set(by_name) - {path.name for path in plan.assets})
    return uploads, metadata, unexpected


def _with_notes(plan: Plan, action):
    with tempfile.TemporaryDirectory() as directory:
        notes = Path(directory) / "notes.md"
        notes.write_text(plan.body, encoding="utf-8")
        return action(str(notes))


def _create(run, plan: Plan) -> None:
    def create(notes: str) -> None:
        command = [
            "gh", "release", "create", plan.tag, "--repo", MONOREPO, "--verify-tag",
            "--title", plan.title, "--notes-file", notes, "--latest=false",
            *(["--prerelease"] if plan.prerelease else []),
            *(str(path) for path in plan.assets),
        ]
        result = run(command, capture_output=True, text=True)
        if result.returncode != 0 and "already exists" not in (result.stderr or ""):
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)

    _with_notes(plan, create)


def _live_release_settled(run, tag: str, sleep, attempts: int = 6) -> dict | None:
    """``_live_release`` retried with backoff: GitHub's release listing lags just-created releases."""
    for attempt in range(attempts):
        live = _live_release(run, tag)
        if live is not None:
            return live
        if attempt < attempts - 1:
            sleep(2 ** attempt)
    return None


def _repair(run, plan: Plan, uploads: list[Path], metadata: list[str]) -> None:
    """Upload missing/mismatched assets first, then fix metadata and publish, so a draft is never published half-full."""
    if uploads:
        _gh(run, "release", "upload", plan.tag, *(str(path) for path in uploads), "--repo", MONOREPO, "--clobber")
    if not metadata:
        return

    def edit(notes: str) -> None:
        _gh(
            run, "release", "edit", plan.tag, "--repo", MONOREPO, "--title", plan.title, "--notes-file", notes,
            "--draft=false", "--latest=false", f"--prerelease={'true' if plan.prerelease else 'false'}",
        )

    _with_notes(plan, edit)


def apply(plans: list[Plan], run=subprocess.run, sleep=time.sleep) -> list[tuple[str, str]]:
    """Create or repair each release; return ``(tag, "created"|"repaired"|"complete")``.

    Any gh failure raises ``CalledProcessError``; rerunning resumes from whatever was left behind.
    A release still incomplete after repair, or holding assets not in its plan, raises ``RuntimeError``.
    """
    results = []
    for plan in plans:
        live = _live_release(run, plan.tag)
        if live is None:
            _create(run, plan)
            status = "created"
        else:
            uploads, metadata, unexpected = _gaps(plan, live)
            if unexpected:
                raise RuntimeError(
                    f"{plan.tag}: live release has assets not in the backup ({', '.join(unexpected)}); "
                    "inspect and delete them by hand, then rerun"
                )
            if not uploads and not metadata:
                results.append((plan.tag, "complete"))
                continue
            _repair(run, plan, uploads, metadata)
            status = "repaired"
        live = _live_release_settled(run, plan.tag, sleep)
        if live is None:
            raise RuntimeError(f"{plan.tag}: release not found after {status}; rerun --apply")
        uploads, metadata, unexpected = _gaps(plan, live)
        if uploads or metadata or unexpected:
            problems = [*(f"asset {path.name}" for path in uploads), *metadata, *(f"unexpected {name}" for name in unexpected)]
            raise RuntimeError(f"{plan.tag}: still incomplete after {status} ({', '.join(problems)}); rerun --apply")
        results.append((plan.tag, status))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore backed-up app releases onto apollo-theme/apollo-theme")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help="org backup directory with releases/")
    parser.add_argument("--inventory", type=Path, default=INVENTORY, help="frozen release inventory JSON")
    parser.add_argument("--apply", action="store_true", help="create or repair the releases on GitHub")
    args = parser.parse_args(argv)
    try:
        plans = plan_releases(args.backup, load_inventory(args.inventory))
    except (OSError, ValueError, KeyError) as error:
        print(f"cannot plan releases: {error}", file=sys.stderr)
        return 1
    if not args.apply:
        for plan in plans:
            print("\t".join((plan.tag, plan.title, ", ".join(path.name for path in plan.assets) or "-")))
        print(f"{len(plans)} plans")
        return 0
    try:
        results = apply(plans)
    except subprocess.CalledProcessError as error:
        print(f"gh failed: {' '.join(map(str, error.cmd[:4]))}: {(error.stderr or '').strip()}; rerun --apply to resume", file=sys.stderr)
        return 1
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    for tag, status in results:
        print(f"{status} {tag}")
    counts = {status: sum(1 for _, s in results if s == status) for status in ("created", "repaired", "complete")}
    print(", ".join(f"{count} {status}" for status, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
