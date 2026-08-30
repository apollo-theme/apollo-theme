<div align="center">

# Apollo Theme

**Two appearances. One color system. Every tool that matters.**

[![Preview](https://img.shields.io/badge/preview-live-fabd2f?style=for-the-badge&labelColor=141617)](https://apollo-theme.github.io/)
[![Integrations](https://img.shields.io/badge/integrations-17-d5c4a1?style=for-the-badge&labelColor=141617)](#integrations)
[![Appearances](https://img.shields.io/badge/appearances-dark%20%2B%20light-8a5200?style=for-the-badge&labelColor=f9f5d7)](#signal-palettes)
[![CI](https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&style=for-the-badge&label=build&labelColor=141617)](https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/apollo-theme/apollo-theme?style=for-the-badge&labelColor=141617&color=83a598)](https://github.com/apollo-theme/apollo-theme/releases/latest)
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

*Simulated previews — explore Apollo Dark and Apollo Light across all 17 integrations.*

</div>

Apollo is a high-contrast color system with dark and light appearances, built for sharp focus and a workspace that feels continuous from terminal to editor. Existing unsuffixed `Apollo` / `apollo` files, selectors, packages, and activation paths remain Apollo Dark compatibility identities; the additive light appearance is `Apollo Light` / `apollo-light`.

## Signal palettes

| Appearance | Canvas | Surface | Text | Focus | Selection | Error | Success | Info |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Apollo Dark** | `#141617` | `#1d2021` | `#cfbc97` | `#fabd2f` | `#3c3836` | `#fb4934` | `#b8bb26` | `#83a598` |
| **Apollo Light** | `#f9f5d7` | `#fbf1c7` | `#3c3836` | `#8a5200` | `#ebdbb2` | `#9d0006` | `#6b6700` | `#076678` |

The machine-readable sources are [`palette/apollo.json`](palette/apollo.json) and [`palette/apollo-light.json`](palette/apollo-light.json). Every application repository carries exact snapshots and deterministic native adapters for both.

## Integrations

| Flight deck | Applications |
| --- | --- |
| **Terminals** | [SonicTerm](sonicterm-apollo-theme) · [WezTerm](wezterm-apollo-theme) · [iTerm2](iterm2-apollo-theme) · [Apple Terminal](apple-terminal-apollo-theme) · [Alacritty](alacritty-apollo-theme) · [Windows Terminal](windows-terminal-apollo-theme) |
| **Editors & IDEs** | [Visual Studio Code](vscode-apollo-theme) · [Visual Studio](visual-studio-apollo-theme) · [Vim](vim-apollo-theme) · [Neovim](nvim-apollo-theme) · [Xcode](xcode-apollo-theme) |
| **Shell & CLI** | [PowerShell](powershell-apollo-theme) · [tmux](tmux-apollo-theme) · [RMUX](rmux-apollo-theme) · [bat](bat-apollo-theme) · [eza](eza-apollo-theme) |
| **Browser** | [Firefox](firefox-apollo-theme) |

Each child is an independent public repository with its own installation guide, generated Dark and Light artifacts, tests, CI, and release history. See the [live preview](https://apollo-theme.github.io/) before choosing an integration.

## Clone the whole constellation

```sh
git clone --recurse-submodules https://github.com/apollo-theme/apollo-theme.git
cd apollo-theme
python3 scripts/generate.py --check
python3 scripts/check.py
python3 -m unittest discover -s tests -v
```

On a development machine with target applications installed:

```sh
python3 scripts/check.py --native
```

Refresh an existing checkout:

```sh
git pull --ff-only
git submodule update --init --recursive
```

## Repository map

The 17 `*-apollo-theme/` paths are application repositories. Two management repositories are also synchronized here:

- [`apollo-theme.github.io/`](apollo-theme.github.io) — organization website and preview SVG source.
- [`.github/organization/`](.github/organization/profile/README.md) — the single-file GitHub organization profile repository.

Read [`CLAUDE.md`](CLAUDE.md) for generation, validation, and child-first release ordering.

## Lineage

Apollo stands on excellent prior art. Thanks to **Gruvbox** for its enduring color language and **SonicTerm** for the high-contrast terminal palette that became Apollo’s starting point. Exact provenance is recorded in [`NOTICE`](NOTICE) and the canonical palette.

This project is not related to the separate 46-color pixel-art palette also named Apollo.

## License

MIT
