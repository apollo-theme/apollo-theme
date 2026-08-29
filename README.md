<h1 align="center">iTerm2 Apollo Themes</h1>

<p align="center">Apollo pairs a near-black, warm-contrast dark preset with Apollo Light's warm paper canvas for iTerm2.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-iterm2"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/iterm2-apollo-theme/actions/workflows/check.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/iterm2-apollo-theme/check.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/iterm2-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/iterm2-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/iterm2-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://iterm2.com/"><img alt="Target: iTerm2 on macOS" src="https://img.shields.io/badge/target-iTerm2%20%C2%B7%20macOS-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-iterm2"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/iterm2.svg" alt="Simulated dark Apollo preview for iTerm2"></a>
  <a href="https://apollo-theme.github.io/#app-iterm2-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/iterm2-light.svg" alt="Simulated Apollo Light preview for iTerm2"></a>
</p>
<p align="center"><sub><strong>Simulated previews.</strong> Rendered output may vary by font and platform.</sub></p>

`Apollo.itermcolors` remains the existing dark preset named **Apollo**. `Apollo Light.itermcolors` is additive; importing it creates the separate **Apollo Light** preset and does not change existing profiles.

## Install

1. Download `Apollo.itermcolors`, `Apollo Light.itermcolors`, or both.
2. In iTerm2, open **Settings → Profiles → Colors**.
3. Open **Color Presets… → Import…** and choose each desired file.

Importing presets does not activate them or modify current profile colors.

## Activate

Open **Settings → Profiles → Colors → Color Presets…**, then choose **Apollo** for dark or **Apollo Light** for light. Apply the choice separately to each profile that should use it.

## Uninstall

Open **Settings → Profiles → Colors → Color Presets… → Delete Preset…**, select **Apollo** and/or **Apollo Light**, and confirm. Existing profiles retain their current copied colors until changed.

## Visual check

For each preset, open a fresh profile and inspect normal, bold, selected, and cursor text plus ANSI colors 0–15. Dark Apollo should retain foreground `#cfbc97`, cursor `#fabd2f`, and canvas `#141617`. Apollo Light should use foreground `#3c3836`, cursor `#8a5200`, and canvas `#f9f5d7`. Selection must remain readable and follow the matching palette's alpha. A useful ANSI preview is:

```sh
for n in $(seq 0 15); do printf '\033[48;5;%sm %2s \033[0m' "$n" "$n"; done; printf '\n'
```

## Development

- `palette/apollo.json` → `Apollo.itermcolors` (dark, compatibility-preserving)
- `palette/apollo-light.json` → `Apollo Light.itermcolors` (light)

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
plutil -lint Apollo.itermcolors "Apollo Light.itermcolors" # macOS
```

Generation and checks never import presets or edit iTerm2 preferences.

## License

[MIT](LICENSE)
