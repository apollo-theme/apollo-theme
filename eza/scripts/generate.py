#!/usr/bin/env python3
"""Generate both eza Apollo theme.yml variants from bundled palettes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "dark": {
        "palette": ROOT / "palette" / "apollo.json",
        "output": ROOT / "theme.yml",
        "sha256": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
        "id": "apollo",
        "name": "Apollo",
        "palette_file": "apollo.json",
    },
    "light": {
        "palette": ROOT / "palette" / "apollo-light.json",
        "output": ROOT / "light" / "theme.yml",
        "sha256": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        "id": "apollo-light",
        "name": "Apollo Light",
        "palette_file": "apollo-light.json",
    },
}


def load_palette(variant: str = "dark") -> dict:
    config = VARIANTS[variant]
    raw = config["palette"].read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != config["sha256"]:
        raise ValueError(f"{variant} palette snapshot hash mismatch: {digest}")
    palette = json.loads(raw)
    if palette.get("id") != config["id"] or palette.get("schemaVersion") != 1:
        raise ValueError(f"unsupported Apollo {variant} palette snapshot")
    return palette


def resolve_role(palette: dict, role: str) -> str:
    reference = palette["roles"][role]
    if not (reference.startswith("{colors.") and reference.endswith("}")):
        raise ValueError(f"role {role!r} is not a color reference")
    return palette["colors"][reference[8:-1]]


def render(palette: dict, variant: str = "dark") -> str:
    role = lambda name: resolve_role(palette, name)
    colors = palette["colors"]
    config = VARIANTS[variant]
    return f'''# {config["name"]} for eza
# Generated from palette/{config["palette_file"]} by scripts/generate.py; do not edit.
# This file overrides eza UI/file-kind styles. Existing LS_COLORS/EZA_COLORS
# still apply afterwards and retain their normal precedence.
colourful: true
filekinds:
  normal: {{foreground: "{role("textPrimary")}"}}
  directory: {{foreground: "{role("information")}", is_bold: true}}
  symlink: {{foreground: "{colors["cyan"]}"}}
  pipe: {{foreground: "{role("warning")}"}}
  block_device: {{foreground: "{colors["magenta"]}"}}
  char_device: {{foreground: "{colors["magenta"]}"}}
  socket: {{foreground: "{role("success")}"}}
  special: {{foreground: "{role("warning")}"}}
  executable: {{foreground: "{role("success")}", is_bold: true}}
  mount_point: {{foreground: "{role("information")}", is_bold: true}}
perms:
  user_read: {{foreground: "{role("textPrimary")}"}}
  user_write: {{foreground: "{role("warning")}"}}
  user_execute_file: {{foreground: "{role("success")}"}}
  user_execute_other: {{foreground: "{role("success")}"}}
  group_read: {{foreground: "{role("textSecondary")}"}}
  group_write: {{foreground: "{role("warning")}"}}
  group_execute: {{foreground: "{role("success")}"}}
  other_read: {{foreground: "{role("textInactive")}"}}
  other_write: {{foreground: "{role("error")}"}}
  other_execute: {{foreground: "{role("success")}"}}
  special_user_file: {{foreground: "{role("error")}", is_bold: true}}
  special_other: {{foreground: "{role("warning")}", is_bold: true}}
  attribute: {{foreground: "{colors["cyan"]}"}}
size:
  major: {{foreground: "{colors["magenta"]}"}}
  minor: {{foreground: "{colors["magenta"]}"}}
  number_byte: {{foreground: "{role("textInactive")}"}}
  number_kilo: {{foreground: "{role("textPrimary")}"}}
  number_mega: {{foreground: "{role("information")}"}}
  number_giga: {{foreground: "{role("warning")}"}}
  number_huge: {{foreground: "{role("error")}"}}
  unit_byte: {{foreground: "{role("textInactive")}"}}
  unit_kilo: {{foreground: "{role("textInactive")}"}}
  unit_mega: {{foreground: "{role("textSecondary")}"}}
  unit_giga: {{foreground: "{role("warning")}"}}
  unit_huge: {{foreground: "{role("error")}"}}
users:
  user_you: {{foreground: "{role("focus")}"}}
  user_root: {{foreground: "{role("error")}", is_bold: true}}
  user_other: {{foreground: "{role("textSecondary")}"}}
  group_yours: {{foreground: "{colors["cyan"]}"}}
  group_other: {{foreground: "{role("textInactive")}"}}
  group_root: {{foreground: "{role("error")}"}}
links:
  normal: {{foreground: "{role("textInactive")}"}}
  multi_link_file: {{foreground: "{role("information")}"}}
git:
  new: {{foreground: "{role("success")}"}}
  modified: {{foreground: "{role("warning")}"}}
  deleted: {{foreground: "{role("error")}"}}
  renamed: {{foreground: "{colors["cyan"]}"}}
  typechange: {{foreground: "{colors["magenta"]}"}}
  ignored: {{foreground: "{role("textInactive")}"}}
  conflicted: {{foreground: "{role("error")}", is_bold: true}}
git_repo:
  branch_main: {{foreground: "{role("focus")}", is_bold: true}}
  branch_other: {{foreground: "{role("information")}"}}
  git_clean: {{foreground: "{role("success")}"}}
  git_dirty: {{foreground: "{role("warning")}"}}
file_type:
  image: {{foreground: "{colors["magenta"]}"}}
  video: {{foreground: "{colors["magenta"]}"}}
  music: {{foreground: "{colors["cyan"]}"}}
  lossless: {{foreground: "{colors["cyan"]}"}}
  crypto: {{foreground: "{role("error")}"}}
  document: {{foreground: "{role("textSecondary")}"}}
  compressed: {{foreground: "{role("warning")}"}}
  temp: {{foreground: "{role("textInactive")}"}}
  compiled: {{foreground: "{role("error")}"}}
  build: {{foreground: "{role("warning")}"}}
  source: {{foreground: "{role("information")}"}}
punctuation: {{foreground: "{role("textInactive")}"}}
date: {{foreground: "{role("textSecondary")}"}}
inode: {{foreground: "{role("textInactive")}"}}
blocks: {{foreground: "{role("textInactive")}"}}
header: {{foreground: "{role("focus")}", is_bold: true}}
octal: {{foreground: "{colors["magenta"]}"}}
flags: {{foreground: "{colors["cyan"]}"}}
symlink_path: {{foreground: "{colors["cyan"]}"}}
control_char: {{foreground: "{role("error")}"}}
broken_symlink: {{foreground: "{role("error")}"}}
broken_path_overlay: {{foreground: "{role("error")}", is_underline: true}}
'''


def render_outputs() -> dict[Path, str]:
    return {
        config["output"]: render(load_palette(variant), variant)
        for variant, config in VARIANTS.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if either eza theme is stale")
    args = parser.parse_args()
    expected = render_outputs()
    if args.check:
        stale = [
            path.relative_to(ROOT)
            for path, text in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != text
        ]
        if stale:
            print("stale generated file(s): " + ", ".join(map(str, stale)))
            return 1
        print("eza theme variants are up to date")
        return 0
    for path, text in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
