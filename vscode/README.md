<h1 align="center">Visual Studio Code Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast dark and light palettes to Visual Studio Code across the editor, workbench, terminal, and development surfaces.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-vscode"><img alt="Preview" src="https://img.shields.io/badge/Preview-open-fabd2f?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/vscode-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/vscode-apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;color=b8bb26&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/vscode-apollo-theme/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/apollo-theme/vscode-apollo-theme?style=flat-square&amp;label=Release&amp;color=83a598&amp;labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-8ec07c?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://code.visualstudio.com/"><img alt="Target: Visual Studio Code" src="https://img.shields.io/badge/target-Visual%20Studio%20Code-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-vscode"><picture><source srcset="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vscode.svg" type="image/svg+xml"><img alt="Simulated preview of Apollo in Visual Studio Code" src="https://img.shields.io/badge/Apollo-Visual%20Studio%20Code-fabd2f?style=for-the-badge&amp;labelColor=141617" width="960"></picture></a>
  <a href="https://apollo-theme.github.io/#app-vscode-light"><picture><source srcset="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vscode-light.svg" type="image/svg+xml"><img alt="Simulated preview of Apollo Light in Visual Studio Code" src="https://img.shields.io/badge/Apollo%20Light-Visual%20Studio%20Code-8a5200?style=for-the-badge&amp;labelColor=f9f5d7" width="960"></picture></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Application chrome and typography may vary; follow the visual checks below against the canonical palette.</sub></p>

> [!IMPORTANT]
> This package uses `apollo-theme` as an organization-compatible publisher placeholder and is **not** represented as published in the Visual Studio Marketplace. Install the locally built VSIX instead.

The public **Apollo Dark** variant keeps the existing unsuffixed **Apollo** selector and compatibility identity; **Apollo Light** keeps its existing **Apollo Light** selector and light identity.

## Coverage

- Workbench and editor chrome, including focus, selection, search, Git, diff, testing, and debugging states.
- TextMate scopes and semantic tokens for common language families.
- Integrated-terminal normal and bright ANSI colors mapped exactly to the canonical palette.
- Deterministic generated output from the repository-owned palette snapshot.

## Install

### From a local VSIX

1. Run `npm ci`.
2. Run `npm run package`.
3. In VS Code, open **Extensions: Install from VSIX...** from the Command Palette.
4. Select `dist/apollo-theme.vsix`.

Alternatively, use an isolated VS Code profile so existing settings and extensions stay untouched:

```sh
code --user-data-dir /tmp/apollo-vscode-profile --extensions-dir /tmp/apollo-vscode-extensions --install-extension dist/apollo-theme.vsix
```

## Activate

Open **Preferences: Color Theme** and select **Apollo** or **Apollo Light**. Both ship in the same VSIX. Choosing a theme changes VS Code's color-theme setting; use an isolated profile if you do not want to alter your normal profile.

## Visual verification

Verify all of the following in VS Code:

- Apollo uses canvas `#141617` with source text `#cfbc97`; Apollo Light uses paper `#f9f5d7` with text `#3c3836`.
- Active focus, cursor, active line number, and find matches use each variant's accent (`#fabd2f` dark, `#8a5200` light).
- Errors are red, warnings gold, information blue, and successful tests/Git additions green.
- Comments remain readable muted brown and `#665c54` is never used for normal text.
- JavaScript/TypeScript, Python, C#, JSON, CSS/HTML, Markdown, and diff views show distinct functions, types, properties, strings, constants, and markup.
- The integrated terminal renders the exact canonical normal and bright ANSI rows, including bright black only in its ANSI slot.

## Uninstall

Open Extensions, locate **Apollo Theme**, select the gear menu, and choose **Uninstall**. From an isolated CLI profile:

```sh
code --user-data-dir /tmp/apollo-vscode-profile --extensions-dir /tmp/apollo-vscode-extensions --uninstall-extension apollo-theme.apollo-theme
```

Then delete the temporary profile/directories if used.

## Develop and validate

```sh
npm ci
npm run generate
npm run check
npm test
npm run package
```

Run one focused test with:

```sh
python3 -m unittest tests.test_theme.VSCodeThemeTests.test_terminal_arrays_match_palette
```

`themes/apollo-color-theme.json` and `themes/apollo-light-color-theme.json` are deterministic generated outputs. Change `scripts/generate.py` for mapping changes, then regenerate. Both files under `palette/` are fixed snapshots and must remain byte-for-byte canonical.

## License

[MIT](LICENSE). Copyright (c) 2026 D0n9X1n.
