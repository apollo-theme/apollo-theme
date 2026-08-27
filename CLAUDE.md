# tmux Apollo theme development

- `palette/apollo.json` is the exact canonical snapshot. Update the pinned SHA-256 in `scripts/generate.py` only when deliberately refreshing it.
- Edit `scripts/generate.py`, not generated `apollo.tmux`.
- Keep the artifact theme-only: no `bind`, prefix, status content, shell commands, plugins, or hooks.
- Generate: `python3 scripts/generate.py`
- Check freshness and isolated tmux options: `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloTmuxThemeTests.test_isolated_tmux_server_applies_apollo_options`
