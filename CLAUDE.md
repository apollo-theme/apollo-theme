# WezTerm Apollo Theme

## Architecture

`palette/apollo.json` is the exact canonical snapshot. `scripts/generate.py` maps it deterministically to the committed native scheme `apollo.toml`; `scripts/check.py` validates snapshot schema, lowercase colors, the WezTerm scheme schema, exact mappings, the Lua activation example, and artifact drift. `tests/test_theme.py` covers ordered arrays and determinism. `tests/wezterm-check.lua` is a CLI fixture that discovers the repository-local scheme.

The native file uses `[colors]` with exact eight-entry `ansi` and `brights` arrays, explicit cursor and selection slots, plus `[metadata]` naming the scheme `Apollo`. Do not add font, opacity, window, or unrelated tab-bar configuration.

Never edit the snapshot independently. Update it from the canonical Apollo palette, regenerate, and commit both changes. Scripts and tests must not write to real user configuration.

## Commands

```sh
# Build
python3 scripts/generate.py

# Generated-file gate
python3 scripts/generate.py --check

# Syntax lint
python3 -m compileall -q scripts tests
luac -p wezterm.lua tests/wezterm-check.lua

# Schema, colors, and drift
python3 scripts/check.py

# Full tests
python3 -m unittest discover -s tests -v

# Named single test
python3 -m unittest tests.test_theme.WezTermThemeTests.test_native_artifact_matches_terminal_palette -v

# Native CLI validation, when WezTerm is installed (run from repository root)
wezterm --config-file tests/wezterm-check.lua show-keys >/dev/null
```
