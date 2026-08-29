# tmux Apollo theme development

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots. Update pinned SHA-256 values only when deliberately refreshing them.
- Edit `scripts/generate.py`, not generated `apollo.tmux` or `apollo-light.tmux`.
- Keep both artifacts theme-only: no `bind`, prefix, status content, shell commands, plugins, or hooks. Users source exactly one variant.
- Generate: `python3 scripts/generate.py`
- Check freshness and isolated tmux options: `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloTmuxThemeTests.test_isolated_tmux_server_applies_apollo_options`
