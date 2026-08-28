<h1 align="center">Alacritty Apollo Theme</h1>

<p align="center">Apollo brings a near-black canvas, warm contrast, and vivid terminal colors to Alacritty.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-alacritty"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/alacritty-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/alacritty-apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/alacritty-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/alacritty-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/alacritty-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://alacritty.org/"><img alt="Target: Alacritty on multiple platforms" src="https://img.shields.io/badge/target-Alacritty%20%C2%B7%20cross--platform-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-alacritty"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/alacritty.svg" alt="Simulated Apollo preview for Alacritty"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Rendered output may vary by font and platform.</sub></p>

## Install and activate

```sh
mkdir -p ~/.config/alacritty/themes
cp apollo.toml ~/.config/alacritty/themes/apollo.toml
```

Import it from `~/.config/alacritty/alacritty.toml` using current Alacritty syntax:

```toml
[general]
import = ["~/.config/alacritty/themes/apollo.toml"]
```

Alacritty reloads the configuration automatically; restart if reload is disabled.

## Uninstall

Remove the Apollo entry from `[general].import`, then remove `~/.config/alacritty/themes/apollo.toml`.

## Visual check

Print ANSI colors 0–15, move the cursor over text, and select text. Confirm the `#141617` canvas, warm foreground, yellow cursor, preserved selected-text color, and the exact normal/bright palette in `palette/apollo.json`. Automated checks validate the importable fragment, not rendered pixels.

## Development

The committed `apollo.toml` is generated from the pinned palette snapshot at `palette/apollo.json`.

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
