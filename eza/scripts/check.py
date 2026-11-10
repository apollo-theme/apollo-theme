#!/usr/bin/env python3
"""Validate both eza themes through isolated EZA_CONFIG_DIR values."""

from __future__ import annotations

import os
import re
import shutil
from html.parser import HTMLParser
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    "dark": ROOT / "theme.yml",
    "light": ROOT / "light" / "theme.yml",
}
RESTRICTED_DARK = "#665c54"
REQUIRED_SECTIONS = {"filekinds", "perms", "size", "users", "links", "git", "git_repo", "file_type"}
REQUIRED_FILE_KINDS = {"normal", "directory", "symlink", "pipe", "block_device", "char_device", "socket", "special", "executable", "mount_point"}
README_CONTRACT_MARKERS = {
    "dark activation command": 'EZA_CONFIG_DIR="$HOME/.config/eza-apollo-theme" eza --color=always -la',
    "light activation command": 'EZA_CONFIG_DIR="$HOME/.config/eza-apollo-theme/light" eza --color=always -la',
}
EXPECTED = {
    "dark": {
        "directory": "\x1b[1;38;2;131;165;152mfolder",
        "symlink": "\x1b[38;2;142;192;124mlink",
        "normal": "\x1b[38;2;207;188;151mplain",
        "executable": "\x1b[1;38;2;184;187;38mrun",
    },
    "light": {
        "directory": "\x1b[1;38;2;7;102;120mfolder",
        "symlink": "\x1b[38;2;53;107;77mlink",
        "normal": "\x1b[38;2;60;56;54mplain",
        "executable": "\x1b[1;38;2;107;103;0mrun",
    },
}


def run(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, capture_output=True, env=env)


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


def variant_for_path(theme_path: Path) -> str:
    for variant, path in THEMES.items():
        if theme_path == path:
            return variant
    raise ValueError(f"unknown theme path: {theme_path}")


def validate_static(theme_path: Path = THEMES["dark"]) -> None:
    text = theme_path.read_text(encoding="utf-8")
    variant = variant_for_path(theme_path)
    if variant == "dark" and RESTRICTED_DARK in text.lower():
        raise AssertionError(f"{RESTRICTED_DARK} remains restricted in Apollo Dark")
    top = {match.group(1) for match in re.finditer(r"^([a-z_]+):(?:\s|$)", text, re.MULTILINE)}
    if not REQUIRED_SECTIONS <= top:
        raise AssertionError(f"missing eza sections: {sorted(REQUIRED_SECTIONS - top)}")
    block = text.split("filekinds:\n", 1)[1].split("\nperms:", 1)[0]
    kinds = {match.group(1) for match in re.finditer(r"^  ([a-z_]+):", block, re.MULTILINE)}
    if kinds != REQUIRED_FILE_KINDS:
        raise AssertionError(f"file-kind coverage mismatch: {sorted(REQUIRED_FILE_KINDS ^ kinds)}")
    if "filenames:" in text or "extensions:" in text:
        raise AssertionError("theme must not replace filename/extension mappings")


def validate_eza(variant: str = "dark") -> None:
    executable = shutil.which("eza")
    if not executable:
        raise FileNotFoundError("eza")
    with tempfile.TemporaryDirectory(prefix=f"apollo-eza-{variant}-") as temp:
        base = Path(temp)
        config = base / "config"
        files = base / "files"
        config.mkdir()
        (files / "folder").mkdir(parents=True)
        shutil.copy2(THEMES[variant], config / "theme.yml")
        (files / "plain").write_text("plain\n", encoding="utf-8")
        executable_file = files / "run"
        executable_file.write_text("#!/bin/sh\n", encoding="utf-8")
        executable_file.chmod(0o755)
        (files / "link").symlink_to("plain")
        env = os.environ.copy()
        env["EZA_CONFIG_DIR"] = str(config)
        env.pop("LS_COLORS", None)
        env.pop("EZA_COLORS", None)
        env.pop("EXA_COLORS", None)
        result = run([executable, "--color=always", "--icons=never", "--classify=never", "--sort=name", "-1", str(files)], env)
        for kind, sequence in EXPECTED[variant].items():
            if sequence not in result.stdout:
                raise AssertionError(f"eza {variant} output lacks Apollo {kind} style")
        for variable in ("LS_COLORS", "EZA_COLORS", "EXA_COLORS"):
            override_env = env.copy()
            override_env[variable] = "di=38;2;251;73;52"
            overridden = run(
                [executable, "--color=always", "--icons=never", "--classify=never", "--list-dirs", "-1", str(files / "folder")],
                override_env,
            ).stdout
            if "38;2;251;73;52" not in overridden:
                raise AssertionError(f"existing {variable} did not retain precedence")


def main() -> int:
    run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"])
    validate_readme_contract((ROOT / "README.md").read_text(encoding="utf-8"))
    for theme_path in THEMES.values():
        validate_static(theme_path)
    if shutil.which("eza"):
        for variant in THEMES:
            validate_eza(variant)
        print("both isolated eza config directories and color-variable precedence passed")
    else:
        print("eza not installed; native schema validation skipped")
    print("eza Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
