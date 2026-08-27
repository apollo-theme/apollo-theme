from __future__ import annotations

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
    def test_generated_module_maps_semantic_roles_and_restores_options(self) -> None:
        palette = generate.load_palette()
        module = generate.render_module(palette)
        self.assertEqual((ROOT / "ApolloTheme.psm1").read_text(), module)
        self.assertEqual((ROOT / "ApolloTheme.psd1").read_text(), generate.render_manifest())
        self.assertEqual((ROOT / "ApolloTheme.profile.ps1").read_text(), generate.render_profile())
        self.assertIn("Get-ApolloSupportedColorProperties", module)
        self.assertIn("$Options.PSObject.Properties[$entry.Value]", module)
        self.assertIn("Set-PSReadLineOption -Colors $supportedColors", module)
        check.validate_static()


if __name__ == "__main__":
    unittest.main()
