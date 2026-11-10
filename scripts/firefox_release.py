#!/usr/bin/env python3
"""Validate, build, and describe a Firefox release without publishing it."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIREFOX = ROOT / "firefox"
TAG_PATTERN = re.compile(r"firefox-v(\d+\.\d+\.\d+)")
REPOSITORY = "apollo-theme/apollo-theme"
GECKO_IDS = {
    Path("manifest.json"): "humble-apollo@d0n9x1n",
    Path("variants/light/manifest.json"): "apollo-light@d0n9x1n",
}
ARTIFACTS = ("apollo-theme.zip", "apollo-light-theme.zip")


def version_from_tag(tag: str) -> str:
    match = TAG_PATTERN.fullmatch(tag)
    if not match:
        raise ValueError("tag must look like firefox-vX.Y.Z")
    return match.group(1)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_versions(directory: Path, version: str) -> None:
    directory = Path(directory)
    found = {
        "dark manifest": _load(directory / "manifest.json")["version"],
        "light manifest": _load(directory / "variants" / "light" / "manifest.json")["version"],
        "package": _load(directory / "package.json")["version"],
    }
    if any(value != version for value in found.values()):
        details = ", ".join(f"{name} ({value})" for name, value in found.items())
        raise ValueError(f"tag version {version} must match {details}")


def check_gecko_ids(directory: Path) -> None:
    directory = Path(directory)
    for relative, expected in GECKO_IDS.items():
        actual = _load(directory / relative)["browser_specific_settings"]["gecko"]["id"]
        if actual != expected:
            raise ValueError(f"gecko id changed: {relative} has {actual}, expected {expected}")


def build(directory: Path, run=subprocess.run) -> list[Path]:
    directory = Path(directory)
    run(["npm", "run", "build"], cwd=directory, check=True)
    return [directory / "web-ext-artifacts" / name for name in ARTIFACTS]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")


def previous_tag(tag: str, root: Path = ROOT) -> str:
    # Read ref names directly: imported annotated tags keep their old internal
    # name (v1.1.1), so `git describe` reports synthetic names for them.
    listed = _git(root, "tag", "--list", "firefox-v*", "--merged", f"{tag}^", "--sort=-version:refname")
    if listed.returncode != 0:
        return ""
    return next((name for name in listed.stdout.split() if name != tag), "")


def release_notes(tag: str, root: Path = ROOT) -> str:
    root = Path(root)
    prev = previous_tag(tag, root)
    log_range = f"{prev}..{tag}" if prev else tag
    # Imported firefox-v* tags predate the monorepo and keep files at the root;
    # only filter by firefox/ when the tagged tree actually contains it.
    in_monorepo = _git(root, "cat-file", "-e", f"{tag}:firefox").returncode == 0
    paths = ["--", "firefox/"] if in_monorepo else []
    log = _git(root, "log", "--no-merges", "--pretty=format:- %s (%h) — %an", log_range, *paths)
    if log.returncode != 0:
        raise ValueError(f"git log failed for {log_range}: {log.stderr.strip()}")
    lines = [f"## Apollo Themes for Firefox {tag}", ""]
    lines.append(f"### Commits since {prev}" if prev else "### Commits")
    lines += ["", log.stdout.strip()]
    if prev:
        lines += ["", f"**Full Changelog**: https://github.com/{REPOSITORY}/compare/{prev}...{tag}"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", required=True, metavar="TAG", help="release tag, e.g. firefox-v1.1.1")
    parser.add_argument("--skip-build", action="store_true", help="validate without running npm run build")
    parser.add_argument("--notes-out", type=Path, help="write release notes to this path")
    args = parser.parse_args(argv)
    tag = args.dry_run
    try:
        version = version_from_tag(tag)
        check_versions(FIREFOX, version)
        check_gecko_ids(FIREFOX)
        paths = [FIREFOX / "web-ext-artifacts" / name for name in ARTIFACTS]
        if not args.skip_build:
            paths = build(FIREFOX)
            missing = [str(path) for path in paths if not path.is_file()]
            if missing:
                raise ValueError("missing release attachments: " + ", ".join(missing))
        if args.notes_out:
            args.notes_out.write_text(release_notes(tag), encoding="utf-8")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"tag {tag}: version {version}, gecko ids ok")
    print("attachments:")
    for path in paths:
        print(f"  {path.relative_to(FIREFOX) if path.is_relative_to(FIREFOX) else path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
