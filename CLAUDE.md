# iTerm2 Apollo Themes

This standalone repository publishes existing dark `Apollo.itermcolors` from `palette/apollo.json` and additive `Apollo Light.itermcolors` from `palette/apollo-light.json`. The dark artifact's filename, bytes, and meaning remain unchanged.

## Architecture

- Both palette files are exact canonical snapshots.
- `scripts/generate.py` retains pure `render(palette)` plist serialization and drives it through an ordered two-output map.
- Check mode rejects missing, stale, and unexpected root-level `.itermcolors` artifacts.
- Both generated presets contain ANSI 0–15 and every required UI role, preserve selected text explicitly, and represent palette selection alpha natively.
- `tests/test_theme.py` pins the light palette SHA-256 and tests identity, appearance, semantic roles, slot order, alpha, and determinism for both variants.
- `scripts/check.py` parses both plists, checks regeneration and all unit tests, and runs `plutil` over both on macOS.

Do not add application settings or installation side effects.

## Install and activate

Import either or both preset files through **Settings → Profiles → Colors → Color Presets… → Import…**. Choose **Apollo** for existing dark or **Apollo Light** for light. Importing must not automatically change current profiles.

## Uninstall

Use **Delete Preset…** for the chosen name. Existing profiles keep copied colors until the user changes them. Scripts and tests must never mutate preferences.

## Visual check

Inspect normal, bold, selected, cursor text, and ANSI 0–15 under both presets. Compare dark against `palette/apollo.json` and light against `palette/apollo-light.json`, including selection alpha and readable selected text.

## Commands

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_theme.ItermThemeTests.test_required_color_roles -v
plutil -lint Apollo.itermcolors "Apollo Light.itermcolors" # macOS
```
