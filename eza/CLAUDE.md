# eza Apollo theme development

- This app lives at `eza/` in the `apollo-theme/apollo-theme` monorepo (<https://github.com/apollo-theme/apollo-theme/tree/main/eza>). It is validated by the root CI job `eza`.
- `palette/apollo.json` and `palette/apollo-light.json` are this app's own exact snapshots of the canonical palettes. Update pinned SHA-256 values only when deliberately refreshing them.
- It runs standalone from its folder: `cd eza && python3 scripts/generate.py --check && python3 -m unittest discover -s tests`.
- Edit `scripts/generate.py`, not generated root `theme.yml` or `light/theme.yml`.
- Target eza's current fixed `theme.yml` schema within the selected `EZA_CONFIG_DIR`. Users point it at the shared clone: `~/.config/apollo-theme/eza` (Dark) or `~/.config/apollo-theme/eza/light` (Light). Do not add filename/extension mappings or reset users' LS_COLORS/EZA_COLORS behavior.
- Generate: `python3 scripts/generate.py`
- Check static coverage and isolated installed-eza behavior: `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloEzaThemeTests.test_isolated_eza_config_applies_theme_and_preserves_ls_colors`
