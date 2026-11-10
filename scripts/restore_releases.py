#!/usr/bin/env python3
"""Recreate every backed-up app release on apollo-theme/apollo-theme under its imported ``<slug>-<tag>`` tag.

Without ``--apply`` this only prints the plans. ``--apply`` skips tags that already have a
release and creates the rest with ``--latest=false`` so the monorepo's own latest release stays.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from migration import DEFAULT_BACKUP, app_release_dirs, migrated_body, release_title, version_key

MONOREPO = "apollo-theme/apollo-theme"


@dataclass(frozen=True)
class Plan:
    tag: str
    title: str
    body: str
    assets: list = field(default_factory=list)


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


def plan_releases(backup: Path = DEFAULT_BACKUP) -> list[Plan]:
    plans = []
    for slug, directory in app_release_dirs(backup):
        for path in sorted(directory.glob("*.json"), key=lambda p: version_key(p.stem)):
            release = json.loads(path.read_text(encoding="utf-8"))
            tag = release["tagName"]
            if tag != path.stem:
                raise ValueError(f"{path} records tag {tag}")
            plans.append(
                Plan(
                    tag=f"{slug}-{tag}",
                    title=release_title(slug, tag, release.get("name") or ""),
                    body=migrated_body(release.get("body") or "", directory.name),
                    assets=_verified_assets(release, directory / tag),
                )
            )
    return plans


def apply(plans: list[Plan], run=subprocess.run) -> list[str]:
    """Create each missing release; return the tags created. Any ``gh release create`` failure raises."""
    created = []
    for plan in plans:
        view = run(["gh", "release", "view", plan.tag, "--repo", MONOREPO], capture_output=True, text=True)
        if view.returncode == 0:
            continue
        with tempfile.TemporaryDirectory() as directory:
            notes = Path(directory) / "notes.md"
            notes.write_text(plan.body, encoding="utf-8")
            command = [
                "gh", "release", "create", plan.tag, "--repo", MONOREPO, "--verify-tag",
                "--title", plan.title, "--notes-file", str(notes), "--latest=false",
                *(str(path) for path in plan.assets),
            ]
            result = run(command, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
        created.append(plan.tag)
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restore backed-up app releases onto apollo-theme/apollo-theme")
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP, help="org backup directory with releases/")
    parser.add_argument("--apply", action="store_true", help="create the missing releases on GitHub")
    args = parser.parse_args(argv)
    try:
        plans = plan_releases(args.backup)
    except (OSError, ValueError, KeyError) as error:
        print(f"cannot plan releases: {error}", file=sys.stderr)
        return 1
    if not args.apply:
        for plan in plans:
            print("\t".join((plan.tag, plan.title, ", ".join(path.name for path in plan.assets) or "-")))
        print(f"{len(plans)} plans")
        return 0
    try:
        created = apply(plans)
    except subprocess.CalledProcessError as error:
        print(f"release create failed: {error.cmd[3]}: {(error.stderr or '').strip()}", file=sys.stderr)
        return 1
    for tag in created:
        print(f"created {tag}")
    print(f"{len(created)} created, {len(plans) - len(created)} already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
