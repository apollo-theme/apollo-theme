# PowerShell Apollo theme development

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots. Update pinned SHA-256 values only when deliberately refreshing them.
- Edit `scripts/generate.py`, not generated module/profile files. Keep one module and the existing GUID.
- Never edit `$PROFILE`; keep activation explicit. Dark is the default, variant switches must preserve the first pre-Apollo capture, and `Disable-ApolloTheme` must restore it.
- Generate: `python3 scripts/generate.py`
- Check generated files and direct PowerShell assertions: `python3 scripts/check.py`
- Test all Python checks: `python3 -m unittest discover -s tests -v`
- Direct native test: `pwsh -NoLogo -NoProfile -NonInteractive -File tests/Test-ApolloTheme.ps1`
- Single unittest: `python3 -m unittest -v tests.test_generated.ApolloPowerShellThemeTests.test_generated_module_supports_reversible_dark_and_light_variants`
