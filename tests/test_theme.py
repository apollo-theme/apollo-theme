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


def load_generator():
    spec = importlib.util.spec_from_file_location("generate", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WezTermThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palette = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
        cls.scheme = tomllib.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_native_artifact_matches_terminal_palette(self):
        terminal = self.palette["terminal"]
        colors = self.scheme["colors"]
        self.assertEqual(self.scheme["metadata"]["name"], "Apollo")
        self.assertEqual(colors["foreground"], terminal["foreground"])
        self.assertEqual(colors["background"], terminal["background"])
        self.assertEqual(colors["cursor_bg"], terminal["cursor"])
        self.assertEqual(colors["cursor_border"], terminal["cursor"])
        self.assertEqual(colors["cursor_fg"], terminal["cursorText"])
        self.assertEqual(colors["selection_fg"], "none")
        self.assertEqual(colors["selection_bg"], "rgba(60, 56, 54, 0.5)")
        self.assertEqual(colors["ansi"], terminal["ansi"])
        self.assertEqual(colors["brights"], terminal["bright"])

    def test_generator_is_deterministic(self):
        generator = load_generator()
        first = generator.render(generator.load_palette(PALETTE_PATH))
        second = generator.render(generator.load_palette(PALETTE_PATH))
        self.assertEqual(first, second)
        self.assertEqual(first, ARTIFACT_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
