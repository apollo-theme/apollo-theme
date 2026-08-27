#!/usr/bin/env python3
"""Validate the Apollo snapshot and generated Alacritty theme fragment."""

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
HEX_COLOR = re.compile(r"^#[0-9a-f]{6}$")
COLOR_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
EXPECTED_TOP_LEVEL = {"schemaVersion", "id", "name", "description", "appearance", "colorSpace", "provenance", "colors", "roles", "terminal", "constraints"}
EXPECTED_COLOR_SECTIONS = {"primary", "cursor", "selection", "normal", "bright"}


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


def validate_theme(theme: dict[str, Any], palette: dict[str, Any]) -> None:
    require(set(theme) == {"colors"}, "Alacritty fragment must contain only [colors] settings")
    colors = theme["colors"]
    require(set(colors) == EXPECTED_COLOR_SECTIONS, "Alacritty color schema is incomplete")
    require(set(colors["primary"]) == {"background", "foreground"}, "Alacritty primary schema is invalid")
    require(set(colors["cursor"]) == {"text", "cursor"}, "Alacritty cursor schema is invalid")
    require(set(colors["selection"]) == {"text", "background"}, "Alacritty selection schema is invalid")
    require(set(colors["normal"]) == set(COLOR_NAMES), "Alacritty normal palette is incomplete")
    require(set(colors["bright"]) == set(COLOR_NAMES), "Alacritty bright palette is incomplete")

    terminal = palette["terminal"]
    expected = {
        "primary": {"background": terminal["background"], "foreground": terminal["foreground"]},
        "cursor": {"text": terminal["cursorText"], "cursor": terminal["cursor"]},
        "selection": {"text": "CellForeground", "background": terminal["selection"]["color"]},
        "normal": dict(zip(COLOR_NAMES, terminal["ansi"], strict=True)),
        "bright": dict(zip(COLOR_NAMES, terminal["bright"], strict=True)),
    }
    require(colors == expected, "Alacritty theme drift")
    for section_name, section in colors.items():
        for name, value in section.items():
            if section_name == "selection" and name == "text":
                require(value == "CellForeground", "selection text must preserve the cell foreground")
            else:
                validate_hex(value, f"colors.{section_name}.{name}")


def main() -> int:
    try:
        palette = load_json(PALETTE_PATH)
        validate_palette(palette)
        with ARTIFACT_PATH.open("rb") as handle:
            theme = tomllib.load(handle)
        validate_theme(theme, palette)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], check=True)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        return 1
    print("Alacritty Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
