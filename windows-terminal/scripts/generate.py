#!/usr/bin/env python3
"""Generate the Windows Terminal Apollo schemes from the palette snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = {
    ROOT / "apollo.json": ROOT / "palette" / "apollo.json",
    ROOT / "apollo-light.json": ROOT / "palette" / "apollo-light.json",
}
NORMAL_NAMES = ("black", "red", "green", "yellow", "blue", "purple", "cyan", "white")
BRIGHT_NAMES = ("brightBlack", "brightRed", "brightGreen", "brightYellow", "brightBlue", "brightPurple", "brightCyan", "brightWhite")


def load_palette(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_scheme(palette: dict[str, Any]) -> OrderedDict[str, str]:
    terminal = palette["terminal"]
    scheme: OrderedDict[str, str] = OrderedDict(
        (
            ("name", palette["name"]),
            ("background", terminal["background"]),
            ("foreground", terminal["foreground"]),
            ("cursorColor", terminal["cursor"]),
            ("selectionBackground", terminal["selection"]["color"]),
        )
    )
    scheme.update(zip(NORMAL_NAMES, terminal["ansi"], strict=True))
    scheme.update(zip(BRIGHT_NAMES, terminal["bright"], strict=True))
    return scheme


def render(palette: dict[str, Any]) -> str:
    return json.dumps(build_scheme(palette), indent=2, ensure_ascii=True) + "\n"


def render_outputs() -> dict[Path, str]:
    return {output_path: render(load_palette(palette_path)) for output_path, palette_path in OUTPUTS.items()}


def find_unexpected_outputs(root: Path = ROOT) -> list[Path]:
    expected_names = {path.name for path in OUTPUTS}
    return sorted(path for path in root.glob("*.json") if path.name not in expected_names)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated schemes are stale")
    args = parser.parse_args()
    rendered_outputs = render_outputs()

    if args.check:
        failed = False
        for path in find_unexpected_outputs():
            print(f"unexpected generated artifact: {path.name}", file=sys.stderr)
            failed = True
        for output_path, rendered in rendered_outputs.items():
            try:
                current = output_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                print(f"missing generated artifact: {output_path.name}", file=sys.stderr)
                failed = True
                continue
            if current != rendered:
                print(f"generated artifact is stale: {output_path.name}", file=sys.stderr)
                failed = True
            else:
                print(f"up to date: {output_path.name}")
        return int(failed)

    for output_path, rendered in rendered_outputs.items():
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"wrote {output_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
