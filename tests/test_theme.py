from __future__ import annotations

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
    def test_artifact_is_deterministic_and_theme_only(self) -> None:
        self.assertEqual(
            (ROOT / "apollo.tmux").read_text(encoding="utf-8"),
            generate.render(generate.load_palette()),
        )
        check.validate_theme_only()

    @unittest.skipUnless(shutil.which("tmux"), "tmux is not installed")
    def test_isolated_tmux_server_applies_apollo_options(self) -> None:
        check.validate_isolated_server("tmux")


if __name__ == "__main__":
    unittest.main()
