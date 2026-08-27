# Alacritty Apollo Theme

## Architecture

`palette/apollo.json` is the exact canonical snapshot. `scripts/generate.py` maps it deterministically to the committed importable fragment `apollo.toml`; `scripts/check.py` validates snapshot schema, lowercase colors, exact Alacritty sections and keys, mappings, and artifact drift. `tests/test_theme.py` covers ordered normal/bright colors, preservation of selected text, fragment scope, and determinism.

The artifact contains only current `[colors.primary]`, `[colors.cursor]`, `[colors.selection]`, `[colors.normal]`, and `[colors.bright]` sections. `CellForeground` is Alacritty's native representation of the canonical `foregroundMode = "preserve"`. Do not invent opacity, font, window, or dim-color settings.

Never edit the snapshot independently. Update it from the canonical Apollo palette, regenerate, and commit both changes. Scripts and tests must not write to real user configuration.

## Commands

```sh
# Build
python3 scripts/generate.py

# Generated-file gate
python3 scripts/generate.py --check

# Syntax lint
python3 -m compileall -q scripts tests

# Schema, colors, and drift
python3 scripts/check.py

# Full tests
python3 -m unittest discover -s tests -v

# Named single test
python3 -m unittest tests.test_theme.AlacrittyThemeTests.test_native_artifact_matches_terminal_palette -v

# Native parser check, when Alacritty is installed
alacritty migrate --dry-run --config-file apollo.toml >/dev/null
```

`migrate --dry-run` checks parsing but does not replace a rendered visual check.
