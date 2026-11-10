<h1 align="center">Apple Terminal Apollo Themes</h1>

<p align="center">Apollo pairs a near-black, warm-contrast dark profile with Apollo Light's warm paper canvas for Apple Terminal.</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-apple-terminal"><img alt="Preview" src="https://img.shields.io/badge/preview-explore-fabd2f?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&amp;style=for-the-badge&amp;label=CI&amp;labelColor=141617&amp;color=b8bb26"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/releases?q=apple-terminal-v"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/apollo-theme/apollo-theme?filter=apple-terminal-v*&amp;display_name=tag&amp;sort=semver&amp;style=for-the-badge&amp;label=release&amp;labelColor=141617&amp;color=d3869b"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-83a598?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://support.apple.com/guide/terminal/welcome/mac"><img alt="Target: Apple Terminal on macOS" src="https://img.shields.io/badge/target-Apple%20Terminal%20%C2%B7%20macOS-fb4934?style=for-the-badge&amp;labelColor=141617"></a>
  <a href="https://github.com/apollo-theme/apollo-theme/blob/main/palette/apollo.json"><img alt="Canonical Apollo palette" src="https://img.shields.io/badge/palette-canonical-8ec07c?style=for-the-badge&amp;labelColor=141617"></a>
</p>

<p align="center">
  <a href="https://apollo-theme.github.io/#app-apple-terminal"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/apple-terminal.svg" alt="Simulated dark Apollo preview for Apple Terminal"></a>
  <a href="https://apollo-theme.github.io/#app-apple-terminal-light"><img src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/apple-terminal-light.svg" alt="Simulated Apollo Light preview for Apple Terminal"></a>
</p>
<p align="center"><sub><strong>Simulated previews.</strong> Rendered output may vary by font and platform.</sub></p>

**Apollo Dark** is the public name for the existing unsuffixed **Apollo** compatibility profile in `Apollo.terminal`; its native profile name remains **Apollo**. **Apollo Light** keeps its `Apollo Light.terminal` identity. `Apollo Light.terminal` is additive and imports as a separate **Apollo Light** profile without changing the existing default or open windows.

## Install

Clone the Apollo Theme repository once; the command is safe to rerun:

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
```

The profiles are then at `~/.config/apollo-theme/apple-terminal/Apollo.terminal` (Apollo Dark) and `~/.config/apollo-theme/apple-terminal/Apollo Light.terminal` (Apollo Light). To skip the clone, download a single file instead:

- https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/apple-terminal/Apollo.terminal
- https://raw.githubusercontent.com/apollo-theme/apollo-theme/main/apple-terminal/Apollo%20Light.terminal

Then import one or both profiles, either from **Terminal → Settings → Profiles → … → Import…** or by opening the files:

```sh
open "$HOME/.config/apollo-theme/apple-terminal/Apollo.terminal"
open "$HOME/.config/apollo-theme/apple-terminal/Apollo Light.terminal"
```

Each import adds a theme-only profile. It sets no shell command and does not modify the current or default profile.

## Activate

Select **Apollo** for dark or **Apollo Light** for light in **Terminal → Settings → Profiles**. Click **Default** only if new windows should use that profile. Existing windows are unchanged; open a new window to inspect the choice.

## Uninstall

Choose another default first if necessary, select **Apollo** and/or **Apollo Light**, and click the minus button. Removing a profile does not change open windows or the other variant.

## Visual check

Open new windows for both profiles and inspect normal, bold, selected, and cursor text plus ANSI colors 0–15. Dark Apollo should retain foreground `#cfbc97`, cursor `#fabd2f`, and canvas `#141617`. Apollo Light should use foreground `#3c3836`, cursor `#8a5200`, and canvas `#f9f5d7`. Verify readable selection and exact ordered terminal slots against the matching palette. A useful ANSI preview is:

```sh
for n in $(seq 0 15); do printf '\033[48;5;%sm %2s \033[0m' "$n" "$n"; done; printf '\n'
```

## Development

- `palette/apollo.json` → `Apollo.terminal` (dark, compatibility-preserving)
- `palette/apollo-light.json` → `Apollo Light.terminal` (light)

```sh
python3 scripts/generate.py
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
plutil -lint Apollo.terminal "Apollo Light.terminal" # macOS
```

Generation and checks never import profiles or modify Terminal preferences.

## License

[MIT](LICENSE)
