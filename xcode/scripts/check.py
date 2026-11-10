#!/usr/bin/env python3
"""Run repository checks without third-party dependencies."""

from __future__ import annotations

from html.parser import HTMLParser

import json
import plistlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEMES = (ROOT / "Apollo.xccolortheme", ROOT / "Apollo Light.xccolortheme")
README_NAMES = ("Apollo Dark", "Apollo Light")
README_MARKERS = ("Apollo.xccolortheme", "Apollo Light.xccolortheme")


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


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))
    json.loads((ROOT / "palette" / "apollo.json").read_text(encoding="utf-8"))
    json.loads((ROOT / "palette" / "apollo-light.json").read_text(encoding="utf-8"))
    for theme in THEMES:
        plistlib.loads(theme.read_bytes())
    run([sys.executable, "scripts/generate.py", "--check"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if sys.platform == "darwin":
        for theme in THEMES:
            run(["plutil", "-lint", str(theme)])
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
