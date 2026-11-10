"""Facts about the 2026-11-09 consolidation of the per-app repositories into this monorepo."""
from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from common import ROOT, SLUGS

MIGRATION_LINE = "_Migrated from `apollo-theme/{repo}` on 2026-11-09; the original repository was consolidated into `apollo-theme/apollo-theme`._"

# Paths under <slug>/ that may differ from the imported source tree. An app's
# allowlist may grow only in the commit that edits that file.
COMMON_ALLOW = ("README.md", "CLAUDE.md", ".github/*", ".gitattributes")
ALLOWLIST = {
    "firefox": ("package.json",),
    "vscode": ("package.json", "scripts/check.py"),
    "powershell": ("ApolloTheme.psd1", "scripts/generate.py"),
    "wezterm": ("apollo.toml", "apollo-light.toml", "scripts/generate.py", "scripts/check.py"),
    "tmux": ("scripts/check.py", "tests/test_theme.py"),
    "rmux": ("scripts/check.py", "tests/test_theme.py"),
    "eza": ("scripts/check.py", "tests/test_theme.py"),
    "bat": ("tests/test_theme.py",),
}
# Retired repositories have no org bundle; their source is a local clone at this commit.
RETIRED = {"wezterm": "0a23a76", "iterm2": "4b8666d", "apple-terminal": "67551c9", "alacritty": "563ac97"}




def _default_build_dir(name: str) -> Path:
    for candidate in (ROOT / ".build" / name, ROOT.parent / name):
        if candidate.exists():
            return candidate
    return ROOT / ".build" / name


DEFAULT_BACKUP = _default_build_dir("org-backup-2026-11-09")
DEFAULT_RETIRED = _default_build_dir("apollo-light-crlf-audit")
APP_REPO = re.compile(r"^(?P<slug>.+)-apollo-theme$")


class MigrationError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    slug: str
    rev: str
    tags: dict
    allow: tuple


def migrated_body(original: str, repo: str) -> str:
    return original.rstrip("\n") + "\n\n" + MIGRATION_LINE.format(repo=repo) + "\n"


def repo_name(slug: str) -> str:
    return f"{slug}-apollo-theme"


def release_title(slug: str, tag: str, name: str) -> str:
    """Restored release title: ``<slug> <tag>`` when the original name was just the tag, else the original name."""
    return f"{slug} {tag}" if (name or tag) == tag else name


def version_key(tag: str) -> tuple:
    return tuple(int(part) for part in re.findall(r"\d+", tag)), tag


def app_release_dirs(backup: Path) -> list[tuple[str, Path]]:
    """``(slug, releases/<slug>-apollo-theme)`` for every backed-up app; unknown ``*-apollo-theme`` dirs fail."""
    releases = Path(backup) / "releases"
    if not releases.is_dir():
        raise FileNotFoundError(f"missing release backup {releases}")
    found = []
    for directory in sorted(releases.iterdir()):
        match = APP_REPO.match(directory.name)
        if not directory.is_dir() or not match:
            continue
        if match["slug"] not in SLUGS:
            raise ValueError(f"unknown app release backup {directory}")
        found.append((match["slug"], directory))
    return found


def allow_for(slug: str) -> tuple:
    return COMMON_ALLOW + ALLOWLIST.get(slug, ())


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MigrationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def bundle_source(slug: str, bundle: Path) -> Source:
    """Source facts from an org-backup bundle: main and every tag peeled to its commit."""
    bundle = Path(bundle)
    if not bundle.is_file():
        raise MigrationError(f"missing bundle {bundle}")
    with tempfile.TemporaryDirectory() as directory:
        mirror = Path(directory) / "mirror.git"
        _git("clone", "-q", "--mirror", str(bundle), str(mirror))
        rev = _git("rev-parse", "--verify", "refs/heads/main^{commit}", cwd=mirror)
        names = _git("for-each-ref", "--format=%(refname:strip=2)", "refs/tags", cwd=mirror).splitlines()
        tags = {name: _git("rev-parse", "--verify", f"refs/tags/{name}^{{commit}}", cwd=mirror) for name in names}
    return Source(slug=slug, rev=rev, tags=tags, allow=allow_for(slug))


def retired_source(slug: str, clone: Path, rev: str) -> Source:
    """Source facts from a retired local clone: the full commit for ``rev`` and ``show-ref -d`` tags."""
    clone = Path(clone)
    if not clone.is_dir():
        raise MigrationError(f"missing retired clone {clone}")
    full = _git("-C", str(clone), "rev-parse", "--verify", f"{rev}^{{commit}}")
    tags: dict[str, str] = {}
    peeled: dict[str, str] = {}
    for line in _git("-C", str(clone), "show-ref", "-d", "--tags").splitlines():
        sha, ref = line.split(" ", 1)
        name = ref.removeprefix("refs/tags/")
        if name.endswith("^{}"):
            peeled[name[:-3]] = sha
        else:
            tags[name] = sha
    tags.update(peeled)
    return Source(slug=slug, rev=full, tags=tags, allow=allow_for(slug))


def source_for(slug: str, backup: Path, retired: Path) -> Source:
    if slug in RETIRED:
        return retired_source(slug, Path(retired) / repo_name(slug), RETIRED[slug])
    return bundle_source(slug, Path(backup) / f"{repo_name(slug)}.bundle")


def sources(backup: Path, retired: Path) -> list[Source]:
    return [source_for(slug, backup, retired) for slug in SLUGS]
