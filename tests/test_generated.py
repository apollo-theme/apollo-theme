from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = load_module("powershell_generate", ROOT / "scripts" / "generate.py")
check = load_module("powershell_check", ROOT / "scripts" / "check.py")


class ApolloPowerShellThemeTests(unittest.TestCase):
    def test_generated_module_supports_reversible_dark_and_light_variants(self) -> None:
        self.assertEqual(
            hashlib.sha256((ROOT / "palette" / "apollo-light.json").read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        module = generate.render_module(generate.load_palettes())
        self.assertEqual((ROOT / "ApolloTheme.psm1").read_text(), module)
        self.assertEqual((ROOT / "ApolloTheme.psd1").read_text(), generate.render_manifest())
        self.assertEqual((ROOT / "ApolloTheme.profile.ps1").read_text(), generate.render_profile())
        self.assertIn("[ValidateSet('Dark', 'Light')]", module)
        self.assertIn("[string] $Variant = 'Dark'", module)
        self.assertIn("Get-ApolloSupportedColorProperties", module)
        self.assertIn("$Options.PSObject.Properties[$entry.Value]", module)
        self.assertIn("if ($null -eq $script:ApolloPreviousColors)", module)
        self.assertIn("Set-PSReadLineOption -Colors $supportedColors", module)
        self.assertIn("ModuleVersion = '0.2.0'", generate.render_manifest())
        self.assertIn("GUID = '5c88f42f-5dbf-45f5-8514-6f99cb3b628e'", generate.render_manifest())
        check.validate_static()

    def test_default_dark_mapping_stays_compatible(self) -> None:
        palettes = generate.load_palettes()
        self.assertEqual(
            generate.token_colors(palettes["Dark"]),
            generate.token_colors(generate.load_palette("Dark")),
        )
        self.assertEqual(generate.token_colors(palettes["Light"])["Default"], "#3c3836")
        self.assertEqual(generate.token_colors(palettes["Light"])["Command"], "#8a5200")

    def test_readme_documents_both_variants_and_safe_lifecycle(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in (
            "previews/powershell.svg",
            "previews/powershell-light.svg",
            "## Install",
            "## Activate",
            "## Restore and uninstall",
            "Enable-ApolloTheme -Variant Light",
            "Disable-ApolloTheme",
            "does not edit `$PROFILE`",
            "terminal profile that has a light background",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)


if __name__ == "__main__":
    unittest.main()
