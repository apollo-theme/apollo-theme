#!/usr/bin/env python3
"""Run repository checks for both Apple Terminal Apollo variants."""

from __future__ import annotations

import json
import plistlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTES = (ROOT / "palette" / "apollo.json", ROOT / "palette" / "apollo-light.json")
THEMES = (ROOT / "Apollo.terminal", ROOT / "Apollo Light.terminal")


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    for palette in PALETTES:
        json.loads(palette.read_text(encoding="utf-8"))
    for theme in THEMES:
        profile = plistlib.loads(theme.read_bytes())
        for key, value in profile.items():
            if key.endswith("Color"):
                plistlib.loads(value)
    run([sys.executable, "scripts/generate.py", "--check"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if sys.platform == "darwin":
        run(["plutil", "-lint", *(str(theme) for theme in THEMES)])
    print("all dark and light checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
