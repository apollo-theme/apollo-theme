<h1 align="center">SonicTerm Apollo Themes</h1>

<p align="center">Apollo pairs a near-black, warm-contrast dark theme with Apollo Light's warm paper canvas for SonicTerm.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-sonicterm"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/sonicterm-apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/sonicterm-apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/sonicterm-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/sonicterm-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/sonicterm-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/D0n9X1n/SonicTerm"><img alt="Target: SonicTerm on macOS, Windows, and Linux" src="https://img.shields.io/badge/target-SonicTerm%20%C2%B7%20cross--platform-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-sonicterm"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg" alt="Simulated dark Apollo preview for SonicTerm"></a>
  <a href="https://apollo-theme.github.io/#app-sonicterm-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm-light.svg" alt="Simulated Apollo Light preview for SonicTerm"></a>
</p>
<p align="center"><sub><strong>Simulated previews.</strong> Rendered output may vary by font and platform.</sub></p>

`Apollo` and `apollo.toml` remain the existing dark theme. `Apollo Light` is additive and lives in `apollo-light.toml`; existing installations and activation settings are unchanged.

## Install

Install either theme or both:

```sh
mkdir -p ~/.sonicterm/themes
cp apollo.toml ~/.sonicterm/themes/apollo.toml
cp apollo-light.toml ~/.sonicterm/themes/apollo-light.toml
```

## Activate

Set exactly one theme in `~/.sonicterm/sonicterm.toml`:

```toml
# Existing dark theme
theme = "apollo"
```

or:

```toml
# Light theme
theme = "apollo-light"
```

Start SonicTerm, or run **Reload Config** in an existing session.

## Uninstall

Select another installed theme, reload the configuration, then remove the corresponding file:

```sh
rm ~/.sonicterm/themes/apollo.toml        # dark Apollo
rm ~/.sonicterm/themes/apollo-light.toml  # Apollo Light
```

Removing one variant does not affect the other.

## Visual check

For each installed variant, open tabs in active, inactive, and hover states, select text, and print ANSI colors 0–15. Dark Apollo should retain its `#141617` canvas and yellow cursor. Apollo Light should use the `#f9f5d7` paper canvas, dark `#3c3836` text, and brown `#8a5200` cursor. In both, confirm readable cursor and selection text plus the exact ordered normal/bright arrays in the matching palette snapshot. Automated checks validate files and values, not rendered pixels.

## Development

Both native files are generated from pinned snapshots:

- `palette/apollo.json` → `apollo.toml` (dark, compatibility-preserving)
- `palette/apollo-light.json` → `apollo-light.toml` (light)

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Generation and checks never modify SonicTerm preferences.

## License

[MIT](LICENSE)
