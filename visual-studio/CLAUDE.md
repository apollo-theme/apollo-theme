# Apollo Theme for Visual Studio

This app lives at `visual-studio/` in [apollo-theme/apollo-theme](https://github.com/apollo-theme/apollo-theme) and ships native Apollo and Apollo Light Visual Studio 2022+ `.vstheme` files. It keeps its own palette snapshot, runs standalone from this folder without the rest of the monorepo, and is validated by the root CI jobs `visual-studio` (portable) and `visual-studio-windows` (native .NET XML validation). Both files under `palette/` are exact canonical snapshots; never hand-edit generated themes or copy obsolete colors from another editor theme.

## Commands

- Regenerate: `python3 scripts/generate.py`
- Determinism check: `python3 scripts/generate.py --check`
- Repository checks: `python3 scripts/check.py`
- All tests: `python3 -m unittest discover -s tests -v`
- One named test: `python3 -m unittest tests.test_theme.VisualStudioThemeTests.test_editor_status_colors_match_palette`
- XML schema validation: `xmllint --noout --schema schemas/vstheme.xsd themes/Apollo.vstheme "themes/Apollo Light.vstheme"`
- Windows native validation: `pwsh -File scripts/validate.ps1`

## Invariants

- Generate Apollo from `palette/apollo.json` and Apollo Light from `palette/apollo-light.json`; own exactly two outputs.
- Preserve `themes/Apollo.vstheme` bytes and all established category GUIDs.
- Map each variant's foreground, accent/focus, and status colors to canonical roles.
- Use stable unique theme GUIDs and the Visual Studio 2022+ theme structure.
- Do not fabricate a VSIX identity or claim a VSIX build. The supported deliverable is `themes/Apollo.vstheme`, imported through Microsoft's Color Theme Designer, until a real extension identity and Windows VS SDK project are available.
- Install docs point at the shared clone path `~/.config/apollo-theme/visual-studio/themes/<file>` (idempotent `[ -d ... ] || git clone`) with `https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/visual-studio/themes/<file>` as the no-clone alternative. Keep the bare `themes/Apollo.vstheme` and `themes/Apollo Light.vstheme` README markers that `scripts/check.py` requires.
