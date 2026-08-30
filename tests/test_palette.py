import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from common import (
    APP_METADATA,
    LIGHT_ARTIFACTS,
    MANAGEMENT_REPOSITORIES,
    PALETTE_PATHS,
    REPOSITORIES,
    contrast_ratio,
    load_palette,
    load_palettes,
    markdown_anchor,
)
from check import check_readme_contract, forbidden_identity_terms, public_identity_metadata, visible_prose


class PaletteTests(unittest.TestCase):
    def test_dark_compatibility_palette_is_unchanged(self):
        self.assertEqual(ROOT / "palette" / "apollo.json", PALETTE_PATHS["dark"])
        self.assertEqual(
            "550f8c36cf4ef6ac99551541d1fe9554f77d563fa1e7c129a6a82583321d61ef",
            __import__("hashlib").sha256(PALETTE_PATHS["dark"].read_bytes()).hexdigest(),
        )

    def test_light_palette_identity_and_slots(self):
        light = load_palette("light")
        self.assertEqual("{colors.background}", light["roles"]["canvas"])
        self.assertEqual("{colors.foreground}", light["roles"]["textPrimary"])
        self.assertEqual("{colors.background}", light["roles"]["cursorText"])
        self.assertEqual("{colors.foreground}", light["roles"]["selectionText"])
        self.assertEqual(
            {
                "background": "#f9f5d7", "surface": "#fbf1c7", "surfaceHover": "#f2e5bc",
                "selection": "#ebdbb2", "foreground": "#3c3836", "foregroundSecondary": "#504945",
                "foregroundInactive": "#665c54", "foregroundBright": "#282828", "accent": "#8a5200",
                "danger": "#9d0006", "success": "#6b6700", "info": "#076678", "magenta": "#8f3f71",
                "cyan": "#356b4d", "ansiBrightBlack": "#665c54",
            },
            light["colors"],
        )
        self.assertEqual("apollo-light", light["id"])
        self.assertEqual("Apollo Light", light["name"])
        self.assertEqual("light", light["appearance"])
        self.assertEqual("#f9f5d7", light["colors"]["background"])
        self.assertEqual("#8a5200", light["colors"]["accent"])
        self.assertEqual("#3c3836", light["terminal"]["ansi"][0])
        self.assertEqual("#282828", light["terminal"]["bright"][7])

    def test_both_palettes_are_unique_and_complete(self):
        palettes = load_palettes()
        self.assertEqual({"dark", "light"}, set(palettes))
        self.assertEqual(2, len({palette["id"] for palette in palettes.values()}))
        self.assertEqual({"dark", "light"}, {palette["appearance"] for palette in palettes.values()})

    def test_every_child_carries_both_exact_palette_snapshots(self):
        for repository in REPOSITORIES:
            with self.subTest(repository=repository):
                self.assertEqual(
                    PALETTE_PATHS["dark"].read_bytes(),
                    (ROOT / repository / "palette" / "apollo.json").read_bytes(),
                )
                self.assertEqual(
                    PALETTE_PATHS["light"].read_bytes(),
                    (ROOT / repository / "palette" / "apollo-light.json").read_bytes(),
                )

    def test_website_carries_both_exact_palette_snapshots(self):
        website = ROOT / "apollo-theme.github.io" / "palette"
        self.assertEqual(PALETTE_PATHS["dark"].read_bytes(), (website / "apollo.json").read_bytes())
        self.assertEqual(PALETTE_PATHS["light"].read_bytes(), (website / "apollo-light.json").read_bytes())

    def test_light_selection_and_cursor_text_roles_meet_contrast(self):
        light = load_palette("light")
        colors = light["colors"]
        selection_text = light["roles"]["selectionText"][8:-1]
        cursor_text = light["roles"]["cursorText"][8:-1]
        self.assertGreaterEqual(contrast_ratio(colors[selection_text], colors["selection"]), 4.5)
        self.assertGreaterEqual(contrast_ratio(colors[cursor_text], colors["accent"]), 4.5)

    def test_every_light_text_role_meets_contrast_on_all_surfaces(self):
        light = load_palette("light")
        colors = light["colors"]
        roles = ("textPrimary", "textSecondary", "textInactive", "focus", "error", "warning", "success", "information")
        for role in roles:
            color_key = light["roles"][role][8:-1]
            for surface in ("background", "surface", "surfaceHover"):
                with self.subTest(role=role, surface=surface):
                    self.assertGreaterEqual(contrast_ratio(colors[color_key], colors[surface]), 4.5)

    def test_light_inverse_semantic_roles_meet_contrast(self):
        light = load_palette("light")
        colors = light["colors"]
        pairs = {
            "textOnFocus": "accent",
            "textOnError": "danger",
            "textOnSuccess": "success",
            "textOnInformation": "info",
        }
        for role, fill in pairs.items():
            color_key = light["roles"][role][8:-1]
            with self.subTest(role=role, fill=fill):
                self.assertGreaterEqual(contrast_ratio(colors[color_key], colors[fill]), 4.5)

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

    def test_every_repository_declares_a_light_artifact(self):
        self.assertEqual(set(REPOSITORIES), set(LIGHT_ARTIFACTS))
        self.assertTrue(all(path and not path.startswith("/") for path in LIGHT_ARTIFACTS.values()))

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

    def test_visible_prose_excludes_non_visible_appearance_names(self):
        prose = visible_prose(
            """
![Apollo Dark](previews/dark.svg)
[![Apollo Light](https://img.shields.io/badge/appearance-Apollo%20Light-blue)](https://example.com)
<!-- Apollo Dark and Apollo Light -->
<span hidden>Apollo Dark</span>
<div aria-hidden="true">Apollo Light</div>
```text
Apollo Dark
```
~~~text
Apollo Light
~~~

    Apollo Dark
	Apollo Light
`Apollo Dark` and ``Apollo Light``
Apollo Dark.theme
Apollo Light.txt
"""
        )
        self.assertNotRegex(prose, r"(?<![\w-])Apollo Dark(?![\w-])")
        self.assertNotRegex(prose, r"(?<![\w-])Apollo Light(?![\w-])")

    def test_visible_prose_excludes_padded_inline_code_without_crossing_lines(self):
        prose = visible_prose(
            "before `` Apollo Dark `` between ```  Apollo Light  ``` after\n"
            "long ```` `Apollo Dark` ```` and ````` ``Apollo Light`` `````\n"
            "first `unmatched Apollo Dark\n"
            "second line stays visible\n"
            "third ```unmatched Apollo Light\n"
            "fourth line stays visible"
        )
        self.assertIn("before  between  after", prose)
        self.assertIn("long  and ", prose)
        self.assertIn("first `unmatched Apollo Dark", prose)
        self.assertIn("second line stays visible", prose)
        self.assertIn("third ```unmatched Apollo Light", prose)
        self.assertIn("fourth line stays visible", prose)

    def test_visible_prose_accepts_longer_markdown_fence_closers(self):
        prose = visible_prose(
            """
before
   ```text
Apollo Dark
   ````
between
   ~~~ text
Apollo Light
   ~~~~~\t
after
"""
        )
        self.assertNotIn("Apollo Dark", prose)
        self.assertNotIn("Apollo Light", prose)
        self.assertIn("before", prose)
        self.assertIn("between", prose)
        self.assertIn("after", prose)

    def test_visible_prose_keeps_mismatched_and_unclosed_fences_hidden(self):
        prose = visible_prose(
            """
before
~~~~text
Apollo Dark
~~~
Apollo Light
`````
Apollo Dark after mismatched marker
~~~~ not-a-closer
Apollo Light after invalid suffix
~~~~
between
```text
Apollo Dark remains fenced to EOF
"""
        )
        self.assertNotIn("Apollo Dark", prose)
        self.assertNotIn("Apollo Light", prose)
        self.assertIn("before", prose)
        self.assertIn("between", prose)

    def test_visible_prose_does_not_treat_inline_triple_backticks_as_a_fence(self):
        prose = visible_prose("```Apollo Dark``` after inline code\nApollo Light remains visible")
        self.assertNotIn("Apollo Dark", prose)
        self.assertIn("after inline code", prose)
        self.assertIn("Apollo Light remains visible", prose)

    def test_visible_prose_excludes_code_inside_markdown_blockquotes(self):
        prose = visible_prose(
            """
> Visible quoted prose before.
> ```text
> Apollo Dark
> Apollo Light
> `````
> Visible quoted prose after.
>
>     Apollo Dark indented code
>\tApollo Light tab-indented code
> Visible quoted Apollo Dark prose remains.
"""
        )
        self.assertNotIn("Apollo Light", prose)
        self.assertNotIn("Apollo Dark indented code", prose)
        self.assertNotIn("Apollo Light tab-indented code", prose)
        self.assertIn("Visible quoted prose before.", prose)
        self.assertIn("Visible quoted prose after.", prose)
        self.assertIn("Visible quoted Apollo Dark prose remains.", prose)

    def test_visible_prose_excludes_fenced_code_inside_markdown_lists(self):
        prose = visible_prose(
            """
- Visible unordered prose before.
- ~~~text
  Apollo Dark in unordered code
  Apollo Light in unordered code
  ~~~~~
- Visible unordered Apollo Dark prose after.

1. Visible ordered prose before.
2. ```text
   Apollo Dark in ordered code
   Apollo Light in ordered code
   `````
3. Visible ordered Apollo Light prose after.
"""
        )
        self.assertNotIn("Apollo Dark in unordered code", prose)
        self.assertNotIn("Apollo Light in unordered code", prose)
        self.assertNotIn("Apollo Dark in ordered code", prose)
        self.assertNotIn("Apollo Light in ordered code", prose)
        self.assertIn("Visible unordered prose before.", prose)
        self.assertIn("Visible unordered Apollo Dark prose after.", prose)
        self.assertIn("Visible ordered prose before.", prose)
        self.assertIn("Visible ordered Apollo Light prose after.", prose)

    def test_visible_prose_excludes_indented_code_inside_markdown_lists(self):
        prose = visible_prose(
            """
- Visible unordered prose before.
-     Apollo Dark in unordered indented code
- Visible unordered Apollo Light prose after.

1. Visible ordered prose before.
2.     Apollo Light in ordered indented code
3. Visible ordered Apollo Dark prose after.
"""
        )
        self.assertNotIn("Apollo Dark in unordered indented code", prose)
        self.assertNotIn("Apollo Light in ordered indented code", prose)
        self.assertIn("Visible unordered prose before.", prose)
        self.assertIn("Visible unordered Apollo Light prose after.", prose)
        self.assertIn("Visible ordered prose before.", prose)
        self.assertIn("Visible ordered Apollo Dark prose after.", prose)

    def test_visible_prose_excludes_mixed_space_tab_indented_code(self):
        prose = visible_prose(" \tApollo Dark\n   \tApollo Light\n")
        self.assertNotIn("Apollo Dark", prose)
        self.assertNotIn("Apollo Light", prose)

    def test_visible_prose_excludes_multiline_inline_code_spans(self):
        prose = visible_prose(
            "before `` padded Apollo Dark\nand Apollo Light `` after closing delimiter\n"
            "visible Apollo Dark prose\n"
            "unmatched `Apollo Light stays visible"
        )
        self.assertNotIn("padded Apollo Dark", prose)
        self.assertNotIn("and Apollo Light", prose)
        self.assertIn("before ", prose)
        self.assertIn(" after closing delimiter", prose)
        self.assertIn("visible Apollo Dark prose", prose)
        self.assertIn("unmatched `Apollo Light stays visible", prose)

    def test_visible_prose_preserves_escaped_backticks_as_visible_text(self):
        prose = visible_prose(r"Escaped \`Apollo Dark\` and \`Apollo Light\` remain visible.")
        self.assertIn(r"\`Apollo Dark\`", prose)
        self.assertIn(r"\`Apollo Light\`", prose)

    def test_visible_prose_hides_unclosed_html_comments_through_eof(self):
        prose = visible_prose(
            "Visible Apollo Dark prose before.\n"
            "<!-- Apollo Light hidden in unclosed comment\n"
            "Apollo Dark hidden through EOF"
        )
        self.assertIn("Visible Apollo Dark prose before.", prose)
        self.assertNotIn("Apollo Light hidden in unclosed comment", prose)
        self.assertNotIn("Apollo Dark hidden through EOF", prose)

    def test_visible_prose_excludes_raw_html_containers_and_preserves_ordinary_html(self):
        prose = visible_prose(
            """
<code>Apollo Dark code</code>
<pre>Apollo Light pre</pre>
<script>Apollo Dark script</script>
<style>Apollo Light style</style>
<template>Apollo Dark template</template>
<p>Ordinary <strong>HTML</strong> keeps an <a href="/dark">Apollo Dark</a> link.</p>
"""
        )
        for hidden_text in ("code", "pre", "script", "style", "template"):
            self.assertNotIn(f"Apollo Dark {hidden_text}", prose)
            self.assertNotIn(f"Apollo Light {hidden_text}", prose)
        self.assertIn("Ordinary HTML keeps an Apollo Dark link.", prose)

    def test_visible_prose_honors_html_hidden_attributes_and_styles(self):
        prose = visible_prose(
            """
<span aria-hidden>Apollo Dark bare</span>
<span aria-hidden="true">Apollo Light double quoted</span>
<span aria-hidden='true'>Apollo Dark single quoted</span>
<span aria-hidden=true>Apollo Light unquoted</span>
<span style="display: none">Apollo Dark display</span>
<span style='visibility:hidden'>Apollo Light visibility</span>
<span aria-hidden="false">Apollo Dark false is visible</span>
<span style="display: block; visibility: visible">Apollo Light style is visible</span>
"""
        )
        for hidden_text in (
            "Apollo Dark bare",
            "Apollo Light double quoted",
            "Apollo Dark single quoted",
            "Apollo Light unquoted",
            "Apollo Dark display",
            "Apollo Light visibility",
        ):
            self.assertNotIn(hidden_text, prose)
        self.assertIn("Apollo Dark false is visible", prose)
        self.assertIn("Apollo Light style is visible", prose)

    def test_visible_prose_uses_a_tag_stack_for_nested_hidden_html(self):
        prose = visible_prose(
            """
<section hidden>
Apollo Dark outer
<span aria-hidden="false">Apollo Light nested</span>
</unexpected>
Apollo Dark after unmatched close
</section>
<div>Visible before <span hidden>Apollo Light child</span> visible after child.</div>
"""
        )
        self.assertNotIn("Apollo Dark outer", prose)
        self.assertNotIn("Apollo Light nested", prose)
        self.assertNotIn("Apollo Dark after unmatched close", prose)
        self.assertNotIn("Apollo Light child", prose)
        self.assertIn("Visible before  visible after child.", prose)

    def test_visible_prose_excludes_hidden_void_elements_without_hiding_following_prose(self):
        prose = visible_prose('<img hidden alt="Apollo Dark">Apollo Light')
        self.assertNotRegex(prose, r"(?<![\w-])Apollo Dark(?![\w-])")
        self.assertRegex(prose, r"(?<![\w-])Apollo Light(?![\w-])")

    def test_visible_prose_excludes_all_markdown_image_forms(self):
        prose = visible_prose(
            """
![Apollo Dark](previews/dark.svg)
![Apollo Light][light-full]
![Apollo Dark][]
![Apollo Light]

[light-full]: previews/light-full.svg
[Apollo Dark]: previews/dark-collapsed.svg
[Apollo Light]: previews/light-shortcut.svg
"""
        )
        self.assertNotRegex(prose, r"(?<![\w-])Apollo Dark(?![\w-])")
        self.assertNotRegex(prose, r"(?<![\w-])Apollo Light(?![\w-])")

    def test_visible_prose_retains_markdown_link_labels(self):
        prose = visible_prose(
            """
[Apollo Dark](README.md), [Apollo Light][light], [Apollo Dark][], and [Apollo Light].
[Theme](guide.md "Apollo Dark") and [Another theme](Apollo Light.md).

[light]: docs/light.md "Apollo Light"
[Apollo Dark]: docs/dark.md
[Apollo Light]: docs/light-shortcut.md
"""
        )
        self.assertEqual(2, len(re.findall(r"(?<![\w-])Apollo Dark(?![\w-])", prose)))
        self.assertEqual(2, len(re.findall(r"(?<![\w-])Apollo Light(?![\w-])", prose)))

    def test_readme_contract_accepts_injected_visible_appearance_names(self):
        repository = "eza-apollo-theme"
        readme = (ROOT / repository / "README.md").read_text(encoding="utf-8")
        without_visible_names = readme.replace("Apollo Dark", "Dark appearance").replace(
            "Apollo Light", "Light appearance"
        )
        with self.assertRaisesRegex(ValueError, "visible appearance names.*Apollo Dark.*Apollo Light"):
            check_readme_contract(repository, without_visible_names)
        check_readme_contract(
            repository,
            without_visible_names + "\n[**Apollo Dark**](#dark) and [**Apollo Light**](#light).\n",
        )

    def test_every_app_readme_presents_dark_and_light(self):
        failures = {}
        for repository, metadata in APP_METADATA.items():
            readme = (ROOT / repository / "README.md").read_text(encoding="utf-8")
            prose = visible_prose(readme)
            slug = metadata["slug"]
            missing_names = [
                name
                for name in ("Apollo Dark", "Apollo Light")
                if not re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", prose)
            ]
            missing_previews = [
                preview
                for preview in (f"previews/{slug}.svg", f"previews/{slug}-light.svg")
                if preview not in readme
            ]
            lowered = readme.lower()
            stale_phrases = [
                phrase
                for phrase in ("light previews will appear", "light coming soon")
                if phrase in lowered
            ]
            if missing_names or missing_previews or stale_phrases:
                failures[repository] = {
                    "missing visible names": missing_names,
                    "missing previews": missing_previews,
                    "stale phrases": stale_phrases,
                }
        if failures:
            details = "\n".join(
                f"{repository}: "
                + ", ".join(
                    f"{contract}={value}"
                    for contract, value in contracts.items()
                    if value
                )
                for repository, contracts in failures.items()
            )
            self.fail(f"child README contracts failed:\n{details}")

    def test_authoritative_readmes_present_the_dark_light_contract(self):
        surfaces = {
            "parent": ROOT / "README.md",
            "pages": ROOT / "apollo-theme.github.io" / "README.md",
            "profile": ROOT / ".github" / "organization" / "profile" / "README.md",
        }
        stale_phrases = (
            "coming soon",
            "will appear",
            "one night palette",
            "viewport pass pending",
            "17 previews verified",
        )
        readmes = {name: path.read_text(encoding="utf-8") for name, path in surfaces.items()}

        failures = {}
        for name, readme in readmes.items():
            prose = visible_prose(readme)
            missing_names = [
                appearance
                for appearance in ("Apollo Dark", "Apollo Light")
                if not re.search(rf"(?<![\w-]){re.escape(appearance)}(?![\w-])", prose)
            ]
            compatibility_sentences = re.split(r"(?<=[.!?])\s+", prose)
            missing_compatibility_prose = not any(
                "Apollo Dark" in sentence
                and "unsuffixed" in sentence.lower()
                and "compatibility" in sentence.lower()
                for sentence in compatibility_sentences
            )
            missing_previews = [
                preview
                for preview in ("previews/sonicterm.svg", "previews/sonicterm-light.svg")
                if preview not in readme
            ]
            lowered = readme.lower()
            found_stale_phrases = [phrase for phrase in stale_phrases if phrase in lowered]
            if missing_names or missing_compatibility_prose or missing_previews or found_stale_phrases:
                failures[name] = {
                    "missing visible names": missing_names,
                    "missing compatibility prose": missing_compatibility_prose,
                    "missing previews": missing_previews,
                    "stale phrases": found_stale_phrases,
                }
        parent = readmes["parent"]
        missing_palette_rows = [
            row
            for row in ("| **Apollo Dark** |", "| **Apollo Light** |")
            if row not in parent
        ]
        compatibility_sentence = (
            "Existing unsuffixed `Apollo` / `apollo` files, selectors, packages, and activation paths "
            "remain Apollo Dark compatibility identities"
        )
        missing_preview_links = [
            link
            for link in (
                "https://apollo-theme.github.io/#app-sonicterm-dark",
                "https://apollo-theme.github.io/#app-sonicterm-light",
            )
            if link not in parent
        ]
        missing_parent_integrations = [
            repository for repository in REPOSITORIES if f"]({repository})" not in parent
        ]
        if (
            missing_palette_rows
            or compatibility_sentence not in parent
            or missing_preview_links
            or missing_parent_integrations
        ):
            failures["parent details"] = {
                "missing palette rows": missing_palette_rows,
                "missing exact compatibility sentence": compatibility_sentence not in parent,
                "missing preview links": missing_preview_links,
                "missing integrations": missing_parent_integrations,
            }

        profile = readmes["profile"]
        missing_profile_palette_rows = [
            row
            for row in ("| **Apollo Dark** |", "| **Apollo Light** |")
            if row not in profile
        ]
        missing_profile_repositories = [
            repository
            for repository in REPOSITORIES
            if f"https://github.com/apollo-theme/{repository}" not in profile
        ]
        if missing_profile_palette_rows or missing_profile_repositories:
            failures["profile details"] = {
                "missing palette rows": missing_profile_palette_rows,
                "missing repository links": missing_profile_repositories,
            }

        if failures:
            details = "\n".join(
                f"{surface}: "
                + ", ".join(
                    f"{contract}={value}"
                    for contract, value in contracts.items()
                    if value
                )
                for surface, contracts in failures.items()
            )
            self.fail(f"authoritative README contracts failed:\n{details}")

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
