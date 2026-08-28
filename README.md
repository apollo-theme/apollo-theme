<h1 align="center">SonicTerm Apollo Theme</h1>

<p align="center">Apollo brings a near-black canvas, warm contrast, and vivid terminal colors to SonicTerm.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-sonicterm"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/sonicterm-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/sonicterm-apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/sonicterm-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/sonicterm-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/sonicterm-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/D0n9X1n/SonicTerm"><img alt="Target: SonicTerm on macOS" src="https://img.shields.io/badge/target-SonicTerm%20%C2%B7%20macOS-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-sonicterm"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg" alt="Simulated Apollo preview for SonicTerm"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Rendered output may vary by font and platform.</sub></p>

## Install and activate

```sh
mkdir -p ~/.sonicterm/themes
cp apollo.toml ~/.sonicterm/themes/apollo.toml
```

Set the theme in `~/.sonicterm/sonicterm.toml`:

```toml
theme = "apollo"
```

Start SonicTerm, or run **Reload Config** in an existing session.

## Uninstall

Select another theme in `~/.sonicterm/sonicterm.toml`, reload, then remove `~/.sonicterm/themes/apollo.toml`.

## Visual check

Open tabs in active, inactive, and hover states, select text, and print ANSI colors 0–15. Confirm a `#141617` canvas, yellow cursor/active tab, muted inactive labels, grey-brown selection, and the exact normal/bright palette in `palette/apollo.json`. Automated checks validate files and values, not rendered pixels.

## Development

The committed `apollo.toml` is generated from the pinned palette snapshot at `palette/apollo.json`.

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
