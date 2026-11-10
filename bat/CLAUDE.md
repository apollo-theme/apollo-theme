# bat Apollo theme development

- This app lives at `bat/` in the `apollo-theme/apollo-theme` monorepo (<https://github.com/apollo-theme/apollo-theme/tree/main/bat>). It is validated by the root CI job `bat`.
- `palette/apollo.json` and `palette/apollo-light.json` are this app's own exact snapshots of the canonical palettes. Update pinned SHA-256 values only when deliberately refreshing them.
- It runs standalone from its folder: `cd bat && python3 scripts/generate.py --check && python3 -m unittest discover -s tests`.
- Edit `scripts/generate.py`, not generated `Apollo.tmTheme` or `Apollo Light.tmTheme`.
- Keep both TextMate scope mappings focused and valid for bat/syntect. Install copies themes from the shared clone at `~/.config/apollo-theme/bat/`; its ownership ledger lives at `$(bat --config-dir)/themes/.apollo-theme-hashes`, never inside the clone. Install/uninstall ownership must preserve pre-existing or modified theme files and rebuild the cache once.
- Generate: `python3 scripts/generate.py`
- Check plist, optional plutil, isolated bat cache, and render: `python3 scripts/check.py`
- Test all: `python3 -m unittest discover -s tests -v`
- Single native test: `python3 -m unittest -v tests.test_theme.ApolloBatThemeTests.test_isolated_bat_cache_builds_and_renders`
