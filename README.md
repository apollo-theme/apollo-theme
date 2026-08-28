<h1 align="center">WezTerm Apollo Theme</h1>

<p align="center">Apollo brings a near-black canvas, warm contrast, and vivid terminal colors to WezTerm.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-wezterm"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/wezterm-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/wezterm-apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/wezterm-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/wezterm-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/wezterm-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://wezterm.org/"><img alt="Target: WezTerm on multiple platforms" src="https://img.shields.io/badge/target-WezTerm%20%C2%B7%20cross--platform-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-wezterm"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/wezterm.svg" alt="Simulated Apollo preview for WezTerm"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Rendered output may vary by font and platform.</sub></p>

## Install and activate

On Unix-like systems:

```sh
mkdir -p ~/.config/wezterm/colors
cp apollo.toml ~/.config/wezterm/colors/apollo.toml
```

On Windows, copy `apollo.toml` to the `colors` directory beside `wezterm.exe`. Then add this to `wezterm.lua` (the included `wezterm.lua` is a minimal example):

```lua
config.color_scheme = 'Apollo'
```

Reload the configuration or restart WezTerm.

## Uninstall

Select another `color_scheme`, reload, then remove the copied `apollo.toml`.

## Visual check

Print ANSI colors 0–15, move the cursor over text, and select differently colored cells. Confirm the `#141617` canvas, warm foreground, yellow cursor, a 50%-alpha grey-brown selection that preserves each cell's foreground, and the exact normal/bright arrays in `palette/apollo.json`. Automated checks validate the TOML and installed WezTerm can load it, but rendered pixels still require this manual check.

## Development

The committed `apollo.toml` is generated from the pinned palette snapshot at `palette/apollo.json`.

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
