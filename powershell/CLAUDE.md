# PowerShell Apollo theme development

This app lives at `powershell/` in [apollo-theme/apollo-theme](https://github.com/apollo-theme/apollo-theme). It keeps its own palette snapshot and runs standalone from this folder (`cd powershell && python3 scripts/generate.py --check && python3 -m unittest discover -s tests`); the root CI job `powershell` validates it.

- `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots. Update pinned SHA-256 values only when deliberately refreshing them.
- Edit `scripts/generate.py`, not generated module/profile files. Keep one module and the existing GUID.
- Generation and tests never edit `$PROFILE`; the README install line is the only profile edit and the user runs it. Keep activation explicit. Dark is the default, variant switches must preserve the first pre-Apollo capture, and `Disable-ApolloTheme` must restore it.
- Generate: `python3 scripts/generate.py`
- Check generated files and direct PowerShell assertions: `python3 scripts/check.py`
- Test all Python checks: `python3 -m unittest discover -s tests -v`
- Direct native test: `pwsh -NoLogo -NoProfile -NonInteractive -File tests/Test-ApolloTheme.ps1`
- Single unittest: `python3 -m unittest -v tests.test_generated.ApolloPowerShellThemeTests.test_generated_module_supports_reversible_dark_and_light_variants`
