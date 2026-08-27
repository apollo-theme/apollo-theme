import hashlib
import json
import plistlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
THEME_PATH = ROOT / "Apollo.itermcolors"
PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"


def color_hex(value):
    channels = ("Red Component", "Green Component", "Blue Component")
    return "#" + "".join(f"{round(value[channel] * 255):02x}" for channel in channels)


class ItermThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palette_bytes = PALETTE_PATH.read_bytes()
        cls.palette = json.loads(cls.palette_bytes)
        cls.theme = plistlib.loads(THEME_PATH.read_bytes())

    def test_palette_snapshot_is_canonical(self):
        self.assertEqual(hashlib.sha256(self.palette_bytes).hexdigest(), PALETTE_SHA256)

    def test_required_color_roles(self):
        terminal = self.palette["terminal"]
        colors = self.palette["colors"]
        expected = {
            **{f"Ansi {index} Color": color for index, color in enumerate(terminal["ansi"] + terminal["bright"])},
            "Background Color": terminal["background"],
            "Bold Color": colors["foregroundBright"],
            "Cursor Color": terminal["cursor"],
            "Cursor Text Color": terminal["cursorText"],
            "Foreground Color": terminal["foreground"],
            "Selection Color": terminal["selection"]["color"],
            "Selected Text Color": terminal["foreground"],
        }
        self.assertEqual(set(self.theme), set(expected))
        for role, expected_hex in expected.items():
            with self.subTest(role=role):
                self.assertEqual(color_hex(self.theme[role]), expected_hex)
                self.assertEqual(self.theme[role]["Color Space"], "sRGB")

        self.assertEqual(
            self.theme["Selection Color"]["Alpha Component"],
            terminal["selection"]["alpha"],
        )

    def test_bright_black_is_ansi_only(self):
        restricted = self.palette["colors"]["ansiBrightBlack"]
        uses = [key for key, value in self.theme.items() if color_hex(value) == restricted]
        self.assertEqual(uses, ["Ansi 8 Color"])


if __name__ == "__main__":
    unittest.main()
