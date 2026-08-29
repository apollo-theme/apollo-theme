from __future__ import annotations

import hashlib
import importlib.util
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = load_module("tmux_generate", ROOT / "scripts" / "generate.py")
check = load_module("tmux_check", ROOT / "scripts" / "check.py")


class ApolloTmuxThemeTests(unittest.TestCase):
    def test_both_variants_are_deterministic_and_theme_only(self) -> None:
        self.assertEqual(
            hashlib.sha256((ROOT / "palette" / "apollo-light.json").read_bytes()).hexdigest(),
            "b0dbdeb719ed1931c424e9590562689325ecac1609e2fed6406ec5c4d3dc5763",
        )
        expected = generate.render_outputs()
        self.assertEqual(set(expected), {ROOT / "apollo.tmux", ROOT / "apollo-light.tmux"})
        for path, text in expected.items():
            self.assertEqual(path.read_text(encoding="utf-8"), text)
            check.validate_theme_only(path)

    @unittest.skipUnless(shutil.which("tmux"), "tmux is not installed")
    def test_isolated_tmux_server_applies_both_variants(self) -> None:
        for variant in ("dark", "light"):
            with self.subTest(variant=variant):
                check.validate_isolated_server("tmux", variant)


if __name__ == "__main__":
    unittest.main()
