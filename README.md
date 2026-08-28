<h1 align="center">iTerm2 Apollo Theme</h1>

<p align="center">Apollo brings a near-black canvas, warm contrast, and vivid terminal colors to iTerm2.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-iterm2"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/iterm2-apollo-theme/actions/workflows/check.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/iterm2-apollo-theme/check.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/iterm2-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/iterm2-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/iterm2-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://iterm2.com/"><img alt="Target: iTerm2 on macOS" src="https://img.shields.io/badge/target-iTerm2%20%C2%B7%20macOS-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-iterm2"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/iterm2.svg" alt="Simulated Apollo preview for iTerm2"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Rendered output may vary by font and platform.</sub></p>

## Install and activate

1. Download [`Apollo.itermcolors`](https://github.com/apollo-theme/iterm2-apollo-theme/raw/main/Apollo.itermcolors).
2. In iTerm2, open **Settings → Profiles → Colors**.
3. Open **Color Presets… → Import…** and choose `Apollo.itermcolors`.
4. Open **Color Presets…** again and select **Apollo**.

## Visual inspection

Open a fresh profile and check normal, bold, selected, and cursor text plus ANSI colors 0–15. Foreground should be `#cfbc97`, the cursor `#fabd2f`, and the canvas `#141617`; selected text must remain readable. A useful ANSI preview is:

```sh
for n in $(seq 0 15); do printf '\033[48;5;%sm %2s \033[0m' "$n" "$n"; done; printf '\n'
```

## Uninstall

In **Settings → Profiles → Colors → Color Presets…**, choose **Delete Preset…**, select **Apollo**, and confirm. Existing profiles retain their current colors until changed.

## Development

The committed theme is generated from `palette/apollo.json` using only Python's standard library.

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.ItermThemeTests.test_required_color_roles -v
```

## License

[MIT](LICENSE)
