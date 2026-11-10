#!/usr/bin/env python3
"""Validate both standalone Apollo Visual Studio theme variants."""

from __future__ import annotations

from html.parser import HTMLParser

import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_SHA256 = {
    "apollo": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
    "apollo-light": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
}
VARIANTS = (
    ("apollo", "dark", "Apollo", "{895D123B-BC2C-58B5-B006-149BC8F1B5E7}", ROOT / "palette" / "apollo.json", ROOT / "themes" / "Apollo.vstheme"),
    ("apollo-light", "light", "Apollo Light", "{28E5D943-7F6B-5B87-B6F0-9AEF73CD4F34}", ROOT / "palette" / "apollo-light.json", ROOT / "themes" / "Apollo Light.vstheme"),
)
ARGB = re.compile(r"^[0-9A-F]{8}$")
REQUIRED_CATEGORIES = {
    "Environment": "{624ED9C3-BDFD-41FA-96C3-7C824EA32E3D}",
    "Text Editor": "{75A05685-00A8-4DED-BAE5-E7A50BFA929A}",
    "Command Window": "{EE1BE240-4E81-4BEB-8EEA-54322B6B1BF5}",
    "Output Window": "{9973EFDF-317D-431C-8BC1-5E88CBFD4F7F}",
}
README_NAMES = ("Apollo Dark", "Apollo Light")
README_MARKERS = ("themes/Apollo.vstheme", "themes/Apollo Light.vstheme")


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
    for marker in README_MARKERS:
        if re.search(rf"(?<![\w/.-]){re.escape(marker)}(?![\w/.-])", markdown) is None:
            raise AssertionError(f"README must include native marker {marker}")


def fail(message: str) -> None:
    raise AssertionError(message)


def category_map(theme: ET.Element) -> dict[str, ET.Element]:
    return {category.attrib["Name"]: category for category in theme.findall("Category")}


def color_map(category: ET.Element) -> dict[str, ET.Element]:
    return {color.attrib["Name"]: color for color in category.findall("Color")}


def source(node: ET.Element, child_name: str) -> str:
    child = node.find(child_name)
    if child is None:
        fail(f"{node.attrib.get('Name')} has no {child_name}")
    assert child is not None
    return child.attrib["Source"]


def argb(color: str) -> str:
    return "FF" + color.removeprefix("#").upper()


def validate_variant(
    variant_id: str,
    appearance: str,
    name: str,
    guid: str,
    palette_path: Path,
    theme_path: Path,
) -> tuple[int, int, int]:
    palette_bytes = palette_path.read_bytes()
    digest = hashlib.sha256(palette_bytes).hexdigest()
    if digest != PALETTE_SHA256[variant_id]:
        fail(f"{palette_path.relative_to(ROOT)} differs from canonical SHA-256: {digest}")
    palette = json.loads(palette_bytes)
    if (palette.get("id"), palette.get("appearance")) != (variant_id, appearance):
        fail(f"{palette_path.name} has incorrect variant semantics")

    root = ET.parse(theme_path).getroot()
    if root.tag != "Themes" or len(root.findall("Theme")) != 1:
        fail(f"{theme_path.name} must contain exactly one Theme")
    theme = root.find("Theme")
    assert theme is not None
    if theme.attrib != {"Name": name, "GUID": guid, "MinVSVersion": "17.0"}:
        fail(f"{theme_path.name} metadata is incorrect: {theme.attrib}")

    categories = category_map(theme)
    if set(categories) != set(REQUIRED_CATEGORIES):
        fail(f"{theme_path.name} categories are incorrect: {sorted(categories)}")
    for category_name, category_guid in REQUIRED_CATEGORIES.items():
        if categories[category_name].attrib.get("GUID") != category_guid:
            fail(f"{theme_path.name} changed {category_name} category GUID")
    if len(categories["Environment"].findall("Color")) < 55:
        fail(f"{theme_path.name} Environment category is incomplete")
    editor = color_map(categories["Text Editor"])
    if len(editor) < 35:
        fail(f"{theme_path.name} Text Editor category is incomplete")

    colors = palette["colors"]
    expected = {
        "Plain Text": ("Foreground", colors["foreground"]),
        "Syntax Error": ("Foreground", colors["danger"]),
        "Warning": ("Foreground", colors["accent"]),
        "Information": ("Foreground", colors["info"]),
        "Track Changes after save": ("Foreground", colors["success"]),
        "Selected Text": ("Background", colors["selection"]),
    }
    for color_name, (channel, value) in expected.items():
        if color_name not in editor or source(editor[color_name], channel) != argb(value):
            fail(f"{theme_path.name}: {color_name} {channel} must be {argb(value)}")

    for element in root.findall(".//*[@Source]"):
        value = element.attrib["Source"].upper()
        if not ARGB.fullmatch(value):
            fail(f"{theme_path.name} has invalid CT_RAW source: {value}")
        if element.attrib.get("Type") != "CT_RAW":
            fail(f"{theme_path.name} has non-CT_RAW generated color")
        if variant_id == "apollo" and value == "FF665C54":
            fail("restricted dark ANSI bright black appears in Visual Studio UI/editor text")

    return (
        len(categories["Environment"].findall("Color")),
        len(editor),
        len(root.findall(".//*[@Source]")),
    )


def main() -> int:
    validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], cwd=ROOT, check=True)
    if len({variant[3] for variant in VARIANTS}) != len(VARIANTS):
        fail("theme GUIDs must be unique")
    counts = [validate_variant(*variant) for variant in VARIANTS]
    print(
        "validated two palette snapshots and Visual Studio variants; "
        + ", ".join(
            f"{variant[0]}={environment} environment/{editor} editor/{channels} channels"
            for variant, (environment, editor, channels) in zip(VARIANTS, counts, strict=True)
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, ET.ParseError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
