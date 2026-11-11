#!/usr/bin/env python3
"""Validate generated PowerShell files and run native assertions when available."""

from __future__ import annotations

import re
import shutil
import subprocess
from html.parser import HTMLParser
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "ApolloTheme.psm1"
MANIFEST = ROOT / "ApolloTheme.psd1"
RESTRICTED_DARK = "#665c54"
REQUIRED_KEYS = {
    "ContinuationPrompt", "Emphasis", "Error", "Default", "Comment", "Keyword",
    "String", "Operator", "Variable", "Command", "Parameter", "Type", "Number",
    "Member", "Selection", "InlinePrediction", "ListPrediction",
    "ListPredictionSelected", "ListPredictionTooltip",
}
README_CONTRACT_MARKERS = {
    "explicit dark activation command": "Enable-ApolloTheme -Variant Dark",
    "explicit light activation command": "Enable-ApolloTheme -Variant Light",
}


def run(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def _blockquote_body(line: str) -> tuple[int, str]:
    """Return blockquote depth and content after standard quote markers."""
    depth = 0
    while match := re.match(r" {0,3}> ?", line):
        depth += 1
        line = line[match.end():]
    return depth, line


def _list_item_body(line: str) -> tuple[int | None, str]:
    """Return list continuation indentation and content after a list marker."""
    match = re.match(r"( {0,3}(?:[-+*]|\d{1,9}[.)]))([ \t]+)", line)
    if match is None:
        return None, line
    whitespace = match.group(2)
    prefix = match.group(1) + whitespace[0]
    return len(prefix.expandtabs(4)), line[len(prefix):]


def _strip_indent(line: str, width: int) -> str | None:
    """Strip at least width columns of spaces or tabs from one line."""
    columns = 0
    index = 0
    while index < len(line) and columns < width and line[index] in " \t":
        columns += 1 if line[index] == " " else 4 - (columns % 4)
        index += 1
    return line[index:] if columns >= width else None


def _strip_indented_code(text: str) -> str:
    """Remove indented code after optional standard blockquote markers."""
    visible: list[str] = []
    for line in text.splitlines(keepends=True):
        body = _blockquote_body(line)[1]
        _, list_body = _list_item_body(body)
        if _strip_indent(list_body, 4) is None:
            visible.append(line)
    return "".join(visible)


def _strip_fenced_code(text: str) -> str:
    """Remove completed CommonMark-style fenced blocks without hiding unmatched text."""
    lines = text.splitlines(keepends=True)
    visible: list[str] = []
    index = 0
    while index < len(lines):
        quote_depth, body = _blockquote_body(lines[index].rstrip("\r\n"))
        list_indent, body = _list_item_body(body)
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})([^\r\n]*)", body)
        if not opening or (opening.group(1)[0] == "`" and "`" in opening.group(2)):
            visible.append(lines[index])
            index += 1
            continue
        fence = opening.group(1)
        closer = re.compile(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t]*")
        closing_index = next(
            (
                candidate
                for candidate in range(index + 1, len(lines))
                if (
                    (quoted := _blockquote_body(lines[candidate].rstrip("\r\n")))[0] == quote_depth
                    and (
                        (candidate_body := (
                            _strip_indent(quoted[1], list_indent)
                            if list_indent is not None
                            else quoted[1]
                        ))
                        is not None
                    )
                    and closer.fullmatch(candidate_body)
                )
            ),
            None,
        )
        if closing_index is None:
            visible.extend(lines[index:])
            break
        index = closing_index + 1
    return "".join(visible)


def _strip_inline_code(text: str) -> str:
    """Remove code spans with isolated opening and exact matching backtick runs."""
    parts: list[str] = []
    index = 0
    while opening := re.search(r"(?<![\\`])(`+)(?!`)", text[index:]):
        start = index + opening.start()
        run = opening.group(1)
        closer = re.search(rf"(?<![\\`]){re.escape(run)}(?!`)", text[start + len(run):])
        if closer is None:
            parts.append(text[index:])
            return "".join(parts)
        parts.append(text[index:start])
        index = start + len(run) + closer.end()
    parts.append(text[index:])
    return "".join(parts)


class _VisibleHTMLCollector(HTMLParser):
    """Collect text from HTML elements that are visible to readers."""

    SUPPRESSED = {"code", "pre", "script", "style", "template"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    HIDDEN_STYLE = re.compile(
        r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\s*(?:!\s*important\s*)?(?=;|$)",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []
        self.suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.VOID:
            return
        suppressed = tag in self.SUPPRESSED or any(
            name == "hidden"
            or (name == "aria-hidden" and (value or "").casefold() == "true")
            or (name == "style" and bool(self.HIDDEN_STYLE.search(value or "")))
            for name, value in attrs
        )
        self.stack.append((tag, suppressed))
        self.suppressed_depth += int(suppressed)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        pass

    def handle_endtag(self, tag: str) -> None:
        match = next((index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index][0] == tag), None)
        if match is None:
            return
        closed = self.stack[match:]
        del self.stack[match:]
        self.suppressed_depth -= sum(suppressed for _, suppressed in closed)

    def handle_data(self, data: str) -> None:
        if not self.suppressed_depth:
            self.parts.append(data)


def visible_prose(text: str) -> str:
    """Return reader-visible prose, excluding code and metadata."""
    text = re.sub(r"<!--(?:.*?-->|.*\Z)", "", text, flags=re.DOTALL)
    text = _strip_fenced_code(text)
    text = _strip_indented_code(text)
    text = _strip_inline_code(text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"!\[[^\]]*\]\[[^\]]*\]", "", text)
    text = re.sub(r"!\[[^\]]*\]", "", text)
    text = re.sub(r"^[ ]{0,3}\[[^\]\n]+\]:[^\n]*(?:\n|$)", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    collector = _VisibleHTMLCollector()
    collector.feed(text)
    collector.close()
    return "".join(collector.parts)


def validate_readme_contract(text: str) -> None:
    prose = visible_prose(text)
    for name in ("Apollo Dark", "Apollo Light"):
        if not re.search(rf"(?<![\w./-]){re.escape(name)}(?![\w./-])", prose):
            raise AssertionError(f"README contract missing visible name {name!r}")
    for label, marker in README_CONTRACT_MARKERS.items():
        if not re.search(rf"(?m)(?<!\S){re.escape(marker)}(?!\S)", text):
            raise AssertionError(f"README contract missing {label}")


def validate_static() -> None:
    text = MODULE.read_text(encoding="utf-8")
    variant_table = text.split("$script:ApolloVariantColors = @{\n", 1)[1]
    dark_table = variant_table.split("    Light = @{", 1)[0]
    if RESTRICTED_DARK in dark_table.lower():
        raise AssertionError(f"{RESTRICTED_DARK} remains restricted in Apollo Dark")
    if "    Light = @{" not in variant_table:
        raise AssertionError("missing Apollo Light color table")
    for required in ("Get-ApolloPSReadLineColors", "Enable-ApolloTheme", "Disable-ApolloTheme"):
        if f"function {required}" not in text:
            raise AssertionError(f"missing exported function {required}")
    if text.count("[ValidateSet('Dark', 'Light')]") != 2:
        raise AssertionError("public variant parameters must accept exactly Dark and Light")
    if text.count("[string] $Variant = 'Dark'") != 2:
        raise AssertionError("public variant parameters must default to Dark")
    if "$Options.PSObject.Properties[$entry.Value]" not in text:
        raise AssertionError("PSReadLine properties must be filtered for version compatibility")
    if "$PROFILE" in text:
        raise AssertionError("module must not rewrite or reference $PROFILE")
    manifest = MANIFEST.read_text(encoding="utf-8")
    if "ModuleVersion = '0.2.1'" not in manifest:
        raise AssertionError("module version must be 0.2.1")
    if "GUID = '5c88f42f-5dbf-45f5-8514-6f99cb3b628e'" not in manifest:
        raise AssertionError("module GUID changed")


def validate_powershell() -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        raise FileNotFoundError("pwsh")
    script = ROOT / "tests" / "Test-ApolloTheme.ps1"
    result = run([shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(script)])
    if "PowerShell Apollo theme tests passed" not in result.stdout:
        raise AssertionError(result.stdout + result.stderr)


def main() -> int:
    run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"])
    validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))
    validate_static()
    if shutil.which("pwsh") or shutil.which("powershell"):
        validate_powershell()
        print("direct PowerShell assertions passed")
    else:
        print("PowerShell not installed; native assertions skipped")
    print("PowerShell Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
