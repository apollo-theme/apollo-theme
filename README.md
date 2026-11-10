<div align="center">

# Apollo Theme

**Two appearances. One color system. Every tool that matters.**

[![Preview](https://img.shields.io/badge/preview-live-fabd2f?style=for-the-badge&labelColor=141617)](https://apollo-theme.github.io/)
[![Integrations](https://img.shields.io/badge/integrations-17-d5c4a1?style=for-the-badge&labelColor=141617)](#integrations)
[![Appearances](https://img.shields.io/badge/appearances-dark%20%2B%20light-8a5200?style=for-the-badge&labelColor=f9f5d7)](#signal-palettes)
[![CI](https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&style=for-the-badge&label=build&labelColor=141617)](https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/apollo-theme/apollo-theme?style=for-the-badge&labelColor=141617&color=b8bb26)](LICENSE)

<table>
<tr>
<th>Apollo Dark</th>
<th>Apollo Light</th>
</tr>
<tr>
<td><a href="https://apollo-theme.github.io/#app-sonicterm-dark"><img alt="Apollo Dark simulated SonicTerm preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg" width="440"></a></td>
<td><a href="https://apollo-theme.github.io/#app-sonicterm-light"><img alt="Apollo Light simulated SonicTerm preview" src="https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm-light.svg" width="440"></a></td>
</tr>
</table>

*Simulated previews — explore Apollo Dark and Apollo Light across all 17 integrations on the [preview site](https://apollo-theme.github.io/).*

</div>

Apollo is a high-contrast color system with dark and light appearances, built for sharp focus and a workspace that feels continuous from terminal to editor. Every integration ships both Apollo Dark and Apollo Light. Existing unsuffixed `Apollo` / `apollo` files, selectors, packages, and activation paths remain Apollo Dark compatibility identities; the additive light appearance is `Apollo Light` / `apollo-light`.

## Signal palettes

| Appearance | Canvas | Surface | Text | Focus | Selection | Error | Success | Info |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Apollo Dark** | `#141617` | `#1d2021` | `#cfbc97` | `#fabd2f` | `#3c3836` | `#fb4934` | `#b8bb26` | `#83a598` |
| **Apollo Light** | `#f9f5d7` | `#fbf1c7` | `#3c3836` | `#8a5200` | `#ebdbb2` | `#9d0006` | `#6b6700` | `#076678` |

The canonical palettes — and why and how each color was picked — live in [apollo-theme/apollo-palette](https://github.com/apollo-theme/apollo-palette). This repository carries a pinned copy in [`palette/apollo.json`](palette/apollo.json) and [`palette/apollo-light.json`](palette/apollo-light.json); [`palette/SOURCE.json`](palette/SOURCE.json) records the apollo-palette commit and checksums. Every app folder carries exact snapshots of both and a deterministic native adapter.

## Integrations

| App | Folder | Platform | Preview images | Live preview |
| --- | --- | --- | --- | --- |
| **SonicTerm** | [`sonicterm/`](https://github.com/apollo-theme/apollo-theme/tree/main/sonicterm) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm-light.svg) | [Dark](https://apollo-theme.github.io/#app-sonicterm-dark) · [Light](https://apollo-theme.github.io/#app-sonicterm-light) |
| **Windows Terminal** | [`windows-terminal/`](https://github.com/apollo-theme/apollo-theme/tree/main/windows-terminal) | Windows | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/windows-terminal.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/windows-terminal-light.svg) | [Dark](https://apollo-theme.github.io/#app-windows-terminal-dark) · [Light](https://apollo-theme.github.io/#app-windows-terminal-light) |
| **Firefox** | [`firefox/`](https://github.com/apollo-theme/apollo-theme/tree/main/firefox) | Browser | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/firefox.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/firefox-light.svg) | [Dark](https://apollo-theme.github.io/#app-firefox-dark) · [Light](https://apollo-theme.github.io/#app-firefox-light) |
| **Visual Studio Code** | [`vscode/`](https://github.com/apollo-theme/apollo-theme/tree/main/vscode) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vscode.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vscode-light.svg) | [Dark](https://apollo-theme.github.io/#app-vscode-dark) · [Light](https://apollo-theme.github.io/#app-vscode-light) |
| **Visual Studio** | [`visual-studio/`](https://github.com/apollo-theme/apollo-theme/tree/main/visual-studio) | Windows | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/visual-studio.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/visual-studio-light.svg) | [Dark](https://apollo-theme.github.io/#app-visual-studio-dark) · [Light](https://apollo-theme.github.io/#app-visual-studio-light) |
| **Vim** | [`vim/`](https://github.com/apollo-theme/apollo-theme/tree/main/vim) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vim.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/vim-light.svg) | [Dark](https://apollo-theme.github.io/#app-vim-dark) · [Light](https://apollo-theme.github.io/#app-vim-light) |
| **Neovim** | [`nvim/`](https://github.com/apollo-theme/apollo-theme/tree/main/nvim) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/nvim.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/nvim-light.svg) | [Dark](https://apollo-theme.github.io/#app-nvim-dark) · [Light](https://apollo-theme.github.io/#app-nvim-light) |
| **Xcode** | [`xcode/`](https://github.com/apollo-theme/apollo-theme/tree/main/xcode) | macOS | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/xcode.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/xcode-light.svg) | [Dark](https://apollo-theme.github.io/#app-xcode-dark) · [Light](https://apollo-theme.github.io/#app-xcode-light) |
| **tmux** | [`tmux/`](https://github.com/apollo-theme/apollo-theme/tree/main/tmux) | Terminal | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/tmux.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/tmux-light.svg) | [Dark](https://apollo-theme.github.io/#app-tmux-dark) · [Light](https://apollo-theme.github.io/#app-tmux-light) |
| **RMUX** | [`rmux/`](https://github.com/apollo-theme/apollo-theme/tree/main/rmux) | Terminal | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/rmux.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/rmux-light.svg) | [Dark](https://apollo-theme.github.io/#app-rmux-dark) · [Light](https://apollo-theme.github.io/#app-rmux-light) |
| **PowerShell** | [`powershell/`](https://github.com/apollo-theme/apollo-theme/tree/main/powershell) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/powershell.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/powershell-light.svg) | [Dark](https://apollo-theme.github.io/#app-powershell-dark) · [Light](https://apollo-theme.github.io/#app-powershell-light) |
| **bat** | [`bat/`](https://github.com/apollo-theme/apollo-theme/tree/main/bat) | CLI | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/bat.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/bat-light.svg) | [Dark](https://apollo-theme.github.io/#app-bat-dark) · [Light](https://apollo-theme.github.io/#app-bat-light) |
| **eza** | [`eza/`](https://github.com/apollo-theme/apollo-theme/tree/main/eza) | CLI | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/eza.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/eza-light.svg) | [Dark](https://apollo-theme.github.io/#app-eza-dark) · [Light](https://apollo-theme.github.io/#app-eza-light) |
| **WezTerm** | [`wezterm/`](https://github.com/apollo-theme/apollo-theme/tree/main/wezterm) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/wezterm.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/wezterm-light.svg) | [Dark](https://apollo-theme.github.io/#app-wezterm-dark) · [Light](https://apollo-theme.github.io/#app-wezterm-light) |
| **iTerm2** | [`iterm2/`](https://github.com/apollo-theme/apollo-theme/tree/main/iterm2) | macOS | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/iterm2.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/iterm2-light.svg) | [Dark](https://apollo-theme.github.io/#app-iterm2-dark) · [Light](https://apollo-theme.github.io/#app-iterm2-light) |
| **Apple Terminal** | [`apple-terminal/`](https://github.com/apollo-theme/apollo-theme/tree/main/apple-terminal) | macOS | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/apple-terminal.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/apple-terminal-light.svg) | [Dark](https://apollo-theme.github.io/#app-apple-terminal-dark) · [Light](https://apollo-theme.github.io/#app-apple-terminal-light) |
| **Alacritty** | [`alacritty/`](https://github.com/apollo-theme/apollo-theme/tree/main/alacritty) | Cross-platform | [Dark](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/alacritty.svg) · [Light](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/alacritty-light.svg) | [Dark](https://apollo-theme.github.io/#app-alacritty-dark) · [Light](https://apollo-theme.github.io/#app-alacritty-light) |

Each folder is self-contained: its own README with installation steps, generated Dark and Light artifacts, generator, tests, and CI job. See the [live preview site](https://apollo-theme.github.io/) before choosing an integration.

## One shared clone

Vim, Neovim, tmux, RMUX, PowerShell, bat, and eza read their theme straight from a single clone of this repository at `~/.config/apollo-theme`. Every install guide starts with the same idempotent line, so running it twice — or for several apps — is safe:

```sh
[ -d "$HOME/.config/apollo-theme/.git" ] || git clone https://github.com/apollo-theme/apollo-theme "$HOME/.config/apollo-theme"
```

Update every clone-based theme at once with `git -C ~/.config/apollo-theme pull --ff-only`. Copy and import apps (terminals, Xcode, Visual Studio) take their files from the same clone, Visual Studio Code is packaged locally from it, and Firefox builds are downloaded from the [Firefox releases](https://github.com/apollo-theme/apollo-theme/releases?q=firefox-v).

## Development

```sh
git clone https://github.com/apollo-theme/apollo-theme.git
cd apollo-theme
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

Limit generation or validation to one app with `--app <slug>`, for example `python3 scripts/check.py --app vscode`. Every folder also works on its own: `cd vscode && python3 scripts/generate.py --check`. On a machine with the target applications installed, `python3 scripts/check.py --native` adds each app's native checks.

Pull a new palette from a local apollo-palette checkout at a tag, branch, or commit. The script copies both palettes into the root and every app folder, rewrites `palette/SOURCE.json`, and regenerates every app; then validate:

```sh
python3 scripts/sync_palette.py ../apollo-palette <ref>
python3 scripts/generate.py --check
python3 scripts/check.py
```

## Releases

Each app is released independently with a tag of the form `<slug>-vX.Y.Z`, for example `firefox-v1.1.1`. Pushing a `firefox-v*` tag publishes the Firefox release through CI. Filter the [releases page](https://github.com/apollo-theme/apollo-theme/releases) by an app's prefix to see its history.

## Lineage

Apollo stands on excellent prior art. Thanks to **Gruvbox** for its enduring color language and **SonicTerm** for the high-contrast terminal palette that became Apollo’s starting point. Exact provenance is recorded in [`NOTICE`](NOTICE) and the canonical palette.

This project is not related to the separate 46-color pixel-art palette also named Apollo.

## License

MIT
