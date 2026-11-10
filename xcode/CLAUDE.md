# Repository guidance

This app lives at `xcode/` in [apollo-theme/apollo-theme](https://github.com/apollo-theme/apollo-theme/tree/main/xcode). It publishes Apollo Dark (the unsuffixed `Apollo` compatibility theme) and Apollo Light for Xcode, runs standalone from this folder with only Python's standard library, and is validated by the root CI job `xcode`. Both files under `palette/` are exact canonical snapshots; `Apollo.xccolortheme` and `Apollo Light.xccolortheme` are generated and committed.

## Architecture

- `palette/apollo.json` and `palette/apollo-light.json`: source snapshots; do not hand-edit generated colors.
- `scripts/generate.py`: deterministic stdlib-only dual Xcode plist generator. Both outputs use the full top-level editor/markup/console schema and all 28 syntax roles.
- Preserve `Apollo.xccolortheme` bytes when changing light support; reject unexpected `.xccolortheme` outputs.
- `tests/test_theme.py`: schema coverage, palette mappings, status colors, and restricted-color checks.
- `scripts/check.py`: regeneration, tests, plist parsing, and macOS `plutil` lint.

## Commands

Run from `xcode/`:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.XcodeThemeTests.test_xcode_26_syntax_role_map -v
plutil -lint Apollo.xccolortheme "Apollo Light.xccolortheme"  # macOS
```

Preserve the full role map and readable semantic hierarchy. Never edit Xcode preferences or install automatically. README install steps clone the repository once to `$HOME/.config/apollo-theme` and copy themes with full quoted source paths; uninstall removes only the copies, never the clone. `#665c54` is ANSI-only and must not appear in this Xcode theme.
