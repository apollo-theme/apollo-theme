#!/usr/bin/env python3
"""Generate the Apollo VS Code theme from the vendored palette snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PALETTE_SHA256 = {
    "apollo": "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
    "apollo-light": "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
}
VARIANTS = (
    ("apollo", "dark", ROOT / "palette" / "apollo.json", ROOT / "themes" / "apollo-color-theme.json"),
    ("apollo-light", "light", ROOT / "palette" / "apollo-light.json", ROOT / "themes" / "apollo-light-color-theme.json"),
)


def alpha(color: str, value: int) -> str:
    """Append an 8-bit alpha channel to a palette color."""
    return f"{color}{value:02x}"


def build_theme(palette: dict[str, Any]) -> dict[str, Any]:
    c = palette["colors"]
    t = palette["terminal"]
    ansi_names = ("Black", "Red", "Green", "Yellow", "Blue", "Magenta", "Cyan", "White")

    colors: dict[str, str] = {
        "focusBorder": c["accent"],
        "foreground": c["foreground"],
        "disabledForeground": c["foregroundInactive"],
        "descriptionForeground": c["foregroundSecondary"],
        "errorForeground": c["danger"],
        "icon.foreground": c["foregroundSecondary"],
        "selection.background": c["selection"],
        "widget.shadow": alpha(c["background"], 128),
        "window.activeBorder": c["selection"],
        "window.inactiveBorder": c["surface"],
        "textBlockQuote.background": c["surface"],
        "textBlockQuote.border": c["accent"],
        "textCodeBlock.background": c["surface"],
        "textLink.activeForeground": c["accent"],
        "textLink.foreground": c["info"],
        "textPreformat.foreground": c["cyan"],
        "textSeparator.foreground": c["selection"],
        "button.background": c["accent"],
        "button.foreground": c["background"],
        "button.hoverBackground": c["foregroundBright"],
        "button.secondaryBackground": c["selection"],
        "button.secondaryForeground": c["foregroundBright"],
        "button.secondaryHoverBackground": c["surfaceHover"],
        "checkbox.background": c["surface"],
        "checkbox.border": c["selection"],
        "checkbox.foreground": c["foreground"],
        "dropdown.background": c["surface"],
        "dropdown.border": c["selection"],
        "dropdown.foreground": c["foreground"],
        "dropdown.listBackground": c["surface"],
        "input.background": c["surface"],
        "input.border": c["selection"],
        "input.foreground": c["foreground"],
        "input.placeholderForeground": c["foregroundInactive"],
        "inputOption.activeBackground": alpha(c["accent"], 38),
        "inputOption.activeBorder": c["accent"],
        "inputOption.activeForeground": c["foregroundBright"],
        "inputValidation.errorBackground": c["surface"],
        "inputValidation.errorBorder": c["danger"],
        "inputValidation.infoBackground": c["surface"],
        "inputValidation.infoBorder": c["info"],
        "inputValidation.warningBackground": c["surface"],
        "inputValidation.warningBorder": c["accent"],
        "scrollbar.shadow": c["background"],
        "scrollbarSlider.activeBackground": alpha(c["foregroundInactive"], 160),
        "scrollbarSlider.background": alpha(c["selection"], 128),
        "scrollbarSlider.hoverBackground": alpha(c["foregroundInactive"], 112),
        "badge.background": c["accent"],
        "badge.foreground": c["background"],
        "progressBar.background": c["accent"],
        "list.activeSelectionBackground": c["selection"],
        "list.activeSelectionForeground": c["foregroundBright"],
        "list.dropBackground": alpha(c["info"], 48),
        "list.errorForeground": c["danger"],
        "list.filterMatchBackground": alpha(c["accent"], 64),
        "list.focusBackground": c["surfaceHover"],
        "list.focusForeground": c["foregroundBright"],
        "list.highlightForeground": c["accent"],
        "list.hoverBackground": c["surfaceHover"],
        "list.hoverForeground": c["foreground"],
        "list.inactiveSelectionBackground": c["surface"],
        "list.inactiveSelectionForeground": c["foreground"],
        "list.invalidItemForeground": c["danger"],
        "list.warningForeground": c["accent"],
        "tree.indentGuidesStroke": c["selection"],
        "activityBar.activeBackground": c["surface"],
        "activityBar.activeBorder": c["accent"],
        "activityBar.background": c["background"],
        "activityBar.border": c["surface"],
        "activityBar.foreground": c["foregroundBright"],
        "activityBar.inactiveForeground": c["foregroundInactive"],
        "activityBarBadge.background": c["accent"],
        "activityBarBadge.foreground": c["background"],
        "sideBar.background": c["background"],
        "sideBar.border": c["surface"],
        "sideBar.dropBackground": alpha(c["info"], 40),
        "sideBar.foreground": c["foregroundSecondary"],
        "sideBarSectionHeader.background": c["surface"],
        "sideBarSectionHeader.border": c["selection"],
        "sideBarSectionHeader.foreground": c["foregroundBright"],
        "sideBarTitle.foreground": c["foregroundBright"],
        "minimap.background": c["background"],
        "minimap.errorHighlight": c["danger"],
        "minimap.findMatchHighlight": c["accent"],
        "minimap.selectionHighlight": c["selection"],
        "minimap.warningHighlight": c["accent"],
        "minimapSlider.activeBackground": alpha(c["foregroundInactive"], 80),
        "minimapSlider.background": alpha(c["selection"], 80),
        "minimapSlider.hoverBackground": alpha(c["foregroundInactive"], 64),
        "editorGroup.border": c["surface"],
        "editorGroup.dropBackground": alpha(c["info"], 32),
        "editorGroupHeader.noTabsBackground": c["background"],
        "editorGroupHeader.tabsBackground": c["background"],
        "editorGroupHeader.tabsBorder": c["surface"],
        "tab.activeBackground": c["background"],
        "tab.activeBorder": c["background"],
        "tab.activeBorderTop": c["accent"],
        "tab.activeForeground": c["foregroundBright"],
        "tab.border": c["surface"],
        "tab.hoverBackground": c["surfaceHover"],
        "tab.hoverForeground": c["foregroundBright"],
        "tab.inactiveBackground": c["background"],
        "tab.inactiveForeground": c["foregroundInactive"],
        "tab.unfocusedActiveForeground": c["foregroundSecondary"],
        "tab.unfocusedInactiveForeground": c["foregroundInactive"],
        "editor.background": c["background"],
        "editor.foreground": c["foreground"],
        "editor.findMatchBackground": alpha(c["accent"], 85),
        "editor.findMatchBorder": c["accent"],
        "editor.findMatchHighlightBackground": alpha(c["accent"], 40),
        "editor.foldBackground": alpha(c["info"], 24),
        "editor.hoverHighlightBackground": alpha(c["selection"], 128),
        "editor.inactiveSelectionBackground": alpha(c["selection"], 112),
        "editor.lineHighlightBackground": c["surface"],
        "editor.lineHighlightBorder": c["surfaceHover"],
        "editor.rangeHighlightBackground": alpha(c["selection"], 96),
        "editor.selectionBackground": c["selection"],
        "editor.selectionHighlightBackground": alpha(c["selection"], 128),
        "editor.snippetFinalTabstopHighlightBorder": c["success"],
        "editor.snippetTabstopHighlightBackground": alpha(c["accent"], 40),
        "editor.symbolHighlightBackground": alpha(c["accent"], 28),
        "editor.wordHighlightBackground": alpha(c["info"], 32),
        "editor.wordHighlightStrongBackground": alpha(c["accent"], 32),
        "editorBracketHighlight.foreground1": c["accent"],
        "editorBracketHighlight.foreground2": c["cyan"],
        "editorBracketHighlight.foreground3": c["magenta"],
        "editorBracketHighlight.foreground4": c["info"],
        "editorBracketHighlight.foreground5": c["success"],
        "editorBracketHighlight.foreground6": c["danger"],
        "editorBracketHighlight.unexpectedBracket.foreground": c["danger"],
        "editorBracketMatch.background": alpha(c["selection"], 128),
        "editorBracketMatch.border": c["accent"],
        "editorCursor.background": t["cursorText"],
        "editorCursor.foreground": t["cursor"],
        "editorError.foreground": c["danger"],
        "editorWarning.foreground": c["accent"],
        "editorInfo.foreground": c["info"],
        "editorHint.foreground": c["cyan"],
        "editorGutter.addedBackground": c["success"],
        "editorGutter.background": c["background"],
        "editorGutter.deletedBackground": c["danger"],
        "editorGutter.foldingControlForeground": c["foregroundInactive"],
        "editorGutter.modifiedBackground": c["accent"],
        "editorIndentGuide.activeBackground1": c["selection"],
        "editorIndentGuide.background1": c["surface"],
        "editorLineNumber.activeForeground": c["accent"],
        "editorLineNumber.foreground": c["foregroundInactive"],
        "editorLink.activeForeground": c["info"],
        "editorWhitespace.foreground": c["selection"],
        "editorRuler.foreground": c["surface"],
        "editorCodeLens.foreground": c["foregroundInactive"],
        "editorLightBulb.foreground": c["accent"],
        "editorLightBulbAutoFix.foreground": c["info"],
        "editorWidget.background": c["surface"],
        "editorWidget.border": c["selection"],
        "editorWidget.foreground": c["foreground"],
        "editorSuggestWidget.background": c["surface"],
        "editorSuggestWidget.border": c["selection"],
        "editorSuggestWidget.foreground": c["foreground"],
        "editorSuggestWidget.highlightForeground": c["accent"],
        "editorSuggestWidget.selectedBackground": c["selection"],
        "editorHoverWidget.background": c["surface"],
        "editorHoverWidget.border": c["selection"],
        "editorHoverWidget.foreground": c["foreground"],
        "peekView.border": c["accent"],
        "peekViewEditor.background": c["surface"],
        "peekViewEditor.matchHighlightBackground": alpha(c["accent"], 48),
        "peekViewResult.background": c["background"],
        "peekViewResult.fileForeground": c["foregroundBright"],
        "peekViewResult.lineForeground": c["foregroundSecondary"],
        "peekViewResult.matchHighlightBackground": alpha(c["accent"], 48),
        "peekViewResult.selectionBackground": c["selection"],
        "peekViewResult.selectionForeground": c["foregroundBright"],
        "peekViewTitle.background": c["surface"],
        "peekViewTitleDescription.foreground": c["foregroundInactive"],
        "peekViewTitleLabel.foreground": c["foregroundBright"],
        "diffEditor.diagonalFill": c["surface"],
        "diffEditor.insertedLineBackground": alpha(c["success"], 18),
        "diffEditor.insertedTextBackground": alpha(c["success"], 40),
        "diffEditor.removedLineBackground": alpha(c["danger"], 18),
        "diffEditor.removedTextBackground": alpha(c["danger"], 40),
        "diffEditorGutter.insertedLineBackground": alpha(c["success"], 80),
        "diffEditorGutter.removedLineBackground": alpha(c["danger"], 80),
        "merge.currentContentBackground": alpha(c["info"], 28),
        "merge.incomingContentBackground": alpha(c["success"], 28),
        "merge.commonContentBackground": alpha(c["selection"], 80),
        "panel.background": c["background"],
        "panel.border": c["surface"],
        "panel.dropBorder": c["accent"],
        "panelSection.border": c["surface"],
        "panelSectionHeader.background": c["surface"],
        "panelSectionHeader.foreground": c["foregroundBright"],
        "panelTitle.activeBorder": c["accent"],
        "panelTitle.activeForeground": c["accent"],
        "panelTitle.inactiveForeground": c["foregroundInactive"],
        "statusBar.background": c["surface"],
        "statusBar.border": c["background"],
        "statusBar.debuggingBackground": c["magenta"],
        "statusBar.debuggingForeground": c["background"],
        "statusBar.focusBorder": c["accent"],
        "statusBar.foreground": c["foregroundSecondary"],
        "statusBar.noFolderBackground": c["surface"],
        "statusBar.noFolderForeground": c["foregroundSecondary"],
        "statusBarItem.activeBackground": alpha(c["foregroundBright"], 28),
        "statusBarItem.errorBackground": c["danger"],
        "statusBarItem.errorForeground": c["background"],
        "statusBarItem.hoverBackground": alpha(c["foregroundBright"], 20),
        "statusBarItem.prominentBackground": c["selection"],
        "statusBarItem.prominentForeground": c["foregroundBright"],
        "statusBarItem.remoteBackground": c["info"],
        "statusBarItem.remoteForeground": c["background"],
        "statusBarItem.warningBackground": c["accent"],
        "statusBarItem.warningForeground": c["background"],
        "titleBar.activeBackground": c["background"],
        "titleBar.activeForeground": c["foregroundBright"],
        "titleBar.border": c["surface"],
        "titleBar.inactiveBackground": c["background"],
        "titleBar.inactiveForeground": c["foregroundInactive"],
        "menu.background": c["surface"],
        "menu.border": c["selection"],
        "menu.foreground": c["foreground"],
        "menu.selectionBackground": c["selection"],
        "menu.selectionForeground": c["foregroundBright"],
        "menu.separatorBackground": c["selection"],
        "menubar.selectionBackground": c["surfaceHover"],
        "menubar.selectionForeground": c["foregroundBright"],
        "commandCenter.activeBackground": c["surfaceHover"],
        "commandCenter.activeForeground": c["foregroundBright"],
        "commandCenter.background": c["surface"],
        "commandCenter.border": c["selection"],
        "commandCenter.foreground": c["foregroundSecondary"],
        "notificationCenter.border": c["selection"],
        "notificationCenterHeader.background": c["surface"],
        "notificationCenterHeader.foreground": c["foregroundBright"],
        "notificationLink.foreground": c["info"],
        "notifications.background": c["surface"],
        "notifications.border": c["selection"],
        "notifications.foreground": c["foreground"],
        "notificationsErrorIcon.foreground": c["danger"],
        "notificationsInfoIcon.foreground": c["info"],
        "notificationsWarningIcon.foreground": c["accent"],
        "extensionButton.prominentBackground": c["accent"],
        "extensionButton.prominentForeground": c["background"],
        "extensionButton.prominentHoverBackground": c["foregroundBright"],
        "pickerGroup.border": c["selection"],
        "pickerGroup.foreground": c["accent"],
        "quickInput.background": c["surface"],
        "quickInput.foreground": c["foreground"],
        "quickInputList.focusBackground": c["selection"],
        "quickInputList.focusForeground": c["foregroundBright"],
        "keybindingLabel.background": c["surfaceHover"],
        "keybindingLabel.border": c["selection"],
        "keybindingLabel.bottomBorder": c["background"],
        "keybindingLabel.foreground": c["foregroundSecondary"],
        "settings.checkboxBackground": c["surface"],
        "settings.checkboxBorder": c["selection"],
        "settings.checkboxForeground": c["foreground"],
        "settings.dropdownBackground": c["surface"],
        "settings.dropdownBorder": c["selection"],
        "settings.dropdownForeground": c["foreground"],
        "settings.headerForeground": c["foregroundBright"],
        "settings.modifiedItemIndicator": c["accent"],
        "settings.numberInputBackground": c["surface"],
        "settings.numberInputBorder": c["selection"],
        "settings.numberInputForeground": c["foreground"],
        "settings.textInputBackground": c["surface"],
        "settings.textInputBorder": c["selection"],
        "settings.textInputForeground": c["foreground"],
        "welcomePage.background": c["background"],
        "welcomePage.progress.background": c["surface"],
        "welcomePage.progress.foreground": c["accent"],
        "walkThrough.embeddedEditorBackground": c["surface"],
        "gitDecoration.addedResourceForeground": c["success"],
        "gitDecoration.conflictingResourceForeground": c["magenta"],
        "gitDecoration.deletedResourceForeground": c["danger"],
        "gitDecoration.ignoredResourceForeground": c["foregroundInactive"],
        "gitDecoration.modifiedResourceForeground": c["accent"],
        "gitDecoration.renamedResourceForeground": c["info"],
        "gitDecoration.stageDeletedResourceForeground": c["danger"],
        "gitDecoration.stageModifiedResourceForeground": c["accent"],
        "gitDecoration.submoduleResourceForeground": c["cyan"],
        "gitDecoration.untrackedResourceForeground": c["success"],
        "debugToolBar.background": c["surface"],
        "debugIcon.breakpointForeground": c["danger"],
        "debugIcon.breakpointCurrentStackframeForeground": c["accent"],
        "debugIcon.continueForeground": c["success"],
        "debugIcon.disconnectForeground": c["danger"],
        "debugIcon.pauseForeground": c["accent"],
        "debugIcon.restartForeground": c["success"],
        "debugIcon.startForeground": c["success"],
        "debugIcon.stepBackForeground": c["info"],
        "debugIcon.stepIntoForeground": c["info"],
        "debugIcon.stepOutForeground": c["info"],
        "debugIcon.stepOverForeground": c["info"],
        "debugIcon.stopForeground": c["danger"],
        "testing.iconErrored": c["danger"],
        "testing.iconFailed": c["danger"],
        "testing.iconPassed": c["success"],
        "testing.iconQueued": c["foregroundInactive"],
        "testing.iconSkipped": c["foregroundInactive"],
        "testing.iconUnset": c["foregroundInactive"],
        "testing.iconRunning": c["accent"],
        "testing.message.error.decorationForeground": c["danger"],
        "testing.message.info.decorationForeground": c["info"],
        "terminal.background": t["background"],
        "terminal.foreground": t["foreground"],
        "terminal.border": c["surface"],
        "terminal.findMatchBackground": alpha(c["accent"], 85),
        "terminal.findMatchBorder": c["accent"],
        "terminal.findMatchHighlightBackground": alpha(c["accent"], 40),
        "terminal.selectionBackground": alpha(t["selection"]["color"], round(255 * t["selection"]["alpha"])),
        "terminalCursor.background": t["cursorText"],
        "terminalCursor.foreground": t["cursor"],
        "terminalCommandDecoration.defaultBackground": c["foregroundInactive"],
        "terminalCommandDecoration.errorBackground": c["danger"],
        "terminalCommandDecoration.successBackground": c["success"],
        "terminalOverviewRuler.cursorForeground": t["cursor"],
        "terminalOverviewRuler.findMatchForeground": c["accent"],
    }
    for index, name in enumerate(ansi_names):
        colors[f"terminal.ansi{name}"] = t["ansi"][index]
        colors[f"terminal.ansiBright{name}"] = t["bright"][index]

    token_colors = [
        {"name": "Comments", "scope": ["comment", "punctuation.definition.comment"], "settings": {"foreground": c["foregroundInactive"], "fontStyle": "italic"}},
        {"name": "Strings", "scope": ["string", "string.quoted", "string.template", "punctuation.definition.string"], "settings": {"foreground": c["success"]}},
        {"name": "Numbers and language constants", "scope": ["constant.numeric", "constant.language", "constant.character", "constant.other"], "settings": {"foreground": c["magenta"]}},
        {"name": "Variables", "scope": ["variable", "variable.other", "meta.definition.variable.name"], "settings": {"foreground": c["foreground"]}},
        {"name": "Parameters", "scope": ["variable.parameter", "meta.parameter"], "settings": {"foreground": c["foregroundSecondary"]}},
        {"name": "Language variables", "scope": ["variable.language", "variable.other.readwrite.instance"], "settings": {"foreground": c["cyan"], "fontStyle": "italic"}},
        {"name": "Control keywords", "scope": ["keyword", "keyword.control", "storage.type", "storage.modifier"], "settings": {"foreground": c["danger"]}},
        {"name": "Operators", "scope": ["keyword.operator", "keyword.other.unit", "punctuation.separator", "punctuation.terminator"], "settings": {"foreground": c["foregroundSecondary"]}},
        {"name": "Functions", "scope": ["entity.name.function", "support.function", "meta.function-call", "variable.function"], "settings": {"foreground": c["accent"]}},
        {"name": "Types", "scope": ["entity.name.type", "entity.name.class", "entity.name.struct", "entity.name.enum", "support.type", "support.class"], "settings": {"foreground": c["accent"]}},
        {"name": "Namespaces", "scope": ["entity.name.namespace", "entity.name.module", "support.module"], "settings": {"foreground": c["cyan"]}},
        {"name": "Members and properties", "scope": ["variable.other.property", "variable.other.object.property", "support.variable.property", "meta.object-literal.key"], "settings": {"foreground": c["info"]}},
        {"name": "Tags", "scope": ["entity.name.tag", "entity.name.tag.html", "entity.name.tag.xml", "punctuation.definition.tag"], "settings": {"foreground": c["cyan"]}},
        {"name": "Attributes", "scope": ["entity.other.attribute-name", "entity.other.attribute-name.html", "entity.other.attribute-name.xml"], "settings": {"foreground": c["accent"]}},
        {"name": "Regular expressions", "scope": ["string.regexp", "constant.other.character-class.regexp", "keyword.operator.quantifier.regexp"], "settings": {"foreground": c["cyan"]}},
        {"name": "Escapes", "scope": ["constant.character.escape", "constant.character.entity", "constant.character.format.placeholder"], "settings": {"foreground": c["accent"]}},
        {"name": "Punctuation", "scope": ["punctuation", "meta.brace", "meta.delimiter"], "settings": {"foreground": c["foregroundSecondary"]}},
        {"name": "Decorators and annotations", "scope": ["meta.decorator", "punctuation.decorator", "storage.type.annotation"], "settings": {"foreground": c["magenta"]}},
        {"name": "JSON keys", "scope": ["support.type.property-name.json", "meta.structure.dictionary.key.python"], "settings": {"foreground": c["info"]}},
        {"name": "CSS selectors", "scope": ["entity.other.attribute-name.class.css", "entity.other.attribute-name.id.css", "entity.name.tag.css"], "settings": {"foreground": c["cyan"]}},
        {"name": "CSS properties", "scope": ["support.type.property-name.css", "support.type.vendored.property-name.css"], "settings": {"foreground": c["info"]}},
        {"name": "Markdown headings", "scope": ["markup.heading", "entity.name.section.markdown", "punctuation.definition.heading.markdown"], "settings": {"foreground": c["accent"], "fontStyle": "bold"}},
        {"name": "Markdown bold", "scope": ["markup.bold", "punctuation.definition.bold.markdown"], "settings": {"foreground": c["foregroundBright"], "fontStyle": "bold"}},
        {"name": "Markdown italic", "scope": ["markup.italic", "punctuation.definition.italic.markdown"], "settings": {"foreground": c["foregroundSecondary"], "fontStyle": "italic"}},
        {"name": "Markdown links", "scope": ["markup.underline.link", "string.other.link", "meta.link.inline.markdown"], "settings": {"foreground": c["info"], "fontStyle": "underline"}},
        {"name": "Markdown quotes", "scope": ["markup.quote", "punctuation.definition.blockquote.markdown"], "settings": {"foreground": c["foregroundSecondary"], "fontStyle": "italic"}},
        {"name": "Markup inserted", "scope": ["markup.inserted", "meta.diff.header.to-file"], "settings": {"foreground": c["success"]}},
        {"name": "Markup deleted", "scope": ["markup.deleted", "meta.diff.header.from-file"], "settings": {"foreground": c["danger"]}},
        {"name": "Markup changed", "scope": ["markup.changed"], "settings": {"foreground": c["accent"]}},
        {"name": "Invalid", "scope": ["invalid", "invalid.illegal", "invalid.deprecated"], "settings": {"foreground": c["danger"], "fontStyle": "bold underline"}},
    ]

    semantic = {
        "namespace": c["cyan"],
        "type": c["accent"],
        "class": c["accent"],
        "enum": c["accent"],
        "interface": c["accent"],
        "struct": c["accent"],
        "typeParameter": c["magenta"],
        "parameter": c["foregroundSecondary"],
        "variable": c["foreground"],
        "variable.readonly": {"foreground": c["magenta"], "fontStyle": "italic"},
        "property": c["info"],
        "enumMember": c["magenta"],
        "event": c["cyan"],
        "function": c["accent"],
        "method": c["accent"],
        "macro": c["magenta"],
        "label": c["cyan"],
        "comment": {"foreground": c["foregroundInactive"], "fontStyle": "italic"},
        "string": c["success"],
        "number": c["magenta"],
        "regexp": c["cyan"],
        "operator": c["foregroundSecondary"],
        "decorator": c["magenta"],
        "keyword": c["danger"],
        "*.declaration": {"fontStyle": "bold"},
        "*.deprecated": {"fontStyle": "strikethrough"},
        "*.documentation": {"foreground": c["foregroundSecondary"]},
        "*.static": {"fontStyle": "italic"},
    }

    return {
        "$schema": "vscode://schemas/color-theme",
        "name": palette["name"],
        "type": palette["appearance"],
        "semanticHighlighting": True,
        "colors": colors,
        "tokenColors": token_colors,
        "semanticTokenColors": semantic,
    }


def render_theme(palette: dict[str, Any]) -> str:
    return json.dumps(build_theme(palette), indent=2, ensure_ascii=False) + "\n"


def load_palette(expected_id: str, appearance: str, path: Path) -> dict[str, Any]:
    palette_bytes = path.read_bytes()
    digest = hashlib.sha256(palette_bytes).hexdigest()
    if digest != PALETTE_SHA256[expected_id]:
        raise ValueError(f"{path.relative_to(ROOT)} differs from canonical SHA-256: {digest}")
    palette = json.loads(palette_bytes)
    if palette.get("schemaVersion") != 1 or palette.get("id") != expected_id:
        raise ValueError(f"{path.relative_to(ROOT)} has invalid identity")
    if palette.get("appearance") != appearance or palette.get("colorSpace") != "srgb":
        raise ValueError(f"{path.relative_to(ROOT)} must be the {appearance} sRGB variant")
    return palette


def render_all() -> dict[Path, str]:
    return {
        output_path: render_theme(load_palette(variant_id, appearance, palette_path))
        for variant_id, appearance, palette_path, output_path in VARIANTS
    }


def write_or_check(outputs: dict[Path, str], check: bool) -> int:
    unexpected = sorted(set((ROOT / "themes").glob("*-color-theme.json")) - set(outputs))
    if unexpected:
        for path in unexpected:
            print(f"unexpected generated output: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    stale: list[Path] = []
    for path, expected in outputs.items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.exists() else ""
            if actual != expected:
                stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}")

    if stale:
        for path in stale:
            print(f"{path.relative_to(ROOT)} is stale; run python3 scripts/generate.py", file=sys.stderr)
        return 1
    if check:
        print("current: " + ", ".join(str(path.relative_to(ROOT)) for path in outputs))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if a generated theme is stale")
    args = parser.parse_args()
    try:
        outputs = render_all()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"generation failed: {error}", file=sys.stderr)
        return 2
    return write_or_check(outputs, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
