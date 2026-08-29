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
    ("apollo", "Apollo", "dark", ROOT / "palette" / "apollo.json", ROOT / "Apollo.terminal"),
    ("apollo-light", "Apollo Light", "light", ROOT / "palette" / "apollo-light.json", ROOT / "Apollo Light.terminal"),
)
ANSI_KEYS = (
    "ANSIBlackColor", "ANSIRedColor", "ANSIGreenColor", "ANSIYellowColor",
    "ANSIBlueColor", "ANSIMagentaColor", "ANSICyanColor", "ANSIWhiteColor",
    "ANSIBrightBlackColor", "ANSIBrightRedColor", "ANSIBrightGreenColor", "ANSIBrightYellowColor",
    "ANSIBrightBlueColor", "ANSIBrightMagentaColor", "ANSIBrightCyanColor", "ANSIBrightWhiteColor",
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generate", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def decode_color(data):
    archive = plistlib.loads(data)
    root = archive["$objects"][archive["$top"]["root"].data]
    components = [float(value) for value in root["NSRGB"].rstrip(b"\0").decode("ascii").split()]
    return components + ([1.0] if len(components) == 3 else [])


def color_hex(data):
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in decode_color(data)[:3])


class TerminalThemeTests(unittest.TestCase):
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

    def test_archived_colors_match_palette(self):
        expected_keys = {"ProfileCurrentVersion", "name", "type", "BackgroundColor", "CursorColor", "SelectionColor", "TextBoldColor", "TextColor", *ANSI_KEYS}
        for palette_id, name, _, palette_path, artifact_path in VARIANTS:
            with self.subTest(variant=palette_id):
                palette = json.loads(palette_path.read_text(encoding="utf-8"))
                profile = plistlib.loads(artifact_path.read_bytes())
                terminal = palette["terminal"]
                expected = {
                    **dict(zip(ANSI_KEYS, terminal["ansi"] + terminal["bright"])),
                    "BackgroundColor": terminal["background"],
                    "CursorColor": terminal["cursor"],
                    "SelectionColor": terminal["selection"]["color"],
                    "TextBoldColor": palette["colors"]["foregroundBright"],
                    "TextColor": terminal["foreground"],
                }
                self.assertEqual(set(profile), expected_keys)
                self.assertEqual(profile["name"], name)
                self.assertEqual(profile["type"], "Window Settings")
                for key, expected_hex in expected.items():
                    self.assertEqual(color_hex(profile[key]), expected_hex)
                self.assertAlmostEqual(decode_color(profile["SelectionColor"])[3], terminal["selection"]["alpha"])

    def test_profile_contains_only_theme_metadata_and_colors(self):
        for _, name, _, _, artifact_path in VARIANTS:
            profile = plistlib.loads(artifact_path.read_bytes())
            self.assertEqual(profile["name"], name)
            self.assertEqual(profile["type"], "Window Settings")

    def test_bright_black_is_ansi_only(self):
        palette = json.loads((ROOT / "palette" / "apollo.json").read_text(encoding="utf-8"))
        profile = plistlib.loads((ROOT / "Apollo.terminal").read_bytes())
        restricted = palette["colors"]["ansiBrightBlack"]
        color_keys = [key for key, value in profile.items() if isinstance(value, bytes)]
        uses = [key for key in color_keys if color_hex(profile[key]) == restricted]
        self.assertEqual(uses, ["ANSIBrightBlackColor"])

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
            for name in ("Apollo.terminal", "Apollo Light.terminal", "Apollo Copy.terminal"):
                (root / name).touch()
            self.assertEqual(generator.find_unexpected_outputs(root), [root / "Apollo Copy.terminal"])


if __name__ == "__main__":
    unittest.main()
