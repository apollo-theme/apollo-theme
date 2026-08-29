#!/usr/bin/env python3
"""Generate the Apollo Vim colorscheme from the bundled palette snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PALETTE_SHA256 = {
    "apollo": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
    "apollo-light": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
}
VARIANT_PATHS = {
    "apollo": (ROOT / "palette" / "apollo.json", ROOT / "colors" / "apollo.vim"),
    "apollo-light": (ROOT / "palette" / "apollo-light.json", ROOT / "colors" / "apollo-light.vim"),
}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
OBSOLETE_COLORS = {
    "#ebdbb2",
    "#cc241d",
    "#98971a",
    "#d79921",
    "#458588",
    "#b16286",
    "#689d6a",
    "#d4be98",
}

COLOR_KEYS = (
    ("bg", "background"),
    ("surface", "surface"),
    ("surface_hover", "surfaceHover"),
    ("selection", "selection"),
    ("fg", "foreground"),
    ("fg_secondary", "foregroundSecondary"),
    ("fg_inactive", "foregroundInactive"),
    ("fg_bright", "foregroundBright"),
    ("accent", "accent"),
    ("danger", "danger"),
    ("success", "success"),
    ("info", "info"),
    ("magenta", "magenta"),
    ("cyan", "cyan"),
)

# Independently hand-selected xterm-256 approximations preserve semantic hue.
CTERM_FALLBACKS = {
    "apollo": (233, 234, 234, 237, 180, 187, 245, 230, 214, 203, 142, 109, 175, 108),
    "apollo-light": (230, 230, 223, 187, 237, 239, 59, 235, 94, 124, 58, 24, 95, 23),
}

# group, foreground, background, GUI attributes, cterm attributes, special color
HIGHLIGHTS = (
    ("Normal", "fg", "bg", "NONE", "NONE", None),
    ("NormalNC", "fg", "bg", "NONE", "NONE", None),
    ("NormalFloat", "fg", "surface", "NONE", "NONE", None),
    ("FloatBorder", "selection", "surface", "NONE", "NONE", None),
    ("FloatTitle", "accent", "surface", "bold", "bold", None),
    ("FloatFooter", "fg_inactive", "surface", "NONE", "NONE", None),
    ("Cursor", "bg", "accent", "NONE", "NONE", None),
    ("lCursor", "bg", "accent", "NONE", "NONE", None),
    ("CursorIM", "bg", "info", "NONE", "NONE", None),
    ("TermCursor", "bg", "accent", "reverse", "reverse", None),
    ("TermCursorNC", "fg_inactive", "surface", "NONE", "NONE", None),
    ("CursorLine", None, "surface", "NONE", "NONE", None),
    ("CursorColumn", None, "surface_hover", "NONE", "NONE", None),
    ("CursorLineNr", "accent", "surface", "bold", "bold", None),
    ("CursorLineFold", "accent", "surface", "NONE", "NONE", None),
    ("CursorLineSign", "accent", "surface", "NONE", "NONE", None),
    ("LineNr", "fg_inactive", "bg", "NONE", "NONE", None),
    ("LineNrAbove", "fg_inactive", "bg", "NONE", "NONE", None),
    ("LineNrBelow", "fg_inactive", "bg", "NONE", "NONE", None),
    ("SignColumn", None, "bg", "NONE", "NONE", None),
    ("FoldColumn", "fg_inactive", "bg", "NONE", "NONE", None),
    ("Folded", "fg_inactive", "surface", "italic", "italic", None),
    ("ColorColumn", None, "surface", "NONE", "NONE", None),
    ("WinSeparator", "selection", "bg", "NONE", "NONE", None),
    ("VertSplit", "selection", "bg", "NONE", "NONE", None),
    ("StatusLine", "fg_bright", "selection", "NONE", "NONE", None),
    ("StatusLineNC", "fg_inactive", "surface", "NONE", "NONE", None),
    ("TabLine", "fg_inactive", "surface", "NONE", "NONE", None),
    ("TabLineSel", "accent", "bg", "bold", "bold", None),
    ("TabLineFill", None, "bg", "NONE", "NONE", None),
    ("WinBar", "fg_secondary", "bg", "bold", "bold", None),
    ("WinBarNC", "fg_inactive", "bg", "NONE", "NONE", None),
    ("Pmenu", "fg", "surface", "NONE", "NONE", None),
    ("PmenuSel", "bg", "accent", "bold", "bold", None),
    ("PmenuKind", "magenta", "surface", "NONE", "NONE", None),
    ("PmenuKindSel", "bg", "accent", "bold", "bold", None),
    ("PmenuExtra", "fg_inactive", "surface", "NONE", "NONE", None),
    ("PmenuExtraSel", "bg", "accent", "NONE", "NONE", None),
    ("PmenuSbar", None, "surface_hover", "NONE", "NONE", None),
    ("PmenuThumb", None, "selection", "NONE", "NONE", None),
    ("WildMenu", "bg", "accent", "bold", "bold", None),
    ("Visual", None, "selection", "NONE", "NONE", None),
    ("VisualNOS", None, "selection", "underline", "underline", None),
    ("Search", "bg", "accent", "NONE", "NONE", None),
    ("IncSearch", "bg", "danger", "bold", "bold", None),
    ("CurSearch", "bg", "danger", "bold", "bold", None),
    ("Substitute", "bg", "success", "NONE", "NONE", None),
    ("MatchParen", "accent", "selection", "bold", "bold", None),
    ("NonText", "selection", None, "NONE", "NONE", None),
    ("Whitespace", "selection", None, "NONE", "NONE", None),
    ("SpecialKey", "selection", None, "NONE", "NONE", None),
    ("EndOfBuffer", "bg", "bg", "NONE", "NONE", None),
    ("Directory", "info", None, "NONE", "NONE", None),
    ("Title", "accent", None, "bold", "bold", None),
    ("Conceal", "fg_inactive", None, "NONE", "NONE", None),
    ("Question", "success", None, "NONE", "NONE", None),
    ("MoreMsg", "info", None, "NONE", "NONE", None),
    ("ModeMsg", "accent", None, "bold", "bold", None),
    ("MsgArea", "fg", "bg", "NONE", "NONE", None),
    ("MsgSeparator", "selection", "bg", "NONE", "NONE", None),
    ("ErrorMsg", "danger", None, "bold", "bold", None),
    ("WarningMsg", "accent", None, "bold", "bold", None),
    ("QuickFixLine", "bg", "info", "NONE", "NONE", None),
    ("SpellBad", None, None, "undercurl", "underline", "danger"),
    ("SpellCap", None, None, "undercurl", "underline", "info"),
    ("SpellLocal", None, None, "undercurl", "underline", "cyan"),
    ("SpellRare", None, None, "undercurl", "underline", "magenta"),
    ("Comment", "fg_inactive", None, "italic", "italic", None),
    ("Constant", "magenta", None, "NONE", "NONE", None),
    ("String", "success", None, "NONE", "NONE", None),
    ("Character", "magenta", None, "NONE", "NONE", None),
    ("Number", "magenta", None, "NONE", "NONE", None),
    ("Boolean", "magenta", None, "bold", "bold", None),
    ("Float", "magenta", None, "NONE", "NONE", None),
    ("Identifier", "info", None, "NONE", "NONE", None),
    ("Function", "accent", None, "NONE", "NONE", None),
    ("Statement", "danger", None, "NONE", "NONE", None),
    ("Conditional", "danger", None, "NONE", "NONE", None),
    ("Repeat", "danger", None, "NONE", "NONE", None),
    ("Label", "danger", None, "NONE", "NONE", None),
    ("Operator", "fg_secondary", None, "NONE", "NONE", None),
    ("Keyword", "danger", None, "NONE", "NONE", None),
    ("Exception", "danger", None, "NONE", "NONE", None),
    ("PreProc", "cyan", None, "NONE", "NONE", None),
    ("Include", "cyan", None, "NONE", "NONE", None),
    ("Define", "cyan", None, "NONE", "NONE", None),
    ("Macro", "cyan", None, "NONE", "NONE", None),
    ("PreCondit", "cyan", None, "NONE", "NONE", None),
    ("Type", "accent", None, "NONE", "NONE", None),
    ("StorageClass", "accent", None, "NONE", "NONE", None),
    ("Structure", "accent", None, "NONE", "NONE", None),
    ("Typedef", "accent", None, "NONE", "NONE", None),
    ("Special", "magenta", None, "NONE", "NONE", None),
    ("SpecialChar", "magenta", None, "NONE", "NONE", None),
    ("Tag", "cyan", None, "NONE", "NONE", None),
    ("Delimiter", "fg_secondary", None, "NONE", "NONE", None),
    ("SpecialComment", "cyan", None, "italic", "italic", None),
    ("Debug", "danger", None, "NONE", "NONE", None),
    ("Underlined", "info", None, "underline", "underline", None),
    ("Ignore", "fg_inactive", None, "NONE", "NONE", None),
    ("Error", "danger", None, "bold", "bold", None),
    ("Todo", "bg", "accent", "bold", "bold", None),
    ("Added", "success", None, "NONE", "NONE", None),
    ("Changed", "accent", None, "NONE", "NONE", None),
    ("Removed", "danger", None, "NONE", "NONE", None),
    ("DiffAdd", "success", "surface", "NONE", "NONE", None),
    ("DiffChange", "accent", "surface", "NONE", "NONE", None),
    ("DiffDelete", "danger", "surface", "NONE", "NONE", None),
    ("DiffText", "bg", "accent", "bold", "bold", None),
    ("DiagnosticError", "danger", None, "NONE", "NONE", None),
    ("DiagnosticWarn", "accent", None, "NONE", "NONE", None),
    ("DiagnosticInfo", "info", None, "NONE", "NONE", None),
    ("DiagnosticHint", "cyan", None, "NONE", "NONE", None),
    ("DiagnosticOk", "success", None, "NONE", "NONE", None),
    ("DiagnosticVirtualTextError", "danger", "surface", "NONE", "NONE", None),
    ("DiagnosticVirtualTextWarn", "accent", "surface", "NONE", "NONE", None),
    ("DiagnosticVirtualTextInfo", "info", "surface", "NONE", "NONE", None),
    ("DiagnosticVirtualTextHint", "cyan", "surface", "NONE", "NONE", None),
    ("DiagnosticVirtualTextOk", "success", "surface", "NONE", "NONE", None),
    ("DiagnosticFloatingError", "danger", "surface", "NONE", "NONE", None),
    ("DiagnosticFloatingWarn", "accent", "surface", "NONE", "NONE", None),
    ("DiagnosticFloatingInfo", "info", "surface", "NONE", "NONE", None),
    ("DiagnosticFloatingHint", "cyan", "surface", "NONE", "NONE", None),
    ("DiagnosticFloatingOk", "success", "surface", "NONE", "NONE", None),
    ("DiagnosticSignError", "danger", "bg", "NONE", "NONE", None),
    ("DiagnosticSignWarn", "accent", "bg", "NONE", "NONE", None),
    ("DiagnosticSignInfo", "info", "bg", "NONE", "NONE", None),
    ("DiagnosticSignHint", "cyan", "bg", "NONE", "NONE", None),
    ("DiagnosticSignOk", "success", "bg", "NONE", "NONE", None),
    ("DiagnosticUnderlineError", None, None, "undercurl", "underline", "danger"),
    ("DiagnosticUnderlineWarn", None, None, "undercurl", "underline", "accent"),
    ("DiagnosticUnderlineInfo", None, None, "undercurl", "underline", "info"),
    ("DiagnosticUnderlineHint", None, None, "undercurl", "underline", "cyan"),
    ("DiagnosticUnderlineOk", None, None, "undercurl", "underline", "success"),
    ("DiagnosticDeprecated", "fg_inactive", None, "strikethrough", "underline", None),
    ("DiagnosticUnnecessary", "fg_inactive", None, "italic", "italic", None),
)


class PaletteError(ValueError):
    """Raised when the palette cannot safely generate a theme."""


def load_palette(variant: str) -> dict[str, Any]:
    palette_path, _ = VARIANT_PATHS[variant]
    try:
        palette_bytes = palette_path.read_bytes()
        palette = json.loads(palette_bytes)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise PaletteError(f"cannot read {palette_path}: {error}") from error

    digest = hashlib.sha256(palette_bytes).hexdigest()
    if digest != PALETTE_SHA256[variant]:
        raise PaletteError(
            f"palette snapshot differs from canonical {palette_path.relative_to(ROOT)} "
            f"(expected {PALETTE_SHA256[variant]}, got {digest})"
        )
    appearance = "light" if variant == "apollo-light" else "dark"
    if palette.get("schemaVersion") != 1 or palette.get("id") != variant:
        raise PaletteError(f"palette must be {variant} schema version 1")
    if palette.get("appearance") != appearance or palette.get("colorSpace") != "srgb":
        raise PaletteError(f"palette must be the {appearance} sRGB Apollo variant")

    colors = palette.get("colors")
    terminal = palette.get("terminal")
    if not isinstance(colors, dict) or not isinstance(terminal, dict):
        raise PaletteError("palette colors and terminal sections are required")

    required = {key for _, key in COLOR_KEYS} | {"ansiBrightBlack"}
    missing = sorted(required - colors.keys())
    if missing:
        raise PaletteError(f"palette is missing colors: {', '.join(missing)}")

    values = list(colors.values())
    values.extend(terminal.get("ansi", []))
    values.extend(terminal.get("bright", []))
    values.extend(terminal.get(key) for key in ("foreground", "background", "cursor", "cursorText"))
    selection = terminal.get("selection")
    if isinstance(selection, dict):
        values.append(selection.get("color"))
    if any(not isinstance(value, str) or not HEX_COLOR.fullmatch(value) for value in values):
        raise PaletteError("all palette colors must be six-digit hexadecimal strings")
    if len(terminal.get("ansi", [])) != 8 or len(terminal.get("bright", [])) != 8:
        raise PaletteError("terminal ansi and bright arrays must each contain eight colors")

    expected_terminal = [
        colors["foreground"] if variant == "apollo-light" else colors["surface"],
        colors["danger"],
        colors["success"],
        colors["accent"],
        colors["info"],
        colors["magenta"],
        colors["cyan"],
        colors["foregroundSecondary"],
        colors["ansiBrightBlack"],
        colors["danger"],
        colors["success"],
        colors["accent"],
        colors["info"],
        colors["magenta"],
        colors["cyan"],
        colors["foregroundBright"],
    ]
    if terminal["ansi"] + terminal["bright"] != expected_terminal:
        raise PaletteError("terminal ANSI arrays do not match the canonical color roles")
    return palette


def vim_value(name: str | None) -> str:
    return "[]" if name is None else f"s:{name}"


def render(palette: dict[str, Any]) -> str:
    variant = palette["id"]
    appearance = palette["appearance"]
    colors = palette["colors"]
    terminal = palette["terminal"]["ansi"] + palette["terminal"]["bright"]
    color_specs = tuple(
        (variable, key, cterm)
        for (variable, key), cterm in zip(COLOR_KEYS, CTERM_FALLBACKS[variant], strict=True)
    )
    lines = [
        '" Generated by scripts/generate.py; do not edit.',
        f'" {palette["name"]} colorscheme for Vim.',
        "",
        "highlight clear",
        "if exists('syntax_on')",
        "  syntax reset",
        "endif",
        f"set background={appearance}",
        f"let g:colors_name = '{variant}'",
        "",
        '" Canonical GUI colors and hue-preserving xterm-256 fallbacks.',
    ]
    for variable, key, cterm in color_specs:
        lines.append(f"let s:{variable} = ['{colors[key]}', {cterm}]")

    lines.extend(
        [
            "",
            "function! s:hi(group, fg, bg, gui, cterm, sp) abort",
            "  let l:fg = empty(a:fg) ? ['NONE', 'NONE'] : a:fg",
            "  let l:bg = empty(a:bg) ? ['NONE', 'NONE'] : a:bg",
            "  let l:command = printf('highlight %s guifg=%s guibg=%s ctermfg=%s ctermbg=%s gui=%s cterm=%s',",
            "        \\ a:group, l:fg[0], l:bg[0], l:fg[1], l:bg[1], a:gui, a:cterm)",
            "  if !empty(a:sp)",
            "    let l:command .= ' guisp=' . a:sp",
            "  endif",
            "  execute l:command",
            "endfunction",
            "",
        ]
    )

    section = None
    for group, fg, bg, gui, cterm, special in HIGHLIGHTS:
        if group == "Normal":
            new_section = "Core UI"
        elif group == "Comment":
            new_section = "Syntax"
        elif group == "Added":
            new_section = "Diff"
        elif group == "DiagnosticError":
            new_section = "Diagnostics"
        else:
            new_section = section
        if new_section != section:
            lines.append(f'" {new_section}')
            section = new_section
        special_value = "''" if special is None else f"s:{special}[0]"
        lines.append(
            "call s:hi("
            f"'{group}', {vim_value(fg)}, {vim_value(bg)}, "
            f"'{gui}', '{cterm}', {special_value})"
        )

    quoted_terminal = ", ".join(f"'{color}'" for color in terminal)
    lines.extend(
        [
            "",
            '" Exact terminal ANSI colors for Vim and compatible terminal plugins.',
            f"let g:terminal_ansi_colors = [{quoted_terminal}]",
            "for s:index in range(0, 15)",
            "  execute 'let g:terminal_color_' . s:index . ' = g:terminal_ansi_colors[' . s:index . ']'",
            "endfor",
            "unlet s:index",
            "",
        ]
    )
    output = "\n".join(lines)
    assert_generated_colors(output, palette)
    return output


def canonical_colors(palette: dict[str, Any]) -> set[str]:
    terminal = palette["terminal"]
    values = set(palette["colors"].values())
    values.update(terminal["ansi"])
    values.update(terminal["bright"])
    values.update(terminal[key] for key in ("foreground", "background", "cursor", "cursorText"))
    values.add(terminal["selection"]["color"])
    return {value.lower() for value in values}


def assert_generated_colors(output: str, palette: dict[str, Any]) -> None:
    literals = {match.lower() for match in re.findall(r"#[0-9a-fA-F]{6}", output)}
    unexpected = sorted(literals - canonical_colors(palette))
    obsolete = sorted(literals & OBSOLETE_COLORS) if palette["id"] == "apollo" else []
    if unexpected:
        raise PaletteError(f"generated output contains non-palette colors: {', '.join(unexpected)}")
    if obsolete:
        raise PaletteError(f"generated output contains obsolete colors: {', '.join(obsolete)}")


def render_all() -> dict[Path, str]:
    return {
        output_path: render(load_palette(variant))
        for variant, (_, output_path) in VARIANT_PATHS.items()
    }


def write_or_check(outputs: dict[Path, str], check: bool) -> int:
    unexpected = sorted(set((ROOT / "colors").glob("*.vim")) - set(outputs))
    if unexpected:
        for path in unexpected:
            print(f"unexpected generated output: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    stale: list[Path] = []
    for path, output in outputs.items():
        if check:
            try:
                current = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                stale.append(path)
                continue
            if current != output:
                stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(output, encoding="utf-8", newline="\n")
            print(f"generated {path.relative_to(ROOT)}")

    if stale:
        for path in stale:
            print(f"out of date: regenerate {path.relative_to(ROOT)} with scripts/generate.py", file=sys.stderr)
        return 1
    if check:
        print("up to date: " + ", ".join(str(path.relative_to(ROOT)) for path in outputs))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files differ")
    args = parser.parse_args()
    try:
        outputs = render_all()
    except PaletteError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return write_or_check(outputs, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
