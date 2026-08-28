<h1 align="center">Apple Terminal Apollo Theme</h1>

<p align="center">Apollo brings a near-black canvas, warm contrast, and vivid terminal colors to Apple Terminal.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-apple-terminal"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apple-terminal-apollo-theme/actions/workflows/check.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apple-terminal-apollo-theme/check.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/apple-terminal-apollo-theme/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/apple-terminal-apollo-theme?display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="https://github.com/apollo-theme/apple-terminal-apollo-theme/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://support.apple.com/guide/terminal/welcome/mac"><img alt="Target: Apple Terminal on macOS" src="https://img.shields.io/badge/target-Apple%20Terminal%20%C2%B7%20macOS-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-apple-terminal"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/apple-terminal.svg" alt="Simulated Apollo preview for Apple Terminal"></a>
</p>
<p align="center"><sub><strong>Simulated preview.</strong> Rendered output may vary by font and platform.</sub></p>

## Install and activate

1. Download [`Apollo.terminal`](https://github.com/apollo-theme/apple-terminal-apollo-theme/raw/main/Apollo.terminal).
2. Double-click it, or in Terminal choose **Settings → Profiles → … → Import…**.
3. Select **Apollo** in **Settings → Profiles** and click **Default** if new windows should use it.
4. Existing windows are unchanged; open a new window to inspect the profile.

The import adds a theme profile only. It does not set a shell command or modify the currently selected profile.

## Visual inspection

Open a new Apollo window and check normal, bold, selected, and cursor text plus ANSI colors 0–15. Foreground should be `#cfbc97`, the cursor `#fabd2f`, and the canvas `#141617`; selected text must remain readable. A useful ANSI preview is:

```sh
for n in $(seq 0 15); do printf '\033[48;5;%sm %2s \033[0m' "$n" "$n"; done; printf '\n'
```

## Uninstall

Open **Terminal → Settings → Profiles**, select **Apollo**, and click the minus button. Choose another default profile first if Apollo is the default. Removing it does not change open windows.

## Development

The committed profile is generated from `palette/apollo.json` using deterministic, standard-library `plistlib` NSKeyedArchiver color data.

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest tests.test_theme.TerminalThemeTests.test_archived_colors_match_palette -v
```

## License

[MIT](LICENSE)
