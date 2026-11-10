# Alacritty Apollo Themes

## Architecture

This standalone repository maps `palette/apollo.json` to existing dark `apollo.toml` and `palette/apollo-light.json` to additive `apollo-light.toml`. Dark artifact bytes, filename, and activation remain unchanged.

`scripts/generate.py` uses an ordered two-output map while retaining pure `render(palette)` TOML serialization. Check mode rejects missing, stale, and unexpected root-level TOML artifacts. `scripts/check.py` validates both palette identities, appearances, selection semantics, exact native sections and mappings, ordered slots, and drift. Tests pin the exact light snapshot hash and exercise both variants.

Artifacts contain only `[colors.primary]`, `[colors.cursor]`, `[colors.selection]`, `[colors.normal]`, and `[colors.bright]`. `CellForeground` is Alacritty's native representation of `foregroundMode = "preserve"`; the format has no selection-alpha field in this fragment. Do not add opacity, font, window, dim colors, or preference mutation.

## Install and activate

Copy one or both files to an Alacritty themes directory. Import exactly one: `apollo.toml` for existing dark Apollo or `apollo-light.toml` for Apollo Light. The existing dark import path must continue to select dark Apollo.

## Uninstall

Remove the active theme from `[general].import`, reload, then remove only the corresponding copied fragment. Scripts and tests must not make these preference changes.

## Visual check

Inspect selected differently colored text, cursor text, and ANSI colors 0–15 with both variants. Verify `CellForeground` preservation, the `#141617` dark canvas, the `#f9f5d7` light canvas, and ordered normal/bright slots against each palette.

## Commands

```sh
# Build both fragments
python3 scripts/generate.py

# Missing, stale, and unexpected generated-file gate
python3 scripts/generate.py --check

# Syntax lint
python3 -m compileall -q scripts tests

# Schema, colors, both mappings, and drift
python3 scripts/check.py

# Full tests
python3 -m unittest discover -s tests -v

# Named single test
python3 -m unittest tests.test_theme.AlacrittyThemeTests.test_native_artifact_matches_terminal_palette -v

# Native parser check, when Alacritty is installed
alacritty migrate --dry-run --config-file apollo.toml >/dev/null
alacritty migrate --dry-run --config-file apollo-light.toml >/dev/null
```

Native parsing does not replace the visual check.
