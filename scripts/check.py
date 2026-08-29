#!/usr/bin/env python3
"""Validate both Apollo snapshots and generated SonicTerm themes."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = (
    ("apollo", "Apollo", "dark", 0.5, ROOT / "palette" / "apollo.json", ROOT / "apollo.toml"),
    ("apollo-light", "Apollo Light", "light", 1.0, ROOT / "palette" / "apollo-light.json", ROOT / "apollo-light.toml"),
)
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
    require(isinstance(value, dict), f"{path.name} root must be an object")
    return value


def validate_hex(value: Any, label: str) -> None:
    require(isinstance(value, str) and HEX_COLOR.fullmatch(value) is not None, f"{label} must be lowercase #rrggbb")


def validate_palette(palette: dict[str, Any], palette_id: str, name: str, appearance: str, alpha: float) -> None:
    require(set(palette) == EXPECTED_TOP_LEVEL, f"{palette_id} top-level schema does not match schemaVersion 1")
    require(palette["schemaVersion"] == 1, f"{palette_id} has unsupported schemaVersion")
    require((palette["id"], palette["name"], palette["appearance"]) == (palette_id, name, appearance), f"{palette_id} identity or appearance is invalid")
    require(palette["colorSpace"] == "srgb", f"{palette_id} color space is invalid")
    colors = palette["colors"]
    require(isinstance(colors, dict) and colors, f"{palette_id} colors must be a non-empty object")
    for color_name, value in colors.items():
        validate_hex(value, f"{palette_id}.colors.{color_name}")

    terminal = palette["terminal"]
    require(set(terminal) == {"foreground", "background", "cursor", "cursorText", "selection", "ansi", "bright"}, f"{palette_id} terminal schema is invalid")
    for field in ("foreground", "background", "cursor", "cursorText"):
        validate_hex(terminal[field], f"{palette_id}.terminal.{field}")
    selection = terminal["selection"]
    require(set(selection) == {"color", "alpha", "foregroundMode"}, f"{palette_id} selection schema is invalid")
    validate_hex(selection["color"], f"{palette_id}.terminal.selection.color")
    require(selection["alpha"] == alpha and selection["foregroundMode"] == "preserve", f"{palette_id} selection semantics changed")
    for group in ("ansi", "bright"):
        require(isinstance(terminal[group], list) and len(terminal[group]) == 8, f"{palette_id} terminal.{group} must contain eight colors")
        for index, value in enumerate(terminal[group]):
            validate_hex(value, f"{palette_id}.terminal.{group}[{index}]")
    require(terminal["foreground"] == colors["foreground"], f"{palette_id} foreground role drift")
    require(terminal["background"] == colors["background"], f"{palette_id} background role drift")
    require(terminal["cursor"] == colors["accent"], f"{palette_id} cursor role drift")
    require(terminal["cursorText"] == colors["background"], f"{palette_id} cursor text role drift")
    require(selection["color"] == colors["selection"], f"{palette_id} selection role drift")


def validate_theme(theme: dict[str, Any], palette: dict[str, Any]) -> None:
    require(set(theme) == EXPECTED_THEME_KEYS, "SonicTerm theme has unknown or missing top-level keys")
    require(theme["name"] == palette["name"] and theme["appearance"] == palette["appearance"], f"{palette['id']} SonicTerm metadata is invalid")
    colors = theme["colors"]
    require(set(colors) == EXPECTED_COLOR_KEYS, f"{palette['id']} SonicTerm [colors] schema is incomplete")
    require(set(colors["ansi"]) == set(COLOR_NAMES), f"{palette['id']} SonicTerm ANSI schema is incomplete")
    require(set(colors["bright"]) == set(COLOR_NAMES), f"{palette['id']} SonicTerm bright schema is incomplete")
    require(set(colors["tab"]) == EXPECTED_TAB_KEYS, f"{palette['id']} SonicTerm tab schema is incomplete")

    terminal = palette["terminal"]
    canonical = palette["colors"]
    require(colors["background"] == terminal["background"], f"{palette['id']} background drift")
    require(colors["foreground"] == terminal["foreground"], f"{palette['id']} foreground drift")
    require(colors["cursor"] == terminal["cursor"], f"{palette['id']} cursor drift")
    require(colors["cursor_text"] == terminal["cursorText"], f"{palette['id']} cursor text drift")
    require(colors["selection_bg"] == terminal["selection"]["color"], f"{palette['id']} selection drift")
    require(colors["selection_fg"] == canonical["foregroundSecondary"], f"{palette['id']} selection foreground drift")
    require([colors["ansi"][name] for name in COLOR_NAMES] == terminal["ansi"], f"{palette['id']} ANSI palette drift")
    require([colors["bright"][name] for name in COLOR_NAMES] == terminal["bright"], f"{palette['id']} bright palette drift")
    require(colors["tab"] == {
        "bar_bg": canonical["background"],
        "active_bg": canonical["background"],
        "active_fg": canonical["accent"],
        "inactive_bg": canonical["background"],
        "inactive_fg": canonical["foregroundInactive"],
        "hover_bg": canonical["surfaceHover"],
        "hover_fg": canonical["foregroundSecondary"],
        "close_button_fg": canonical["accent"],
    }, f"{palette['id']} tab palette drift")


def main() -> int:
    try:
        for palette_id, name, appearance, alpha, palette_path, artifact_path in VARIANTS:
            palette = load_json(palette_path)
            validate_palette(palette, palette_id, name, appearance, alpha)
            with artifact_path.open("rb") as handle:
                validate_theme(tomllib.load(handle), palette)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], check=True)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        return 1
    print("SonicTerm Apollo dark and light theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
