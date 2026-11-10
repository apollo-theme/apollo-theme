<h1 align="center">Windows Terminal Apollo Themes</h1>

<p align="center">Apollo pairs a near-black, warm-contrast dark scheme with Apollo Light's warm paper canvas for Windows Terminal.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-windows-terminal"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/windows-terminal-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/windows-terminal-apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/windows-terminal-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/windows-terminal-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/windows-terminal-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/microsoft/terminal"><img alt="Target: Windows Terminal on Windows" src="https://img.shields.io/badge/target-Windows%20Terminal%20%C2%B7%20Windows-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-windows-terminal"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/windows-terminal.svg" alt="Simulated dark Apollo preview for Windows Terminal"></a>
  <a href="https://apollo-theme.github.io/#app-windows-terminal-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/windows-terminal-light.svg" alt="Simulated Apollo Light preview for Windows Terminal"></a>
</p>
<p align="center"><sub><strong>Simulated previews.</strong> Rendered output may vary by font and platform.</sub></p>

**Apollo Dark** is the public name for the existing unsuffixed `apollo.json` compatibility scheme, whose native name remains **Apollo**. **Apollo Light** keeps its current `apollo-light.json` scheme identity; existing profile settings that name `Apollo` remain dark.

## Install

Open Windows Terminal **Settings**, choose **Open JSON file**, and paste the object from `apollo.json`, `apollo-light.json`, or both into the top-level `schemes` array. Do not replace the entire settings file.

## Activate

Set the desired profile or profile defaults to one of these exact names:

```json
"colorScheme": "Apollo"
```

or:

```json
"colorScheme": "Apollo Light"
```

Save the settings file; Windows Terminal reloads it.

## Uninstall

Select another `colorScheme`, then remove the scheme object whose `name` is `Apollo` and/or `Apollo Light` from the `schemes` array. Removing one variant does not affect the other.

## Visual check

For both schemes, print ANSI colors 0–15, move the cursor over text, and select text. Dark Apollo should retain `#141617`; Apollo Light should use `#f9f5d7`. Confirm readable foreground/cursor contrast and exact normal/bright slots from the matching palette. Windows Terminal schemes cannot express selection alpha or cursor-text color, so each selection color is emitted as the palette's opaque RGB value. JSON checks performed off Windows do not replace a rendered Windows Terminal check.

## Development

- `palette/apollo.json` → `apollo.json` (dark, compatibility-preserving)
- `palette/apollo-light.json` → `apollo-light.json` (light)

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Generation and checks never read or write Windows Terminal settings.

## License

[MIT](LICENSE)
