from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check  # noqa: E402
import generate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PALETTE = ROOT / "palette" / "apollo.json"
GENERATED = (
    ROOT / "colors" / "apollo.lua",
    ROOT / "lua" / "apollo" / "palette.lua",
    ROOT / "lua" / "apollo" / "init.lua",
)
EXPECTED_PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"
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


class ThemeTests(unittest.TestCase):
    def test_palette_snapshot_is_exact(self) -> None:
        self.assertEqual(
            hashlib.sha256(PALETTE.read_bytes()).hexdigest(),
            EXPECTED_PALETTE_SHA256,
        )

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
Apollo Light.txt
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
        required = (
            "Apollo Dark",
            "Apollo Light",
            "vim.cmd.colorscheme('apollo')",
            "vim.cmd.colorscheme('apollo-light')",
        )
        for token in required:
            with self.subTest(token=token):
                mutated = readme.replace(token, "")
                self.assertNotEqual(mutated, readme)
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(mutated)
                self.assertIn(token, str(caught.exception))

    def test_visible_prose_hides_closed_and_unclosed_comments(self) -> None:
        closed = check.visible_prose("Before.<!-- Apollo Dark and Apollo Light -->After.")
        self.assertEqual(closed, "Before.After.")
        unclosed = check.visible_prose("Before.<!-- Apollo Dark\nApollo Light")
        self.assertEqual(unclosed, "Before.")

    def test_readme_native_commands_require_exact_activate_boundaries(self) -> None:
        dark_marker, light_marker = check.README_MARKERS

        def contract(dark: str = dark_marker, light: str = light_marker) -> str:
            return (
                "Apollo Dark and Apollo Light are available.\n\n"
                "## Activate\n\n"
                "```lua\n"
                f"{dark}\n"
                "```\n\n"
                f"Use `{light}` for the light variant.\n\n"
                "## Next\n"
            )

        check.validate_readme_contract(contract())
        for marker, argument in ((dark_marker, "dark"), (light_marker, "light")):
            for invalid in ("X" + marker, marker + "X", marker + " extra"):
                with self.subTest(marker=marker, invalid=invalid):
                    kwargs = {argument: invalid}
                    with self.assertRaises(AssertionError) as caught:
                        check.validate_readme_contract(contract(**kwargs))
                    self.assertIn(marker, str(caught.exception))

            with self.subTest(marker_outside_activation=marker):
                kwargs = {argument: "vim.cmd.colorscheme('disabled')"}
                relocated = marker + "\n\n" + contract(**kwargs)
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(relocated)
                self.assertIn(marker, str(caught.exception))

        check.validate_readme_contract(
            contract(dark="  " + dark_marker + "\t", light=" " + light_marker + " ")
        )

    def test_generated_theme_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_light_variant_contract(self) -> None:
        palette_path = ROOT / "palette" / "apollo-light.json"
        self.assertEqual(
            hashlib.sha256(palette_path.read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        palette = json.loads(palette_path.read_text(encoding="utf-8"))
        entrypoint = (ROOT / "colors" / "apollo-light.lua").read_text(encoding="utf-8")
        light_palette = (ROOT / "lua" / "apollo" / "light-palette.lua").read_text(encoding="utf-8")
        implementation = (ROOT / "lua" / "apollo" / "light.lua").read_text(encoding="utf-8")
        self.assertEqual((palette["id"], palette["appearance"]), ("apollo-light", "light"))
        self.assertEqual(entrypoint, "-- Generated by scripts/generate.py; do not edit.\nrequire('apollo.light').load()\n")
        self.assertIn("background = '#f9f5d7'", light_palette)
        self.assertIn("vim.o.background = 'light'", implementation)
        self.assertIn("vim.g.colors_name = 'apollo-light'", implementation)

    def test_check_rejects_unexpected_generated_output(self) -> None:
        unexpected = ROOT / "colors" / "unexpected.lua"
        unexpected.write_text("-- unexpected\n", encoding="utf-8")
        try:
            result = generate.write_or_check(generate.render_all(), check=True)
        finally:
            unexpected.unlink()
        self.assertEqual(result, 1)

    def test_native_theme_uses_only_canonical_colors(self) -> None:
        palette = json.loads(PALETTE.read_text(encoding="utf-8"))
        canonical = {value.lower() for value in palette["colors"].values()}
        canonical.update(value.lower() for value in palette["terminal"]["ansi"])
        canonical.update(value.lower() for value in palette["terminal"]["bright"])
        canonical.update(
            palette["terminal"][key].lower()
            for key in ("foreground", "background", "cursor", "cursorText")
        )
        canonical.add(palette["terminal"]["selection"]["color"].lower())

        literals: set[str] = set()
        for path in GENERATED:
            literals.update(
                match.lower()
                for match in re.findall(
                    r"#[0-9a-fA-F]{6}", path.read_text(encoding="utf-8")
                )
            )
        self.assertTrue(literals, "generated Neovim theme contains no color literals")
        self.assertLessEqual(literals, canonical)
        self.assertFalse(literals & OBSOLETE_COLORS)


if __name__ == "__main__":
    unittest.main()
