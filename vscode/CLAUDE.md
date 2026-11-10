# Apollo Theme for VS Code

This is a standalone VS Code color-theme extension containing Apollo and Apollo Light. `palette/apollo.json` and `palette/apollo-light.json` are exact canonical snapshots; never hand-edit generated theme JSON or substitute colors from older local extensions.

## Commands

- Install dependencies: `npm ci`
- Regenerate: `npm run generate`
- Determinism and repository checks: `npm run check`
- All tests: `npm test`
- One named test: `python3 -m unittest tests.test_theme.VSCodeThemeTests.test_terminal_arrays_match_palette`
- Build VSIX: `npm run package`

## Invariants

- Generate Apollo from `palette/apollo.json` and Apollo Light from `palette/apollo-light.json`; check mode owns exactly two outputs.
- Preserve `themes/apollo-color-theme.json` byte-for-byte when changing light support.
- Keep each variant's foreground, accent/cursor/focus, and semantic status colors mapped to its canonical roles.
- Integrated-terminal normal and bright arrays must exactly equal the corresponding palette arrays.
- The package must contribute Apollo as `vs-dark` and Apollo Light as `vs`; one VSIX contains both.
- The publisher is an organization-compatible placeholder; do not claim Marketplace publication.
- Do not publish, install over a user's existing extension, or edit user settings while validating.
