#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import HEX_COLOR, REPOSITORIES, ROOT, contrast_ratio, iter_hex_colors, load_palette

EXPECTED_ANSI = [
    "#1d2021",
    "#fb4934",
    "#b8bb26",
    "#fabd2f",
    "#83a598",
    "#d3869b",
    "#8ec07c",
    "#d5c4a1",
]
EXPECTED_BRIGHT = [
    "#665c54",
    "#fb4934",
    "#b8bb26",
    "#fabd2f",
    "#83a598",
    "#d3869b",
    "#8ec07c",
    "#fbf1c7",
]


def check_palette() -> None:
    palette = load_palette()
    if palette["terminal"]["ansi"] != EXPECTED_ANSI:
        raise ValueError("canonical ANSI slots changed unexpectedly")
    if palette["terminal"]["bright"] != EXPECTED_BRIGHT:
        raise ValueError("canonical bright slots changed unexpectedly")
    invalid = sorted({color for color in iter_hex_colors(palette) if not HEX_COLOR.fullmatch(color)})
    if invalid:
        raise ValueError(f"invalid lowercase six-digit colors: {', '.join(invalid)}")
    colors = palette["colors"]
    minimum = palette["constraints"]["minimumTextContrast"]
    for role in ("foreground", "foregroundSecondary", "foregroundInactive", "accent"):
        ratio = contrast_ratio(colors[role], colors["background"])
        if ratio < minimum:
            raise ValueError(f"{role} contrast is {ratio:.2f}, below {minimum:.2f}")
    if contrast_ratio(colors["ansiBrightBlack"], colors["background"]) >= minimum:
        raise ValueError("restricted bright black no longer needs its usage constraint")


def check_repository(repository: str) -> None:
    directory = ROOT / repository
    required = ("README.md", "CLAUDE.md", "LICENSE", "palette/apollo.json", "scripts/generate.py", "scripts/check.py")
    missing = [path for path in required if not (directory / path).exists()]
    if missing:
        raise FileNotFoundError(f"{repository}: missing {', '.join(missing)}")
    snapshot = json.loads((directory / "palette" / "apollo.json").read_text(encoding="utf-8"))
    if snapshot != load_palette():
        raise ValueError(f"{repository}: palette snapshot differs from canonical palette")
    subprocess.run([sys.executable, "scripts/generate.py", "--check"], cwd=directory, check=True)
    subprocess.run([sys.executable, "scripts/check.py"], cwd=directory, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Apollo palette and application repositories")
    parser.add_argument("--repo", choices=REPOSITORIES, action="append", help="limit validation to a repository")
    args = parser.parse_args()
    check_palette()
    for repository in tuple(args.repo or REPOSITORIES):
        check_repository(repository)
        print(f"{repository}: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
