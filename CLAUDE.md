# Repository guidance

This standalone repository publishes Apollo for Apple Terminal. `palette/apollo.json` is the exact canonical snapshot and `Apollo.terminal` is generated and committed.

## Architecture

- `palette/apollo.json`: source palette snapshot; do not hand-edit generated colors.
- `scripts/generate.py`: deterministic stdlib-only XML plist generator; color values are binary NSKeyedArchiver `NSColor` payloads matching Terminal's native profile format.
- `Apollo.terminal`: generated theme-only Terminal profile.
- `tests/test_theme.py`: archive decoding, exact colors, safe profile keys, alpha, and restricted-color checks.
- `scripts/check.py`: regeneration, nested archive parsing, tests, and macOS `plutil` lint.

## Commands

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.TerminalThemeTests.test_archived_colors_match_palette -v
plutil -lint Apollo.terminal  # macOS
```

Keep profile output limited to colors plus `name`, `type`, and version metadata. Never add shell commands, run `defaults write`, import automatically, or mutate a current/default profile. Use `#665c54` only for ANSI bright black.
