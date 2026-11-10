#!/usr/bin/env python3
"""Generate the Apollo Neovim colorscheme from the bundled palette snapshot."""

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
VARIANTS = {
    "apollo": {
        "appearance": "dark",
        "palette": ROOT / "palette" / "apollo.json",
        "outputs": {
            ROOT / "colors" / "apollo.lua": "entrypoint",
            ROOT / "lua" / "apollo" / "palette.lua": "palette",
            ROOT / "lua" / "apollo" / "init.lua": "implementation",
        },
    },
    "apollo-light": {
        "appearance": "light",
        "palette": ROOT / "palette" / "apollo-light.json",
        "outputs": {
            ROOT / "colors" / "apollo-light.lua": "entrypoint",
            ROOT / "lua" / "apollo" / "light-palette.lua": "palette",
            ROOT / "lua" / "apollo" / "light.lua": "implementation",
        },
    },
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
OBSOLETE_CAPTURES = {
    "@method",
    "@method.call",
    "@parameter",
    "@field",
    "@conditional",
    "@repeat",
    "@text",
    "@text.title",
    "@text.literal",
    "@text.uri",
}

# group, Lua highlight spec
HIGHLIGHTS = (
    ("Normal", "{ fg = p.foreground, bg = p.background }"),
    ("NormalNC", "{ fg = p.foreground, bg = p.background }"),
    ("NormalFloat", "{ fg = p.foreground, bg = p.surface }"),
    ("FloatBorder", "{ fg = p.selection, bg = p.surface }"),
    ("FloatTitle", "{ fg = p.accent, bg = p.surface, bold = true }"),
    ("FloatFooter", "{ fg = p.foregroundInactive, bg = p.surface }"),
    ("Cursor", "{ fg = p.background, bg = p.accent }"),
    ("lCursor", "{ fg = p.background, bg = p.accent }"),
    ("CursorIM", "{ fg = p.background, bg = p.info }"),
    ("TermCursor", "{ fg = p.background, bg = p.accent, reverse = true }"),
    ("TermCursorNC", "{ fg = p.foregroundInactive, bg = p.surface }"),
    ("CursorLine", "{ bg = p.surface }"),
    ("CursorColumn", "{ bg = p.surfaceHover }"),
    ("CursorLineNr", "{ fg = p.accent, bg = p.surface, bold = true }"),
    ("CursorLineFold", "{ fg = p.accent, bg = p.surface }"),
    ("CursorLineSign", "{ fg = p.accent, bg = p.surface }"),
    ("LineNr", "{ fg = p.foregroundInactive, bg = p.background }"),
    ("LineNrAbove", "{ fg = p.foregroundInactive, bg = p.background }"),
    ("LineNrBelow", "{ fg = p.foregroundInactive, bg = p.background }"),
    ("SignColumn", "{ bg = p.background }"),
    ("FoldColumn", "{ fg = p.foregroundInactive, bg = p.background }"),
    ("Folded", "{ fg = p.foregroundInactive, bg = p.surface, italic = true }"),
    ("ColorColumn", "{ bg = p.surface }"),
    ("WinSeparator", "{ fg = p.selection, bg = p.background }"),
    ("StatusLine", "{ fg = p.foregroundBright, bg = p.selection }"),
    ("StatusLineNC", "{ fg = p.foregroundInactive, bg = p.surface }"),
    ("TabLine", "{ fg = p.foregroundInactive, bg = p.surface }"),
    ("TabLineSel", "{ fg = p.accent, bg = p.background, bold = true }"),
    ("TabLineFill", "{ bg = p.background }"),
    ("WinBar", "{ fg = p.foregroundSecondary, bg = p.background, bold = true }"),
    ("WinBarNC", "{ fg = p.foregroundInactive, bg = p.background }"),
    ("Pmenu", "{ fg = p.foreground, bg = p.surface }"),
    ("PmenuSel", "{ fg = p.background, bg = p.accent, bold = true }"),
    ("PmenuKind", "{ fg = p.magenta, bg = p.surface }"),
    ("PmenuKindSel", "{ fg = p.background, bg = p.accent, bold = true }"),
    ("PmenuExtra", "{ fg = p.foregroundInactive, bg = p.surface }"),
    ("PmenuExtraSel", "{ fg = p.background, bg = p.accent }"),
    ("PmenuSbar", "{ bg = p.surfaceHover }"),
    ("PmenuThumb", "{ bg = p.selection }"),
    ("PmenuMatch", "{ fg = p.accent, bg = p.surface, bold = true }"),
    ("PmenuMatchSel", "{ fg = p.background, bg = p.accent, bold = true }"),
    ("ComplMatchIns", "{ fg = p.accent, bold = true }"),
    ("WildMenu", "{ fg = p.background, bg = p.accent, bold = true }"),
    ("Visual", "{ bg = p.selection }"),
    ("VisualNOS", "{ bg = p.selection, underline = true }"),
    ("Search", "{ fg = p.background, bg = p.accent }"),
    ("IncSearch", "{ fg = p.background, bg = p.danger, bold = true }"),
    ("CurSearch", "{ fg = p.background, bg = p.danger, bold = true }"),
    ("Substitute", "{ fg = p.background, bg = p.success }"),
    ("MatchParen", "{ fg = p.accent, bg = p.selection, bold = true }"),
    ("NonText", "{ fg = p.selection }"),
    ("Whitespace", "{ fg = p.selection }"),
    ("SpecialKey", "{ fg = p.selection }"),
    ("EndOfBuffer", "{ fg = p.background, bg = p.background }"),
    ("Directory", "{ fg = p.info }"),
    ("Title", "{ fg = p.accent, bold = true }"),
    ("Conceal", "{ fg = p.foregroundInactive }"),
    ("Question", "{ fg = p.success }"),
    ("MoreMsg", "{ fg = p.info }"),
    ("ModeMsg", "{ fg = p.accent, bold = true }"),
    ("MsgArea", "{ fg = p.foreground, bg = p.background }"),
    ("MsgSeparator", "{ fg = p.selection, bg = p.background }"),
    ("ErrorMsg", "{ fg = p.danger, bold = true }"),
    ("WarningMsg", "{ fg = p.accent, bold = true }"),
    ("QuickFixLine", "{ fg = p.background, bg = p.info }"),
    ("SpellBad", "{ sp = p.danger, undercurl = true }"),
    ("SpellCap", "{ sp = p.info, undercurl = true }"),
    ("SpellLocal", "{ sp = p.cyan, undercurl = true }"),
    ("SpellRare", "{ sp = p.magenta, undercurl = true }"),
    ("Comment", "{ fg = p.foregroundInactive, italic = true }"),
    ("Constant", "{ fg = p.magenta }"),
    ("String", "{ fg = p.success }"),
    ("Character", "{ fg = p.magenta }"),
    ("Number", "{ fg = p.magenta }"),
    ("Boolean", "{ fg = p.magenta, bold = true }"),
    ("Float", "{ fg = p.magenta }"),
    ("Identifier", "{ fg = p.info }"),
    ("Function", "{ fg = p.accent }"),
    ("Statement", "{ fg = p.danger }"),
    ("Conditional", "{ fg = p.danger }"),
    ("Repeat", "{ fg = p.danger }"),
    ("Label", "{ fg = p.danger }"),
    ("Operator", "{ fg = p.foregroundSecondary }"),
    ("Keyword", "{ fg = p.danger }"),
    ("Exception", "{ fg = p.danger }"),
    ("PreProc", "{ fg = p.cyan }"),
    ("Include", "{ fg = p.cyan }"),
    ("Define", "{ fg = p.cyan }"),
    ("Macro", "{ fg = p.cyan }"),
    ("PreCondit", "{ fg = p.cyan }"),
    ("Type", "{ fg = p.accent }"),
    ("StorageClass", "{ fg = p.accent }"),
    ("Structure", "{ fg = p.accent }"),
    ("Typedef", "{ fg = p.accent }"),
    ("Special", "{ fg = p.magenta }"),
    ("SpecialChar", "{ fg = p.magenta }"),
    ("Tag", "{ fg = p.cyan }"),
    ("Delimiter", "{ fg = p.foregroundSecondary }"),
    ("SpecialComment", "{ fg = p.cyan, italic = true }"),
    ("Debug", "{ fg = p.danger }"),
    ("Underlined", "{ fg = p.info, underline = true }"),
    ("Ignore", "{ fg = p.foregroundInactive }"),
    ("Error", "{ fg = p.danger, bold = true }"),
    ("Todo", "{ fg = p.background, bg = p.accent, bold = true }"),
    ("Added", "{ fg = p.success }"),
    ("Changed", "{ fg = p.accent }"),
    ("Removed", "{ fg = p.danger }"),
    ("DiffAdd", "{ fg = p.success, bg = p.surface }"),
    ("DiffChange", "{ fg = p.accent, bg = p.surface }"),
    ("DiffDelete", "{ fg = p.danger, bg = p.surface }"),
    ("DiffText", "{ fg = p.background, bg = p.accent, bold = true }"),
    ("DiagnosticError", "{ fg = p.danger }"),
    ("DiagnosticWarn", "{ fg = p.accent }"),
    ("DiagnosticInfo", "{ fg = p.info }"),
    ("DiagnosticHint", "{ fg = p.cyan }"),
    ("DiagnosticOk", "{ fg = p.success }"),
    ("DiagnosticVirtualTextError", "{ fg = p.danger, bg = p.surface }"),
    ("DiagnosticVirtualTextWarn", "{ fg = p.accent, bg = p.surface }"),
    ("DiagnosticVirtualTextInfo", "{ fg = p.info, bg = p.surface }"),
    ("DiagnosticVirtualTextHint", "{ fg = p.cyan, bg = p.surface }"),
    ("DiagnosticVirtualTextOk", "{ fg = p.success, bg = p.surface }"),
    ("DiagnosticFloatingError", "{ fg = p.danger, bg = p.surface }"),
    ("DiagnosticFloatingWarn", "{ fg = p.accent, bg = p.surface }"),
    ("DiagnosticFloatingInfo", "{ fg = p.info, bg = p.surface }"),
    ("DiagnosticFloatingHint", "{ fg = p.cyan, bg = p.surface }"),
    ("DiagnosticFloatingOk", "{ fg = p.success, bg = p.surface }"),
    ("DiagnosticSignError", "{ fg = p.danger, bg = p.background }"),
    ("DiagnosticSignWarn", "{ fg = p.accent, bg = p.background }"),
    ("DiagnosticSignInfo", "{ fg = p.info, bg = p.background }"),
    ("DiagnosticSignHint", "{ fg = p.cyan, bg = p.background }"),
    ("DiagnosticSignOk", "{ fg = p.success, bg = p.background }"),
    ("DiagnosticUnderlineError", "{ sp = p.danger, undercurl = true }"),
    ("DiagnosticUnderlineWarn", "{ sp = p.accent, undercurl = true }"),
    ("DiagnosticUnderlineInfo", "{ sp = p.info, undercurl = true }"),
    ("DiagnosticUnderlineHint", "{ sp = p.cyan, undercurl = true }"),
    ("DiagnosticUnderlineOk", "{ sp = p.success, undercurl = true }"),
    ("DiagnosticDeprecated", "{ fg = p.foregroundInactive, strikethrough = true }"),
    ("DiagnosticUnnecessary", "{ fg = p.foregroundInactive, italic = true }"),
    ("LspReferenceText", "{ bg = p.surfaceHover }"),
    ("LspReferenceRead", "{ bg = p.surfaceHover }"),
    ("LspReferenceWrite", "{ bg = p.selection, bold = true }"),
    ("LspSignatureActiveParameter", "{ fg = p.accent, bold = true }"),
    ("LspCodeLens", "{ fg = p.foregroundInactive, italic = true }"),
    ("LspCodeLensSeparator", "{ fg = p.selection }"),
    ("LspInlayHint", "{ fg = p.foregroundInactive, bg = p.surface, italic = true }"),
    ("SnippetTabstop", "{ bg = p.selection }"),
)

CAPTURE_LINKS = (
    ("@variable", "Normal"),
    ("@variable.builtin", "Special"),
    ("@variable.parameter", "Normal"),
    ("@variable.parameter.builtin", "Special"),
    ("@variable.member", "Identifier"),
    ("@constant", "Constant"),
    ("@constant.builtin", "Constant"),
    ("@constant.macro", "Macro"),
    ("@module", "Identifier"),
    ("@module.builtin", "Special"),
    ("@label", "Label"),
    ("@string", "String"),
    ("@string.documentation", "SpecialComment"),
    ("@string.regexp", "Special"),
    ("@string.escape", "SpecialChar"),
    ("@string.special", "Special"),
    ("@string.special.symbol", "Constant"),
    ("@string.special.path", "Directory"),
    ("@string.special.url", "Underlined"),
    ("@character", "Character"),
    ("@character.special", "SpecialChar"),
    ("@boolean", "Boolean"),
    ("@number", "Number"),
    ("@number.float", "Float"),
    ("@type", "Type"),
    ("@type.builtin", "Type"),
    ("@type.definition", "Typedef"),
    ("@attribute", "Special"),
    ("@attribute.builtin", "Special"),
    ("@property", "Identifier"),
    ("@function", "Function"),
    ("@function.builtin", "Function"),
    ("@function.call", "Function"),
    ("@function.macro", "Macro"),
    ("@function.method", "Function"),
    ("@function.method.call", "Function"),
    ("@constructor", "Type"),
    ("@operator", "Operator"),
    ("@keyword", "Keyword"),
    ("@keyword.coroutine", "Keyword"),
    ("@keyword.function", "Keyword"),
    ("@keyword.operator", "Operator"),
    ("@keyword.import", "Include"),
    ("@keyword.type", "Keyword"),
    ("@keyword.modifier", "StorageClass"),
    ("@keyword.repeat", "Repeat"),
    ("@keyword.return", "Keyword"),
    ("@keyword.debug", "Debug"),
    ("@keyword.exception", "Exception"),
    ("@keyword.conditional", "Conditional"),
    ("@keyword.conditional.ternary", "Conditional"),
    ("@keyword.directive", "PreProc"),
    ("@keyword.directive.define", "Define"),
    ("@punctuation.delimiter", "Delimiter"),
    ("@punctuation.bracket", "Delimiter"),
    ("@punctuation.special", "Special"),
    ("@comment", "Comment"),
    ("@comment.documentation", "SpecialComment"),
    ("@comment.error", "DiagnosticError"),
    ("@comment.warning", "DiagnosticWarn"),
    ("@comment.todo", "Todo"),
    ("@comment.note", "DiagnosticInfo"),
    ("@markup.heading", "Title"),
    ("@markup.heading.1", "Title"),
    ("@markup.heading.2", "Title"),
    ("@markup.heading.3", "Title"),
    ("@markup.heading.4", "Title"),
    ("@markup.heading.5", "Title"),
    ("@markup.heading.6", "Title"),
    ("@markup.quote", "Comment"),
    ("@markup.math", "Special"),
    ("@markup.link", "Identifier"),
    ("@markup.link.label", "Identifier"),
    ("@markup.link.url", "Underlined"),
    ("@markup.raw", "String"),
    ("@markup.raw.block", "String"),
    ("@markup.list", "Special"),
    ("@markup.list.checked", "DiagnosticOk"),
    ("@markup.list.unchecked", "DiagnosticWarn"),
    ("@diff.plus", "Added"),
    ("@diff.minus", "Removed"),
    ("@diff.delta", "Changed"),
    ("@tag", "Tag"),
    ("@tag.builtin", "Tag"),
    ("@tag.attribute", "Identifier"),
    ("@tag.delimiter", "Delimiter"),
)

CAPTURE_SPECS = (
    ("@markup.strong", "{ bold = true }"),
    ("@markup.italic", "{ italic = true }"),
    ("@markup.strikethrough", "{ strikethrough = true }"),
    ("@markup.underline", "{ underline = true }"),
)


class PaletteError(ValueError):
    """Raised when the palette cannot safely generate a theme."""


def load_palette(variant: str = "apollo") -> dict[str, Any]:
    metadata = VARIANTS[variant]
    palette_path = metadata["palette"]
    assert isinstance(palette_path, Path)
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
    appearance = metadata["appearance"]
    if palette.get("schemaVersion") != 1 or palette.get("id") != variant:
        raise PaletteError(f"palette must be {variant} schema version 1")
    if palette.get("appearance") != appearance or palette.get("colorSpace") != "srgb":
        raise PaletteError(f"palette must be the {appearance} sRGB Apollo variant")

    colors = palette.get("colors")
    terminal = palette.get("terminal")
    if not isinstance(colors, dict) or not isinstance(terminal, dict):
        raise PaletteError("palette colors and terminal sections are required")

    required = {
        "background",
        "surface",
        "surfaceHover",
        "selection",
        "foreground",
        "foregroundSecondary",
        "foregroundInactive",
        "foregroundBright",
        "accent",
        "danger",
        "success",
        "info",
        "magenta",
        "cyan",
        "ansiBrightBlack",
    }
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


def render_entrypoint(module: str = "apollo") -> str:
    return "\n".join(
        (
            "-- Generated by scripts/generate.py; do not edit.",
            f"require('{module}').load()",
            "",
        )
    )


def render_palette(palette: dict[str, Any]) -> str:
    colors = palette["colors"]
    terminal = palette["terminal"]
    lines = [
        "-- Generated by scripts/generate.py; do not edit.",
        "local M = {",
    ]
    for key, value in colors.items():
        lines.append(f"  {key} = '{value}',")
    lines.extend(
        (
            f"  terminalForeground = '{terminal['foreground']}',",
            f"  terminalBackground = '{terminal['background']}',",
            f"  terminalCursor = '{terminal['cursor']}',",
            f"  terminalCursorText = '{terminal['cursorText']}',",
            f"  terminalSelection = '{terminal['selection']['color']}',",
            "  terminal = {",
        )
    )
    for value in terminal["ansi"] + terminal["bright"]:
        lines.append(f"    '{value}',")
    lines.extend(("  },", "}", "", "return M", ""))
    return "\n".join(lines)


def render_implementation(
    palette_module: str = "apollo.palette",
    appearance: str = "dark",
    colors_name: str = "apollo",
) -> str:
    lines = [
        "-- Generated by scripts/generate.py; do not edit.",
        f"local p = require('{palette_module}')",
        "",
        "local M = {}",
        "",
        "local highlights = {",
    ]
    for group, spec in HIGHLIGHTS:
        lines.append(f"  {{ '{group}', {spec} }},")
    lines.append("")
    lines.append("  -- Neovim 0.12 standard Tree-sitter captures.")
    for capture, link in CAPTURE_LINKS:
        lines.append(f"  {{ '{capture}', {{ link = '{link}' }} }},")
    for capture, spec in CAPTURE_SPECS:
        lines.append(f"  {{ '{capture}', {spec} }},")
    lines.extend(
        (
            "}",
            "",
            "function M.load()",
            "  vim.cmd('highlight clear')",
            "  if vim.fn.exists('syntax_on') == 1 then",
            "    vim.cmd('syntax reset')",
            "  end",
            f"  vim.o.background = '{appearance}'",
            f"  vim.g.colors_name = '{colors_name}'",
            "",
            "  for _, highlight in ipairs(highlights) do",
            "    vim.api.nvim_set_hl(0, highlight[1], highlight[2])",
            "  end",
            "",
            "  for index, color in ipairs(p.terminal) do",
            "    vim.g['terminal_color_' .. (index - 1)] = color",
            "  end",
            "end",
            "",
            "return M",
            "",
        )
    )
    return "\n".join(lines)


def canonical_colors(palette: dict[str, Any]) -> set[str]:
    terminal = palette["terminal"]
    values = set(palette["colors"].values())
    values.update(terminal["ansi"])
    values.update(terminal["bright"])
    values.update(terminal[key] for key in ("foreground", "background", "cursor", "cursorText"))
    values.add(terminal["selection"]["color"])
    return {value.lower() for value in values}


def assert_generated_output(outputs: dict[Path, str], palette: dict[str, Any]) -> None:
    combined = "\n".join(outputs.values())
    literals = {match.lower() for match in re.findall(r"#[0-9a-fA-F]{6}", combined)}
    unexpected = sorted(literals - canonical_colors(palette))
    obsolete = sorted(literals & OBSOLETE_COLORS) if palette["id"] == "apollo" else []
    captures = set(re.findall(r"'(@[A-Za-z0-9_.]+)'", combined))
    old_captures = sorted(captures & OBSOLETE_CAPTURES)
    if unexpected:
        raise PaletteError(f"generated output contains non-palette colors: {', '.join(unexpected)}")
    if obsolete:
        raise PaletteError(f"generated output contains obsolete colors: {', '.join(obsolete)}")
    if old_captures:
        raise PaletteError(f"generated output contains obsolete captures: {', '.join(old_captures)}")


def render_variant(variant: str, palette: dict[str, Any]) -> dict[Path, str]:
    metadata = VARIANTS[variant]
    appearance = metadata["appearance"]
    outputs = metadata["outputs"]
    assert isinstance(appearance, str)
    assert isinstance(outputs, dict)
    module = "apollo" if variant == "apollo" else "apollo.light"
    palette_module = "apollo.palette" if variant == "apollo" else "apollo.light-palette"
    rendered = {
        path: {
            "entrypoint": lambda: render_entrypoint(module),
            "palette": lambda: render_palette(palette),
            "implementation": lambda: render_implementation(
                palette_module, appearance, variant
            ),
        }[kind]()
        for path, kind in outputs.items()
    }
    assert_generated_output(rendered, palette)
    return rendered


def render_all() -> dict[Path, str]:
    rendered: dict[Path, str] = {}
    for variant in VARIANTS:
        rendered.update(render_variant(variant, load_palette(variant)))
    return rendered


def write_or_check(outputs: dict[Path, str], check: bool) -> int:
    candidates = set((ROOT / "colors").glob("*.lua"))
    candidates.update((ROOT / "lua" / "apollo").glob("*.lua"))
    unexpected = sorted(candidates - set(outputs))
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
            print(f"out of date: {path.relative_to(ROOT)}", file=sys.stderr)
        print("run scripts/generate.py to regenerate native files", file=sys.stderr)
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
