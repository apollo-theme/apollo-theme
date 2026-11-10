#!/usr/bin/env python3
"""Generate Apollo.xccolortheme from the repository palette snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PALETTE_SHA256 = {
    "apollo": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
    "apollo-light": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
}
VARIANTS = {
    "apollo": ("dark", ROOT / "palette" / "apollo.json", ROOT / "Apollo.xccolortheme"),
    "apollo-light": ("light", ROOT / "palette" / "apollo-light.json", ROOT / "Apollo Light.xccolortheme"),
}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

SYNTAX_COLOR_KEYS = {
    "xcode.syntax.attribute": "accent",
    "xcode.syntax.character": "success",
    "xcode.syntax.comment": "foregroundInactive",
    "xcode.syntax.comment.doc": "foregroundInactive",
    "xcode.syntax.comment.doc.keyword": "cyan",
    "xcode.syntax.declaration.other": "cyan",
    "xcode.syntax.declaration.type": "accent",
    "xcode.syntax.identifier.class": "accent",
    "xcode.syntax.identifier.class.system": "cyan",
    "xcode.syntax.identifier.constant": "magenta",
    "xcode.syntax.identifier.constant.system": "magenta",
    "xcode.syntax.identifier.function": "cyan",
    "xcode.syntax.identifier.function.system": "info",
    "xcode.syntax.identifier.macro": "accent",
    "xcode.syntax.identifier.macro.system": "accent",
    "xcode.syntax.identifier.type": "accent",
    "xcode.syntax.identifier.type.system": "cyan",
    "xcode.syntax.identifier.variable": "foreground",
    "xcode.syntax.identifier.variable.system": "foregroundSecondary",
    "xcode.syntax.keyword": "danger",
    "xcode.syntax.mark": "accent",
    "xcode.syntax.markup.aside.kind": "info",
    "xcode.syntax.markup.code": "magenta",
    "xcode.syntax.number": "magenta",
    "xcode.syntax.plain": "foreground",
    "xcode.syntax.preprocessor": "magenta",
    "xcode.syntax.string": "success",
    "xcode.syntax.url": "info",
}

BOLD_SYNTAX_ROLES = {
    "xcode.syntax.comment.doc.keyword",
    "xcode.syntax.keyword",
    "xcode.syntax.mark",
}
MEDIUM_SYNTAX_ROLES = {
    "xcode.syntax.attribute",
    "xcode.syntax.declaration.other",
    "xcode.syntax.declaration.type",
    "xcode.syntax.identifier.class",
    "xcode.syntax.identifier.class.system",
    "xcode.syntax.identifier.function",
    "xcode.syntax.identifier.function.system",
    "xcode.syntax.identifier.type",
    "xcode.syntax.identifier.type.system",
}


def load_palette(variant: str) -> dict:
    appearance, palette_path, _ = VARIANTS[variant]
    palette_bytes = palette_path.read_bytes()
    digest = hashlib.sha256(palette_bytes).hexdigest()
    if digest != PALETTE_SHA256[variant]:
        raise ValueError(f"{palette_path.relative_to(ROOT)} differs from canonical SHA-256: {digest}")
    palette = json.loads(palette_bytes)
    if palette.get("schemaVersion") != 1 or palette.get("id") != variant:
        raise ValueError(f"{palette_path.relative_to(ROOT)} has invalid identity")
    if palette.get("appearance") != appearance or palette.get("colorSpace") != "srgb":
        raise ValueError(f"{palette_path.relative_to(ROOT)} must be the {appearance} sRGB variant")
    return palette


def number(value: float) -> str:
    rendered = f"{value:.6f}".rstrip("0").rstrip(".")
    return rendered or "0"


def rgba(hex_color: str, alpha: float = 1.0) -> str:
    if not HEX_COLOR.fullmatch(hex_color):
        raise ValueError(f"invalid sRGB color: {hex_color!r}")
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    return " ".join(number(channel) for channel in (*channels, alpha))


def syntax_font(role: str) -> str:
    if role in BOLD_SYNTAX_ROLES:
        return "SFMono-Bold - 12.0"
    if role in MEDIUM_SYNTAX_ROLES:
        return "SFMono-Medium - 12.0"
    return "SFMono-Regular - 12.0"


def render(palette: dict) -> bytes:
    colors = palette["colors"]
    c = lambda key, alpha=1.0: rgba(colors[key], alpha)

    syntax_colors = {
        role: c(color_key) for role, color_key in SYNTAX_COLOR_KEYS.items()
    }
    syntax_fonts = {role: syntax_font(role) for role in SYNTAX_COLOR_KEYS}

    # The top-level keys and syntax roles mirror the complete Xcode 26.6 built-in
    # High Contrast (Dark) schema. Only theme data is emitted; no preferences.
    theme = {
        "DVTConsoleDebuggerInputTextColor": c("foreground"),
        "DVTConsoleDebuggerInputTextFont": "SFMono-Regular - 12.0",
        "DVTConsoleDebuggerOutputTextColor": c("foregroundSecondary"),
        "DVTConsoleDebuggerOutputTextFont": "SFMono-Regular - 12.0",
        "DVTConsoleDebuggerPromptTextColor": c("success"),
        "DVTConsoleDebuggerPromptTextFont": "SFMono-Medium - 12.0",
        "DVTConsoleExectuableInputTextColor": c("foreground"),
        "DVTConsoleExectuableInputTextFont": "SFMono-Regular - 12.0",
        "DVTConsoleExectuableOutputTextColor": c("foregroundSecondary"),
        "DVTConsoleExectuableOutputTextFont": "SFMono-Regular - 12.0",
        "DVTConsoleTextBackgroundColor": c("background"),
        "DVTConsoleTextInsertionPointColor": c("accent"),
        "DVTConsoleTextSelectionColor": c("selection"),
        "DVTFontAndColorVersion": 1,
        "DVTLineSpacing": 1.1,
        "DVTMarkupTextBackgroundColor": c("surface"),
        "DVTMarkupTextBorderColor": c("selection"),
        "DVTMarkupTextCodeFont": "SFMono-Regular - 10.0",
        "DVTMarkupTextEmphasisColor": c("foregroundSecondary"),
        "DVTMarkupTextEmphasisFont": ".AppleSystemUIFontItalic - 10.0",
        "DVTMarkupTextInlineCodeColor": c("magenta"),
        "DVTMarkupTextLinkColor": c("info"),
        "DVTMarkupTextLinkFont": ".AppleSystemUIFont - 10.0",
        "DVTMarkupTextNormalColor": c("foreground"),
        "DVTMarkupTextNormalFont": ".AppleSystemUIFont - 10.0",
        "DVTMarkupTextOtherHeadingColor": c("foregroundSecondary"),
        "DVTMarkupTextOtherHeadingFont": ".AppleSystemUIFont - 14.0",
        "DVTMarkupTextPrimaryHeadingColor": c("foregroundBright"),
        "DVTMarkupTextPrimaryHeadingFont": ".AppleSystemUIFont - 24.0",
        "DVTMarkupTextSecondaryHeadingColor": c("foregroundSecondary"),
        "DVTMarkupTextSecondaryHeadingFont": ".AppleSystemUIFont - 18.0",
        "DVTMarkupTextStrongColor": c("foregroundBright"),
        "DVTMarkupTextStrongFont": ".AppleSystemUIFontBold - 10.0",
        "DVTScrollbarMarkerAnalyzerColor": c("info"),
        "DVTScrollbarMarkerBreakpointColor": c("accent"),
        "DVTScrollbarMarkerDiffColor": c("success"),
        "DVTScrollbarMarkerDiffConflictColor": c("danger"),
        "DVTScrollbarMarkerErrorColor": c("danger"),
        "DVTScrollbarMarkerRuntimeIssueColor": c("magenta"),
        "DVTScrollbarMarkerWarningColor": c("accent"),
        "DVTSourceTextBackground": c("background"),
        "DVTSourceTextBlockDimBackgroundColor": c("surfaceHover"),
        "DVTSourceTextCurrentLineHighlightColor": c("surface"),
        "DVTSourceTextInsertionPointColor": c("accent"),
        "DVTSourceTextInvisiblesColor": c("foregroundSecondary"),
        "DVTSourceTextSelectionColor": c("selection"),
        "DVTSourceTextSyntaxColors": syntax_colors,
        "DVTSourceTextSyntaxFonts": syntax_fonts,
    }
    return plistlib.dumps(theme, fmt=plistlib.FMT_XML, sort_keys=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of writing when the committed theme is stale",
    )
    args = parser.parse_args()

    try:
        outputs = {
            output_path: render(load_palette(variant))
            for variant, (_, _, output_path) in VARIANTS.items()
        }
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"generation failed: {error}", file=sys.stderr)
        return 2

    unexpected = sorted(set(ROOT.glob("*.xccolortheme")) - set(outputs))
    if unexpected:
        for path in unexpected:
            print(f"unexpected generated output: {path.name}", file=sys.stderr)
        return 1

    stale = [
        path for path, generated in outputs.items()
        if not path.exists() or path.read_bytes() != generated
    ] if args.check else []
    if stale:
        for path in stale:
            print(f"out of date: {path.name}", file=sys.stderr)
        return 1
    if args.check:
        print("up to date: " + ", ".join(path.name for path in outputs))
        return 0

    for path, generated in outputs.items():
        path.write_bytes(generated)
        print(f"generated: {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
