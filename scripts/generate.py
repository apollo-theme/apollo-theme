#!/usr/bin/env python3
"""Generate Apollo.itermcolors from the repository palette snapshot."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
OUTPUT_PATH = ROOT / "Apollo.itermcolors"
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_palette() -> dict:
    palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    if palette.get("id") != "apollo" or palette.get("colorSpace") != "srgb":
        raise ValueError("palette snapshot must describe Apollo in sRGB")
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
            "Selection Color": color(
                terminal["selection"]["color"], terminal["selection"]["alpha"]
            ),
            # Explicitly preserving the foreground avoids low-contrast automatic inversion.
            "Selected Text Color": color(terminal["foreground"]),
        }
    )
    return plistlib.dumps(theme, fmt=plistlib.FMT_XML, sort_keys=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the committed theme is stale",
    )
    args = parser.parse_args()

    generated = render(load_palette())
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_bytes() != generated:
            print(f"out of date: {OUTPUT_PATH.name}", file=sys.stderr)
            return 1
        print(f"up to date: {OUTPUT_PATH.name}")
        return 0

    OUTPUT_PATH.write_bytes(generated)
    print(f"generated: {OUTPUT_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
