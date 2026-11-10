#!/usr/bin/env python3
"""Validate both Apollo snapshots and generated WezTerm color schemes."""

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
    require(isinstance(value, dict), f"{path.name} root must be an object")
    return value


def validate_hex(value: Any, label: str) -> None:
    require(isinstance(value, str) and HEX_COLOR.fullmatch(value) is not None, f"{label} must be lowercase #rrggbb")


def rgba(color: str, alpha: float) -> str:
    red, green, blue = (int(color[offset : offset + 2], 16) for offset in (1, 3, 5))
    return f"rgba({red}, {green}, {blue}, {alpha:g})"


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


def validate_scheme(scheme: dict[str, Any], palette: dict[str, Any]) -> None:
    require(set(scheme) == {"colors", "metadata"}, "WezTerm scheme has unknown or missing sections")
    colors = scheme["colors"]
    metadata = scheme["metadata"]
    require(set(colors) == EXPECTED_COLOR_KEYS, f"{palette['id']} WezTerm [colors] schema is incomplete")
    require(set(metadata) == EXPECTED_METADATA_KEYS, f"{palette['id']} WezTerm [metadata] schema is incomplete")
    require(metadata == {"name": palette["name"], "author": "D0n9X1n", "origin_url": REPOSITORY_URL}, f"{palette['id']} WezTerm metadata drift")
    terminal = palette["terminal"]
    require(colors == {
        "foreground": terminal["foreground"],
        "background": terminal["background"],
        "cursor_fg": terminal["cursorText"],
        "cursor_bg": terminal["cursor"],
        "cursor_border": terminal["cursor"],
        "selection_fg": "none",
        "selection_bg": rgba(terminal["selection"]["color"], terminal["selection"]["alpha"]),
        "ansi": terminal["ansi"],
        "brights": terminal["bright"],
    }, f"{palette['id']} WezTerm color scheme drift")


def validate_example() -> None:
    text = EXAMPLE_PATH.read_text(encoding="utf-8")
    require("config.color_scheme = 'Apollo'" in text, "wezterm.lua must keep activating dark Apollo")
    require("config.color_scheme_dirs" not in text, "example should use the standard colors directory")


def main() -> int:
    try:
        for palette_id, name, appearance, alpha, palette_path, artifact_path in VARIANTS:
            palette = load_json(palette_path)
            validate_palette(palette, palette_id, name, appearance, alpha)
            with artifact_path.open("rb") as handle:
                validate_scheme(tomllib.load(handle), palette)
        validate_example()
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"], check=True)
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        return 1
    print("WezTerm Apollo dark and light theme checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
