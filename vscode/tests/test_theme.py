from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check  # noqa: E402
import generate  # noqa: E402


class VSCodeThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.palette_path = ROOT / "palette" / "apollo.json"
        cls.palette = json.loads(cls.palette_path.read_text(encoding="utf-8"))
        cls.theme_path = ROOT / "themes" / "apollo-color-theme.json"
        cls.theme = json.loads(cls.theme_path.read_text(encoding="utf-8"))

    def test_readme_documentation_contract(self) -> None:
        decoys = """
<!-- Apollo Dark and Apollo Light -->
![Apollo Dark](preview.svg)
![Apollo Light][preview]
<img alt="Apollo Light" src="badge.svg">
<span hidden>Apollo Dark</span>
<span aria-hidden="true">Apollo Light</span>
<span style="display: none">Apollo Light</span>
`Apollo Dark`
``Apollo Dark``
```Apollo Light```
<code>Apollo Light</code>
    Apollo Dark
Apollo Dark.md
Apollo Light.json
```text
Apollo Dark
Apollo Light
```
"""
        prose = check.visible_prose(decoys)
        self.assertNotIn("Apollo Dark", prose)
        self.assertNotIn("Apollo Light", prose)
        visible_html = check.visible_prose(
            '<span aria-hidden="false">Apollo Dark and Apollo Light</span>'
        )
        self.assertIn("Apollo Dark", visible_html)
        self.assertIn("Apollo Light", visible_html)
        linked = check.visible_prose("[Apollo Dark](dark.md) and [Apollo Light](light.md)")
        self.assertIn("Apollo Dark", linked)
        self.assertIn("Apollo Light", linked)
        sentences = check.visible_prose("Apollo Dark. Apollo Light is supported.")
        self.assertIn("Apollo Dark", sentences)
        self.assertIn("Apollo Light", sentences)
        padded = check.visible_prose(
            "before `` Apollo Dark `` after\n"
            "left ```  Apollo Light  ``` right\n"
            "start ``` `` Apollo Dark `` ``` finish"
        )
        self.assertEqual(padded, "before  after\nleft  right\nstart  finish")
        multiline = check.visible_prose(
            "before `` Apollo Dark\nApollo Light `` after\nvisible words stay"
        )
        self.assertNotIn("Apollo Dark", multiline)
        self.assertNotIn("Apollo Light", multiline)
        self.assertIn("before  after", multiline)
        self.assertIn("visible words stay", multiline)
        listed_fences = check.visible_prose(
            "Before.\n"
            "- ```text\n"
            "  Apollo Dark\n"
            "  ```\n"
            "Between.\n"
            "10. ~~~text\n"
            "    Apollo Light\n"
            "    ~~~\n"
            "After.\n"
        )
        self.assertEqual(" ".join(listed_fences.split()), "Before. Between. After.")
        listed_indented = check.visible_prose(
            "- Item.\n\n"
            "      Apollo Dark\n"
            "1. Item.\n\n"
            "       Apollo Light\n"
            "Visible.\n"
        )
        self.assertNotIn("Apollo Dark", listed_indented)
        self.assertNotIn("Apollo Light", listed_indented)
        self.assertIn("Visible.", listed_indented)
        tab = chr(9)
        mixed_indented = check.visible_prose(
            f" {tab}Apollo Dark\n"
            f"   {tab}Apollo Light\n"
            "Visible root prose.\n"
            "- Item.\n\n"
            f"  {tab}  Apollo Dark\n"
            "1. Item.\n\n"
            f"   {tab}   Apollo Light\n"
            "Visible list prose.\n"
        )
        self.assertNotIn("Apollo Dark", mixed_indented)
        self.assertNotIn("Apollo Light", mixed_indented)
        self.assertIn("Visible root prose.", mixed_indented)
        self.assertIn("Visible list prose.", mixed_indented)
        escaped_code = check.visible_prose(
            "Before \\`Apollo Dark\\` and \\`Apollo Light\\` after."
        )
        self.assertIn("Apollo Dark", escaped_code)
        self.assertIn("Apollo Light", escaped_code)
        self.assertIn("Before", escaped_code)
        self.assertIn("after.", escaped_code)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        check.validate_readme_contract(readme)
        required = ("Apollo Dark", "Apollo Light", "**Apollo**", "**Apollo Light**")
        for token in required:
            with self.subTest(token=token):
                mutated = readme.replace(token, "")
                self.assertNotEqual(mutated, readme)
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(mutated)
                self.assertIn(token, str(caught.exception))

        for marker in check.README_MARKERS:
            with self.subTest(marker_outside_activation=marker):
                relocated = readme.replace(marker, "").replace("## Coverage", f"{marker}\n\n## Coverage", 1)
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(relocated)
                self.assertIn(marker, str(caught.exception))

    def test_visible_prose_hides_closed_and_unclosed_comments(self) -> None:
        closed = check.visible_prose("Before.<!-- Apollo Dark and Apollo Light -->After.")
        self.assertEqual(closed, "Before.After.")
        unclosed = check.visible_prose("Before.<!-- Apollo Dark\nApollo Light")
        self.assertEqual(unclosed, "Before.")

    def test_readme_selector_labels_require_exact_token_boundaries(self) -> None:
        dark_marker, light_marker = check.README_MARKERS

        def contract(dark: str = dark_marker, light: str = light_marker) -> str:
            return (
                "Apollo Dark and Apollo Light are available.\n\n"
                "## Activate\n\n"
                f"Select {dark} or {light}.\n\n"
                "## Next\n"
            )

        check.validate_readme_contract(contract())
        for marker, argument in ((dark_marker, "dark"), (light_marker, "light")):
            for invalid in ("X" + marker, marker + "X", "*" + marker + "*"):
                with self.subTest(marker=marker, invalid=invalid):
                    kwargs = {argument: invalid}
                    with self.assertRaises(AssertionError) as caught:
                        check.validate_readme_contract(contract(**kwargs))
                    self.assertIn(marker, str(caught.exception))

    def test_palette_snapshot_is_canonical(self) -> None:
        digest = hashlib.sha256(self.palette_path.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
        )

    def test_generated_theme_is_current(self) -> None:
        self.assertEqual(self.theme_path.read_text(encoding="utf-8"), generate.render_theme(self.palette))

    def test_terminal_arrays_match_palette(self) -> None:
        colors = self.theme["colors"]
        ansi_keys = [
            "terminal.ansiBlack",
            "terminal.ansiRed",
            "terminal.ansiGreen",
            "terminal.ansiYellow",
            "terminal.ansiBlue",
            "terminal.ansiMagenta",
            "terminal.ansiCyan",
            "terminal.ansiWhite",
        ]
        bright_keys = [key.replace("terminal.ansi", "terminal.ansiBright") for key in ansi_keys]
        self.assertEqual([colors[key] for key in ansi_keys], self.palette["terminal"]["ansi"])
        self.assertEqual([colors[key] for key in bright_keys], self.palette["terminal"]["bright"])
        self.assertEqual(colors["terminal.foreground"], "#cfbc97")
        self.assertEqual(colors["terminalCursor.foreground"], "#fabd2f")

    def test_restricted_color_is_only_bright_black(self) -> None:
        found: list[str] = []

        def visit(value: object, path: str) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    visit(child, f"{path}.{key}" if path else key)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, f"{path}[{index}]")
            elif isinstance(value, str) and value.lower() == "#665c54":
                found.append(path)

        visit(self.theme, "")
        self.assertEqual(found, ["colors.terminal.ansiBrightBlack"])

    def test_semantic_and_textmate_coverage(self) -> None:
        semantic = self.theme["semanticTokenColors"]
        for token in ("class", "function", "keyword", "number", "property", "string", "variable.readonly"):
            self.assertIn(token, semantic)

        scopes = {
            scope
            for rule in self.theme["tokenColors"]
            for scope in (rule["scope"] if isinstance(rule["scope"], list) else [rule["scope"]])
        }
        for scope in ("comment", "entity.name.function", "entity.name.type", "keyword.control", "markup.heading", "string"):
            self.assertIn(scope, scopes)

    def test_light_variant_contract(self) -> None:
        palette_path = ROOT / "palette" / "apollo-light.json"
        self.assertEqual(
            hashlib.sha256(palette_path.read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        palette = json.loads(palette_path.read_text(encoding="utf-8"))
        theme_path = ROOT / "themes" / "apollo-light-color-theme.json"
        theme_text = theme_path.read_text(encoding="utf-8")
        theme = json.loads(theme_text)
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))

        self.assertEqual((palette["id"], palette["appearance"]), ("apollo-light", "light"))
        self.assertEqual((theme["name"], theme["type"]), ("Apollo Light", "light"))
        self.assertEqual(theme_text, generate.render_theme(palette))
        self.assertEqual(theme["colors"]["editor.background"], palette["colors"]["background"])
        self.assertEqual(
            package["contributes"]["themes"],
            [
                {"label": "Apollo", "uiTheme": "vs-dark", "path": "./themes/apollo-color-theme.json"},
                {"label": "Apollo Light", "uiTheme": "vs", "path": "./themes/apollo-light-color-theme.json"},
            ],
        )
        self.assertEqual((package["version"], lock["version"], lock["packages"][""]["version"]), ("0.2.0",) * 3)

    def test_check_rejects_unexpected_generated_output(self) -> None:
        unexpected = ROOT / "themes" / "unexpected-color-theme.json"
        unexpected.write_text("{}\n", encoding="utf-8")
        try:
            result = generate.write_or_check(generate.render_all(), check=True)
        finally:
            unexpected.unlink()
        self.assertEqual(result, 1)

    def test_workbench_coverage(self) -> None:
        colors = self.theme["colors"]
        required = {
            "activityBar.background",
            "button.background",
            "diffEditor.insertedTextBackground",
            "editor.background",
            "editorError.foreground",
            "editorGutter.addedBackground",
            "input.background",
            "list.activeSelectionBackground",
            "menu.background",
            "notificationCenter.border",
            "panel.background",
            "peekView.border",
            "sideBar.background",
            "statusBar.background",
            "tab.activeBackground",
            "terminal.background",
            "titleBar.activeBackground",
        }
        self.assertTrue(required.issubset(colors), sorted(required - colors.keys()))
        self.assertGreaterEqual(len(colors), 150)


if __name__ == "__main__":
    unittest.main()
