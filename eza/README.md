<h1 align="center">eza Apollo Theme</h1>

<p align="center">Apollo gives eza warm, high-contrast file listings while preserving normal color-variable precedence.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-eza"><img alt="Preview" src="https://img.shields.io/badge/status-Preview-fabd2f?style=flat-square&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/eza-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/eza-apollo-theme/ci.yml?branch=main&style=flat-square&label=CI&labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/eza-apollo-theme/releases/latest"><img alt="Latest Release" src="https://img.shields.io/github/v/release/apollo-theme/eza-apollo-theme?display_name=tag&sort=semver&style=flat-square&label=Release&color=d3869b&labelColor=141617"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-b8bb26?style=flat-square&labelColor=141617"></a>
  <a href="https://github.com/eza-community/eza"><img alt="eza 0.23.5 or newer" src="https://img.shields.io/badge/eza-0.23.5%2B-83a598?style=flat-square&labelColor=141617"></a>
  <a href="palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=flat-square&labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-eza"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/eza.svg" alt="Simulated eza Apollo Dark preview"></a>
  <a href="https://apollo-theme.github.io/#app-eza-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/eza-light.svg" alt="Simulated eza Apollo Light preview"></a>
</p>
<p align="center"><em>Simulated preview. File metadata, terminal rendering, and color-variable overrides may vary.</em></p>

Apollo Dark preserves the root `theme.yml` and existing root configuration-directory selector for compatibility. Apollo Light is the explicit `light/theme.yml` companion. Both match eza's fixed filename within whichever `EZA_CONFIG_DIR` you select and style core file kinds, permissions, sizes, users, links, Git state, and metadata without replacing filename or extension mappings.

## Install

Clone Apollo into its own directory without replacing `~/.config/eza/theme.yml` or changing existing color variables:

```sh
git clone https://github.com/apollo-theme/eza-apollo-theme "$HOME/.config/eza-apollo-theme"
```

## Activate

Select the directory containing the variant's fixed `theme.yml`:

```sh
# Dark (root theme.yml)
EZA_CONFIG_DIR="$HOME/.config/eza-apollo-theme" eza --color=always -la

# Light (light/theme.yml)
EZA_CONFIG_DIR="$HOME/.config/eza-apollo-theme/light" eza --color=always -la
```

Export either directory to opt in for the current shell. Apollo Light styles eza output but cannot change the terminal itself, so use a light terminal canvas. No existing eza configuration or color variable is modified. Existing `LS_COLORS`, `EZA_COLORS`, and `EXA_COLORS` keep eza's normal precedence and may intentionally override either variant's file-kind colors.

## Uninstall

```sh
unset EZA_CONFIG_DIR
rm -rf "$HOME/.config/eza-apollo-theme"
```

## Visual check

Run either activation command in a directory containing folders, executable files, symlinks, and ordinary files. File-kind roles should be distinct on the matching terminal canvas. Existing `LS_COLORS` or `EZA_COLORS` may intentionally override these colors.

## Development

The native check uses a temporary `EZA_CONFIG_DIR` and verifies theme parsing, rendered file kinds, and `LS_COLORS` precedence with eza v0.23.5 or newer.

```sh
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Root `theme.yml` and `light/theme.yml` are deterministic generated outputs. Make mapping changes in `scripts/generate.py`, then regenerate rather than editing either theme directly.

## License

[MIT](LICENSE)
