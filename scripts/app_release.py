#!/usr/bin/env python3
"""Validate and build the release assets for one app tag (every app except Firefox)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from common import APPS, ROOT

TAG_PATTERN = re.compile(r"([a-z0-9-]+)-v(\d+\.\d+\.\d+)")
REPOSITORY = "apollo-theme/apollo-theme"
# Files left out of every app zip: generation, tests, and repository plumbing.
DEV_PARTS = {"scripts", "tests", "palette", ".github", "CLAUDE.md", ".gitignore", ".gitattributes", ".vscodeignore", "package-lock.json"}
ZIP_TIME = (1980, 1, 1, 0, 0, 0)

# Source file (relative to the app folder) -> release asset name. GitHub rewrites
# spaces in asset names, so every name here is space-free. A file is attached raw
# only when it imports as-is: iTerm2, Xcode, and bat take the theme name from the
# file name and eza needs the name theme.yml, so their Light files ship only in the zip.
RAW_ASSETS: dict[str, dict[str, str]] = {
    "sonicterm": {"apollo.toml": "apollo.toml", "apollo-light.toml": "apollo-light.toml"},
    "windows-terminal": {"apollo.json": "apollo.json", "apollo-light.json": "apollo-light.json"},
    "vscode": {},
    "visual-studio": {"themes/Apollo.vstheme": "Apollo.vstheme", "themes/Apollo Light.vstheme": "Apollo-Light.vstheme"},
    "vim": {"colors/apollo.vim": "apollo.vim", "colors/apollo-light.vim": "apollo-light.vim"},
    "nvim": {},
    "xcode": {"Apollo.xccolortheme": "Apollo.xccolortheme"},
    "tmux": {"apollo.tmux": "apollo.tmux", "apollo-light.tmux": "apollo-light.tmux"},
    "rmux": {"apollo-rmux.conf": "apollo-rmux.conf", "apollo-rmux-light.conf": "apollo-rmux-light.conf"},
    "powershell": {"ApolloTheme.psm1": "ApolloTheme.psm1", "ApolloTheme.psd1": "ApolloTheme.psd1", "ApolloTheme.profile.ps1": "ApolloTheme.profile.ps1"},
    "bat": {"Apollo.tmTheme": "Apollo.tmTheme"},
    "eza": {"theme.yml": "theme.yml"},
    "wezterm": {"apollo.toml": "apollo.toml", "apollo-light.toml": "apollo-light.toml", "wezterm.lua": "wezterm.lua"},
    "iterm2": {"Apollo.itermcolors": "Apollo.itermcolors"},
    "apple-terminal": {"Apollo.terminal": "Apollo.terminal", "Apollo Light.terminal": "Apollo-Light.terminal"},
    "alacritty": {"apollo.toml": "apollo.toml", "apollo-light.toml": "apollo-light.toml"},
}


def parse_tag(tag: str) -> tuple[str, str]:
    match = TAG_PATTERN.fullmatch(tag)
    if match and match.group(1) == "firefox":
        raise ValueError("firefox tags are released by scripts/firefox_release.py")
    if not match or match.group(1) not in RAW_ASSETS:
        raise ValueError("tag must look like <app>-vX.Y.Z for one of: " + ", ".join(RAW_ASSETS))
    return match.group(1), match.group(2)


def declared_versions(slug: str) -> dict[str, str]:
    folder = ROOT / slug
    if slug == "vscode":
        return {"package.json": json.loads((folder / "package.json").read_text(encoding="utf-8"))["version"]}
    if slug == "powershell":
        match = re.search(r"ModuleVersion\s*=\s*'([^']+)'", (folder / "ApolloTheme.psd1").read_text(encoding="utf-8"))
        return {"ApolloTheme.psd1": match.group(1) if match else ""}
    return {}


def check_version(slug: str, version: str) -> None:
    for source, found in declared_versions(slug).items():
        if found != version:
            raise ValueError(f"tag version {version} must match {slug}/{source} ({found})")


def shippable_files(slug: str) -> list[str]:
    listed = subprocess.run(["git", "ls-files", "-z", "--", slug], cwd=ROOT, check=True, capture_output=True).stdout
    relative = (Path(name).relative_to(slug) for name in listed.decode("utf-8").split("\0") if name)
    return sorted(path.as_posix() for path in relative if not DEV_PARTS & set(path.parts))


def build_zip(slug: str, version: str, out: Path) -> Path:
    prefix = f"apollo-{slug}-{version}"
    path = Path(out) / f"{prefix}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in shippable_files(slug):
            info = zipfile.ZipInfo(f"{prefix}/{name}", date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (ROOT / slug / name).read_bytes())
    return path


def build_vsix(version: str, out: Path, package_dir: Path, run=subprocess.run) -> Path:
    run(["npm", "run", "package"], cwd=package_dir, check=True)
    built = package_dir / "dist" / "apollo-theme.vsix"
    if not built.is_file():
        raise ValueError(f"missing release attachment: {built}")
    return Path(shutil.copyfile(built, Path(out) / f"apollo-theme-{version}.vsix"))


def write_checksums(paths: list[Path], out: Path) -> Path:
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in sorted(paths, key=lambda p: p.name)]
    target = Path(out) / "SHA256SUMS"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def expected_assets(slug: str, version: str, vsix: bool = True) -> list[str]:
    names = [*RAW_ASSETS[slug].values(), f"apollo-{slug}-{version}.zip"]
    if slug == "vscode" and vsix:
        names.append(f"apollo-theme-{version}.vsix")
    return names + ["SHA256SUMS"]


def check_assets(out: Path, expected: list[str]) -> None:
    found = sorted(path.name for path in Path(out).iterdir())
    if found != sorted(expected):
        raise ValueError(f"release assets in {out} must be exactly {sorted(expected)}, found {found}")


def build_assets(slug: str, version: str, out: Path, run=subprocess.run, vsix_dir: Path | None = ROOT / "vscode") -> list[Path]:
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory {out} must be empty")
    out.mkdir(parents=True, exist_ok=True)
    paths = [Path(shutil.copyfile(ROOT / slug / source, out / name)) for source, name in RAW_ASSETS[slug].items()]
    paths.append(build_zip(slug, version, out))
    if slug == "vscode" and vsix_dir is not None:
        paths.append(build_vsix(version, out, Path(vsix_dir), run))
    paths.append(write_checksums(paths, out))
    check_assets(out, expected_assets(slug, version, vsix=vsix_dir is not None))
    return paths


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")


def previous_tag(tag: str, slug: str, root: Path = ROOT) -> str:
    listed = _git(root, "tag", "--list", f"{slug}-v*", "--merged", f"{tag}^", "--sort=-version:refname")
    if listed.returncode != 0:
        return ""
    return next((name for name in listed.stdout.split() if name != tag), "")


def release_notes(tag: str, root: Path = ROOT) -> str:
    slug, _ = parse_tag(tag)
    prev = previous_tag(tag, slug, root)
    log_range = f"{prev}..{tag}" if prev else tag
    # Imported tags predate the monorepo and keep files at the root; only filter
    # by the app folder when the tagged tree actually contains it.
    in_monorepo = _git(Path(root), "cat-file", "-e", f"{tag}:{slug}").returncode == 0
    paths = ["--", f"{slug}/"] if in_monorepo else []
    log = _git(Path(root), "log", "--no-merges", "--pretty=format:- %s (%h) — %an", log_range, *paths)
    if log.returncode != 0:
        raise ValueError(f"git log failed for {log_range}: {log.stderr.strip()}")
    lines = [f"## Apollo Themes for {APPS[slug]['name']} {tag}", ""]
    lines.append(f"### Commits since {prev}" if prev else "### Commits")
    lines += ["", log.stdout.strip() or "- No changes in this folder."]
    if prev:
        lines += ["", f"**Full Changelog**: https://github.com/{REPOSITORY}/compare/{prev}...{tag}"]
    return "\n".join(lines) + "\n"


def check_all() -> None:
    # Unversioned apps have no declared version; 0.0.0 only names the test build.
    with tempfile.TemporaryDirectory() as tmp:
        for slug in RAW_ASSETS:
            version = next(iter(declared_versions(slug).values()), "0.0.0")
            paths = build_assets(slug, version, Path(tmp) / slug, vsix_dir=None)
            print(f"{slug}: " + ", ".join(path.name for path in paths))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", metavar="TAG", help="release tag, e.g. iterm2-v0.2.0")
    mode.add_argument("--check-all", action="store_true", help="build every app's assets (no VSIX) into a temporary directory")
    parser.add_argument("--out", type=Path, default=ROOT / "release-assets", help="directory for the release assets")
    parser.add_argument("--notes-out", type=Path, help="write release notes to this path")
    args = parser.parse_args(argv)
    try:
        if args.check_all:
            check_all()
            return 0
        slug, version = parse_tag(args.dry_run)
        check_version(slug, version)
        paths = build_assets(slug, version, args.out)
        if args.notes_out:
            args.notes_out.write_text(release_notes(args.dry_run), encoding="utf-8")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"tag {args.dry_run}: {APPS[slug]['name']} {version}")
    print("attachments:")
    for path in paths:
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
