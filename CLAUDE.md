# Repository guidance

This standalone repository publishes Apollo for iTerm2. `palette/apollo.json` is the exact canonical snapshot and `Apollo.itermcolors` is generated and committed.

## Architecture

- `palette/apollo.json`: source palette snapshot; do not hand-edit generated colors.
- `scripts/generate.py`: deterministic stdlib-only plist generator.
- `Apollo.itermcolors`: generated native iTerm2 color preset.
- `tests/test_theme.py`: palette, role, alpha, and restricted-color checks.
- `scripts/check.py`: regeneration, tests, plist parsing, and macOS `plutil` lint.

## Commands

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.ItermThemeTests.test_required_color_roles -v
plutil -lint Apollo.itermcolors  # macOS
```

Keep all ANSI 0–15 and every required UI color role. Use `#665c54` only for ANSI bright black. Do not add app preference mutation or installation side effects.
