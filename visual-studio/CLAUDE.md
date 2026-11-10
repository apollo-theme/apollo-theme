# Apollo Theme for Visual Studio

This standalone repository ships native Apollo and Apollo Light Visual Studio 2022+ `.vstheme` files. Both files under `palette/` are exact canonical snapshots; never hand-edit generated themes or copy obsolete colors from another editor theme.

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
