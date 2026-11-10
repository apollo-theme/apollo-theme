import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate.py"
CHECKER_PATH = ROOT / "scripts" / "check.py"
NORMAL_NAMES = ("black", "red", "green", "yellow", "blue", "purple", "cyan", "white")
BRIGHT_NAMES = ("brightBlack", "brightRed", "brightGreen", "brightYellow", "brightBlue", "brightPurple", "brightCyan", "brightWhite")
LIGHT_SHA256 = "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763"
EXPECTED_TOP_LEVEL = {"schemaVersion", "id", "name", "description", "appearance", "colorSpace", "provenance", "colors", "roles", "terminal", "constraints"}
VARIANTS = (
    ("apollo", "Apollo", "dark", ROOT / "palette" / "apollo.json", ROOT / "apollo.json"),
    ("apollo-light", "Apollo Light", "light", ROOT / "palette" / "apollo-light.json", ROOT / "apollo-light.json"),
)
README_MARKERS = ('"colorScheme": "Apollo"', '"colorScheme": "Apollo Light"')


def load_generator():
    spec = importlib.util.spec_from_file_location("generate", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_checker():
    spec = importlib.util.spec_from_file_location("check", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def contract_fixture(prose, markers=README_MARKERS):
    return f"{prose}\n\n```\n" + "\n".join(markers) + "\n```\n"


class WindowsTerminalThemeTests(unittest.TestCase):
    def test_readme_contract(self):
        load_checker().validate_readme_contract()

    def test_readme_contract_rejects_each_missing_value(self):
        checker = load_checker()
        text = contract_fixture("Apollo Dark keeps the compatibility identity; Apollo Light keeps the light identity.")
        for value in ("Apollo Dark", "Apollo Light", *README_MARKERS):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, re.escape(value)):
                    checker.validate_readme_contract(text.replace(value, "", 1))

    def test_readme_contract_rejects_marker_prefixes_and_suffixes(self):
        checker = load_checker()
        prose = "Apollo Dark keeps compatibility; Apollo Light remains additive."
        mutations = {
            README_MARKERS[0]: ("X" + README_MARKERS[0], README_MARKERS[0] + "X", '"colorScheme": "ApolloX"'),
            README_MARKERS[1]: ("X" + README_MARKERS[1], README_MARKERS[1] + "X", '"colorScheme": "Apollo LightX"'),
        }
        for marker, decoys in mutations.items():
            index = README_MARKERS.index(marker)
            for decoy in decoys:
                with self.subTest(marker=marker, decoy=decoy):
                    markers = list(README_MARKERS)
                    markers[index] = decoy
                    with self.assertRaisesRegex(ValueError, re.escape(marker)):
                        checker.validate_readme_contract(contract_fixture(prose, markers))

    def test_readme_contract_ignores_nonvisible_names(self):
        checker = load_checker()
        hidden_sources = (
            "![Apollo Dark](dark.svg) ![Apollo Light](light.svg)",
            "[![Apollo Dark](badge.svg)](#) [![Apollo Light](badge-light.svg)](#)",
            "<!-- Apollo Dark and Apollo Light -->",
            "<!-- Apollo Dark and Apollo Light",
            "<span hidden>Apollo Dark and Apollo Light</span>",
            '<span aria-hidden="true">Apollo Dark and Apollo Light</span>',
            "```text\nApollo Dark and Apollo Light\n```",
            "    Apollo Dark and Apollo Light",
            "`Apollo Dark` and `Apollo Light`",
            "``Apollo Dark`` and ```Apollo Light```",
            "Apollo Dark.md and Apollo Light.md",
        )
        for source in hidden_sources:
            with self.subTest(source=source):
                with self.assertRaises(ValueError) as caught:
                    checker.validate_readme_contract(contract_fixture(source))
                self.assertIn("Apollo Dark", str(caught.exception))
                self.assertIn("Apollo Light", str(caught.exception))

    def test_readme_contract_keeps_visible_link_text(self):
        load_checker().validate_readme_contract(contract_fixture(
            "[Apollo Dark](dark) keeps compatibility; [Apollo Light](light) remains additive."
        ))

    def test_visible_prose_distinguishes_images_from_shortcut_links(self):
        checker = load_checker()
        images = """
![Apollo Dark](dark.svg)
![Apollo Light][light-image]
![Apollo Dark][]
![Apollo Light]
[light-image]: light.svg
[Apollo Dark]: dark.svg
[Apollo Light]: light.svg
"""
        self.assertEqual(checker.visible_prose(images), "")
        links = """
[Apollo Dark] and [Apollo Light]
[Apollo Dark]: dark
[Apollo Light]: light
"""
        self.assertEqual(checker.visible_prose(links), "Apollo Dark and Apollo Light")
        checker.validate_readme_contract(contract_fixture(links))

    def test_visible_prose_excludes_quoted_and_multiline_code(self):
        checker = load_checker()
        markdown = """
> ```text
> Apollo Dark
> ```
>     Apollo Light
> ordinary visible blockquote prose

``Apollo Dark
Apollo Light``
trailing visible text
"""
        self.assertEqual(
            checker.visible_prose(markdown),
            "ordinary visible blockquote prose trailing visible text",
        )
        with self.assertRaises(ValueError) as caught:
            checker.validate_readme_contract(contract_fixture(markdown))
        self.assertIn("Apollo Dark", str(caught.exception))
        self.assertIn("Apollo Light", str(caught.exception))
        quoted_indented = ">     Apollo Dark\n>\tApollo Light\n> \tApollo Dark\nVisible tail"
        self.assertEqual(checker.visible_prose(quoted_indented), "Visible tail")

    def test_visible_prose_tracks_hidden_html_structure(self):
        checker = load_checker()
        cases = (
            ("hidden sibling", "<span hidden>x</span>Apollo Dark<span>y</span>", "Apollo Dark y"),
            ("nested hidden", "<span hidden>x<span>Apollo Dark</span>z</span>Apollo Light", "Apollo Light"),
            ("unquoted aria hidden", "<span aria-hidden=true>Apollo Dark</span>Apollo Light", "Apollo Light"),
            ("false aria hidden", "<span aria-hidden=false>Apollo Dark</span>", "Apollo Dark"),
            ("visible nested", "<span>Apollo Dark<strong> and Apollo Light</strong></span>", "Apollo Dark and Apollo Light"),
            ("hidden styles", '<span style="display: none">Apollo Dark</span><span style="visibility: hidden">Apollo Light</span>visible', "visible"),
            ("hidden elements", "<code>Apollo Dark</code><pre>Apollo Light</pre><script>script</script><style>style</style><template>template</template>visible", "visible"),
            ("void metadata", '<img alt="Apollo Dark"><span>Apollo Light</span>', "Apollo Light"),
            ("unclosed hidden", "Apollo Dark<span hidden>Apollo Light", "Apollo Dark"),
            ("unclosed visible", "<span>Apollo Dark", "Apollo Dark"),
            ("malformed closing", "</span>Apollo Dark", "Apollo Dark"),
            ("unclosed comment", "Visible before<!-- Apollo Dark and Apollo Light", "Visible before"),
        )
        for label, text, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(checker.visible_prose(text), expected)

    def test_visible_prose_handles_markdown_fences(self):
        checker = load_checker()
        cases = (
            ("longer backtick closer", "```python\nApollo Dark\n  `````   \nApollo Light", "Apollo Light"),
            ("longer tilde closer", "~~~text\nApollo Dark\n   ~~~~~~ \t\nApollo Light", "Apollo Light"),
            ("short closer", "````text\nApollo Dark\n```\nApollo Light", ""),
            ("mismatched closer", "~~~text\nApollo Dark\n````\nApollo Light", ""),
            ("unclosed fence", "Apollo Dark\n```text\nApollo Light", "Apollo Dark"),
            ("inline triple backticks", "```Apollo Dark``` and Apollo Light", "and Apollo Light"),
        )
        for label, text, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(checker.visible_prose(text), expected)

    def test_visible_prose_excludes_list_nested_fences(self):
        checker = load_checker()
        cases = (
            (
                "unordered list",
                "- visible before\n- ~~~text\n  Apollo Dark and Apollo Light\n  ~~~~\n- visible after",
                "- visible before - visible after",
            ),
            (
                "ordered list",
                "1. visible before\n1. ```text\n   Apollo Dark\n   Apollo Light\n   `````\n2. visible after",
                "1. visible before 2. visible after",
            ),
            (
                "inline triple backticks",
                "- ```Apollo Dark``` and visible inline tail",
                "- and visible inline tail",
            ),
        )
        for label, text, expected in cases:
            with self.subTest(label=label):
                self.assertEqual(checker.visible_prose(text), expected)

    def test_visible_prose_excludes_list_indented_code(self):
        checker = load_checker()
        self.assertEqual(
            checker.visible_prose(
                "- visible before\n-     Apollo Dark\n"
                "1.     Apollo Light\n2. visible after"
            ),
            "- visible before 2. visible after",
        )
        self.assertEqual(
            checker.visible_prose(
                " \tApollo Dark\n   \tApollo Light\n"
                "-  \tApollo Dark\n1.    \tApollo Light\nVisible tail"
            ),
            "Visible tail",
        )

    def test_visible_prose_keeps_escaped_backticks_visible(self):
        checker = load_checker()
        escaped = r"\`Apollo Dark\` and \`Apollo Light\` remain visible"
        prose = checker.visible_prose(escaped)
        self.assertIn("Apollo Dark", prose)
        self.assertIn("Apollo Light", prose)
        checker.validate_readme_contract(contract_fixture(escaped))

    def test_light_palette_snapshot_is_canonical(self):
        path = ROOT / "palette" / "apollo-light.json"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), LIGHT_SHA256)

    def test_palette_variant_schema_and_semantics(self):
        for palette_id, name, appearance, palette_path, _ in VARIANTS:
            with self.subTest(variant=palette_id):
                palette = json.loads(palette_path.read_text(encoding="utf-8"))
                self.assertEqual(set(palette), EXPECTED_TOP_LEVEL)
                self.assertEqual(palette["schemaVersion"], 1)
                self.assertEqual((palette["id"], palette["name"], palette["appearance"]), (palette_id, name, appearance))
                self.assertEqual(palette["colorSpace"], "srgb")
                terminal = palette["terminal"]
                colors = palette["colors"]
                self.assertEqual(terminal["foreground"], colors["foreground"])
                self.assertEqual(terminal["background"], colors["background"])
                self.assertEqual(terminal["cursor"], colors["accent"])
                self.assertEqual(terminal["cursorText"], colors["background"])
                self.assertEqual(set(terminal["selection"]), {"color", "alpha", "foregroundMode"})
                self.assertEqual(terminal["selection"]["color"], colors["selection"])
                self.assertEqual(terminal["selection"]["alpha"], 0.5 if appearance == "dark" else 1.0)
                self.assertEqual(terminal["selection"]["foregroundMode"], "preserve")
                self.assertEqual(len(terminal["ansi"]), 8)
                self.assertEqual(len(terminal["bright"]), 8)

    def test_native_artifact_matches_terminal_palette(self):
        expected_keys = {"name", "background", "foreground", "cursorColor", "selectionBackground", *NORMAL_NAMES, *BRIGHT_NAMES}
        for palette_id, name, _, palette_path, artifact_path in VARIANTS:
            with self.subTest(variant=palette_id):
                palette = json.loads(palette_path.read_text(encoding="utf-8"))
                scheme = json.loads(artifact_path.read_text(encoding="utf-8"))
                terminal = palette["terminal"]
                self.assertEqual(set(scheme), expected_keys)
                self.assertEqual(scheme["name"], name)
                self.assertEqual(scheme["background"], terminal["background"])
                self.assertEqual(scheme["foreground"], terminal["foreground"])
                self.assertEqual(scheme["cursorColor"], terminal["cursor"])
                self.assertEqual(scheme["selectionBackground"], terminal["selection"]["color"])
                self.assertEqual([scheme[slot] for slot in NORMAL_NAMES], terminal["ansi"])
                self.assertEqual([scheme[slot] for slot in BRIGHT_NAMES], terminal["bright"])
                self.assertNotIn("magenta", scheme)
                self.assertNotIn("brightMagenta", scheme)

    def test_generator_is_deterministic(self):
        generator = load_generator()
        expected = [(artifact, palette) for _, _, _, palette, artifact in VARIANTS]
        self.assertEqual(list(generator.OUTPUTS.items()), expected)
        first = generator.render_outputs()
        self.assertEqual(first, generator.render_outputs())
        for artifact_path, rendered in first.items():
            self.assertEqual(rendered, artifact_path.read_text(encoding="utf-8"))

    def test_generator_finds_unexpected_native_outputs(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("apollo.json", "apollo-light.json", "apollo-copy.json"):
                (root / name).touch()
            self.assertEqual(generator.find_unexpected_outputs(root), [root / "apollo-copy.json"])


if __name__ == "__main__":
    unittest.main()
