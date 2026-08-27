#!/usr/bin/env python3
"""Run repository checks without third-party dependencies."""

from __future__ import annotations

import json
import plistlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "Apollo.itermcolors"


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    json.loads((ROOT / "palette" / "apollo.json").read_text(encoding="utf-8"))
    plistlib.loads(THEME.read_bytes())
    run([sys.executable, "scripts/generate.py", "--check"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if sys.platform == "darwin":
        run(["plutil", "-lint", str(THEME)])
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
