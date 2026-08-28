import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import APP_METADATA, MANAGEMENT_REPOSITORIES, REPOSITORIES, contrast_ratio, load_palette, markdown_anchor
from check import forbidden_identity_terms, public_identity_metadata


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
        self.assertEqual(17, len(REPOSITORIES))
        self.assertEqual(len(REPOSITORIES), len(set(REPOSITORIES)))
        self.assertEqual(set(REPOSITORIES), set(APP_METADATA))
        self.assertEqual({"apollo-theme.github.io", ".github/organization"}, set(MANAGEMENT_REPOSITORIES))

    def test_app_preview_slugs_are_stable_and_unique(self):
        slugs = [metadata["slug"] for metadata in APP_METADATA.values()]
        self.assertEqual(17, len(slugs))
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertTrue(all(slug and " " not in slug for slug in slugs))

    def test_app_metadata_supports_readmes_and_repository_settings(self):
        required = {"slug", "name", "family", "workflow", "platform", "badge_fragment", "install_anchor", "description", "topics"}
        families = {"terminal", "browser", "editor", "multiplexer", "shell", "utility"}
        for repository, metadata in APP_METADATA.items():
            with self.subTest(repository=repository):
                self.assertEqual(required, set(metadata))
                self.assertIn(metadata["family"], families)
                self.assertTrue(metadata["description"].startswith(f"{metadata['name']} Apollo Theme"))
                self.assertIn(metadata["slug"].split("-")[0], " ".join(metadata["topics"]))
                self.assertNotIn("gruvbox", metadata["topics"])
                self.assertTrue(metadata["workflow"].endswith(".yml"))
                readme = (ROOT / repository / "README.md").read_text(encoding="utf-8")
                self.assertIn(f"img.shields.io/badge/{metadata['badge_fragment']}".lower(), readme.lower())
                headings = (line.removeprefix("## ") for line in readme.splitlines() if line.startswith("## "))
                self.assertIn(metadata["install_anchor"], {markdown_anchor(heading) for heading in headings})

    def test_sonicterm_identity_is_allowed_only_for_target_app_language(self):
        allowed = """# SonicTerm Apollo Theme
Apollo brings terminal colors to SonicTerm.
Start SonicTerm after updating `~/.sonicterm/sonicterm.toml`.
```sh
open -a SonicTerm
```
"""
        self.assertEqual([], forbidden_identity_terms("sonicterm-apollo-theme", allowed))
        self.assertEqual(
            ["sonicterm"],
            forbidden_identity_terms("sonicterm-apollo-theme", "SonicTerm lineage"),
        )
        self.assertEqual(
            ["sonicterm"],
            forbidden_identity_terms(
                "sonicterm-apollo-theme",
                "SonicTerm has the upstream palette that inspired Apollo.",
            ),
        )
        self.assertEqual(
            ["sonicterm"],
            forbidden_identity_terms("wezterm-apollo-theme", "SonicTerm theme"),
        )

    def test_package_metadata_uses_apollo_only_identity(self):
        for repository in REPOSITORIES:
            with self.subTest(repository=repository):
                public_metadata = public_identity_metadata(ROOT / repository).lower()
                self.assertNotIn("gruvbox", public_metadata)
                self.assertNotIn("base16", public_metadata)
                self.assertNotIn("sonicterm-modified", public_metadata)

    def test_public_identity_metadata_ignores_package_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "name": "apollo-theme",
                        "displayName": "Apollo Theme",
                        "description": "Canonical Apollo colors.",
                        "keywords": ["apollo", "theme"],
                        "scripts": {"check:base16": "python3 scripts/check.py"},
                    }
                ),
                encoding="utf-8",
            )
            self.assertNotIn("base16", public_identity_metadata(root).lower())

    def test_public_identity_metadata_includes_extension_and_module_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(
                json.dumps({"name": "Firefox Apollo Theme", "description": "Gruvbox lineage"}),
                encoding="utf-8",
            )
            (root / "ApolloTheme.psd1").write_text(
                "Description = 'Base16 module metadata'\nFunctionsToExport = @('Base16Internal')\n",
                encoding="utf-8",
            )
            metadata = public_identity_metadata(root).lower()
            self.assertIn("gruvbox", metadata)
            self.assertIn("base16 module metadata", metadata)
            self.assertNotIn("base16internal", metadata)


if __name__ == "__main__":
    unittest.main()
