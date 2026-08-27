#!/usr/bin/env python3
"""Validate the Apollo snapshot and generated WezTerm color scheme."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
ARTIFACT_PATH = ROOT / "apollo.toml"
EXAMPLE_PATH = ROOT / "wezterm.lua"
HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")
EXPECTED_TOP_LEVEL = {"schemaVersion", "id", "name", "description", "appearance", "colorSpace", "provenance", "colors", "roles", "terminal", "constraints"}
EXPECTED_COLOR_KEYS = {"foreground", "background", "cursor_fg", "cursor_bg", "cursor_border", "selection_fg", "selection_bg", "ansi", "brights"}
EXPECTED_METADATA_KEYS = {"name", "author", "origin_url"}
REPOSITORY_URL = "https://github.com/apollo-theme/wezterm-apollo-theme"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), "palette root must be an object")
    return value


def validate_hex(value: Any, label: str) -> None:
    require(isinstance(value, str) and HEX_COLOR.fullmatch(value) is not None, f"{label} must be lowercase #rrggbb")


def validate_palette(palette: dict[str, Any]) -> None:
    require(set(palette) == EXPECTED_TOP_LEVEL, "palette top-level schema does not match schemaVersion 1")
    require(palette["schemaVersion"] == 1, "unsupported schemaVersion")
    require(palette["id"] == "apollo" and palette["name"] == "Apollo", "unexpected palette identity")
    require(palette["appearance"] == "dark" and palette["colorSpace"] == "srgb", "unexpected palette appearance or color space")
    colors = palette["colors"]
    require(isinstance(colors, dict) and colors, "colors must be a non-empty object")
    for name, value in colors.items():
        validate_hex(value, f"colors.{name}")

    terminal = palette["terminal"]
    require(set(terminal) == {"foreground", "background", "cursor", "cursorText", "selection", "ansi", "bright"}, "terminal schema is invalid")
    for name in ("foreground", "background", "cursor", "cursorText"):
        validate_hex(terminal[name], f"terminal.{name}")
    require(set(terminal["selection"]) == {"color", "alpha", "foregroundMode"}, "selection schema is invalid")
    validate_hex(terminal["selection"]["color"], "terminal.selection.color")
    require(terminal["selection"]["alpha"] == 0.5 and terminal["selection"]["foregroundMode"] == "preserve", "selection semantics changed")
    for group in ("ansi", "bright"):
        require(isinstance(terminal[group], list) and len(terminal[group]) == 8, f"terminal.{group} must contain eight colors")
        for index, value in enumerate(terminal[group]):
            validate_hex(value, f"terminal.{group}[{index}]")
    require(terminal["foreground"] == colors["foreground"], "foreground role drift")
    require(terminal["background"] == colors["background"], "background role drift")
    require(terminal["cursor"] == colors["accent"], "cursor role drift")
    require(terminal["cursorText"] == colors["background"], "cursor text role drift")
    require(terminal["selection"]["color"] == colors["selection"], "selection role drift")


def validate_scheme(scheme: dict[str, Any], palette: dict[str, Any]) -> None:
    require(set(scheme) == {"colors", "metadata"}, "WezTerm scheme has unknown or missing sections")
    colors = scheme["colors"]
    metadata = scheme["metadata"]
    require(set(colors) == EXPECTED_COLOR_KEYS, "WezTerm [colors] schema is incomplete")
    require(set(metadata) == EXPECTED_METADATA_KEYS, "WezTerm [metadata] schema is incomplete")
    require(metadata == {"name": "Apollo", "author": "D0n9X1n", "origin_url": REPOSITORY_URL}, "WezTerm metadata drift")

    terminal = palette["terminal"]
    canonical = palette["colors"]
    expected = {
        "foreground": terminal["foreground"],
        "background": terminal["background"],
        "cursor_fg": terminal["cursorText"],
        "cursor_bg": terminal["cursor"],
        "cursor_border": terminal["cursor"],
        "selection_fg": canonical["foregroundSecondary"],
        "selection_bg": terminal["selection"]["color"],
        "ansi": terminal["ansi"],
        "brights": terminal["bright"],
    }
    require(colors == expected, "WezTerm color scheme drift")
    for name, value in colors.items():
        values = value if isinstance(value, list) else [value]
        for index, color in enumerate(values):
            validate_hex(color, f"colors.{name}[{index}]")


def validate_example() -> None:
    text = EXAMPLE_PATH.read_text(encoding="utf-8")
    require("config.color_scheme = 'Apollo'" in text, "wezterm.lua must activate Apollo")
    require("config.color_scheme_dirs" not in text, "example should use the standard colors directory")


def main() -> int:
    try:
        palette = load_json(PALETTE_PATH)
        validate_palette(palette)
        with ARTIFACT_PATH.open("rb") as handle:
            scheme = tomllib.load(handle)
        validate_scheme(scheme, palette)
        validate_example()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], check=True)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        return 1
    print("WezTerm Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
