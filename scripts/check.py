#!/usr/bin/env python3
"""Validate the Apollo snapshot and generated SonicTerm theme."""

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
EXPECTED_THEME_KEYS = {"name", "appearance", "colors"}
EXPECTED_COLOR_KEYS = {"background", "foreground", "cursor", "cursor_text", "selection_bg", "selection_fg", "ansi", "bright", "tab"}
EXPECTED_TAB_KEYS = {"bar_bg", "active_bg", "active_fg", "inactive_bg", "inactive_fg", "hover_bg", "hover_fg", "close_button_fg"}


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
    selection = terminal["selection"]
    require(set(selection) == {"color", "alpha", "foregroundMode"}, "terminal.selection schema is invalid")
    validate_hex(selection["color"], "terminal.selection.color")
    require(selection["alpha"] == 0.5 and selection["foregroundMode"] == "preserve", "selection semantics changed")
    for group in ("ansi", "bright"):
        require(isinstance(terminal[group], list) and len(terminal[group]) == 8, f"terminal.{group} must contain eight colors")
        for index, value in enumerate(terminal[group]):
            validate_hex(value, f"terminal.{group}[{index}]")

    require(terminal["foreground"] == colors["foreground"], "terminal foreground must match colors.foreground")
    require(terminal["background"] == colors["background"], "terminal background must match colors.background")
    require(terminal["cursor"] == colors["accent"], "terminal cursor must match colors.accent")
    require(terminal["cursorText"] == colors["background"], "terminal cursorText must match colors.background")
    require(terminal["selection"]["color"] == colors["selection"], "terminal selection must match colors.selection")


def validate_theme(theme: dict[str, Any], palette: dict[str, Any]) -> None:
    require(set(theme) == EXPECTED_THEME_KEYS, "SonicTerm theme has unknown or missing top-level keys")
    require(theme["name"] == "Apollo" and theme["appearance"] == "dark", "SonicTerm metadata is invalid")
    colors = theme["colors"]
    require(set(colors) == EXPECTED_COLOR_KEYS, "SonicTerm [colors] schema is incomplete")
    require(set(colors["ansi"]) == set(COLOR_NAMES), "SonicTerm ANSI schema is incomplete")
    require(set(colors["bright"]) == set(COLOR_NAMES), "SonicTerm bright schema is incomplete")
    require(set(colors["tab"]) == EXPECTED_TAB_KEYS, "SonicTerm tab schema is incomplete")

    terminal = palette["terminal"]
    canonical = palette["colors"]
    require(colors["background"] == terminal["background"], "background drift")
    require(colors["foreground"] == terminal["foreground"], "foreground drift")
    require(colors["cursor"] == terminal["cursor"], "cursor drift")
    require(colors["cursor_text"] == terminal["cursorText"], "cursor text drift")
    require(colors["selection_bg"] == terminal["selection"]["color"], "selection drift")
    require(colors["selection_fg"] == canonical["foregroundSecondary"], "selection foreground drift")
    require([colors["ansi"][name] for name in COLOR_NAMES] == terminal["ansi"], "ANSI palette drift")
    require([colors["bright"][name] for name in COLOR_NAMES] == terminal["bright"], "bright palette drift")
    require(
        colors["tab"]
        == {
            "bar_bg": canonical["background"],
            "active_bg": canonical["background"],
            "active_fg": canonical["accent"],
            "inactive_bg": canonical["background"],
            "inactive_fg": canonical["foregroundInactive"],
            "hover_bg": canonical["surfaceHover"],
            "hover_fg": canonical["foregroundSecondary"],
            "close_button_fg": canonical["accent"],
        },
        "tab palette drift",
    )
    for section_name in ("ansi", "bright", "tab"):
        for name, value in colors[section_name].items():
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
    print("SonicTerm Apollo theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
