from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

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
