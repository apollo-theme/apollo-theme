# bat Apollo theme development

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots. Update pinned SHA-256 values only when deliberately refreshing them.
- Edit `scripts/generate.py`, not generated `Apollo.tmTheme` or `Apollo Light.tmTheme`.
- Keep both TextMate scope mappings focused and valid for bat/syntect. Install/uninstall ownership must preserve pre-existing or modified theme files and rebuild the cache once.
- Generate: `python3 scripts/generate.py`
- Check plist, optional plutil, isolated bat cache, and render: `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloBatThemeTests.test_isolated_bat_cache_builds_and_renders`
