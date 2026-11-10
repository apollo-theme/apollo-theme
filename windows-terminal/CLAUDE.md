# Windows Terminal Apollo Themes

## Architecture

This standalone repository maps `palette/apollo.json` to existing dark `apollo.json` and `palette/apollo-light.json` to additive `apollo-light.json`. Existing dark bytes, filename, scheme name `Apollo`, and profile activation remain unchanged. Light uses scheme name `Apollo Light`.

`scripts/generate.py` retains pure `render(palette)` JSON serialization behind an ordered two-output map. Check mode rejects missing, stale, and unexpected root-level JSON artifacts. `scripts/check.py` validates both identities, appearances, selection semantics, exact scheme fields, mappings, slot order, and drift. Tests pin the exact light palette hash and cover both variants.

Each artifact is one scheme object for insertion into a user's `schemes` array, never a replacement `settings.json`. Windows Terminal calls magenta slots `purple` and `brightPurple`. The scheme format cannot represent selection alpha or cursor-text color, so selection uses the palette RGB value and `cursorText` is not emitted. Do not add profile settings or preference mutation.

## Install and activate

Users paste one or both objects into the top-level `schemes` array. `"colorScheme": "Apollo"` must continue to select dark; `"colorScheme": "Apollo Light"` selects light.

## Uninstall

Activate another scheme, then remove only the object with the corresponding `name`. Scripts and tests must never edit user settings.

## Visual check

On Windows, inspect ANSI colors 0–15, cursor, foreground, and selection for both variants. Confirm dark uses `#141617`, light uses `#f9f5d7`, scheme names are distinct, and the opaque selection mapping is readable. There is no documented non-GUI validation command for a standalone scheme object.

## Commands

```sh
# Build both scheme objects
python3 scripts/generate.py

# Missing, stale, and unexpected generated-file gate
python3 scripts/generate.py --check

# Syntax lint
python3 -m compileall -q scripts tests

# JSON schema, colors, both mappings, and drift
python3 scripts/check.py

# Full tests
python3 -m unittest discover -s tests -v

# Named single test
python3 -m unittest tests.test_theme.WindowsTerminalThemeTests.test_native_artifact_matches_terminal_palette -v
```
