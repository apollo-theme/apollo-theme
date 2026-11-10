#!/usr/bin/env python3
"""Validate both Apollo snapshots and generated Windows Terminal schemes."""

from __future__ import annotations

from html.parser import HTMLParser
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = (
    ("apollo", "Apollo", "dark", 0.5, ROOT / "palette" / "apollo.json", ROOT / "apollo.json"),
    ("apollo-light", "Apollo Light", "light", 1.0, ROOT / "palette" / "apollo-light.json", ROOT / "apollo-light.json"),
)
HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")
NORMAL_NAMES = ("black", "red", "green", "yellow", "blue", "purple", "cyan", "white")
BRIGHT_NAMES = ("brightBlack", "brightRed", "brightGreen", "brightYellow", "brightBlue", "brightPurple", "brightCyan", "brightWhite")
EXPECTED_TOP_LEVEL = {"schemaVersion", "id", "name", "description", "appearance", "colorSpace", "provenance", "colors", "roles", "terminal", "constraints"}
REQUIRED_SCHEME_KEYS = {"name", "foreground", "background", *NORMAL_NAMES, *BRIGHT_NAMES}
OPTIONAL_SCHEME_KEYS = {"cursorColor", "selectionBackground"}
README_MARKERS = ('"colorScheme": "Apollo"', '"colorScheme": "Apollo Light"')


class _VisibleHTMLParser(HTMLParser):
    HIDDEN_ELEMENTS = {"code", "pre", "script", "style", "template"}
    VOID_ELEMENTS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []
        self.hidden_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag = tag.lower()
        attributes = {name.lower(): value for name, value in attrs}
        style = re.sub(r"\s+", "", (attributes.get("style") or "").lower())
        hidden = bool(
            self.hidden_depth
            or tag in self.HIDDEN_ELEMENTS
            or "hidden" in attributes
            or (attributes.get("aria-hidden") or "").lower() == "true"
            or "display:none" in style
            or "visibility:hidden" in style
        )
        if tag not in self.VOID_ELEMENTS:
            self.stack.append((tag, hidden))
            if hidden:
                self.hidden_depth += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not any(open_tag == tag for open_tag, _ in self.stack):
            return
        while self.stack:
            open_tag, hidden = self.stack.pop()
            if hidden:
                self.hidden_depth -= 1
            if open_tag == tag:
                break

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def _indent_width(value: str) -> int:
    return len(value.expandtabs(4))


def visible_prose(text: str) -> str:
    text = re.sub(r"<!--.*?(?:-->|$)", "", text, flags=re.DOTALL)
    lines: list[str] = []
    fence: tuple[str, int, int] | None = None
    for line in text.splitlines():
        line = re.sub(r"^(?: {0,3}> ?)+", "", line)
        if fence is not None:
            stripped = line.lstrip(" ")
            marker = re.match(r"(`{3,}|~{3,})", stripped)
            if marker and len(line) - len(stripped) <= fence[2]:
                token = marker.group(1)
                suffix = stripped[len(token):]
                if token[0] == fence[0] and len(token) >= fence[1] and not suffix.strip():
                    fence = None
            continue

        list_item = re.match(
            r"^ {0,3}(?:[-+*]|\d{1,9}[.)])(?P<indent>[ \t]+)(?P<body>.*)$",
            line,
        )
        candidate = list_item.group("body") if list_item else line
        indent = list_item.group("indent")[1:] if list_item else candidate[: len(candidate) - len(candidate.lstrip(" \t"))]
        if _indent_width(indent) >= 4:
            continue
        stripped = candidate.lstrip(" ")
        marker = re.match(r"(`{3,}|~{3,})", stripped) if len(candidate) - len(stripped) <= 3 else None
        if marker:
            token = marker.group(1)
            suffix = stripped[len(token):]
            if token[0] == "~" or "`" not in suffix:
                base_indent = list_item.start("body") if list_item else 0
                fence = (token[0], len(token), base_indent + 3)
                continue
        if not list_item and _indent_width(indent) >= 4:
            continue
        lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"(?<![\\`])(?P<ticks>`+)(?!`)[\s\S]*?(?<!\\)(?P=ticks)(?!`)", "", text)
    text = re.sub(r"!\[[^\]\n]*\]\([^\n)]*\)", "", text)
    text = re.sub(r"!\[[^\]\n]*\]\[[^\]\n]*\]", "", text)
    text = re.sub(r"!\[[^\]\n]*\]", "", text)
    text = re.sub(r"^ {0,3}\[[^\]\n]+\]:.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?<!!)\[([^\]\n]+)\]\([^\n)]*\)", r"\1", text)
    text = re.sub(r"(?<!!)\[([^\]\n]+)\]\[[^\]\n]*\]", r"\1", text)
    text = re.sub(r"(?<!!)\[([^\]\n]+)\]", r"\1", text)
    parser = _VisibleHTMLParser()
    parser.feed(text)
    return " ".join(" ".join(parser.parts).split())


def _has_exact_marker(text: str, marker: str) -> bool:
    pattern = rf"^[ \t]*{re.escape(marker)}[ \t]*$"
    return re.search(pattern, text, flags=re.MULTILINE) is not None


def validate_readme_contract(text: str | None = None) -> None:
    if text is None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
    prose = visible_prose(text)
    missing = [
        name for name in ("Apollo Dark", "Apollo Light")
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-]|\.[A-Za-z0-9])", prose) is None
    ]
    missing.extend(marker for marker in README_MARKERS if not _has_exact_marker(text, marker))
    if missing:
        raise ValueError(f"README contract missing: {', '.join(missing)}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"{path.name} root must be an object")
    return value


def validate_hex(value: Any, label: str) -> None:
    require(isinstance(value, str) and HEX_COLOR.fullmatch(value) is not None, f"{label} must be lowercase #rrggbb")


def validate_palette(palette: dict[str, Any], palette_id: str, name: str, appearance: str, alpha: float) -> None:
    require(set(palette) == EXPECTED_TOP_LEVEL, f"{palette_id} top-level schema does not match schemaVersion 1")
    require(palette["schemaVersion"] == 1, f"{palette_id} has unsupported schemaVersion")
    require((palette["id"], palette["name"], palette["appearance"]) == (palette_id, name, appearance), f"{palette_id} identity or appearance is invalid")
    require(palette["colorSpace"] == "srgb", f"{palette_id} color space is invalid")
    colors = palette["colors"]
    require(isinstance(colors, dict) and colors, f"{palette_id} colors must be a non-empty object")
    for color_name, value in colors.items():
        validate_hex(value, f"{palette_id}.colors.{color_name}")
    terminal = palette["terminal"]
    require(set(terminal) == {"foreground", "background", "cursor", "cursorText", "selection", "ansi", "bright"}, f"{palette_id} terminal schema is invalid")
    for field in ("foreground", "background", "cursor", "cursorText"):
        validate_hex(terminal[field], f"{palette_id}.terminal.{field}")
    selection = terminal["selection"]
    require(set(selection) == {"color", "alpha", "foregroundMode"}, f"{palette_id} selection schema is invalid")
    validate_hex(selection["color"], f"{palette_id}.terminal.selection.color")
    require(selection["alpha"] == alpha and selection["foregroundMode"] == "preserve", f"{palette_id} selection semantics changed")
    for group in ("ansi", "bright"):
        require(isinstance(terminal[group], list) and len(terminal[group]) == 8, f"{palette_id} terminal.{group} must contain eight colors")
        for index, value in enumerate(terminal[group]):
            validate_hex(value, f"{palette_id}.terminal.{group}[{index}]")
    require(terminal["foreground"] == colors["foreground"], f"{palette_id} foreground role drift")
    require(terminal["background"] == colors["background"], f"{palette_id} background role drift")
    require(terminal["cursor"] == colors["accent"], f"{palette_id} cursor role drift")
    require(terminal["cursorText"] == colors["background"], f"{palette_id} cursor text role drift")
    require(selection["color"] == colors["selection"], f"{palette_id} selection role drift")


def validate_scheme(scheme: dict[str, Any], palette: dict[str, Any]) -> None:
    require(REQUIRED_SCHEME_KEYS <= set(scheme), f"{palette['id']} Windows Terminal scheme is missing required fields")
    require(set(scheme) == REQUIRED_SCHEME_KEYS | OPTIONAL_SCHEME_KEYS, f"{palette['id']} Windows Terminal scheme has unknown fields")
    require("magenta" not in scheme and "brightMagenta" not in scheme, "Windows Terminal uses purple field names")
    terminal = palette["terminal"]
    require(scheme == {
        "name": palette["name"],
        "background": terminal["background"],
        "foreground": terminal["foreground"],
        "cursorColor": terminal["cursor"],
        "selectionBackground": terminal["selection"]["color"],
        **dict(zip(NORMAL_NAMES, terminal["ansi"], strict=True)),
        **dict(zip(BRIGHT_NAMES, terminal["bright"], strict=True)),
    }, f"{palette['id']} Windows Terminal scheme drift")
    for field, value in scheme.items():
        if field != "name":
            validate_hex(value, f"{palette['id']}.{field}")


def main() -> int:
    try:
        validate_readme_contract()
        for palette_id, name, appearance, alpha, palette_path, artifact_path in VARIANTS:
            palette = load_json(palette_path)
            validate_palette(palette, palette_id, name, appearance, alpha)
            validate_scheme(load_json(artifact_path), palette)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], check=True)
    except (OSError, json.JSONDecodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        return 1
    print("Windows Terminal Apollo dark and light theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
