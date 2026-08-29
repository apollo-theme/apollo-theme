<h1 align="center">Alacritty Apollo Themes</h1>

<p align="center">Apollo pairs a near-black, warm-contrast dark fragment with Apollo Light's warm paper canvas for Alacritty.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-alacritty"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/alacritty-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/alacritty-apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/alacritty-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/alacritty-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/alacritty-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://alacritty.org/"><img alt="Target: Alacritty on multiple platforms" src="https://img.shields.io/badge/target-Alacritty%20%C2%B7%20cross--platform-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-alacritty"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/alacritty.svg" alt="Simulated dark Apollo preview for Alacritty"></a>
  <a href="https://apollo-theme.github.io/#app-alacritty-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/alacritty-light.svg" alt="Simulated Apollo Light preview for Alacritty"></a>
</p>
<p align="center"><sub><strong>Simulated previews.</strong> Rendered output may vary by font and platform.</sub></p>

`apollo.toml` remains the existing dark Apollo fragment. `apollo-light.toml` adds Apollo Light without changing the dark filename, bytes, or activation path.

## Install

Install either fragment or both:

```sh
mkdir -p ~/.config/alacritty/themes
cp apollo.toml ~/.config/alacritty/themes/apollo.toml
cp apollo-light.toml ~/.config/alacritty/themes/apollo-light.toml
```

## Activate

Import exactly one variant from `~/.config/alacritty/alacritty.toml`:

```toml
[general]
import = ["~/.config/alacritty/themes/apollo.toml"] # existing dark Apollo
```

or:

```toml
[general]
import = ["~/.config/alacritty/themes/apollo-light.toml"] # Apollo Light
```

Alacritty reloads the configuration automatically; restart if reload is disabled.

## Uninstall

Remove the selected Apollo entry from `[general].import`, reload, then remove `apollo.toml` and/or `apollo-light.toml` from the themes directory. Removing one variant does not affect the other.

## Visual check

For each variant, print ANSI colors 0–15, move the cursor over text, and select differently colored text. Dark Apollo should retain `#141617`; Apollo Light should use `#f9f5d7`. Both should preserve selected-cell foreground through `CellForeground`, show a readable cursor, and match the ordered normal/bright palette arrays. The parser check validates the fragment, not rendered pixels.

## Development

- `palette/apollo.json` → `apollo.toml` (dark, compatibility-preserving)
- `palette/apollo-light.json` → `apollo-light.toml` (light)

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Generation and checks never edit Alacritty preferences.

## License

[MIT](LICENSE)
