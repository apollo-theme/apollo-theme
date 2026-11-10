# eza Apollo theme development

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots. Update pinned SHA-256 values only when deliberately refreshing them.
- Edit `scripts/generate.py`, not generated root `theme.yml` or `light/theme.yml`.
- Target eza's current fixed `theme.yml` schema within the selected `EZA_CONFIG_DIR`. Do not add filename/extension mappings or reset users' LS_COLORS/EZA_COLORS behavior.
- Generate: `python3 scripts/generate.py`
- Check static coverage and isolated installed-eza behavior: `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloEzaThemeTests.test_isolated_eza_config_applies_theme_and_preserves_ls_colors`
