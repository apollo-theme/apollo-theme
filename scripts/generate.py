#!/usr/bin/env python3
"""Generate the SonicTerm Apollo theme from the canonical palette snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
OUTPUT_PATH = ROOT / "apollo.toml"
COLOR_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")


def load_palette(path: Path = PALETTE_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def assignment(name: str, value: str) -> str:
    return f'{name} = "{value}"'


def render(palette: dict[str, Any]) -> str:
    colors = palette["colors"]
    terminal = palette["terminal"]
    ansi = dict(zip(COLOR_NAMES, terminal["ansi"], strict=True))
    bright = dict(zip(COLOR_NAMES, terminal["bright"], strict=True))

    lines = [
        '# Generated from palette/apollo.json by scripts/generate.py; do not edit.',
        assignment("name", palette["name"]),
        assignment("appearance", palette["appearance"]),
        "",
        "[colors]",
        assignment("background", terminal["background"]),
        assignment("foreground", terminal["foreground"]),
        assignment("cursor", terminal["cursor"]),
        assignment("cursor_text", terminal["cursorText"]),
        assignment("selection_bg", terminal["selection"]["color"]),
        assignment("selection_fg", colors["foregroundSecondary"]),
        "",
        "[colors.ansi]",
        *(assignment(name, ansi[name]) for name in COLOR_NAMES),
        "",
        "[colors.bright]",
        *(assignment(name, bright[name]) for name in COLOR_NAMES),
        "",
        "[colors.tab]",
        assignment("bar_bg", colors["background"]),
        assignment("active_bg", colors["background"]),
        assignment("active_fg", colors["accent"]),
        assignment("inactive_bg", colors["background"]),
        assignment("inactive_fg", colors["foregroundInactive"]),
        assignment("hover_bg", colors["surfaceHover"]),
        assignment("hover_fg", colors["foregroundSecondary"]),
        assignment("close_button_fg", colors["accent"]),
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
