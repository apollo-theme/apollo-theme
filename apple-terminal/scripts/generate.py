#!/usr/bin/env python3
"""Generate the Apple Terminal Apollo profiles from the palette snapshots."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    ROOT / "Apollo.terminal": ROOT / "palette" / "apollo.json",
    ROOT / "Apollo Light.terminal": ROOT / "palette" / "apollo-light.json",
}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
ANSI_KEYS = (
    "ANSIBlackColor", "ANSIRedColor", "ANSIGreenColor", "ANSIYellowColor",
    "ANSIBlueColor", "ANSIMagentaColor", "ANSICyanColor", "ANSIWhiteColor",
    "ANSIBrightBlackColor", "ANSIBrightRedColor", "ANSIBrightGreenColor", "ANSIBrightYellowColor",
    "ANSIBrightBlueColor", "ANSIBrightMagentaColor", "ANSIBrightCyanColor", "ANSIBrightWhiteColor",
)


def load_palette(path: Path) -> dict:
    palette = json.loads(path.read_text(encoding="utf-8"))
    if palette.get("id") not in {"apollo", "apollo-light"} or palette.get("colorSpace") != "srgb":
        raise ValueError("palette snapshot must describe an Apollo variant in sRGB")
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
            {"NSRGB": nsrgb, "$class": plistlib.UID(2), "NSColorSpace": 2},
            {"$classname": "NSColor", "$classes": ["NSColor", "NSObject"]},
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
        "name": palette["name"],
        "type": "Window Settings",
    }
    for key, value in zip(ANSI_KEYS, terminal["ansi"] + terminal["bright"]):
        profile[key] = archived_color(value)
    profile.update(
        {
            "BackgroundColor": archived_color(terminal["background"]),
            "CursorColor": archived_color(terminal["cursor"]),
            "SelectionColor": archived_color(terminal["selection"]["color"], terminal["selection"]["alpha"]),
            "TextBoldColor": archived_color(colors["foregroundBright"]),
            "TextColor": archived_color(terminal["foreground"]),
        }
    )
    return plistlib.dumps(profile, fmt=plistlib.FMT_XML, sort_keys=False)


def render_outputs() -> dict[Path, bytes]:
    return {output_path: render(load_palette(palette_path)) for output_path, palette_path in OUTPUTS.items()}


def find_unexpected_outputs(root: Path = ROOT) -> list[Path]:
    expected_names = {path.name for path in OUTPUTS}
    return sorted(path for path in root.glob("*.terminal") if path.name not in expected_names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail instead of writing when a committed profile is stale")
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
