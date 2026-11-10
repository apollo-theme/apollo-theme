#!/usr/bin/env python3
"""Copy both Apollo palettes from an apollo-palette checkout at a ref, pin them, and regenerate every app."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from common import ROOT, SLUGS

PALETTE_REPOSITORY = "https://github.com/apollo-theme/apollo-palette"
PALETTE_FILES = ("apollo.json", "apollo-light.json")


def sync(repo, ref, root=ROOT, slugs=SLUGS, run=subprocess.run) -> str:
    repo, root = Path(repo), Path(root)
    sha = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "-q", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not sha:
        raise LookupError(f"unknown ref {ref}")
    files = {
        name: subprocess.run(["git", "-C", str(repo), "show", f"{sha}:palette/{name}"], capture_output=True, check=True).stdout
        for name in PALETTE_FILES
    }
    for target in (root, *(root / slug for slug in slugs)):
        for name, data in files.items():
            (target / "palette" / name).write_bytes(data)
    pin = {
        "repository": PALETTE_REPOSITORY,
        "commit": sha,
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
    }
    (root / "palette" / "SOURCE.json").write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")
    for slug in slugs:
        run([sys.executable, "scripts/generate.py"], cwd=root / slug, check=True)
    return sha


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Apollo palettes from an apollo-palette checkout")
    parser.add_argument("palette_repo", type=Path, help="path to a local apollo-palette clone")
    parser.add_argument("ref", help="tag, branch, or commit in the palette repository")
    args = parser.parse_args()
    try:
        sha = sync(args.palette_repo, args.ref)
    except LookupError as error:
        print(error, file=sys.stderr)
        return 2
    print(f"palette pinned to {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
