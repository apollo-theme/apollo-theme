# vim-apollo-theme

## Commands

Run commands from this repository root.

- Build: `python3 scripts/generate.py`
- Generated-file drift check: `python3 scripts/generate.py --check`
- Lint: `python3 -m compileall -q scripts tests`
- Test everything: `python3 scripts/check.py`
- Single Python test: `python3 -m unittest tests.test_theme.ThemeTests.test_generated_theme_is_current`
- Editor test: `vim -Nu NONE -n -es -i NONE -S tests/headless.vim`

Only Python's standard library is allowed for build and check scripts.

## Architecture

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots.
- `scripts/generate.py` validates both snapshot hashes/schemas and deterministically owns `colors/apollo.vim` plus `colors/apollo-light.vim`.
- Both native colorschemes are generated. Preserve dark bytes and use independent hue-preserving cterm fallback tables.
- `scripts/check.py` runs drift, unit, canonical-color, and clean headless Vim checks.
- `tests/test_theme.py` guards snapshot identity, deterministic output, and obsolete colors.
- `tests/headless.vim` verifies loading, GUI/256-color highlights, and terminal ANSI globals.

Keep the repository standalone. Do not read a parent palette at build time, add runtime dependencies, or introduce editor-plugin-specific highlight groups.
