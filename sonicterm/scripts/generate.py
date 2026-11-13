#!/usr/bin/env python3
"""Generate the SonicTerm Apollo themes from the canonical palette snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    ROOT / "apollo.toml": ROOT / "palette" / "apollo.json",
    ROOT / "apollo-light.toml": ROOT / "palette" / "apollo-light.json",
}
COLOR_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
# SonicTerm-only chrome: Apollo Dark's tab bar sits darker than the canvas.
BAR_BG = {"apollo": "#101010"}


def load_palette(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def assignment(name: str, value: str) -> str:
    return f'{name} = "{value}"'


def render(palette: dict[str, Any]) -> str:
    colors = palette["colors"]
    terminal = palette["terminal"]
    ansi = dict(zip(COLOR_NAMES, terminal["ansi"], strict=True))
    bright = dict(zip(COLOR_NAMES, terminal["bright"], strict=True))
    source_name = "apollo-light.json" if palette["id"] == "apollo-light" else "apollo.json"

    lines = [
        f"# Generated from palette/{source_name} by scripts/generate.py; do not edit.",
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
        assignment("bar_bg", BAR_BG.get(palette["id"], colors["background"])),
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


def render_outputs() -> dict[Path, str]:
    return {output_path: render(load_palette(palette_path)) for output_path, palette_path in OUTPUTS.items()}


def find_unexpected_outputs(root: Path = ROOT) -> list[Path]:
    expected_names = {path.name for path in OUTPUTS}
    return sorted(path for path in root.glob("*.toml") if path.name not in expected_names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated themes are stale")
    args = parser.parse_args()
    rendered_outputs = render_outputs()

    if args.check:
        failed = False
        for path in find_unexpected_outputs():
            print(f"unexpected generated artifact: {path.name}", file=sys.stderr)
            failed = True
        for output_path, rendered in rendered_outputs.items():
            try:
                current = output_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                print(f"missing generated artifact: {output_path.name}", file=sys.stderr)
                failed = True
                continue
            if current != rendered:
                print(f"generated artifact is stale: {output_path.name}", file=sys.stderr)
                failed = True
            else:
                print(f"up to date: {output_path.name}")
        return int(failed)

    for output_path, rendered in rendered_outputs.items():
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {output_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
