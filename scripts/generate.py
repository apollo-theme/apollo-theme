#!/usr/bin/env python3
"""Generate the iTerm2 Apollo themes from the repository palette snapshots."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    ROOT / "Apollo.itermcolors": ROOT / "palette" / "apollo.json",
    ROOT / "Apollo Light.itermcolors": ROOT / "palette" / "apollo-light.json",
}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_palette(path: Path) -> dict:
    palette = json.loads(path.read_text(encoding="utf-8"))
    if palette.get("id") not in {"apollo", "apollo-light"} or palette.get("colorSpace") != "srgb":
        raise ValueError("palette snapshot must describe an Apollo variant in sRGB")
    terminal = palette.get("terminal", {})
    if len(terminal.get("ansi", [])) != 8 or len(terminal.get("bright", [])) != 8:
        raise ValueError("palette snapshot must contain eight ANSI and eight bright colors")
    return palette


def color(hex_color: str, alpha: float = 1.0) -> dict:
    if not HEX_COLOR.fullmatch(hex_color):
        raise ValueError(f"invalid sRGB color: {hex_color!r}")
    red, green, blue = (int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    return {
        "Alpha Component": alpha,
        "Blue Component": blue,
        "Color Space": "sRGB",
        "Green Component": green,
        "Red Component": red,
    }


def render(palette: dict) -> bytes:
    terminal = palette["terminal"]
    colors = palette["colors"]
    theme = {}
    for index, value in enumerate(terminal["ansi"] + terminal["bright"]):
        theme[f"Ansi {index} Color"] = color(value)
    theme.update(
        {
            "Background Color": color(terminal["background"]),
            "Bold Color": color(colors["foregroundBright"]),
            "Cursor Color": color(terminal["cursor"]),
            "Cursor Text Color": color(terminal["cursorText"]),
            "Foreground Color": color(terminal["foreground"]),
            "Selection Color": color(terminal["selection"]["color"], terminal["selection"]["alpha"]),
            # Explicitly preserving the foreground avoids low-contrast automatic inversion.
            "Selected Text Color": color(terminal["foreground"]),
        }
    )
    return plistlib.dumps(theme, fmt=plistlib.FMT_XML, sort_keys=False)


def render_outputs() -> dict[Path, bytes]:
    return {output_path: render(load_palette(palette_path)) for output_path, palette_path in OUTPUTS.items()}


def find_unexpected_outputs(root: Path = ROOT) -> list[Path]:
    expected_names = {path.name for path in OUTPUTS}
    return sorted(path for path in root.glob("*.itermcolors") if path.name not in expected_names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail instead of writing when a committed theme is stale")
    args = parser.parse_args()
    rendered_outputs = render_outputs()

    if args.check:
        failed = False
        for path in find_unexpected_outputs():
            print(f"unexpected generated artifact: {path.name}", file=sys.stderr)
            failed = True
        for output_path, generated in rendered_outputs.items():
            if not output_path.exists():
                print(f"missing generated artifact: {output_path.name}", file=sys.stderr)
                failed = True
            elif output_path.read_bytes() != generated:
                print(f"out of date: {output_path.name}", file=sys.stderr)
                failed = True
            else:
                print(f"up to date: {output_path.name}")
        return int(failed)

    for output_path, generated in rendered_outputs.items():
        output_path.write_bytes(generated)
        print(f"generated: {output_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
