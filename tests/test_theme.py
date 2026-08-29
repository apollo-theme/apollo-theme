from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PALETTE = ROOT / "palette" / "apollo.json"
THEME = ROOT / "colors" / "apollo.vim"
EXPECTED_PALETTE_SHA256 = "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef"
OBSOLETE_COLORS = {
    "#ebdbb2",
    "#cc241d",
    "#98971a",
    "#d79921",
    "#458588",
    "#b16286",
    "#689d6a",
    "#d4be98",
}


class ThemeTests(unittest.TestCase):
    def test_palette_snapshot_is_exact(self) -> None:
        self.assertEqual(
            hashlib.sha256(PALETTE.read_bytes()).hexdigest(),
            EXPECTED_PALETTE_SHA256,
        )

    def test_generated_theme_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_light_variant_contract(self) -> None:
        palette_path = ROOT / "palette" / "apollo-light.json"
        self.assertEqual(
            hashlib.sha256(palette_path.read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        palette = json.loads(palette_path.read_text(encoding="utf-8"))
        theme = (ROOT / "colors" / "apollo-light.vim").read_text(encoding="utf-8")
        self.assertEqual((palette["id"], palette["appearance"]), ("apollo-light", "light"))
        self.assertIn("set background=light", theme)
        self.assertIn("let g:colors_name = 'apollo-light'", theme)
        self.assertIn("let s:bg = ['#f9f5d7', 230]", theme)
        self.assertIn("let s:danger = ['#9d0006', 124]", theme)
        self.assertIn("let s:cyan = ['#356b4d', 23]", theme)

    def test_check_rejects_unexpected_generated_output(self) -> None:
        unexpected = ROOT / "colors" / "unexpected.vim"
        unexpected.write_text('" unexpected\n', encoding="utf-8")
        try:
            result = generate.write_or_check(generate.render_all(), check=True)
        finally:
            unexpected.unlink()
        self.assertEqual(result, 1)

    def test_native_theme_uses_only_canonical_colors(self) -> None:
        palette = json.loads(PALETTE.read_text(encoding="utf-8"))
        canonical = {value.lower() for value in palette["colors"].values()}
        canonical.update(value.lower() for value in palette["terminal"]["ansi"])
        canonical.update(value.lower() for value in palette["terminal"]["bright"])
        canonical.update(
            palette["terminal"][key].lower()
            for key in ("foreground", "background", "cursor", "cursorText")
        )
        canonical.add(palette["terminal"]["selection"]["color"].lower())

        literals = {
            match.lower()
            for match in re.findall(r"#[0-9a-fA-F]{6}", THEME.read_text(encoding="utf-8"))
        }
        self.assertTrue(literals, "generated Vim theme contains no color literals")
        self.assertLessEqual(literals, canonical)
        self.assertFalse(literals & OBSOLETE_COLORS)


if __name__ == "__main__":
    unittest.main()
