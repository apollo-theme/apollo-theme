# Apple Terminal Apollo Themes

This app lives at `apple-terminal/` in [apollo-theme/apollo-theme](https://github.com/apollo-theme/apollo-theme). It keeps its own palette snapshot, runs standalone from this folder without the rest of the monorepo, and is validated by the root CI job `apple-terminal` (macOS). It publishes existing dark `Apollo.terminal` from `palette/apollo.json` and additive `Apollo Light.terminal` from `palette/apollo-light.json`. The dark artifact's filename, bytes, internal profile name, and activation semantics remain unchanged.

## Architecture

- Both palette files are exact canonical snapshots.
- `scripts/generate.py` retains pure `render(palette)` XML-plist serialization and drives it through an ordered two-output map.
- Color values remain binary NSKeyedArchiver `NSColor` payloads matching Terminal's native format.
- Check mode rejects missing, stale, and unexpected root-level `.terminal` artifacts.
- Profiles remain limited to colors plus `name`, `type`, and version metadata; light uses internal name `Apollo Light`.
- Tests pin the light palette SHA-256 and verify archive decoding, both identities/appearances, exact ordered colors, alpha, safe keys, and determinism.
- `scripts/check.py` parses nested color archives, runs generation and the full suite, and lints both profiles with `plutil` on macOS.

Never add shell commands, run `defaults write`, import automatically, or mutate a current/default profile.

## Install and activate

Users clone the monorepo once to `~/.config/apollo-theme` (idempotent `[ -d ... ] || git clone`) and import `~/.config/apollo-theme/apple-terminal/Apollo.terminal` and/or `~/.config/apollo-theme/apple-terminal/Apollo Light.terminal`, or download `https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/apple-terminal/<file>` without cloning, through Terminal's profile importer. Public docs call the unsuffixed dark profile **Apollo Dark**; its native profile name stays **Apollo**. Select **Apollo** for existing dark or **Apollo Light** for light, and choose **Default** only by explicit user action. Existing windows remain unchanged.

## Uninstall

Select another default if necessary, then remove the chosen profile with the minus button. Scripts and tests must not perform these changes.

## Visual check

Open new windows for both profiles. Inspect normal, bold, cursor, selection, and ANSI 0–15, comparing each with its matching palette. Verify dark uses `#141617`, light uses `#f9f5d7`, and profile names remain distinct.

## Commands

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_theme.TerminalThemeTests.test_archived_colors_match_palette -v
plutil -lint Apollo.terminal "Apollo Light.terminal" # macOS
```
