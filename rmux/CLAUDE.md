# RMUX Apollo theme development

- This app lives at `rmux/` in the `apollo-theme/apollo-theme` monorepo (<https://github.com/apollo-theme/apollo-theme/tree/main/rmux>), separate from `tmux/` by project decision. It is validated by the root CI job `rmux`.
- `palette/apollo.json` and `palette/apollo-light.json` are this app's own exact snapshots of the canonical palettes. Update pinned SHA-256 values only when deliberately refreshing them.
- It runs standalone from its folder: `cd rmux && python3 scripts/generate.py --check && python3 -m unittest discover -s tests`.
- Edit `scripts/generate.py`, not generated `apollo-rmux.conf` or `apollo-rmux-light.conf`.
- Keep both RMUX variants separate and theme-only: no unrelated rmux.conf content, keys, prefix, status content, commands, or hooks. Users source exactly one variant from the shared clone at `~/.config/apollo-theme/rmux/`.
- Generate: `python3 scripts/generate.py`
- Check with isolated RMUX (or compatible tmux fallback): `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloRmuxThemeTests.test_isolated_rmux_compatible_server_applies_apollo_options`
