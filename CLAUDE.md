# SonicTerm Apollo Theme

## Architecture

`palette/apollo.json` is the exact canonical snapshot. `scripts/generate.py` maps it deterministically to the committed strict SonicTerm artifact `apollo.toml`; `scripts/check.py` validates snapshot schema, lowercase colors, the complete native schema, mappings, and artifact drift. `tests/test_theme.py` focuses on ordered ANSI/bright arrays, tab roles, and determinism.

The theme must contain every SonicTerm slot: top-level metadata; primary, cursor, and selection colors; two eight-color tables; and all eight tab fields. Tab chrome uses canonical canvas, accent, inactive, and hover roles. `selection_fg` is concrete because SonicTerm requires it even though the canonical selection mode preserves text. The deprecated-but-required close-button slot uses the canonical accent role. Do not add window, font, opacity, or application configuration.

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
python3 -m unittest tests.test_theme.SonicTermThemeTests.test_native_artifact_matches_terminal_palette -v
```

SonicTerm has no standalone theme-validation CLI. Validate the installed result manually as described in `README.md`.
