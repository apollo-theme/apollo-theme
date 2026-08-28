<div align="center">

# Apollo Theme

**One color system. Every tool that matters.**

[![Preview](https://img.shields.io/badge/preview-live-fabd2f?style=for-the-badge&labelColor=141617)](https://apollo-theme.github.io/)
[![Integrations](https://img.shields.io/badge/integrations-17-d5c4a1?style=for-the-badge&labelColor=141617)](#integrations)
[![CI](https://img.shields.io/github/actions/workflow/status/apollo-theme/apollo-theme/ci.yml?branch=main&style=for-the-badge&label=build&labelColor=141617)](https://github.com/apollo-theme/apollo-theme/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/apollo-theme/apollo-theme?style=for-the-badge&labelColor=141617&color=83a598)](https://github.com/apollo-theme/apollo-theme/releases/latest)
[![License](https://img.shields.io/github/license/apollo-theme/apollo-theme?style=for-the-badge&labelColor=141617&color=b8bb26)](LICENSE)

[![Explore Apollo Theme](https://raw.githubusercontent.com/apollo-theme/apollo-theme.github.io/main/previews/sonicterm.svg)](https://apollo-theme.github.io/)

*Simulated preview — explore all 17 integrations on the live site.*

</div>

Apollo is a high-contrast dark color system built for long nights, sharp focus, and a workspace that feels continuous from terminal to editor. This repository is the canonical palette, synchronized catalog, and validation hub for the entire family.

## Signal palette

| Canvas | Surface | Text | Focus | Selection | Error | Success | Info |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `#141617` | `#1d2021` | `#cfbc97` | `#fabd2f` | `#3c3836` | `#fb4934` | `#b8bb26` | `#83a598` |

The machine-readable source is [`palette/apollo.json`](palette/apollo.json). Every application repository carries an exact snapshot and a deterministic native adapter.

## Integrations

| Flight deck | Applications |
| --- | --- |
| **Terminals** | [SonicTerm](sonicterm-apollo-theme) · [WezTerm](wezterm-apollo-theme) · [iTerm2](iterm2-apollo-theme) · [Apple Terminal](apple-terminal-apollo-theme) · [Alacritty](alacritty-apollo-theme) · [Windows Terminal](windows-terminal-apollo-theme) |
| **Editors & IDEs** | [Visual Studio Code](vscode-apollo-theme) · [Visual Studio](visual-studio-apollo-theme) · [Vim](vim-apollo-theme) · [Neovim](nvim-apollo-theme) · [Xcode](xcode-apollo-theme) |
| **Shell & CLI** | [PowerShell](powershell-apollo-theme) · [tmux](tmux-apollo-theme) · [RMUX](rmux-apollo-theme) · [bat](bat-apollo-theme) · [eza](eza-apollo-theme) |
| **Browser** | [Firefox](firefox-apollo-theme) |

Each child is an independent public repository with its own installation guide, generated artifact, tests, CI, and release history. See the [live preview](https://apollo-theme.github.io/) before choosing an integration.

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
