import hashlib
import json
import plistlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "palette" / "apollo.json"
THEME_PATH = ROOT / "Apollo.terminal"
PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"

ANSI_KEYS = [
    "ANSIBlackColor",
    "ANSIRedColor",
    "ANSIGreenColor",
    "ANSIYellowColor",
    "ANSIBlueColor",
    "ANSIMagentaColor",
    "ANSICyanColor",
    "ANSIWhiteColor",
    "ANSIBrightBlackColor",
    "ANSIBrightRedColor",
    "ANSIBrightGreenColor",
    "ANSIBrightYellowColor",
    "ANSIBrightBlueColor",
    "ANSIBrightMagentaColor",
    "ANSIBrightCyanColor",
    "ANSIBrightWhiteColor",
]


def decode_color(data):
    archive = plistlib.loads(data)
    root = archive["$objects"][archive["$top"]["root"].data]
    components = [float(value) for value in root["NSRGB"].rstrip(b"\0").decode("ascii").split()]
    if len(components) == 3:
        components.append(1.0)
    return components


def color_hex(data):
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in decode_color(data)[:3])


class TerminalThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palette_bytes = PALETTE_PATH.read_bytes()
        cls.palette = json.loads(cls.palette_bytes)
        cls.profile = plistlib.loads(THEME_PATH.read_bytes())

    def test_palette_snapshot_is_canonical(self):
        self.assertEqual(hashlib.sha256(self.palette_bytes).hexdigest(), PALETTE_SHA256)

    def test_archived_colors_match_palette(self):
        terminal = self.palette["terminal"]
        colors = self.palette["colors"]
        expected = {
            **dict(zip(ANSI_KEYS, terminal["ansi"] + terminal["bright"])),
            "BackgroundColor": terminal["background"],
            "CursorColor": terminal["cursor"],
            "SelectionColor": terminal["selection"]["color"],
            "TextBoldColor": colors["foregroundBright"],
            "TextColor": terminal["foreground"],
        }
        for key, expected_hex in expected.items():
            with self.subTest(key=key):
                self.assertEqual(color_hex(self.profile[key]), expected_hex)

        self.assertAlmostEqual(
            decode_color(self.profile["SelectionColor"])[3],
            terminal["selection"]["alpha"],
        )

    def test_profile_contains_only_theme_metadata_and_colors(self):
        expected_keys = {
            "ProfileCurrentVersion",
            "name",
            "type",
            "BackgroundColor",
            "CursorColor",
            "SelectionColor",
            "TextBoldColor",
            "TextColor",
            *ANSI_KEYS,
        }
        self.assertEqual(set(self.profile), expected_keys)
        self.assertEqual(self.profile["name"], "Apollo")
        self.assertEqual(self.profile["type"], "Window Settings")

    def test_bright_black_is_ansi_only(self):
        restricted = self.palette["colors"]["ansiBrightBlack"]
        color_keys = [key for key, value in self.profile.items() if isinstance(value, bytes)]
        uses = [key for key in color_keys if color_hex(self.profile[key]) == restricted]
        self.assertEqual(uses, ["ANSIBrightBlackColor"])


if __name__ == "__main__":
    unittest.main()
