#!/usr/bin/env python3
"""Generate Apollo.terminal from the repository palette snapshot."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
OUTPUT_PATH = ROOT / "Apollo.terminal"
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
ANSI_KEYS = (
    "ANSIBlackColor",
    "ANSIRedColor",
    "ANSIGreenColor",
    "ANSIYellowColor",
    "ANSIBlueColor",
    "ANSIMagentaColor",
    "ANSICyanColor",
    "ANSIWhiteColor",
    "ANSIBrightBlackColor",
    "ANSIBrightRedColor",
    "ANSIBrightGreenColor",
    "ANSIBrightYellowColor",
    "ANSIBrightBlueColor",
    "ANSIBrightMagentaColor",
    "ANSIBrightCyanColor",
    "ANSIBrightWhiteColor",
)


def load_palette() -> dict:
    palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    if palette.get("id") != "apollo" or palette.get("colorSpace") != "srgb":
        raise ValueError("palette snapshot must describe Apollo in sRGB")
    terminal = palette.get("terminal", {})
    if len(terminal.get("ansi", [])) != 8 or len(terminal.get("bright", [])) != 8:
        raise ValueError("palette snapshot must contain eight ANSI and eight bright colors")
    return palette


def number(value: float) -> str:
    return format(value, ".9g")


def archived_color(hex_color: str, alpha: float = 1.0) -> bytes:
    """Build the NSKeyedArchiver NSColor envelope used by Terminal profiles."""
    if not HEX_COLOR.fullmatch(hex_color):
        raise ValueError(f"invalid sRGB color: {hex_color!r}")
    components = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    if alpha != 1.0:
        components.append(alpha)
    nsrgb = (" ".join(number(component) for component in components) + "\0").encode("ascii")
    archive = {
        "$version": 100000,
        "$objects": [
            "$null",
            {
                "NSRGB": nsrgb,
                "$class": plistlib.UID(2),
                "NSColorSpace": 2,
            },
            {
                "$classname": "NSColor",
                "$classes": ["NSColor", "NSObject"],
            },
        ],
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": plistlib.UID(1)},
    }
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY, sort_keys=False)


def render(palette: dict) -> bytes:
    terminal = palette["terminal"]
    colors = palette["colors"]
    profile = {
        "ProfileCurrentVersion": 2.09,
        "name": "Apollo",
        "type": "Window Settings",
    }
    for key, value in zip(ANSI_KEYS, terminal["ansi"] + terminal["bright"]):
        profile[key] = archived_color(value)
    profile.update(
        {
            "BackgroundColor": archived_color(terminal["background"]),
            "CursorColor": archived_color(terminal["cursor"]),
            "SelectionColor": archived_color(
                terminal["selection"]["color"], terminal["selection"]["alpha"]
            ),
            "TextBoldColor": archived_color(colors["foregroundBright"]),
            "TextColor": archived_color(terminal["foreground"]),
        }
    )
    return plistlib.dumps(profile, fmt=plistlib.FMT_XML, sort_keys=False)


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
