import importlib.util
import json
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
ARTIFACT_PATH = ROOT / "apollo.toml"
GENERATOR_PATH = ROOT / "scripts" / "generate.py"
COLOR_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")


def load_generator():
    spec = importlib.util.spec_from_file_location("generate", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AlacrittyThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
        cls.theme = tomllib.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_native_artifact_matches_terminal_palette(self):
        terminal = self.palette["terminal"]
        colors = self.theme["colors"]
        self.assertEqual(colors["primary"], {"background": terminal["background"], "foreground": terminal["foreground"]})
        self.assertEqual(colors["cursor"], {"text": terminal["cursorText"], "cursor": terminal["cursor"]})
        self.assertEqual(colors["selection"], {"text": "CellForeground", "background": terminal["selection"]["color"]})
        self.assertEqual([colors["normal"][name] for name in COLOR_NAMES], terminal["ansi"])
        self.assertEqual([colors["bright"][name] for name in COLOR_NAMES], terminal["bright"])

    def test_fragment_contains_only_colors(self):
        self.assertEqual(set(self.theme), {"colors"})

    def test_generator_is_deterministic(self):
        generator = load_generator()
        first = generator.render(generator.load_palette(PALETTE_PATH))
        second = generator.render(generator.load_palette(PALETTE_PATH))
        self.assertEqual(first, second)
        self.assertEqual(first, ARTIFACT_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
