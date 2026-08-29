#!/usr/bin/env python3
"""Generate the WezTerm Apollo color schemes from the palette snapshots."""

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
REPOSITORY_URL = "https://github.com/apollo-theme/wezterm-apollo-theme"


def load_palette(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(quoted(value) for value in values) + "]"


def rgba(color: str, alpha: float) -> str:
    red, green, blue = (int(color[offset : offset + 2], 16) for offset in (1, 3, 5))
    return f"rgba({red}, {green}, {blue}, {alpha:g})"


def render(palette: dict[str, Any]) -> str:
    terminal = palette["terminal"]
    source_name = "apollo-light.json" if palette["id"] == "apollo-light" else "apollo.json"
    lines = [
        f"# Generated from palette/{source_name} by scripts/generate.py; do not edit.",
        "[colors]",
        f'foreground = {quoted(terminal["foreground"])}',
        f'background = {quoted(terminal["background"])}',
        f'cursor_fg = {quoted(terminal["cursorText"])}',
        f'cursor_bg = {quoted(terminal["cursor"])}',
        f'cursor_border = {quoted(terminal["cursor"])}',
        'selection_fg = "none"',
        f'selection_bg = {quoted(rgba(terminal["selection"]["color"], terminal["selection"]["alpha"]))}',
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


def render_outputs() -> dict[Path, str]:
    return {output_path: render(load_palette(palette_path)) for output_path, palette_path in OUTPUTS.items()}


def find_unexpected_outputs(root: Path = ROOT) -> list[Path]:
    expected_names = {path.name for path in OUTPUTS}
    return sorted(path for path in root.glob("*.toml") if path.name not in expected_names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated schemes are stale")
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
