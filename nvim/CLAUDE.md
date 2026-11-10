# nvim-apollo-theme

## Commands

Run commands from this repository root.

- Build: `python3 scripts/generate.py`
- Generated-file drift check: `python3 scripts/generate.py --check`
- Lint: `python3 -m compileall -q scripts tests`
- Test everything: `python3 scripts/check.py`
- Single Python test: `python3 -m unittest tests.test_theme.ThemeTests.test_generated_theme_is_current`
- Editor test: `nvim --headless --clean -u NONE -l tests/headless.lua`

Only Python's standard library is allowed for build and check scripts.

## Architecture

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots.
- `scripts/generate.py` validates both snapshot hashes/schemas and deterministically owns all six shipped Lua files.
- `colors/apollo.lua` keeps `require('apollo').load()` as the dark default; `colors/apollo-light.lua` loads separate generated light palette/implementation modules. Preserve existing dark Lua bytes.
- `scripts/check.py` runs drift, unit, canonical-color, and clean headless Neovim checks.
- `tests/test_theme.py` guards snapshot identity, deterministic output, and obsolete colors.
- `tests/headless.lua` verifies loading, representative highlights, current Tree-sitter links, and terminal ANSI globals.

Keep the repository standalone and plugin-neutral. Do not edit generated Lua directly, read a parent palette at build time, add runtime dependencies, or add deprecated Tree-sitter capture aliases.
