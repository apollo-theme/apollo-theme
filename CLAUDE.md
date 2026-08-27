# PowerShell Apollo theme development

- `palette/apollo.json` is the exact canonical snapshot. Update the pinned SHA-256 in `scripts/generate.py` only when deliberately refreshing it.
- Edit `scripts/generate.py`, not generated module/profile files.
- Never edit `$PROFILE`; keep activation explicit and `Disable-ApolloTheme` restorative.
- Generate: `python3 scripts/generate.py`
- Check generated files and direct PowerShell assertions: `python3 scripts/check.py`
- Test all Python checks: `python3 -m unittest discover -s tests -v`
- Direct native test: `pwsh -NoLogo -NoProfile -NonInteractive -File tests/Test-ApolloTheme.ps1`
- Single unittest: `python3 -m unittest -v tests.test_generated.ApolloPowerShellThemeTests.test_generated_module_maps_semantic_roles_and_restores_options`
