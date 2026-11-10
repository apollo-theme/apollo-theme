<h1 align="center">WezTerm Apollo Themes</h1>

<p align="center">Apollo pairs a near-black, warm-contrast dark scheme with Apollo Light's warm paper canvas for WezTerm.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-wezterm"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/releases?q=wezterm-v"><img alt="Latest WezTerm release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter=wezterm-v*&amp;display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://wezterm.org/"><img alt="Target: WezTerm on multiple platforms" src="https://img.shields.io/badge/target-WezTerm%20%C2%B7%20cross--platform-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-wezterm"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/wezterm.svg" alt="Simulated dark Apollo preview for WezTerm"></a>
  <a href="https://apollo-theme.github.io/#app-wezterm-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/wezterm-light.svg" alt="Simulated Apollo Light preview for WezTerm"></a>
</p>
<p align="center"><sub><strong>Simulated previews.</strong> Rendered output may vary by font and platform.</sub></p>

**Apollo Dark** is the public name for the existing unsuffixed **Apollo** compatibility scheme in `apollo.toml`. **Apollo Light** is additive in `apollo-light.toml`; the included `wezterm.lua` intentionally continues to activate Apollo Dark, and existing `'Apollo'` activations are unchanged.

## Install

On Unix-like systems, clone the Apollo Theme repository once, then copy either scheme or both:

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
mkdir -p ~/.config/wezterm/colors
cp "$HOME/.config/apollo-theme/wezterm/apollo.toml" ~/.config/wezterm/colors/apollo.toml
cp "$HOME/.config/apollo-theme/wezterm/apollo-light.toml" ~/.config/wezterm/colors/apollo-light.toml
```

On Windows, copy the same two files from the `wezterm` folder of the clone to the `colors` directory beside `wezterm.exe`.

WezTerm reads the copies, so the clone can be deleted after copying if no other Apollo app uses it.

## Activate

Add exactly one name to your `wezterm.lua`:

```lua
config.color_scheme = 'Apollo'       -- Apollo Dark
```

or:

```lua
config.color_scheme = 'Apollo Light' -- Apollo Light
```

Reload the configuration or restart WezTerm.

## Uninstall

Select another `color_scheme`, reload, then remove the copied file for each variant you installed:

```sh
rm ~/.config/wezterm/colors/apollo.toml        # Apollo Dark
rm ~/.config/wezterm/colors/apollo-light.toml  # Apollo Light
```

Removing one variant does not affect the other.

## Visual check

For both variants, print ANSI colors 0–15, move the cursor over differently colored text, and select those cells. Apollo Dark should retain its `#141617` canvas and 50%-alpha grey-brown selection. Apollo Light should use the `#f9f5d7` canvas and opaque `#ebdbb2` selection. Both must preserve each selected cell's foreground (`selection_fg = "none"`) and match the ordered arrays in their palette snapshot. Native loading and TOML checks do not replace rendered-pixel inspection.

## Development

This app lives in the [`wezterm/`](https://github.com/apollo-theme/apollo-theme/tree/main/wezterm) folder of the Apollo Theme repository. Both schemes are generated from its pinned palette snapshots:

- `palette/apollo.json` → `apollo.toml` (Apollo Dark, compatibility-preserving)
- `palette/apollo-light.json` → `apollo-light.toml` (Apollo Light)

Run from `wezterm/`:

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Generation and checks never modify WezTerm preferences.

## License

[MIT](LICENSE)
