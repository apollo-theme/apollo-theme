#!/usr/bin/env python3
"""Validate both standalone Apollo VS Code theme variants."""

from __future__ import annotations

from html.parser import HTMLParser

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PALETTE_SHA256 = {
    "apollo": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
    "apollo-light": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
}
VARIANTS = (
    ("apollo", "dark", ROOT / "palette" / "apollo.json", ROOT / "themes" / "apollo-color-theme.json"),
    ("apollo-light", "light", ROOT / "palette" / "apollo-light.json", ROOT / "themes" / "apollo-light-color-theme.json"),
)
HEX = re.compile(r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")
README_NAMES = ("Apollo Dark", "Apollo Light")
README_MARKERS = ("**Apollo**", "**Apollo Light**")


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


def validate_readme_contract(markdown: str) -> None:
    prose = visible_prose(markdown)
    for name in README_NAMES:
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w./-])", prose) is None:
            raise AssertionError(f"README visible prose must include {name}")
    activation = re.search(r"(?ms)^## Activate\s*$\n(.*?)(?=^## |\Z)", markdown)
    guidance = activation.group(1) if activation else ""
    for marker in README_MARKERS:
        if re.search(rf"(?<![\w*]){re.escape(marker)}(?![\w*])", guidance) is None:
            raise AssertionError(f"README activation guidance must include selector label {marker}")


def fail(message: str) -> None:
    raise AssertionError(message)


def walk_colors(value: Any, path: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            found.extend(walk_colors(child, f"{path}.{key}" if path else key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_colors(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value.startswith("#"):
        found.append((path, value))
    return found


def validate_variant(variant_id: str, appearance: str, palette_path: Path, theme_path: Path) -> tuple[int, int, int]:
    digest = hashlib.sha256(palette_path.read_bytes()).hexdigest()
    if digest != PALETTE_SHA256[variant_id]:
        fail(f"{palette_path.relative_to(ROOT)} differs from canonical SHA-256: {digest}")

    palette = json.loads(palette_path.read_text(encoding="utf-8"))
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    if (palette.get("id"), palette.get("appearance")) != (variant_id, appearance):
        fail(f"{palette_path.name} has incorrect variant semantics")
    if (theme.get("name"), theme.get("type")) != (palette["name"], appearance):
        fail(f"{theme_path.name} has incorrect name/type semantics")

    colors = theme["colors"]
    terminal = palette["terminal"]
    ansi_names = ("Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")
    ansi = [colors[f"terminal.ansi{name}"] for name in ansi_names]
    bright = [colors[f"terminal.ansiBright{name}"] for name in ansi_names]
    if ansi != terminal["ansi"] or bright != terminal["bright"]:
        fail(f"{theme_path.name} terminal arrays do not exactly match its palette")
    if colors["editor.foreground"] != palette["colors"]["foreground"]:
        fail(f"{theme_path.name} editor foreground is incorrect")
    if colors["focusBorder"] != palette["colors"]["accent"]:
        fail(f"{theme_path.name} focus color is incorrect")

    statuses = {
        "editorError.foreground": "danger",
        "editorWarning.foreground": "accent",
        "editorInfo.foreground": "info",
        "testing.iconPassed": "success",
    }
    for key, role in statuses.items():
        if colors.get(key) != palette["colors"][role]:
            fail(f"{theme_path.name} semantic status {key} must use {role}")

    invalid = [(path, color) for path, color in walk_colors(theme) if not HEX.fullmatch(color)]
    if invalid:
        fail(f"{theme_path.name} contains invalid hex colors: {invalid}")
    if len(colors) < 150:
        fail(f"{theme_path.name} is incomplete: only {len(colors)} color keys")
    if not theme.get("semanticHighlighting") or len(theme.get("semanticTokenColors", {})) < 20:
        fail(f"{theme_path.name} semantic highlighting coverage is incomplete")
    if len(theme.get("tokenColors", [])) < 25:
        fail(f"{theme_path.name} TextMate scope coverage is incomplete")
    return len(colors), len(theme["tokenColors"]), len(theme["semanticTokenColors"])


def main() -> int:
    validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], cwd=ROOT, check=True)
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))

    if package.get("publisher") != "apollo-theme":
        fail("publisher must remain 'apollo-theme'")
    if package.get("repository", {}).get("url") != "https://github.com/apollo-theme/vscode-apollo-theme.git":
        fail("package repository URL is incorrect")
    expected_contributions = [
        {"label": "Apollo", "uiTheme": "vs-dark", "path": "./themes/apollo-color-theme.json"},
        {"label": "Apollo Light", "uiTheme": "vs", "path": "./themes/apollo-light-color-theme.json"},
    ]
    if package.get("contributes", {}).get("themes") != expected_contributions:
        fail("package must contribute exactly Apollo/vs-dark and Apollo Light/vs")
    versions = (package.get("version"), lock.get("version"), lock.get("packages", {}).get("", {}).get("version"))
    if versions != ("0.2.0", "0.2.0", "0.2.0"):
        fail(f"package and lock versions must all be 0.2.0, got {versions}")

    counts = [validate_variant(*variant) for variant in VARIANTS]
    print(
        "validated two palette snapshots and theme variants; "
        + ", ".join(
            f"{variant[0]}={colors} colors/{textmate} TextMate/{semantic} semantic"
            for variant, (colors, textmate, semantic) in zip(VARIANTS, counts, strict=True)
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
