"""Facts about the 2026-11-09 consolidation of the per-app repositories into this monorepo."""
from __future__ import annotations

import json
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
    "firefox": ("package.json", "tests/test_theme.py"),
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
INVENTORY = ROOT / "scripts" / "release_inventory.json"


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


class Problem(str):
    """An inventory problem message; ``missing`` marks absent backup files (planning raises FileNotFoundError)."""

    missing: bool = False

    @classmethod
    def absent(cls, message: str) -> "Problem":
        problem = cls(message)
        problem.missing = True
        return problem


def load_inventory(path: Path = INVENTORY) -> dict[str, dict[str, list[str]]]:
    """``{repo: {tag: [asset names]}}`` recorded from the live source repositories before migration."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    releases = data.get("releases") if isinstance(data, dict) else None
    if not isinstance(releases, dict) or not releases:
        raise ValueError(f"{path}: releases must be a non-empty object")
    for repo, tags in releases.items():
        if not isinstance(tags, dict):
            raise ValueError(f"{path}: {repo} must map tags to asset lists")
        for tag, assets in tags.items():
            if not isinstance(assets, list) or not all(isinstance(name, str) for name in assets):
                raise ValueError(f"{path}: {repo} {tag} assets must be a list of names")
    return releases


def inventory_problems(backup: Path, inventory: dict, repos=None, scan_unknown: bool = True) -> list[Problem]:
    """Every inventory release must be in the backup (JSON, assets, files) and nothing else may be."""
    releases = Path(backup) / "releases"
    problems: list[Problem] = []
    for repo in sorted(inventory if repos is None else repos):
        if repo not in inventory:
            problems.append(Problem(f"{repo}: not in release inventory"))
            continue
        directory = releases / repo
        if not directory.is_dir():
            problems.append(Problem.absent(f"{repo}: missing release backup {directory}"))
            continue
        for tag, names in sorted(inventory[repo].items(), key=lambda item: version_key(item[0])):
            path = directory / f"{tag}.json"
            if not path.is_file():
                problems.append(Problem.absent(f"{repo}: backup {tag}.json missing"))
                continue
            try:
                release = json.loads(path.read_text(encoding="utf-8"))
                recorded_tag = release["tagName"]
                recorded = sorted(asset["name"] for asset in release.get("assets", []))
            except (OSError, ValueError, KeyError, TypeError) as error:
                problems.append(Problem(f"{repo}: backup {tag}.json unreadable: {error}"))
                continue
            if recorded_tag != tag:
                problems.append(Problem(f"{repo}: backup {tag}.json records tag {recorded_tag}"))
            if recorded != sorted(names):
                problems.append(Problem(f"{repo}: backup {tag} assets differ from inventory"))
            for name in sorted(names):
                if not (directory / tag / name).is_file():
                    problems.append(Problem.absent(f"{repo}: backup asset {tag}/{name} missing"))
        for path in sorted(directory.glob("*.json")):
            if path.stem not in inventory[repo]:
                problems.append(Problem(f"{repo}: backup {path.name} not in inventory"))
    if scan_unknown and releases.is_dir():
        for directory in sorted(releases.iterdir()):
            if directory.is_dir() and APP_REPO.match(directory.name) and directory.name not in inventory:
                problems.append(Problem(f"{directory.name}: release backup not in inventory"))
    return problems


def normalize_body(body: str | None) -> str:
    return (body or "").replace("\r\n", "\n").rstrip()


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
