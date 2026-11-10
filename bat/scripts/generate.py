#!/usr/bin/env python3
"""Generate both Apollo TextMate themes from bundled palette snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "dark": {
        "palette": ROOT / "palette" / "apollo.json",
        "output": ROOT / "Apollo.tmTheme",
        "sha256": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
        "id": "apollo",
        "name": "Apollo",
        "semantic_class": "theme.dark.apollo",
    },
    "light": {
        "palette": ROOT / "palette" / "apollo-light.json",
        "output": ROOT / "Apollo Light.tmTheme",
        "sha256": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        "id": "apollo-light",
        "name": "Apollo Light",
        "semantic_class": "theme.light.apollo-light",
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


def render(palette: dict, variant: str = "dark") -> bytes:
    role = lambda name: resolve_role(palette, name)
    colors = palette["colors"]
    config = VARIANTS[variant]

    def rule(name: str, scope: str, foreground: str, font_style: str = "") -> dict:
        settings = {"foreground": foreground}
        if font_style:
            settings["fontStyle"] = font_style
        return {"name": name, "scope": scope, "settings": settings}

    theme = {
        "name": config["name"],
        "author": "D0n9X1n",
        "semanticClass": config["semantic_class"],
        "settings": [
            {
                "settings": {
                    "background": role("canvas"),
                    "caret": role("cursor"),
                    "foreground": role("textPrimary"),
                    "invisibles": role("textInactive"),
                    "lineHighlight": colors["surface"],
                    "selection": role("selection"),
                    "selectionForeground": role("textPrimary"),
                }
            },
            rule("Comments", "comment, punctuation.definition.comment", role("textInactive"), "italic"),
            rule("Strings", "string, constant.other.symbol", role("success")),
            rule("Numbers and constants", "constant.numeric, constant.language, constant.character", colors["magenta"]),
            rule("Keywords", "keyword, storage.modifier", role("information")),
            rule("Operators", "keyword.operator, punctuation.separator, punctuation.terminator", role("textSecondary")),
            rule("Functions", "entity.name.function, support.function", role("focus")),
            rule("Parameters", "variable.parameter", colors["magenta"]),
            rule("Variables", "variable, meta.definition.variable", role("textPrimary")),
            rule("Types", "entity.name.type, entity.name.class, support.type, storage.type", colors["cyan"]),
            rule("Properties", "variable.other.property, support.variable.property", colors["cyan"]),
            rule("Tags", "entity.name.tag", role("information")),
            rule("Attributes", "entity.other.attribute-name", role("focus")),
            rule("Headings", "markup.heading", role("focus"), "bold"),
            rule("Bold", "markup.bold", role("textSecondary"), "bold"),
            rule("Italic", "markup.italic", role("textSecondary"), "italic"),
            rule("Links", "markup.underline.link", role("information"), "underline"),
            rule("Inserted", "markup.inserted", role("success")),
            rule("Changed", "markup.changed", role("warning")),
            rule("Deleted and invalid", "markup.deleted, invalid", role("error")),
        ],
    }
    return plistlib.dumps(theme, fmt=plistlib.FMT_XML, sort_keys=False)


def render_outputs() -> dict[Path, bytes]:
    return {
        config["output"]: render(load_palette(variant), variant)
        for variant, config in VARIANTS.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if either TextMate theme is stale")
    args = parser.parse_args()
    expected = render_outputs()
    if args.check:
        stale = [
            path.relative_to(ROOT)
            for path, content in expected.items()
            if not path.exists() or path.read_bytes() != content
        ]
        if stale:
            print("stale generated file(s): " + ", ".join(map(str, stale)))
            return 1
        print("bat theme variants are up to date")
        return 0
    for path, content in expected.items():
        path.write_bytes(content)
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
