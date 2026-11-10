#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

from common import (
    APPS,
    CLONE_APPS,
    FORBIDDEN_LINEAGE_PHRASES,
    HEX_COLOR,
    MONOREPO,
    ROOT,
    SLUGS,
    contrast_ratio,
    iter_hex_colors,
    load_palette,
    load_palettes,
    markdown_anchor,
    readme_blocks,
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


def check_layout() -> None:
    if (ROOT / ".gitmodules").exists():
        raise ValueError(".gitmodules must not exist")
    for slug in SLUGS:
        if not (ROOT / slug).is_dir() or (ROOT / slug / ".git").exists():
            raise ValueError(f"{slug}: must be a plain tracked folder")
        if (ROOT / slug / ".github").exists():
            raise ValueError(f"{slug}: nested .github is not allowed")


def check_source_pin(root: Path = ROOT) -> None:
    pin = json.loads((root / "palette" / "SOURCE.json").read_text(encoding="utf-8"))
    if pin.get("repository") != "https://github.com/apollo-theme/apollo-palette" or not re.fullmatch(r"[0-9a-f]{40}", pin.get("commit", "")):
        raise ValueError("SOURCE.json: repository or commit invalid")
    for name in ("apollo.json", "apollo-light.json"):
        if hashlib.sha256((root / "palette" / name).read_bytes()).hexdigest() != pin["sha256"].get(name):
            raise ValueError(f"SOURCE.json: {name} sha256 mismatch")


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


class _VisibleHTMLParser(HTMLParser):
    VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    RAW_CONTAINERS = {"code", "pre", "script", "style", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []

    @staticmethod
    def _hidden_by_style(style: str) -> bool:
        declarations = (declaration.partition(":") for declaration in style.split(";"))
        return any(
            name.strip().lower() in {"display", "visibility"}
            and value.strip().lower().removesuffix("!important").strip() in {"none", "hidden"}
            for name, separator, value in declarations
            if separator
        )

    def _is_hidden(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        attributes = {name.lower(): value for name, value in attrs}
        aria_hidden = attributes.get("aria-hidden")
        return (
            (self.stack[-1][1] if self.stack else False)
            or tag in self.RAW_CONTAINERS
            or "hidden" in attributes
            or ("aria-hidden" in attributes and (aria_hidden is None or aria_hidden.lower() == "true"))
            or self._hidden_by_style(attributes.get("style") or "")
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in self.VOID_ELEMENTS:
            self.stack.append((tag, self._is_hidden(tag, attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        pass

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def _without_blockquote_prefix(line: str) -> str:
    while match := re.match(r" {0,3}> ?", line):
        line = line[match.end() :]
    return line


def _list_item_body(line: str) -> tuple[int | None, str]:
    match = re.match(r"( {0,3}(?:[-+*]|\d{1,9}[.)]))([ \t]+)", line)
    if match is None:
        return None, line
    prefix = match.group(1) + match.group(2)[0]
    return len(prefix.expandtabs(4)), line[len(prefix) :]


def _without_list_marker(line: str) -> str:
    return _list_item_body(line)[1]


def _strip_indent(line: str, width: int) -> str | None:
    columns = 0
    index = 0
    while index < len(line) and columns < width and line[index] in " \t":
        columns += 1 if line[index] == " " else 4 - columns % 4
        index += 1
    return line[index:] if columns >= width else None


def _without_fenced_code(text: str) -> str:
    visible_lines: list[str] = []
    marker = ""
    opening_length = 0
    list_indent: int | None = None
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        newline = line[len(content) :]
        markdown = _without_blockquote_prefix(content)
        if marker:
            candidate = (
                _strip_indent(markdown, list_indent)
                if list_indent is not None
                else markdown
            )
            closing = (
                re.fullmatch(
                    rf" {{0,3}}({re.escape(marker)}{{{opening_length},}})[ \t]*",
                    candidate,
                )
                if candidate is not None
                else None
            )
            if closing:
                marker = ""
                opening_length = 0
                list_indent = None
            visible_lines.append(newline)
            continue
        list_indent, candidate = _list_item_body(markdown)
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})(.*)", candidate)
        if opening:
            fence, info = opening.groups()
            if fence[0] == "~" or "`" not in info:
                marker = fence[0]
                opening_length = len(fence)
                visible_lines.append(newline)
                continue
        list_indent = None
        visible_lines.append(line)
    return "".join(visible_lines)


def _without_indented_code(text: str) -> str:
    visible_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        newline = line[len(content) :]
        markdown = _without_list_marker(_without_blockquote_prefix(content))
        if re.match(r"(?: {4}| {0,3}\t)", markdown):
            visible_lines.append(newline)
        else:
            visible_lines.append(line)
    return "".join(visible_lines)


def visible_prose(text: str) -> str:
    text = _without_fenced_code(text)
    text = _without_indented_code(text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]\n]*\](?:\([^\n)]*\)|\[[^\]\n]*\])?", "", text)
    text = re.sub(r"(?m)^[ \t]{0,3}\[[^\]\n]+\]:[^\n]*$", "", text)
    text = re.sub(r"\[([^\]\n]*)\]\([^\n)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]\n]*)\]\[[^\]\n]*\]", r"\1", text)
    text = re.sub(r"(?<![`\\])(`+)(?!`).*?(?<![`\\])\1(?!`)", "", text, flags=re.DOTALL)
    parser = _VisibleHTMLParser()
    parser.feed(text)
    prose = "".join(parser.parts)
    return re.sub(r"(?<![\w-])Apollo (?:Dark|Light)\.[^\s]+", "", prose, flags=re.IGNORECASE)


def forbidden_identity_terms(slug: str, text: str) -> list[str]:
    lowered = text.lower()
    forbidden = [phrase for phrase in FORBIDDEN_LINEAGE_PHRASES if phrase in lowered]
    prose = visible_prose(lowered)
    references = [line for line in prose.splitlines() if re.search(r"\bsonicterm\b", line)]
    if references:
        if slug != "sonicterm":
            forbidden.append("sonicterm")
        elif any(re.search(r"\b(lineage|provenance|upstream|derived|inspired|starting point|based on)\b", line) for line in references):
            forbidden.append("sonicterm")
    return list(dict.fromkeys(forbidden))


SHARED_CLONE_COMMAND = '[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"'
SHARED_CLONE_REMOVAL = re.compile(r"""rm\s+-rf\s+(?:"\$\{?HOME\}?/\.config/apollo-theme/?"|\$\{?HOME\}?/\.config/apollo-theme/?|~/\.config/apollo-theme/?)(?![\w./-])""")
REMOVE_SHARED_CLONE_HEADING = "Remove the shared clone"
DEAD_REPOSITORY_URL = re.compile(r"github\.com/apollo-theme/[a-z0-9-]+-apollo-theme", re.IGNORECASE)


def readme_sections(readme: str) -> dict[str, str]:
    """Map each ``## `` heading to its body, up to the next ``## `` heading."""
    sections: dict[str, str] = {}
    heading: str | None = None
    lines: list[str] = []
    for line in readme.splitlines():
        if line.startswith("## "):
            if heading is not None:
                sections[heading] = "\n".join(lines)
            heading, lines = line.removeprefix("## ").strip(), []
        elif heading is not None:
            lines.append(line)
    if heading is not None:
        sections[heading] = "\n".join(lines)
    return sections


def check_shared_clone_contract(slug: str, readme: str) -> None:
    problems: list[str] = []
    if SHARED_CLONE_COMMAND not in readme:
        problems.append("shared clone install command")
    for marker in ("install", "uninstall"):
        if not readme_blocks(readme, marker):
            problems.append(f"smoke:{marker} block")
    sections = readme_sections(readme)
    remove_section = sections.get(REMOVE_SHARED_CLONE_HEADING)
    if remove_section is None:
        problems.append(f"{REMOVE_SHARED_CLONE_HEADING} section")
    else:
        if not SHARED_CLONE_REMOVAL.search(remove_section):
            problems.append(f"{REMOVE_SHARED_CLONE_HEADING} command")
        omitted = [APPS[other]["name"] for other in CLONE_APPS if not re.search(rf"(?<![\w-]){re.escape(APPS[other]['name'])}(?![\w-])", remove_section)]
        if omitted:
            problems.append(f"{REMOVE_SHARED_CLONE_HEADING} apps {omitted}")
    misplaced = [heading for heading, body in sections.items() if heading != REMOVE_SHARED_CLONE_HEADING and SHARED_CLONE_REMOVAL.search(body)]
    if misplaced:
        problems.append(f"shared clone removed outside {REMOVE_SHARED_CLONE_HEADING!r} (in {misplaced})")
    if problems:
        raise ValueError(f"{slug}: README shared clone contract violated {problems}")


def check_readme_contract(slug: str, readme: str | None = None, *, claude: str | None = None, metadata: str | None = None) -> None:
    app = APPS[slug]
    directory = ROOT / slug
    if readme is None:
        readme = (directory / "README.md").read_text(encoding="utf-8")
    if claude is None:
        claude = (directory / "CLAUDE.md").read_text(encoding="utf-8")
    if metadata is None:
        metadata = public_identity_metadata(directory)
    public_metadata = [readme, claude, metadata]
    combined = "\n".join(public_metadata).lower()
    expected_titles = (
        f"<h1 align=\"center\">{app['name']} Apollo Theme</h1>",
        f"<h1 align=\"center\">{app['name']} Apollo Themes</h1>",
    )
    required_fragments = {
        "workflow badge": "img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml",
        "release badge": f"img.shields.io/github/v/release/apollo-theme/apollo-theme?filter={slug}-v",
        "preview badge": 'alt="Preview"',
        "canonical palette badge": "img.shields.io/badge/palette-canonical-",
        "dark preview image": f"raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{slug}.svg",
        "dark website deep link": f"https://apollo-theme.github.io/#app-{slug}",
        "light preview image": f"raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/{slug}-light.svg",
        "light website deep link": f"https://apollo-theme.github.io/#app-{slug}-light",
        "light variant name": "Apollo Light",
        "simulation caption": "simulated preview",
    }
    missing = [label for label, fragment in required_fragments.items() if fragment.lower() not in readme.lower()]
    if not any(title.lower() in readme.lower() for title in expected_titles):
        missing.append("app-first title")
    headings = (line.removeprefix("## ") for line in readme.splitlines() if line.startswith("## "))
    anchors = {markdown_anchor(heading) for heading in headings}
    if app["install_anchor"] not in anchors:
        missing.append("install section")
    lowered = readme.lower()
    if 'href="license"' not in lowered and f'href="{MONOREPO}/blob/main/{slug}/license"'.lower() not in lowered:
        missing.append("license link")
    if "img.shields.io/badge/license-mit" not in lowered and "img.shields.io/github/license/" not in lowered:
        missing.append("license badge")
    if f"img.shields.io/badge/{app['badge_fragment']}".lower() not in lowered:
        missing.append("app or platform badge")
    prose = visible_prose(readme)
    appearance_names = ("Apollo Dark", "Apollo Light")
    missing_appearances = [
        name
        for name in appearance_names
        if not re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", prose)
    ]
    if missing_appearances:
        missing.append(f"visible appearance names {missing_appearances}")
    if missing:
        raise ValueError(f"{slug}: README branding contract missing {missing}")
    dead = sorted(set(DEAD_REPOSITORY_URL.findall("\n".join(public_metadata))))
    if dead:
        raise ValueError(f"{slug}: per-app repository URLs must point to the monorepo {dead}")
    if slug in CLONE_APPS:
        check_shared_clone_contract(slug, readme)
    forbidden = forbidden_identity_terms(slug, combined)
    if forbidden:
        raise ValueError(f"{slug}: forbidden lineage phrases {forbidden}")


def check_repository(slug: str, native: bool) -> None:
    directory = ROOT / slug
    light_artifact = APPS[slug]["light_artifact"]
    required = (".gitattributes", "README.md", "CLAUDE.md", "LICENSE", "palette/apollo.json", "palette/apollo-light.json", "scripts/generate.py", "scripts/check.py")
    missing = [path for path in required if not (directory / path).exists()]
    if not (directory / light_artifact).exists():
        missing.append(light_artifact)
    if missing:
        raise FileNotFoundError(f"{slug}: missing {', '.join(missing)}")
    attributes = (directory / ".gitattributes").read_text(encoding="utf-8").splitlines()
    if "* text=auto eol=lf" not in attributes:
        raise ValueError(f"{slug}: .gitattributes must preserve LF across Windows checkouts")
    for variant, filename in (("dark", "apollo.json"), ("light", "apollo-light.json")):
        snapshot_path = directory / "palette" / filename
        canonical_path = ROOT / "palette" / filename
        if snapshot_path.read_bytes() != canonical_path.read_bytes():
            raise ValueError(f"{slug}: {variant} palette snapshot differs byte-for-byte from canonical palette")
    check_readme_contract(slug)
    if slug == "firefox":
        dark_manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        light_manifest_path = directory / "variants" / "light" / "manifest.json"
        if not light_manifest_path.exists():
            raise FileNotFoundError("firefox: missing variants/light/manifest.json")
        light_manifest = json.loads(light_manifest_path.read_text(encoding="utf-8"))
        dark_guid = dark_manifest["browser_specific_settings"]["gecko"]["id"]
        light_guid = light_manifest["browser_specific_settings"]["gecko"]["id"]
        if dark_guid != "humble-apollo@d0n9x1n":
            raise ValueError("firefox: dark Gecko GUID changed")
        if light_guid != "apollo-light@d0n9x1n" or light_guid == dark_guid:
            raise ValueError("firefox: light Gecko GUID is missing or collides with dark")
    subprocess.run([sys.executable, "scripts/generate.py", "--check"], cwd=directory, check=True)
    if native:
        subprocess.run([sys.executable, "scripts/check.py"], cwd=directory, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Apollo palette and application folders")
    parser.add_argument("--app", choices=SLUGS, action="append", help="limit validation to an app folder")
    parser.add_argument("--native", action="store_true", help="also run each selected app's own checker")
    args = parser.parse_args()
    check_layout()
    check_source_pin()
    check_palette()
    for slug in tuple(args.app or SLUGS):
        check_repository(slug, args.native)
        print(f"{slug}: valid{' with native checks' if args.native else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
