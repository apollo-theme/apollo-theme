<h1 align="center">Xcode Apollo Theme</h1>

<p align="center">Apollo brings warm, high-contrast dark and light palettes to Xcode 26 for readable source, markup, debugger output, and status feedback.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-xcode"><img alt="Preview" src="https://img.shields.io/badge/Preview-open-fabd2f?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/xcode-apollo-theme/actions/workflows/check.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/xcode-apollo-theme/check.yml?branch=main&amp;style=flat-square&amp;label=CI&amp;color=b8bb26&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/xcode-apollo-theme/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/apollo-theme/xcode-apollo-theme?style=flat-square&amp;label=Release&amp;color=83a598&amp;labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-8ec07c?style=flat-square&amp;labelColor=141617"></a>
  <a href="https://developer.apple.com/xcode/"><img alt="Target: Xcode 26" src="https://img.shields.io/badge/target-Xcode%2026-d3869b?style=flat-square&amp;labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-fabd2f?style=flat-square&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-xcode"><img alt="Simulated preview of Apollo in Xcode" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/xcode.svg" width="960"></a>
  <a href="https://apollo-theme.github.io/#app-xcode-light"><img alt="Simulated preview of Apollo Light in Xcode" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/xcode-light.svg" width="960"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Xcode chrome and typography may vary; inspect the installed native theme using the checks below.</sub></p>

The public **Apollo Dark** variant keeps the existing unsuffixed identity in `Apollo.xccolortheme`; **Apollo Light** keeps its existing light identity in `Apollo Light.xccolortheme`.

## Coverage

- Xcode 26 source, markup, and debugger-console surfaces.
- Selection, current line, insertion point, warnings, errors, and runtime issues.
- Twenty-eight syntax roles following the installed Xcode 26 theme schema.
- A generated native color-theme plist that does not edit Xcode preferences.

## Install and activate

Quit Xcode, then install the theme:

```sh
mkdir -p ~/Library/Developer/Xcode/UserData/FontAndColorThemes
cp Apollo.xccolortheme "Apollo Light.xccolortheme" ~/Library/Developer/Xcode/UserData/FontAndColorThemes/
```

Open Xcode and select **Settings → Themes → Apollo** or **Apollo Light**. The file adds a color theme only; it does not edit Xcode preferences.

## Visual verification

Inspect Swift, Objective-C/C, strings, numbers, comments, documentation comments, types, functions, macros, and URLs. Also inspect the debugger console, selection, current line, insertion point, warnings, errors, and runtime issues. Apollo source should be `#cfbc97` on `#141617`; Apollo Light should be `#3c3836` on `#f9f5d7`. In both, verify comments, warnings/errors, markup, and debugger colors remain readable and semantically distinct.

## Uninstall

Quit Xcode and remove the theme file:

```sh
rm ~/Library/Developer/Xcode/UserData/FontAndColorThemes/Apollo.xccolortheme \
  ~/Library/Developer/Xcode/UserData/FontAndColorThemes/'Apollo Light.xccolortheme'
```

Reopen Xcode and choose another theme if needed.

## Develop and validate

Both committed themes are generated from their matching palette snapshots using only Python's standard library. Their 28 syntax roles mirror the installed Xcode 26 theme schema.

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.XcodeThemeTests.test_xcode_26_syntax_role_map -v
plutil -lint Apollo.xccolortheme "Apollo Light.xccolortheme"
```

## License

[MIT](LICENSE). Copyright (c) 2026 D0n9X1n.
