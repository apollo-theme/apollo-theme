#!/usr/bin/env python3
"""Generate the WezTerm Apollo color scheme from the palette snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
OUTPUT_PATH = ROOT / "apollo.toml"
REPOSITORY_URL = "https://github.com/apollo-theme/wezterm-apollo-theme"


def load_palette(path: Path = PALETTE_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(quoted(value) for value in values) + "]"


def render(palette: dict[str, Any]) -> str:
    colors = palette["colors"]
    terminal = palette["terminal"]
    lines = [
        "# Generated from palette/apollo.json by scripts/generate.py; do not edit.",
        "[colors]",
        f'foreground = {quoted(terminal["foreground"])}',
        f'background = {quoted(terminal["background"])}',
        f'cursor_fg = {quoted(terminal["cursorText"])}',
        f'cursor_bg = {quoted(terminal["cursor"])}',
        f'cursor_border = {quoted(terminal["cursor"])}',
        f'selection_fg = {quoted(colors["foregroundSecondary"])}',
        f'selection_bg = {quoted(terminal["selection"]["color"])}',
        f'ansi = {toml_array(terminal["ansi"])}',
        f'brights = {toml_array(terminal["bright"])}',
        "",
        "[metadata]",
        f'name = {quoted(palette["name"])}',
        f'author = {quoted("D0n9X1n")}',
        f'origin_url = {quoted(REPOSITORY_URL)}',
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if apollo.toml is stale")
    args = parser.parse_args()
    rendered = render(load_palette())

    if args.check:
        try:
            current = OUTPUT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"missing generated artifact: {OUTPUT_PATH.name}", file=sys.stderr)
            return 1
        if current != rendered:
            print(f"generated artifact is stale: {OUTPUT_PATH.name}", file=sys.stderr)
            return 1
        print(f"up to date: {OUTPUT_PATH.name}")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
