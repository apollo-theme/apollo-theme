#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from common import (
    APP_METADATA,
    FORBIDDEN_LINEAGE_PHRASES,
    HEX_COLOR,
    MANAGEMENT_REPOSITORIES,
    REPOSITORIES,
    ROOT,
    contrast_ratio,
    iter_hex_colors,
    load_palette,
    markdown_anchor,
)

EXPECTED_ANSI = [
    "#1d2021",
    "#fb4934",
    "#b8bb26",
    "#fabd2f",
    "#83a598",
    "#d3869b",
    "#8ec07c",
    "#d5c4a1",
]
EXPECTED_BRIGHT = [
    "#665c54",
    "#fb4934",
    "#b8bb26",
    "#fabd2f",
    "#83a598",
    "#d3869b",
    "#8ec07c",
    "#fbf1c7",
]


def check_palette() -> None:
    palette = load_palette()
    if palette["terminal"]["ansi"] != EXPECTED_ANSI:
        raise ValueError("canonical ANSI slots changed unexpectedly")
    if palette["terminal"]["bright"] != EXPECTED_BRIGHT:
        raise ValueError("canonical bright slots changed unexpectedly")
    invalid = sorted({color for color in iter_hex_colors(palette) if not HEX_COLOR.fullmatch(color)})
    if invalid:
        raise ValueError(f"invalid lowercase six-digit colors: {', '.join(invalid)}")
    colors = palette["colors"]
    minimum = palette["constraints"]["minimumTextContrast"]
    for role in ("foreground", "foregroundSecondary", "foregroundInactive", "accent"):
        ratio = contrast_ratio(colors[role], colors["background"])
        if ratio < minimum:
            raise ValueError(f"{role} contrast is {ratio:.2f}, below {minimum:.2f}")
    if contrast_ratio(colors["ansiBrightBlack"], colors["background"]) >= minimum:
        raise ValueError("restricted bright black no longer needs its usage constraint")


def check_submodules() -> None:
    gitmodules = ROOT / ".gitmodules"
    if not gitmodules.exists():
        raise FileNotFoundError(".gitmodules is missing")
    output = subprocess.run(
        ["git", "config", "--file", str(gitmodules), "--get-regexp", r"^submodule\..*\.(path|url)$"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    entries: dict[str, dict[str, str]] = {}
    for line in output.splitlines():
        key, value = line.split(maxsplit=1)
        prefix, field = key.rsplit(".", 1)
        entries.setdefault(prefix, {})[field] = value
    expected_paths = set(REPOSITORIES) | set(MANAGEMENT_REPOSITORIES)
    paths = {entry.get("path") for entry in entries.values()}
    if paths != expected_paths:
        missing = sorted(expected_paths - paths)
        extra = sorted(paths - expected_paths)
        raise ValueError(f"submodule paths differ: missing={missing}, extra={extra}")
    for entry in entries.values():
        path = entry["path"]
        expected_url = MANAGEMENT_REPOSITORIES.get(path, f"https://github.com/apollo-theme/{path}.git")
        if entry.get("url") != expected_url:
            raise ValueError(f"{path}: expected submodule URL {expected_url}")
    states = subprocess.run(
        ["git", "submodule", "status", "--recursive"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    if len(states) != len(expected_paths) or any(line.startswith(("-", "+", "U")) for line in states):
        raise ValueError("submodules are missing, conflicted, or not at recorded commits")

    profile_files = sorted(
        path.relative_to(ROOT / ".github" / "organization").as_posix()
        for path in (ROOT / ".github" / "organization").rglob("*")
        if path.is_file() and ".git" not in path.parts
    )
    if profile_files != ["profile/README.md"]:
        raise ValueError(f"organization profile repository must contain only profile/README.md, got {profile_files}")


def public_identity_metadata(directory: Path) -> str:
    values: list[str] = []
    for relative, fields in (
        ("package.json", ("name", "displayName", "description", "keywords")),
        ("manifest.json", ("name", "description")),
    ):
        path = directory / relative
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for field in fields:
            value = data.get(field)
            if isinstance(value, list):
                values.extend(str(item) for item in value)
            elif value is not None:
                values.append(str(value))
    module_manifest = directory / "ApolloTheme.psd1"
    if module_manifest.exists():
        for line in module_manifest.read_text(encoding="utf-8").splitlines():
            if re.match(r"\s*(Author|CompanyName|Copyright|Description|Tags)\s*=", line, re.IGNORECASE):
                values.append(line)
    return "\n".join(values)


def visible_prose(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"<[^>]+>", "", text)


def forbidden_identity_terms(repository: str, text: str) -> list[str]:
    lowered = text.lower()
    forbidden = [phrase for phrase in FORBIDDEN_LINEAGE_PHRASES if phrase in lowered]
    prose = visible_prose(lowered)
    references = [line for line in prose.splitlines() if re.search(r"\bsonicterm\b", line)]
    allowed_patterns = (
        r"^\s*#*\s*sonicterm apollo theme\s*$",
        r"\b(?:colors?|configuration|theme)\s+(?:for|to)\s+sonicterm\b",
        r"\bstart\s+sonicterm\b",
        r"\b(?:every|strict)\s+sonicterm\s+(?:artifact|slots?)\b",
        r"\bbecause\s+sonicterm\s+requires\b",
        r"^\s*sonicterm\s+has no standalone theme-validation cli\b",
    )
    if references and (
        repository != "sonicterm-apollo-theme"
        or any(not any(re.search(pattern, line) for pattern in allowed_patterns) for line in references)
    ):
        forbidden.append("sonicterm")
    return list(dict.fromkeys(forbidden))


def check_readme_contract(repository: str) -> None:
    metadata = APP_METADATA[repository]
    directory = ROOT / repository
    readme = (directory / "README.md").read_text(encoding="utf-8")
    public_metadata = [
        readme,
        (directory / "CLAUDE.md").read_text(encoding="utf-8"),
        public_identity_metadata(directory),
    ]
    combined = "\n".join(public_metadata).lower()
    expected_title = f"<h1 align=\"center\">{metadata['name']} Apollo Theme</h1>"
    required_fragments = {
        "app-first title": expected_title,
        "workflow badge": f"img.shields.io/github/actions/workflow/status/apollo-theme/{repository}/{metadata['workflow']}",
        "release badge": f"img.shields.io/github/v/release/apollo-theme/{repository}",
        "preview badge": 'alt="Preview"',
        "canonical palette badge": "img.shields.io/badge/palette-canonical-",
        "preview image": f"raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{metadata['slug']}.svg",
        "website deep link": f"https://apollo-theme.github.io/#app-{metadata['slug']}",
        "simulation caption": "simulated preview",
    }
    missing = [label for label, fragment in required_fragments.items() if fragment.lower() not in readme.lower()]
    headings = (line.removeprefix("## ") for line in readme.splitlines() if line.startswith("## "))
    anchors = {markdown_anchor(heading) for heading in headings}
    if metadata["install_anchor"] not in anchors:
        missing.append("install section")
    lowered = readme.lower()
    license_links = ('href="license"', f'href="https://github.com/apollo-theme/{repository}/blob/main/license"')
    if not any(link in lowered for link in license_links):
        missing.append("license link")
    if "img.shields.io/badge/license-mit" not in lowered and "img.shields.io/github/license/" not in lowered:
        missing.append("license badge")
    if f"img.shields.io/badge/{metadata['badge_fragment']}".lower() not in lowered:
        missing.append("app or platform badge")
    if missing:
        raise ValueError(f"{repository}: README branding contract missing {missing}")
    forbidden = forbidden_identity_terms(repository, combined)
    if forbidden:
        raise ValueError(f"{repository}: forbidden lineage phrases {forbidden}")


def check_repository(repository: str, native: bool) -> None:
    directory = ROOT / repository
    required = (".gitattributes", "README.md", "CLAUDE.md", "LICENSE", "palette/apollo.json", "scripts/generate.py", "scripts/check.py")
    missing = [path for path in required if not (directory / path).exists()]
    if missing:
        raise FileNotFoundError(f"{repository}: missing {', '.join(missing)}")
    attributes = (directory / ".gitattributes").read_text(encoding="utf-8").splitlines()
    if "* text=auto eol=lf" not in attributes:
        raise ValueError(f"{repository}: .gitattributes must preserve LF across Windows checkouts")
    snapshot = json.loads((directory / "palette" / "apollo.json").read_text(encoding="utf-8"))
    if snapshot != load_palette():
        raise ValueError(f"{repository}: palette snapshot differs from canonical palette")
    check_readme_contract(repository)
    subprocess.run([sys.executable, "scripts/generate.py", "--check"], cwd=directory, check=True)
    if native:
        subprocess.run([sys.executable, "scripts/check.py"], cwd=directory, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Apollo palette and application repositories")
    parser.add_argument("--repo", choices=REPOSITORIES, action="append", help="limit validation to a repository")
    parser.add_argument("--native", action="store_true", help="also run each selected child's app-specific checker")
    args = parser.parse_args()
    check_submodules()
    check_palette()
    for repository in tuple(args.repo or REPOSITORIES):
        check_repository(repository, args.native)
        print(f"{repository}: valid{' with native checks' if args.native else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
