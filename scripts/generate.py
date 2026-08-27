#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import REPOSITORIES, ROOT


def generate(repository: str, check: bool) -> None:
    script = ROOT / repository / "scripts" / "generate.py"
    if not script.exists():
        raise FileNotFoundError(f"{repository}: missing scripts/generate.py")
    command = [sys.executable, str(script)]
    if check:
        command.append("--check")
    subprocess.run(command, cwd=ROOT / repository, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate every Apollo application theme")
    parser.add_argument("--check", action="store_true", help="fail if committed artifacts differ")
    parser.add_argument("--repo", choices=REPOSITORIES, action="append", help="limit generation to a repository")
    args = parser.parse_args()

    selected = tuple(args.repo or REPOSITORIES)
    for repository in selected:
        generate(repository, args.check)
        print(f"{repository}: {'current' if args.check else 'generated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
