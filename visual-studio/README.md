<h1 align="center">Visual Studio Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast dark and light palettes to Visual Studio 2022+ across the editor, environment chrome, and output surfaces.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-visual-studio"><img alt="Preview" src="https://img.shields.io/badge/Preview-open-fabd2f?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/visual-studio-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/visual-studio-apollo-theme/ci.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;color=b8bb26&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/visual-studio-apollo-theme/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/apollo-theme/visual-studio-apollo-theme?style=flat-square&amp;label=Release&amp;color=83a598&amp;labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-8ec07c?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://visualstudio.microsoft.com/"><img alt="Target: Visual Studio 2022+" src="https://img.shields.io/badge/target-Visual%20Studio%202022%2B-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-visual-studio"><img alt="Simulated preview of Apollo in Visual Studio" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/visual-studio.svg" width="960"></a>
  <a href="https://apollo-theme.github.io/#app-visual-studio-light"><img alt="Simulated preview of Apollo Light in Visual Studio" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/visual-studio-light.svg" width="960"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Application chrome and typography may vary; follow the visual checks below against the canonical palette.</sub></p>

> [!IMPORTANT]
> This repository ships native `themes/Apollo.vstheme` and `themes/Apollo Light.vstheme` sources and deliberately does **not** produce a VSIX. Use a temporary Color Theme Designer project to load either without inventing an unverified extension package.

The public **Apollo Dark** variant keeps the existing unsuffixed identity in `themes/Apollo.vstheme`; **Apollo Light** keeps its existing light identity in `themes/Apollo Light.vstheme`.

## Coverage

- Visual Studio 2022+ environment chrome and editor syntax.
- Diagnostics, active focus, search, selection, and current-statement cues.
- Command Window and Output Window categories.
- Deterministic generated output from the repository-owned palette snapshot.

## Install

1. Install [Visual Studio Color Theme Designer 2022](https://marketplace.visualstudio.com/items?itemName=idex.colorthemedesigner2022).
2. In Visual Studio 2022, create a temporary **VSTheme Project**.
3. Close the generated theme editor, replace that project's generated `.vstheme` file with `themes/Apollo.vstheme` or `themes/Apollo Light.vstheme`, and reopen it from Solution Explorer.
4. Choose **Preview** for a temporary check or **Apply** to make that variant available to the IDE.

The designer does not document a direct standalone-file import command. The temporary project is therefore required to load and apply this source `.vstheme` without fabricating a VSIX. Keep a backup/export of your previous environment settings if you want to restore custom colors exactly.

## Activate

After applying a theme, open **Tools > Options > Environment > General** and select **Apollo** or **Apollo Light** in the color-theme list. Restart Visual Studio if a tool window still caches old colors.

## Visual verification

Open a C# solution and verify:

- Apollo uses canvas `#141617` and text `#cfbc97`; Apollo Light uses paper `#f9f5d7` and text `#3c3836`.
- Keywords and syntax errors are red; strings and saved changes are green.
- Types and methods use gold `#fabd2f`; properties/information use blue; constants use magenta; namespaces use cyan.
- Active focus/search/current-statement cues use gold; selection uses dark brown without reducing text readability.
- Solution Explorer, tool windows, tabs, menus, status bar, Command Window, and Output Window remain legible.
- Normal interface/editor text never uses restricted `#665c54`.

## Uninstall or restore

Because this repository ships theme source rather than an installed extension, there is no Apollo entry in **Manage Extensions**. Select another color theme under **Tools > Options > Environment > General** to stop using Apollo, then delete the temporary VSTheme project if it is no longer needed.

## Develop and validate

Portable generation and checks:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
xmllint --noout --schema schemas/vstheme.xsd themes/Apollo.vstheme "themes/Apollo Light.vstheme"
```

Run one focused test with:

```sh
python3 -m unittest tests.test_theme.VisualStudioThemeTests.test_editor_status_colors_match_palette
```

On Windows, run the native .NET XML validation path:

```powershell
pwsh -File scripts/validate.ps1
```

Both portable and Windows paths run in CI. Both `.vstheme` files are deterministic generated outputs; change mappings in `scripts/generate.py` and regenerate. Both palette snapshots must remain byte-for-byte canonical.

## Why there is no VSIX

A correct Visual Studio theme VSIX needs a genuine extension/product identity, VSIX manifest, and Visual Studio SDK/MSBuild packaging project validated on Windows. No such identity or project was supplied, and inventing them would produce a misleading or unverified package. The native `.vstheme` is complete and loadable as source through a Color Theme Designer VSTheme project; Windows CI validates and stages it as the supported build artifact.

## License

[MIT](LICENSE). Copyright (c) 2026 D0n9X1n.
