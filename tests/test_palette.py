import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import REPOSITORIES, contrast_ratio, load_palette


class PaletteTests(unittest.TestCase):
    def test_terminal_slots(self):
        terminal = load_palette()["terminal"]
        self.assertEqual(terminal["ansi"][0], "#1d2021")
        self.assertEqual(terminal["ansi"][3], "#fabd2f")
        self.assertEqual(terminal["bright"][0], "#665c54")
        self.assertEqual(terminal["bright"][7], "#fbf1c7")

    def test_primary_roles_meet_text_contrast(self):
        colors = load_palette()["colors"]
        for role in ("foreground", "foregroundSecondary", "foregroundInactive", "accent"):
            with self.subTest(role=role):
                self.assertGreaterEqual(contrast_ratio(colors[role], colors["background"]), 4.5)

    def test_bright_black_is_restricted(self):
        palette = load_palette()
        colors = palette["colors"]
        self.assertLess(contrast_ratio(colors["ansiBrightBlack"], colors["background"]), 4.5)
        self.assertIn(colors["ansiBrightBlack"], palette["constraints"]["restrictedColors"])

    def test_repository_names_follow_convention(self):
        self.assertTrue(all(name.endswith("-apollo-theme") for name in REPOSITORIES))
        self.assertEqual(len(REPOSITORIES), len(set(REPOSITORIES)))


if __name__ == "__main__":
    unittest.main()
