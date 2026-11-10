#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import ROOT, SLUGS


def generate(slug: str, check: bool) -> None:
    script = ROOT / slug / "scripts" / "generate.py"
    if not script.exists():
        raise FileNotFoundError(f"{slug}: missing scripts/generate.py")
    command = [sys.executable, str(script)]
    if check:
        command.append("--check")
    subprocess.run(command, cwd=ROOT / slug, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate every Apollo application theme")
    parser.add_argument("--check", action="store_true", help="fail if committed artifacts differ")
    parser.add_argument("--app", choices=SLUGS, action="append", help="limit generation to an app folder")
    args = parser.parse_args()

    selected = tuple(args.app or SLUGS)
    for slug in selected:
        generate(slug, args.check)
        print(f"{slug}: {'current' if args.check else 'generated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
