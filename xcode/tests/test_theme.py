import hashlib
import json
import plistlib
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check  # noqa: E402

PALETTE_PATH = ROOT / "palette" / "apollo.json"
THEME_PATH = ROOT / "Apollo.xccolortheme"
PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"

XCODE_26_SYNTAX_ROLES = {
    "xcode.syntax.attribute",
    "xcode.syntax.character",
    "xcode.syntax.comment",
    "xcode.syntax.comment.doc",
    "xcode.syntax.comment.doc.keyword",
    "xcode.syntax.declaration.other",
    "xcode.syntax.declaration.type",
    "xcode.syntax.identifier.class",
    "xcode.syntax.identifier.class.system",
    "xcode.syntax.identifier.constant",
    "xcode.syntax.identifier.constant.system",
    "xcode.syntax.identifier.function",
    "xcode.syntax.identifier.function.system",
    "xcode.syntax.identifier.macro",
    "xcode.syntax.identifier.macro.system",
    "xcode.syntax.identifier.type",
    "xcode.syntax.identifier.type.system",
    "xcode.syntax.identifier.variable",
    "xcode.syntax.identifier.variable.system",
    "xcode.syntax.keyword",
    "xcode.syntax.mark",
    "xcode.syntax.markup.aside.kind",
    "xcode.syntax.markup.code",
    "xcode.syntax.number",
    "xcode.syntax.plain",
    "xcode.syntax.preprocessor",
    "xcode.syntax.string",
    "xcode.syntax.url",
}


def rgba_hex(value):
    channels = [float(channel) for channel in value.split()]
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in channels[:3])


class XcodeThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palette_bytes = PALETTE_PATH.read_bytes()
        cls.palette = json.loads(cls.palette_bytes)
        cls.theme = plistlib.loads(THEME_PATH.read_bytes())

    def test_readme_documentation_contract(self):
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
Apollo Light.xccolortheme
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
            "Apollo.xccolortheme",
            "Apollo Light.xccolortheme",
        )
        for token in required:
            with self.subTest(token=token):
                mutated = readme.replace(token, "")
                self.assertNotEqual(mutated, readme)
                with self.assertRaises(AssertionError) as caught:
                    check.validate_readme_contract(mutated)
                self.assertIn(token, str(caught.exception))

    def test_visible_prose_hides_closed_and_unclosed_comments(self):
        closed = check.visible_prose("Before.<!-- Apollo Dark and Apollo Light -->After.")
        self.assertEqual(closed, "Before.After.")
        unclosed = check.visible_prose("Before.<!-- Apollo Dark\nApollo Light")
        self.assertEqual(unclosed, "Before.")

    def test_readme_native_paths_require_exact_token_boundaries(self):
        dark_marker, light_marker = check.README_MARKERS

        def contract(dark=dark_marker, light=light_marker):
            return (
                "Apollo Dark and Apollo Light are available.\n\n"
                f"Use `{dark}` or `{light}`.\n"
            )

        check.validate_readme_contract(contract())
        for marker, argument in ((dark_marker, "dark"), (light_marker, "light")):
            for invalid in ("X" + marker, marker + "X"):
                with self.subTest(marker=marker, invalid=invalid):
                    kwargs = {argument: invalid}
                    with self.assertRaises(AssertionError) as caught:
                        check.validate_readme_contract(contract(**kwargs))
                    self.assertIn(marker, str(caught.exception))

    def test_palette_snapshot_is_canonical(self):
        self.assertEqual(hashlib.sha256(self.palette_bytes).hexdigest(), PALETTE_SHA256)

    def test_generated_themes_are_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_rejects_unexpected_generated_output(self):
        unexpected = ROOT / "Unexpected.xccolortheme"
        unexpected.write_bytes(plistlib.dumps({}))
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        finally:
            unexpected.unlink()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_xcode_26_syntax_role_map(self):
        syntax_colors = self.theme["DVTSourceTextSyntaxColors"]
        syntax_fonts = self.theme["DVTSourceTextSyntaxFonts"]
        self.assertEqual(set(syntax_colors), XCODE_26_SYNTAX_ROLES)
        self.assertEqual(set(syntax_fonts), XCODE_26_SYNTAX_ROLES)
        self.assertEqual(rgba_hex(syntax_colors["xcode.syntax.plain"]), self.palette["colors"]["foreground"])
        self.assertEqual(rgba_hex(syntax_colors["xcode.syntax.comment"]), self.palette["colors"]["foregroundInactive"])

    def test_editor_and_status_roles_use_exact_palette_colors(self):
        colors = self.palette["colors"]
        self.assertEqual(rgba_hex(self.theme["DVTSourceTextBackground"]), colors["background"])
        self.assertEqual(rgba_hex(self.theme["DVTSourceTextInsertionPointColor"]), colors["accent"])
        self.assertEqual(rgba_hex(self.theme["DVTScrollbarMarkerErrorColor"]), colors["danger"])
        self.assertEqual(rgba_hex(self.theme["DVTScrollbarMarkerDiffConflictColor"]), colors["danger"])
        self.assertEqual(rgba_hex(self.theme["DVTScrollbarMarkerWarningColor"]), colors["accent"])
        self.assertEqual(rgba_hex(self.theme["DVTConsoleDebuggerPromptTextColor"]), colors["success"])

    def test_light_variant_contract(self):
        palette_path = ROOT / "palette" / "apollo-light.json"
        self.assertEqual(
            hashlib.sha256(palette_path.read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        palette = json.loads(palette_path.read_text(encoding="utf-8"))
        theme = plistlib.loads((ROOT / "Apollo Light.xccolortheme").read_bytes())
        self.assertEqual((palette["id"], palette["appearance"]), ("apollo-light", "light"))
        self.assertEqual(rgba_hex(theme["DVTSourceTextBackground"]), palette["colors"]["background"])
        self.assertEqual(set(theme["DVTSourceTextSyntaxColors"]), XCODE_26_SYNTAX_ROLES)
        self.assertEqual(set(theme), set(self.theme))

    def test_restricted_bright_black_is_not_used_for_xcode_text(self):
        restricted = self.palette["colors"]["ansiBrightBlack"]
        color_values = [value for key, value in self.theme.items() if key.endswith("Color") or key == "DVTSourceTextBackground"]
        color_values.extend(self.theme["DVTSourceTextSyntaxColors"].values())
        self.assertNotIn(restricted, {rgba_hex(value) for value in color_values})


if __name__ == "__main__":
    unittest.main()
