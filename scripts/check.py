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
    LIGHT_ARTIFACTS,
    MANAGEMENT_REPOSITORIES,
    REPOSITORIES,
    ROOT,
    contrast_ratio,
    iter_hex_colors,
    load_palette,
    load_palettes,
    markdown_anchor,
)

EXPECTED_LIGHT_COLORS = {
    "background": "#f9f5d7",
    "surface": "#fbf1c7",
    "surfaceHover": "#f2e5bc",
    "selection": "#ebdbb2",
    "foreground": "#3c3836",
    "foregroundSecondary": "#504945",
    "foregroundInactive": "#665c54",
    "foregroundBright": "#282828",
    "accent": "#8a5200",
    "danger": "#9d0006",
    "success": "#6b6700",
    "info": "#076678",
    "magenta": "#8f3f71",
    "cyan": "#356b4d",
    "ansiBrightBlack": "#665c54",
}

EXPECTED_LIGHT_ROLES = {
    "canvas": "{colors.background}",
    "textPrimary": "{colors.foreground}",
    "textSecondary": "{colors.foregroundSecondary}",
    "textInactive": "{colors.foregroundInactive}",
    "focus": "{colors.accent}",
    "cursor": "{colors.accent}",
    "cursorText": "{colors.background}",
    "selection": "{colors.selection}",
    "selectionText": "{colors.foreground}",
    "error": "{colors.danger}",
    "warning": "{colors.accent}",
    "success": "{colors.success}",
    "information": "{colors.info}",
    "textOnFocus": "{colors.background}",
    "textOnError": "{colors.background}",
    "textOnSuccess": "{colors.background}",
    "textOnInformation": "{colors.background}",
}

EXPECTED_TERMINAL = {
    "dark": {
        "ansi": ["#1d2021", "#fb4934", "#b8bb26", "#fabd2f", "#83a598", "#d3869b", "#8ec07c", "#d5c4a1"],
        "bright": ["#665c54", "#fb4934", "#b8bb26", "#fabd2f", "#83a598", "#d3869b", "#8ec07c", "#fbf1c7"],
    },
    "light": {
        "ansi": ["#3c3836", "#9d0006", "#6b6700", "#8a5200", "#076678", "#8f3f71", "#356b4d", "#504945"],
        "bright": ["#665c54", "#9d0006", "#6b6700", "#8a5200", "#076678", "#8f3f71", "#356b4d", "#282828"],
    },
}


def check_palette() -> None:
    palettes = load_palettes()
    expected_identity = {
        "dark": ("apollo", "Apollo"),
        "light": ("apollo-light", "Apollo Light"),
    }
    if {palette["id"] for palette in palettes.values()} != {"apollo", "apollo-light"}:
        raise ValueError("Apollo palette IDs must be unique and canonical")
    for variant, palette in palettes.items():
        terminal = palette["terminal"]
        colors = palette["colors"]
        expected_id, expected_name = expected_identity[variant]
        if palette.get("schemaVersion") != 1 or palette.get("colorSpace") != "srgb":
            raise ValueError(f"{variant}: unsupported palette schema")
        if (palette["id"], palette["name"], palette["appearance"]) != (expected_id, expected_name, variant):
            raise ValueError(f"{variant}: palette identity mismatch")
        if variant == "light" and colors != EXPECTED_LIGHT_COLORS:
            raise ValueError("light: canonical colors changed unexpectedly")
        if variant == "light" and palette["roles"] != EXPECTED_LIGHT_ROLES:
            raise ValueError("light: canonical semantic roles changed unexpectedly")
        if terminal["ansi"] != EXPECTED_TERMINAL[variant]["ansi"]:
            raise ValueError(f"{variant}: canonical ANSI slots changed unexpectedly")
        if terminal["bright"] != EXPECTED_TERMINAL[variant]["bright"]:
            raise ValueError(f"{variant}: canonical bright slots changed unexpectedly")
        if terminal["foreground"] != colors["foreground"] or terminal["background"] != colors["background"]:
            raise ValueError(f"{variant}: terminal foreground/background role mismatch")
        cursor_text_key = palette["roles"]["cursorText"][8:-1]
        if terminal["cursor"] != colors["accent"] or terminal["cursorText"] != colors[cursor_text_key]:
            raise ValueError(f"{variant}: terminal cursor roles mismatch")
        selection = terminal["selection"]
        expected_alpha = 0.5 if variant == "dark" else 1.0
        if selection != {"color": colors["selection"], "alpha": expected_alpha, "foregroundMode": "preserve"}:
            raise ValueError(f"{variant}: selection contract mismatch")
        invalid = sorted({color for color in iter_hex_colors(palette) if not HEX_COLOR.fullmatch(color)})
        if invalid:
            raise ValueError(f"{variant}: invalid lowercase six-digit colors: {', '.join(invalid)}")
        for role, reference in palette["roles"].items():
            match = re.fullmatch(r"\{colors\.([A-Za-z][A-Za-z0-9]*)\}", reference)
            if not match or match.group(1) not in colors:
                raise ValueError(f"{variant}: invalid role reference for {role}: {reference}")
        minimum = palette["constraints"]["minimumTextContrast"]
        semantic_text_roles = ("textPrimary", "textSecondary", "textInactive", "focus", "error", "warning", "success", "information")
        direct_text_colors = ("foregroundBright", "magenta", "cyan")
        surfaces = ("background",) if variant == "dark" else ("background", "surface", "surfaceHover")
        for role in semantic_text_roles:
            color_key = palette["roles"][role][8:-1]
            for surface in surfaces:
                ratio = contrast_ratio(colors[color_key], colors[surface])
                if ratio < minimum:
                    raise ValueError(f"{variant}: {role} on {surface} is {ratio:.2f}, below {minimum:.2f}")
        for color_key in direct_text_colors:
            for surface in surfaces:
                ratio = contrast_ratio(colors[color_key], colors[surface])
                if ratio < minimum:
                    raise ValueError(f"{variant}: {color_key} on {surface} is {ratio:.2f}, below {minimum:.2f}")
        selection_text_key = palette["roles"].get("selectionText", "{colors.foreground}")[8:-1]
        if contrast_ratio(colors[selection_text_key], colors["selection"]) < minimum:
            raise ValueError(f"{variant}: selected text contrast is below {minimum:.2f}")
        if contrast_ratio(colors[cursor_text_key], colors["accent"]) < minimum:
            raise ValueError(f"{variant}: cursor text contrast is below {minimum:.2f}")
        if variant == "light":
            for role, fill in (("textOnFocus", "accent"), ("textOnError", "danger"), ("textOnSuccess", "success"), ("textOnInformation", "info")):
                color_key = palette["roles"][role][8:-1]
                ratio = contrast_ratio(colors[color_key], colors[fill])
                if ratio < minimum:
                    raise ValueError(f"light: {role} contrast is {ratio:.2f}, below {minimum:.2f}")
            provenance = palette["provenance"]
            if provenance["sourceCommit"] != "5d15b2765f59754d7ac263c88a0f6e3e58124951" or provenance["sourceSha256"] != "55116926ba2b625837d9ae89349a5688d60d0b32acdbd8887e1c0d225f079c3d":
                raise ValueError("light: Gruvbox source provenance changed unexpectedly")
        for restricted in palette["constraints"]["restrictedColors"]:
            if restricted not in colors.values() and restricted not in terminal["ansi"] + terminal["bright"]:
                raise ValueError(f"{variant}: restricted color is not part of the palette: {restricted}")
        if variant == "dark" and contrast_ratio(colors["ansiBrightBlack"], colors["background"]) >= minimum:
            raise ValueError("dark: restricted bright black no longer needs its usage constraint")


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
        ("variants/light/manifest.json", ("name", "description")),
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
    if references:
        if repository != "sonicterm-apollo-theme":
            forbidden.append("sonicterm")
        elif any(re.search(r"\b(lineage|provenance|upstream|derived|inspired|starting point|based on)\b", line) for line in references):
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
    expected_titles = (
        f"<h1 align=\"center\">{metadata['name']} Apollo Theme</h1>",
        f"<h1 align=\"center\">{metadata['name']} Apollo Themes</h1>",
    )
    required_fragments = {
        "workflow badge": f"img.shields.io/github/actions/workflow/status/apollo-theme/{repository}/{metadata['workflow']}",
        "release badge": f"img.shields.io/github/v/release/apollo-theme/{repository}",
        "preview badge": 'alt="Preview"',
        "canonical palette badge": "img.shields.io/badge/palette-canonical-",
        "dark preview image": f"raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{metadata['slug']}.svg",
        "dark website deep link": f"https://apollo-theme.github.io/#app-{metadata['slug']}",
        "light preview image": f"raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{metadata['slug']}-light.svg",
        "light website deep link": f"https://apollo-theme.github.io/#app-{metadata['slug']}-light",
        "light variant name": "Apollo Light",
        "simulation caption": "simulated preview",
    }
    missing = [label for label, fragment in required_fragments.items() if fragment.lower() not in readme.lower()]
    if not any(title.lower() in readme.lower() for title in expected_titles):
        missing.append("app-first title")
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
    required = (".gitattributes", "README.md", "CLAUDE.md", "LICENSE", "palette/apollo.json", "palette/apollo-light.json", "scripts/generate.py", "scripts/check.py")
    missing = [path for path in required if not (directory / path).exists()]
    if not (directory / LIGHT_ARTIFACTS[repository]).exists():
        missing.append(LIGHT_ARTIFACTS[repository])
    if missing:
        raise FileNotFoundError(f"{repository}: missing {', '.join(missing)}")
    attributes = (directory / ".gitattributes").read_text(encoding="utf-8").splitlines()
    if "* text=auto eol=lf" not in attributes:
        raise ValueError(f"{repository}: .gitattributes must preserve LF across Windows checkouts")
    for variant, filename in (("dark", "apollo.json"), ("light", "apollo-light.json")):
        snapshot_path = directory / "palette" / filename
        canonical_path = ROOT / "palette" / filename
        if snapshot_path.read_bytes() != canonical_path.read_bytes():
            raise ValueError(f"{repository}: {variant} palette snapshot differs byte-for-byte from canonical palette")
    check_readme_contract(repository)
    if repository == "firefox-apollo-theme":
        dark_manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        light_manifest_path = directory / "variants" / "light" / "manifest.json"
        if not light_manifest_path.exists():
            raise FileNotFoundError("firefox-apollo-theme: missing variants/light/manifest.json")
        light_manifest = json.loads(light_manifest_path.read_text(encoding="utf-8"))
        dark_guid = dark_manifest["browser_specific_settings"]["gecko"]["id"]
        light_guid = light_manifest["browser_specific_settings"]["gecko"]["id"]
        if dark_guid != "humble-apollo@d0n9x1n":
            raise ValueError("firefox-apollo-theme: dark Gecko GUID changed")
        if light_guid != "apollo-light@d0n9x1n" or light_guid == dark_guid:
            raise ValueError("firefox-apollo-theme: light Gecko GUID is missing or collides with dark")
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
