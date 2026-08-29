import hashlib
import importlib.util
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate.py"
COLOR_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
LIGHT_SHA256 = "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763"
EXPECTED_TOP_LEVEL = {"schemaVersion", "id", "name", "description", "appearance", "colorSpace", "provenance", "colors", "roles", "terminal", "constraints"}
VARIANTS = (
    ("apollo", "Apollo", "dark", ROOT / "palette" / "apollo.json", ROOT / "apollo.toml"),
    ("apollo-light", "Apollo Light", "light", ROOT / "palette" / "apollo-light.json", ROOT / "apollo-light.toml"),
)


def load_generator():
    spec = importlib.util.spec_from_file_location("generate", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SonicTermThemeTests(unittest.TestCase):
    def test_light_palette_snapshot_is_canonical(self):
        palette_path = ROOT / "palette" / "apollo-light.json"
        self.assertEqual(hashlib.sha256(palette_path.read_bytes()).hexdigest(), LIGHT_SHA256)

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
                self.assertEqual(set(terminal), {"foreground", "background", "cursor", "cursorText", "selection", "ansi", "bright"})
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
        for palette_id, name, appearance, palette_path, artifact_path in VARIANTS:
            with self.subTest(variant=palette_id):
                palette = json.loads(palette_path.read_text(encoding="utf-8"))
                theme = tomllib.loads(artifact_path.read_text(encoding="utf-8"))
                terminal = palette["terminal"]
                colors = theme["colors"]
                self.assertEqual(theme["name"], name)
                self.assertEqual(theme["appearance"], appearance)
                self.assertEqual(colors["background"], terminal["background"])
                self.assertEqual(colors["foreground"], terminal["foreground"])
                self.assertEqual(colors["cursor"], terminal["cursor"])
                self.assertEqual(colors["cursor_text"], terminal["cursorText"])
                self.assertEqual(colors["selection_bg"], terminal["selection"]["color"])
                self.assertEqual(colors["selection_fg"], palette["colors"]["foregroundSecondary"])
                self.assertEqual([colors["ansi"][slot] for slot in COLOR_NAMES], terminal["ansi"])
                self.assertEqual([colors["bright"][slot] for slot in COLOR_NAMES], terminal["bright"])

    def test_tab_slots_follow_canonical_roles(self):
        for palette_id, _, _, palette_path, artifact_path in VARIANTS:
            with self.subTest(variant=palette_id):
                palette = json.loads(palette_path.read_text(encoding="utf-8"))
                tab = tomllib.loads(artifact_path.read_text(encoding="utf-8"))["colors"]["tab"]
                colors = palette["colors"]
                self.assertEqual(tab, {
                    "bar_bg": colors["background"],
                    "active_bg": colors["background"],
                    "active_fg": colors["accent"],
                    "inactive_bg": colors["background"],
                    "inactive_fg": colors["foregroundInactive"],
                    "hover_bg": colors["surfaceHover"],
                    "hover_fg": colors["foregroundSecondary"],
                    "close_button_fg": colors["accent"],
                })

    def test_generator_is_deterministic(self):
        generator = load_generator()
        expected = [(artifact, palette) for _, _, _, palette, artifact in VARIANTS]
        self.assertEqual(list(generator.OUTPUTS.items()), expected)
        first = generator.render_outputs()
        second = generator.render_outputs()
        self.assertEqual(first, second)
        for artifact_path, rendered in first.items():
            self.assertEqual(rendered, artifact_path.read_text(encoding="utf-8"))

    def test_generator_finds_unexpected_native_outputs(self):
        generator = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("apollo.toml", "apollo-light.toml", "apollo-copy.toml"):
                (root / name).touch()
            self.assertEqual(generator.find_unexpected_outputs(root), [root / "apollo-copy.toml"])


if __name__ == "__main__":
    unittest.main()
