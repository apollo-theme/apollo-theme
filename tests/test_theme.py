import hashlib
import importlib.util
import json
import plistlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate.py"
DARK_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"
LIGHT_SHA256 = "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763"
EXPECTED_TOP_LEVEL = {"schemaVersion", "id", "name", "description", "appearance", "colorSpace", "provenance", "colors", "roles", "terminal", "constraints"}
VARIANTS = (
    ("apollo", "Apollo", "dark", ROOT / "palette" / "apollo.json", ROOT / "Apollo.itermcolors"),
    ("apollo-light", "Apollo Light", "light", ROOT / "palette" / "apollo-light.json", ROOT / "Apollo Light.itermcolors"),
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generate", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def color_hex(value):
    channels = ("Red Component", "Green Component", "Blue Component")
    return "#" + "".join(f"{round(value[channel] * 255):02x}" for channel in channels)


class ItermThemeTests(unittest.TestCase):
    def test_palette_snapshot_is_canonical(self):
        path = ROOT / "palette" / "apollo.json"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), DARK_SHA256)

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

    def test_required_color_roles(self):
        for palette_id, _, _, palette_path, artifact_path in VARIANTS:
            with self.subTest(variant=palette_id):
                palette = json.loads(palette_path.read_text(encoding="utf-8"))
                theme = plistlib.loads(artifact_path.read_bytes())
                terminal = palette["terminal"]
                colors = palette["colors"]
                expected = {
                    **{f"Ansi {index} Color": value for index, value in enumerate(terminal["ansi"] + terminal["bright"])},
                    "Background Color": terminal["background"],
                    "Bold Color": colors["foregroundBright"],
                    "Cursor Color": terminal["cursor"],
                    "Cursor Text Color": terminal["cursorText"],
                    "Foreground Color": terminal["foreground"],
                    "Selection Color": terminal["selection"]["color"],
                    "Selected Text Color": terminal["foreground"],
                }
                self.assertEqual(set(theme), set(expected))
                for role, expected_hex in expected.items():
                    self.assertEqual(color_hex(theme[role]), expected_hex)
                    self.assertEqual(theme[role]["Color Space"], "sRGB")
                self.assertEqual(theme["Selection Color"]["Alpha Component"], terminal["selection"]["alpha"])

    def test_bright_black_is_ansi_only(self):
        palette = json.loads((ROOT / "palette" / "apollo.json").read_text(encoding="utf-8"))
        theme = plistlib.loads((ROOT / "Apollo.itermcolors").read_bytes())
        restricted = palette["colors"]["ansiBrightBlack"]
        uses = [key for key, value in theme.items() if color_hex(value) == restricted]
        self.assertEqual(uses, ["Ansi 8 Color"])

    def test_generator_has_deterministic_two_output_map(self):
        generator = load_generator()
        expected = [(artifact, palette) for _, _, _, palette, artifact in VARIANTS]
        self.assertEqual(list(generator.OUTPUTS.items()), expected)
        first = generator.render_outputs()
        self.assertEqual(first, generator.render_outputs())
        for artifact_path, rendered in first.items():
            self.assertEqual(rendered, artifact_path.read_bytes())

    def test_generator_finds_unexpected_native_outputs(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("Apollo.itermcolors", "Apollo Light.itermcolors", "Apollo Copy.itermcolors"):
                (root / name).touch()
            self.assertEqual(generator.find_unexpected_outputs(root), [root / "Apollo Copy.itermcolors"])


if __name__ == "__main__":
    unittest.main()
